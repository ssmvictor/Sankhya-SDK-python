# -*- coding: utf-8 -*-
"""
Unit tests do worker do AsyncOnDemandRequestWrapper.

O comportamento esperado segue a referência .NET
(``Src/Sankhya/RequestWrappers/OnDemandRequestWrapper.cs``). A sincronização
com a task worker é feita por eventos; os timeouts só são atingidos quando o
comportamento esperado não ocorre (evitam travar a suíte).
"""

import asyncio
from typing import Callable, List, Optional, Sequence
from unittest.mock import MagicMock, patch

import pytest

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
from sankhya_sdk.helpers.service_request_extensions import ServiceRequestExtensions
from sankhya_sdk.exceptions import (
    CanceledOnDemandRequestWrapperException,
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


# =============================================================================
# Cancelamento (.NET OnDemandRequestWrapper.cs:105-108)
# =============================================================================


class TestAsyncOnDemandCancellation:
    """Comportamento do wrapper após o cancelamento."""

    @pytest.mark.asyncio
    async def test_add_after_cancellation_raises(self):
        """add() recusa entidades quando o cancelamento já foi solicitado."""
        cancel_event = asyncio.Event()
        service = _RecordingService()
        wrapper = await _create_wrapper(service, cancel_event=cancel_event)
        try:
            cancel_event.set()

            with pytest.raises(CanceledOnDemandRequestWrapperException):
                await wrapper.add(Partner(name="A"))

            assert wrapper.queue_size == 0
        finally:
            await _dispose_quietly(wrapper)

        assert service.batches == []


# =============================================================================
# Montagem das requisições (.NET OnDemandRequestWrapper.cs:222-237, 291-318)
# =============================================================================


def _resolve_failing_for(name: str) -> Callable:
    """resolve_with_entity real, exceto para a entidade ``name``."""
    original = ServiceRequestExtensions.resolve_with_entity

    def resolve(request, entity, *args, **kwargs):
        if entity.name == name:
            raise ValueError(f"entidade inválida: {name}")
        return original(request, entity, *args, **kwargs)

    return resolve


class TestAsyncOnDemandRequestBuilding:
    """Lotes usam Resolve(ICollection) e nenhuma entidade é perdida em silêncio."""

    @pytest.mark.asyncio
    async def test_batch_is_built_from_the_whole_collection(self):
        """O lote é uma única requisição montada com resolve_with_collection."""
        service = _RecordingService()
        # Throughput acima do número de entidades: só o flush envia
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        partners = [Partner(name="A"), Partner(name="B")]
        try:
            with patch.object(
                ServiceRequestExtensions,
                "resolve_with_collection",
                wraps=ServiceRequestExtensions.resolve_with_collection,
            ) as resolve:
                for partner in partners:
                    await wrapper.add(partner)
                await _flush(wrapper)

            resolve.assert_called_once()
            assert resolve.call_args.args[1] == partners
            assert service.batches == [["A", "B"]]
            assert wrapper.entities_sent == 2
            assert wrapper.entities_sent_successfully == 2
        finally:
            await _dispose_quietly(wrapper)

    @pytest.mark.asyncio
    async def test_batch_build_failure_falls_back_to_individual_requests(
        self, failure_events
    ):
        """Falha ao montar o lote: as entidades são enviadas individualmente."""
        service = _RecordingService()
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            with patch.object(
                ServiceRequestExtensions,
                "resolve_with_collection",
                side_effect=RuntimeError("falha ao montar o lote"),
            ):
                await wrapper.add(Partner(name="A"))
                await wrapper.add(Partner(name="B"))
                await _flush(wrapper)

            assert service.batches == [["A"], ["B"]]
            assert wrapper.entities_sent == 2
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            await _dispose_quietly(wrapper)

    @pytest.mark.asyncio
    async def test_entity_build_failure_publishes_failure_event(
        self, failure_events
    ):
        """Entidade que não pode ser montada gera OnDemandRequestFailureEvent."""
        service = _RecordingService()
        wrapper = await _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        invalid = Partner(name="B")
        try:
            with patch.object(
                ServiceRequestExtensions,
                "resolve_with_collection",
                side_effect=RuntimeError("falha ao montar o lote"),
            ), patch.object(
                ServiceRequestExtensions,
                "resolve_with_entity",
                side_effect=_resolve_failing_for("B"),
            ):
                await wrapper.add(Partner(name="A"))
                await wrapper.add(invalid)
                await wrapper.add(Partner(name="C"))
                await _flush(wrapper)

            assert service.batches == [["A"], ["C"]]
            assert wrapper.entities_sent == 3
            assert wrapper.entities_sent_successfully == 2
            assert len(failure_events) == 1
            assert failure_events[0].entity is invalid
            assert isinstance(failure_events[0].exception, ValueError)
        finally:
            await _dispose_quietly(wrapper)
