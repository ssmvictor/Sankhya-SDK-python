# -*- coding: utf-8 -*-
"""
Unit tests para OnDemandRequestWrapper e AsyncOnDemandRequestWrapper.

Testes básicos de inicialização e propriedades, evitando bloqueios de threads.
"""

import asyncio
import threading
import time
from typing import Callable, List, Optional, Sequence
from unittest.mock import MagicMock, patch
import pytest

from pydantic import Field

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
from sankhya_sdk.helpers.service_request_extensions import ServiceRequestExtensions
from sankhya_sdk.exceptions import (
    CanceledOnDemandRequestWrapperException,
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestTimeoutException,
)
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.request_wrappers import on_demand_request_wrapper as wrapper_module
from sankhya_sdk.request_wrappers.on_demand_request_wrapper import (
    OnDemandRequestWrapper,
)


# =============================================================================
# Test Entity
# =============================================================================


class TestEntity(EntityBase):
    """Entidade de teste simples."""
    
    id: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)


# =============================================================================
# Import Tests
# =============================================================================


class TestOnDemandRequestWrapperImports:
    """Testes de importação dos módulos."""

    def test_sync_wrapper_imports(self):
        """Verifica que wrapper síncrono pode ser importado."""
        from sankhya_sdk.request_wrappers.on_demand_request_wrapper import (
            OnDemandRequestWrapper,
        )
        assert OnDemandRequestWrapper is not None

    def test_async_wrapper_imports(self):
        """Verifica que wrapper assíncrono pode ser importado."""
        from sankhya_sdk.request_wrappers.async_on_demand_request_wrapper import (
            AsyncOnDemandRequestWrapper,
        )
        assert AsyncOnDemandRequestWrapper is not None

    def test_factory_imports(self):
        """Verifica que factory pode ser importado."""
        from sankhya_sdk.request_wrappers.on_demand_request_factory import (
            OnDemandRequestFactory,
        )
        assert OnDemandRequestFactory is not None

    def test_async_factory_imports(self):
        """Verifica que factory assíncrono pode ser importado."""
        from sankhya_sdk.request_wrappers.async_on_demand_request_factory import (
            AsyncOnDemandRequestFactory,
        )
        assert AsyncOnDemandRequestFactory is not None

    def test_interfaces_imports(self):
        """Verifica que interfaces podem ser importadas."""
        from sankhya_sdk.request_wrappers.interfaces import (
            IOnDemandRequestWrapper,
            IAsyncOnDemandRequestWrapper,
        )
        assert IOnDemandRequestWrapper is not None
        assert IAsyncOnDemandRequestWrapper is not None


# =============================================================================
# Event Publishing Tests
# =============================================================================


class TestEventPublishing:
    """Testes para publicação de eventos de falha."""

    def test_event_bus_publish_subscribe(self):
        """Verifica publicação e recebimento de eventos."""
        received_events: list = []
        
        def handler(event: OnDemandRequestFailureEvent) -> None:
            received_events.append(event)
        
        EventBus.subscribe(OnDemandRequestFailureEvent, handler)
        
        try:
            # Publica evento
            entity = TestEntity(id=1, name="Test")
            event = OnDemandRequestFailureEvent(
                entity=entity,
                is_update=False,
                exception=Exception("Test error"),
            )
            EventBus.publish(event)
            
            assert len(received_events) == 1
            assert received_events[0].entity == entity
            assert not received_events[0].is_update
        finally:
            EventBus.unsubscribe(OnDemandRequestFailureEvent, handler)

    def test_event_bus_unsubscribe(self):
        """Verifica remoção de handler."""
        received_events: list = []
        
        def handler(event: OnDemandRequestFailureEvent) -> None:
            received_events.append(event)
        
        EventBus.subscribe(OnDemandRequestFailureEvent, handler)
        EventBus.unsubscribe(OnDemandRequestFailureEvent, handler)
        
        # Publica evento
        entity = TestEntity(id=1, name="Test")
        event = OnDemandRequestFailureEvent(
            entity=entity,
            is_update=True,
            exception=Exception("Test error"),
        )
        EventBus.publish(event)
        
        assert len(received_events) == 0

    def test_failure_event_attributes(self):
        """Verifica atributos do evento de falha."""
        entity = TestEntity(id=42, name="TestName")
        exc = ValueError("Validation failed")
        
        event = OnDemandRequestFailureEvent(
            entity=entity,
            is_update=True,
            exception=exc,
            error_message="Custom message",
            retry_count=2,
        )
        
        assert event.entity == entity
        assert event.is_update is True
        assert event.exception == exc
        assert event.error_message == "Custom message"
        assert event.retry_count == 2


# =============================================================================
# OnDemandRequestInstance Tests
# =============================================================================


class TestOnDemandRequestInstance:
    """Testes para OnDemandRequestInstance."""

    def test_instance_creation(self):
        """Verifica criação de instância."""
        from uuid import uuid4
        from sankhya_sdk.value_objects.on_demand_request_instance import (
            OnDemandRequestInstance,
        )
        
        key = uuid4()
        instance = OnDemandRequestInstance(
            key=key,
            service=ServiceName.CRUD_SAVE,
            entity_type=TestEntity,
            instance=None,  # type: ignore
            is_async=False,
        )
        
        assert instance.key == key
        assert instance.service == ServiceName.CRUD_SAVE
        assert instance.entity_type == TestEntity
        assert not instance.is_async


# =============================================================================
# Interface Protocol Tests
# =============================================================================


class TestInterfaceProtocols:
    """Testes para verificar que as classes implementam os protocolos."""

    def test_sync_wrapper_has_required_methods(self):
        """Verifica que wrapper síncrono tem métodos requeridos."""
        from sankhya_sdk.request_wrappers.on_demand_request_wrapper import (
            OnDemandRequestWrapper,
        )
        
        # Verifica métodos
        assert hasattr(OnDemandRequestWrapper, "add")
        assert hasattr(OnDemandRequestWrapper, "flush")
        assert hasattr(OnDemandRequestWrapper, "dispose")
        assert hasattr(OnDemandRequestWrapper, "__enter__")
        assert hasattr(OnDemandRequestWrapper, "__exit__")

    def test_async_wrapper_has_required_methods(self):
        """Verifica que wrapper assíncrono tem métodos requeridos."""
        from sankhya_sdk.request_wrappers.async_on_demand_request_wrapper import (
            AsyncOnDemandRequestWrapper,
        )
        
        # Verifica métodos
        assert hasattr(AsyncOnDemandRequestWrapper, "add")
        assert hasattr(AsyncOnDemandRequestWrapper, "flush")
        assert hasattr(AsyncOnDemandRequestWrapper, "dispose")
        assert hasattr(AsyncOnDemandRequestWrapper, "__aenter__")
        assert hasattr(AsyncOnDemandRequestWrapper, "__aexit__")

    def test_factory_has_required_methods(self):
        """Verifica que factory tem métodos requeridos."""
        from sankhya_sdk.request_wrappers.on_demand_request_factory import (
            OnDemandRequestFactory,
        )
        
        assert hasattr(OnDemandRequestFactory, "create_instance")
        assert hasattr(OnDemandRequestFactory, "get_instance_by_key")
        assert hasattr(OnDemandRequestFactory, "get_instance_for_service")
        assert hasattr(OnDemandRequestFactory, "flush_by_key")
        assert hasattr(OnDemandRequestFactory, "flush_all")
        assert hasattr(OnDemandRequestFactory, "finalize_by_key")
        assert hasattr(OnDemandRequestFactory, "finalize_all")


# =============================================================================
# Infraestrutura para testes do worker
# =============================================================================

# Limite de espera pela thread worker. Só é atingido quando o comportamento
# esperado não ocorre: a sincronização dos testes é feita por eventos.
SYNC_TIMEOUT = 10.0


def _names(request) -> List[str]:
    """Retorna os nomes das entidades (NOMEPARC) enviadas em uma requisição."""
    return [
        row.local_fields["NOMEPARC"]
        for row in request.request_body.data_set.data_rows
    ]


class _RecordingService:
    """
    Serviço simulado que registra cada lote recebido pelo worker.

    ``outcomes`` define, em ordem, a exceção lançada por cada chamada
    (``None`` = sucesso). Com ``block_first_call`` a primeira chamada fica
    bloqueada até ``release`` ser sinalizado, segurando o worker em um
    ponto conhecido.
    """

    def __init__(
        self,
        outcomes: Sequence[Optional[BaseException]] = (),
        block_first_call: bool = False,
    ) -> None:
        self._cond = threading.Condition()
        self._outcomes = list(outcomes)
        self._block_first_call = block_first_call
        self.batches: List[List[str]] = []
        self.first_call_started = threading.Event()
        self.release = threading.Event()

    def __call__(self, request) -> MagicMock:
        with self._cond:
            self.batches.append(_names(request))
            index = len(self.batches)
            outcome = self._outcomes.pop(0) if self._outcomes else None
            self._cond.notify_all()
        if index == 1 and self._block_first_call:
            self.first_call_started.set()
            self.release.wait(SYNC_TIMEOUT)
        if outcome is not None:
            raise outcome
        return MagicMock()

    def wait_for_calls(self, count: int) -> bool:
        """Aguarda o worker fazer ``count`` chamadas (False se não fizer)."""
        with self._cond:
            return self._cond.wait_for(
                lambda: len(self.batches) >= count, SYNC_TIMEOUT
            )


def _create_wrapper(
    service: _RecordingService,
    cancel_token: Optional[threading.Event] = None,
    **kwargs,
) -> OnDemandRequestWrapper:
    """Cria um wrapper de salvamento cujo contexto delega ao serviço simulado."""
    context = MagicMock()
    context.service_invoker.side_effect = service
    return OnDemandRequestWrapper(
        service=ServiceName.CRUD_SERVICE_SAVE,
        cancel_token=cancel_token or threading.Event(),
        context=context,
        **kwargs,
    )


def _call_with_timeout(func: Callable[[], object]) -> None:
    """Executa ``func`` em thread daemon e falha se ela não terminar."""
    errors: List[BaseException] = []

    def target() -> None:
        try:
            func()
        except BaseException as exc:  # repassado ao teste
            errors.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(SYNC_TIMEOUT)
    assert not thread.is_alive(), (
        f"{getattr(func, '__qualname__', func)} não terminou em {SYNC_TIMEOUT}s"
    )
    if errors:
        raise errors[0]


def _dispose_quietly(wrapper: OnDemandRequestWrapper) -> None:
    """Libera o wrapper na limpeza do teste sem mascarar a falha original."""
    thread = threading.Thread(target=wrapper.dispose, daemon=True)
    thread.start()
    thread.join(SYNC_TIMEOUT)


@pytest.fixture
def failure_events():
    """Captura os OnDemandRequestFailureEvent publicados durante o teste."""
    events: List[OnDemandRequestFailureEvent] = []
    lock = threading.Lock()

    def handler(event: OnDemandRequestFailureEvent) -> None:
        with lock:
            events.append(event)

    EventBus.subscribe(OnDemandRequestFailureEvent, handler)
    try:
        yield events
    finally:
        EventBus.unsubscribe(OnDemandRequestFailureEvent, handler)


# =============================================================================
# Retry (.NET OnDemandRequestWrapper.cs:242-289)
# =============================================================================


class TestOnDemandRetry:
    """Timeout e deadlock são repetidos uma única vez, de imediato."""

    def test_timeout_is_retried_once(self, failure_events):
        """Timeout reenvia o mesmo lote uma vez, sem fallback individual."""
        service = _RecordingService(
            outcomes=[ServiceRequestTimeoutException(ServiceName.CRUD_SERVICE_SAVE)]
        )
        wrapper = _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            wrapper.add(Partner(name="A"))
            wrapper.add(Partner(name="B"))
            _call_with_timeout(wrapper.flush)

            assert service.batches == [["A", "B"], ["A", "B"]]
            assert wrapper.request_count == 2
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            _dispose_quietly(wrapper)

    def test_deadlock_is_retried_once_without_delay(self, failure_events):
        """Deadlock reenvia o lote uma vez, imediatamente (sem sleep)."""
        service = _RecordingService(
            outcomes=[ServiceRequestDeadlockException("deadlock")]
        )
        with patch.object(wrapper_module, "time", wraps=time, create=True) as clock:
            wrapper = _create_wrapper(
                service, throughput=10, allow_above_throughput=False
            )
            try:
                wrapper.add(Partner(name="A"))
                wrapper.add(Partner(name="B"))
                _call_with_timeout(wrapper.flush)
            finally:
                _dispose_quietly(wrapper)

        assert service.batches == [["A", "B"], ["A", "B"]]
        clock.sleep.assert_not_called()
        assert wrapper.entities_sent_successfully == 2
        assert failure_events == []

    def test_competition_is_not_retried(self, failure_events):
        """Concorrência não é repetida: o lote cai no envio individual."""
        service = _RecordingService(outcomes=[ServiceRequestCompetitionException()])
        wrapper = _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            wrapper.add(Partner(name="A"))
            wrapper.add(Partner(name="B"))
            _call_with_timeout(wrapper.flush)

            assert service.batches == [["A", "B"], ["A"], ["B"]]
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            _dispose_quietly(wrapper)

    def test_second_timeout_falls_back_to_individual_requests(self, failure_events):
        """Se a nova tentativa também falha, cada entidade é reenviada sozinha."""
        timeout = ServiceRequestTimeoutException(ServiceName.CRUD_SERVICE_SAVE)
        service = _RecordingService(outcomes=[timeout, timeout, timeout, timeout])
        wrapper = _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        partner = Partner(name="A")
        try:
            wrapper.add(partner)
            _call_with_timeout(wrapper.flush)

            # Lote (2 tentativas) + envio individual (2 tentativas)
            assert service.batches == [["A"], ["A"], ["A"], ["A"]]
            assert wrapper.entities_sent_successfully == 0
            assert len(failure_events) == 1
            assert failure_events[0].entity is partner
            assert failure_events[0].exception is timeout
        finally:
            _dispose_quietly(wrapper)


# =============================================================================
# Cancelamento (.NET OnDemandRequestWrapper.cs:105-108)
# =============================================================================


class TestOnDemandCancellation:
    """Comportamento do wrapper após o cancelamento."""

    def test_add_after_cancellation_raises(self):
        """add() recusa entidades quando o cancelamento já foi solicitado."""
        cancel_token = threading.Event()
        service = _RecordingService()
        wrapper = _create_wrapper(service, cancel_token=cancel_token)
        try:
            cancel_token.set()

            with pytest.raises(CanceledOnDemandRequestWrapperException):
                wrapper.add(Partner(name="A"))

            assert wrapper.queue_size == 0
        finally:
            _dispose_quietly(wrapper)

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


class TestOnDemandRequestBuilding:
    """Lotes usam Resolve(ICollection) e nenhuma entidade é perdida em silêncio."""

    def test_batch_is_built_from_the_whole_collection(self):
        """O lote é uma única requisição montada com resolve_with_collection."""
        service = _RecordingService()
        # Throughput acima do número de entidades: só o flush envia
        wrapper = _create_wrapper(
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
                    wrapper.add(partner)
                _call_with_timeout(wrapper.flush)

            resolve.assert_called_once()
            assert resolve.call_args.args[1] == partners
            assert service.batches == [["A", "B"]]
            assert wrapper.entities_sent == 2
            assert wrapper.entities_sent_successfully == 2
        finally:
            _dispose_quietly(wrapper)

    def test_batch_build_failure_falls_back_to_individual_requests(
        self, failure_events
    ):
        """Falha ao montar o lote: as entidades são enviadas individualmente."""
        service = _RecordingService()
        wrapper = _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            with patch.object(
                ServiceRequestExtensions,
                "resolve_with_collection",
                side_effect=RuntimeError("falha ao montar o lote"),
            ):
                wrapper.add(Partner(name="A"))
                wrapper.add(Partner(name="B"))
                _call_with_timeout(wrapper.flush)

            assert service.batches == [["A"], ["B"]]
            assert wrapper.entities_sent == 2
            assert wrapper.entities_sent_successfully == 2
            assert failure_events == []
        finally:
            _dispose_quietly(wrapper)

    def test_entity_build_failure_publishes_failure_event(self, failure_events):
        """Entidade que não pode ser montada gera OnDemandRequestFailureEvent."""
        service = _RecordingService()
        wrapper = _create_wrapper(
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
                wrapper.add(Partner(name="A"))
                wrapper.add(invalid)
                wrapper.add(Partner(name="C"))
                _call_with_timeout(wrapper.flush)

            assert service.batches == [["A"], ["C"]]
            assert wrapper.entities_sent == 3
            assert wrapper.entities_sent_successfully == 2
            assert len(failure_events) == 1
            assert failure_events[0].entity is invalid
            assert isinstance(failure_events[0].exception, ValueError)
        finally:
            _dispose_quietly(wrapper)


# =============================================================================
# Flush
# =============================================================================


class TestOnDemandFlush:
    """flush() não pode bloquear para sempre."""

    def test_flush_returns_when_batch_processing_raises(self):
        """Erro inesperado no processamento do lote ainda conclui o flush."""
        service = _RecordingService()
        wrapper = _create_wrapper(
            service, throughput=10, allow_above_throughput=False
        )
        try:
            with patch.object(
                wrapper, "_process_batch", side_effect=RuntimeError("falha")
            ) as process_batch:
                wrapper.add(Partner(name="A"))
                _call_with_timeout(wrapper.flush)

            process_batch.assert_called_once()
            assert wrapper.queue_size == 0
        finally:
            _dispose_quietly(wrapper)
