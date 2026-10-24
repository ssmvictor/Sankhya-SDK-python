# -*- coding: utf-8 -*-
"""
Unit tests do worker do AsyncOnDemandRequestWrapper.

O comportamento esperado segue a referência .NET
(``Src/Sankhya/RequestWrappers/OnDemandRequestWrapper.cs``). A sincronização
com a task worker é feita por eventos; os timeouts só são atingidos quando o
comportamento esperado não ocorre (evitam travar a suíte).
"""

import asyncio
from typing import List, Optional, Sequence
from unittest.mock import MagicMock, patch

import pytest

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
from sankhya_sdk.exceptions import (
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestTimeoutException,
)
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.request_wrappers.async_on_demand_request_wrapper import (
    AsyncOnDemandRequestWrapper,
)


# =============================================================================
# Infraestrutura
# =============================================================================

SYNC_TIMEOUT = 10.0


def _names(request) -> List[str]:
    """Retorna os nomes das entidades (NOMEPARC) enviadas em uma requisição."""
    return [
        row.local_fields["NOMEPARC"]
        for row in request.request_body.data_set.data_rows
    ]


class _RecordingService:
    """
    Serviço assíncrono simulado que registra cada lote recebido pelo worker.

    ``outcomes`` define, em ordem, a exceção lançada por cada chamada
    (``None`` = sucesso). Com ``block_first_call`` a primeira chamada fica
    bloqueada até ``release`` ser sinalizado.
    """

    def __init__(
        self,
        outcomes: Sequence[Optional[BaseException]] = (),
        block_first_call: bool = False,
    ) -> None:
        self._cond = asyncio.Condition()
        self._outcomes = list(outcomes)
        self._block_first_call = block_first_call
        self.batches: List[List[str]] = []
        self.first_call_started = asyncio.Event()
        self.release = asyncio.Event()

    async def __call__(self, request) -> MagicMock:
        async with self._cond:
            self.batches.append(_names(request))
            index = len(self.batches)
            outcome = self._outcomes.pop(0) if self._outcomes else None
            self._cond.notify_all()
        if index == 1 and self._block_first_call:
            self.first_call_started.set()
            await self.release.wait()
        if outcome is not None:
            raise outcome
        return MagicMock()

    async def wait_for_calls(self, count: int) -> bool:
        """Aguarda o worker fazer ``count`` chamadas (False se não fizer)."""

        async def reached() -> None:
            async with self._cond:
                await self._cond.wait_for(lambda: len(self.batches) >= count)

        try:
            await asyncio.wait_for(reached(), SYNC_TIMEOUT)
        except asyncio.TimeoutError:
            return False
        return True


async def _create_wrapper(
    service: _RecordingService,
    cancel_event: Optional[asyncio.Event] = None,
    start: bool = True,
    **kwargs,
) -> AsyncOnDemandRequestWrapper:
    """Cria um wrapper de salvamento cujo contexto delega ao serviço simulado."""
    context = MagicMock()
    context.service_invoker_async = service
    wrapper = AsyncOnDemandRequestWrapper(
        service=ServiceName.CRUD_SERVICE_SAVE,
        cancel_event=cancel_event or asyncio.Event(),
        context=context,
        **kwargs,
    )
    if start:
        await wrapper.start()
    return wrapper


async def _flush(wrapper: AsyncOnDemandRequestWrapper) -> None:
    """Executa flush falhando (em vez de travar) se ele não terminar."""
    await asyncio.wait_for(wrapper.flush(), SYNC_TIMEOUT)


async def _dispose_quietly(wrapper: AsyncOnDemandRequestWrapper) -> None:
    """Libera o wrapper na limpeza do teste sem mascarar a falha original."""
    try:
        await asyncio.wait_for(wrapper.dispose(), SYNC_TIMEOUT)
    except asyncio.TimeoutError:
        pass


@pytest.fixture
def failure_events():
    """Captura os OnDemandRequestFailureEvent publicados durante o teste."""
    events: List[OnDemandRequestFailureEvent] = []
    EventBus.subscribe(OnDemandRequestFailureEvent, events.append)
    try:
        yield events
    finally:
        EventBus.unsubscribe(OnDemandRequestFailureEvent, events.append)


# =============================================================================
# Retry (.NET OnDemandRequestWrapper.cs:242-289)
# =============================================================================


class TestAsyncOnDemandRetry:
    """Timeout e deadlock são repetidos uma única vez, de imediato."""

    @pytest.mark.asyncio
    async def test_timeout_is_retried_once(self, failure_events):
        """Timeout reenvia o mesmo lote uma vez, sem fallback individual."""
        service = _RecordingService(
            outcomes=[ServiceRequestTimeoutException(ServiceName.CRUD_SERVICE_SAVE)]
        )
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            await wrapper.add(Partner(name="A"))
            await wrapper.add(Partner(name="B"))
            await _flush(wrapper)

            assert service.batches == [["A", "B"], ["A", "B"]]
            assert wrapper.request_count == 2
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            await _dispose_quietly(wrapper)

    @pytest.mark.asyncio
    async def test_deadlock_is_retried_once_without_delay(self, failure_events):
        """Deadlock reenvia o lote uma vez, imediatamente (sem sleep)."""
        service = _RecordingService(
            outcomes=[ServiceRequestDeadlockException("deadlock")]
        )
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            with patch("asyncio.sleep", wraps=asyncio.sleep) as sleep:
                await wrapper.add(Partner(name="A"))
                await wrapper.add(Partner(name="B"))
                await _flush(wrapper)

            assert service.batches == [["A", "B"], ["A", "B"]]
            delays = [c.args[0] for c in sleep.call_args_list if c.args]
            assert [delay for delay in delays if delay > 0] == []
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            await _dispose_quietly(wrapper)

    @pytest.mark.asyncio
    async def test_competition_is_not_retried(self, failure_events):
        """Concorrência não é repetida: o lote cai no envio individual."""
        service = _RecordingService(outcomes=[ServiceRequestCompetitionException()])
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            await wrapper.add(Partner(name="A"))
            await wrapper.add(Partner(name="B"))
            await _flush(wrapper)

            assert service.batches == [["A", "B"], ["A"], ["B"]]
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            await _dispose_quietly(wrapper)

    @pytest.mark.asyncio
    async def test_second_timeout_falls_back_to_individual_requests(
        self, failure_events
    ):
        """Se a nova tentativa também falha, cada entidade é reenviada sozinha."""
        timeout = ServiceRequestTimeoutException(ServiceName.CRUD_SERVICE_SAVE)
        service = _RecordingService(outcomes=[timeout, timeout, timeout, timeout])
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        partner = Partner(name="A")
        try:
            await wrapper.add(partner)
            await _flush(wrapper)

            # Lote (2 tentativas) + envio individual (2 tentativas)
            assert service.batches == [["A"], ["A"], ["A"], ["A"]]
            assert wrapper.entities_sent_successfully == 0
            assert len(failure_events) == 1
            assert failure_events[0].entity is partner
            assert failure_events[0].exception is timeout
        finally:
            await _dispose_quietly(wrapper)
