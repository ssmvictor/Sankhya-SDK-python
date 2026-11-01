# -*- coding: utf-8 -*-
"""
Unit tests para OnDemandRequestFactory e AsyncOnDemandRequestFactory.
"""

import asyncio
import threading
from typing import Optional
from unittest.mock import MagicMock, call, patch
from uuid import uuid4
import pytest
import pytest_asyncio

from pydantic import Field

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.request_wrappers.on_demand_request_factory import (
    OnDemandRequestFactory,
)
from sankhya_sdk.request_wrappers.async_on_demand_request_factory import (
    AsyncOnDemandRequestFactory,
)


# =============================================================================
# Test Entity
# =============================================================================


class FactoryTestEntity(EntityBase):
    """Entidade de teste simples."""
    
    id: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)


# =============================================================================
# Synchronous Factory Tests
# =============================================================================


class TestOnDemandRequestFactory:
    """Testes para OnDemandRequestFactory."""

    def setup_method(self):
        """Limpa o factory antes de cada teste."""
        OnDemandRequestFactory.clear()

    def teardown_method(self):
        """Limpa o factory após cada teste."""
        OnDemandRequestFactory.finalize_all()
        OnDemandRequestFactory.clear()

    def test_create_instance_returns_uuid(self):
        """Verifica que create_instance retorna UUID."""
        cancel_token = threading.Event()
        
        key = OnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_token=cancel_token,
        )
        
        assert key is not None
        assert OnDemandRequestFactory.get_instance_count() == 1

    def test_get_instance_by_key(self):
        """Verifica busca de instância por chave."""
        cancel_token = threading.Event()
        
        key = OnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_token=cancel_token,
        )
        
        wrapper = OnDemandRequestFactory.get_instance_by_key(key)
        
        assert wrapper is not None
        assert not wrapper.is_disposed

    def test_get_instance_for_service(self):
        """Verifica busca de instância por serviço e tipo."""
        cancel_token = threading.Event()
        
        OnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_token=cancel_token,
        )
        
        wrapper = OnDemandRequestFactory.get_instance_for_service(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
        )
        
        assert wrapper is not None

    def test_get_instance_for_service_returns_none_if_not_found(self):
        """Verifica que retorna None se não encontrado."""
        wrapper = OnDemandRequestFactory.get_instance_for_service(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
        )
        
        assert wrapper is None

    def test_finalize_by_key(self):
        """Verifica finalização de instância específica."""
        cancel_token = threading.Event()
        
        key = OnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_token=cancel_token,
        )
        
        OnDemandRequestFactory.finalize_by_key(key)
        
        wrapper = OnDemandRequestFactory.get_instance_by_key(key)
        assert wrapper is None

    def test_finalize_all(self):
        """Verifica finalização de todas as instâncias."""
        cancel_token = threading.Event()
        
        # Cria múltiplas instâncias
        for i in range(3):
            OnDemandRequestFactory.create_instance(
                entity_type=FactoryTestEntity,
                service=ServiceName.CRUD_SAVE,
                cancel_token=cancel_token,
            )
        
        assert OnDemandRequestFactory.get_instance_count() == 3
        
        OnDemandRequestFactory.finalize_all()
        
        assert OnDemandRequestFactory.get_instance_count() == 0

    def test_flush_by_key(self):
        """Verifica flush de instância específica."""
        cancel_token = threading.Event()
        
        key = OnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_token=cancel_token,
        )
        
        wrapper = OnDemandRequestFactory.get_instance_by_key(key)
        assert wrapper is not None
        
        # Não deve lançar exceção
        OnDemandRequestFactory.flush_by_key(key)


# =============================================================================
# Asynchronous Factory Tests
# =============================================================================


class TestAsyncOnDemandRequestFactory:
    """Testes para AsyncOnDemandRequestFactory."""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Limpa o factory antes e após cada teste."""
        await AsyncOnDemandRequestFactory.clear()
        yield
        await AsyncOnDemandRequestFactory.finalize_all()
        await AsyncOnDemandRequestFactory.clear()

    @pytest.mark.asyncio
    async def test_create_instance_returns_uuid(self):
        """Verifica que create_instance retorna UUID."""
        cancel_event = asyncio.Event()
        
        key = await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_event=cancel_event,
        )
        
        assert key is not None
        assert await AsyncOnDemandRequestFactory.get_instance_count() == 1

    @pytest.mark.asyncio
    async def test_get_instance_by_key(self):
        """Verifica busca de instância por chave."""
        cancel_event = asyncio.Event()
        
        key = await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_event=cancel_event,
        )
        
        wrapper = await AsyncOnDemandRequestFactory.get_instance_by_key(key)
        
        assert wrapper is not None
        assert not wrapper.is_disposed

    @pytest.mark.asyncio
    async def test_get_instance_for_service(self):
        """Verifica busca de instância por serviço e tipo."""
        cancel_event = asyncio.Event()
        
        await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_event=cancel_event,
        )
        
        wrapper = await AsyncOnDemandRequestFactory.get_instance_for_service(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
        )
        
        assert wrapper is not None

    @pytest.mark.asyncio
    async def test_get_instance_for_service_returns_none_if_not_found(self):
        """Verifica que retorna None se não encontrado."""
        wrapper = await AsyncOnDemandRequestFactory.get_instance_for_service(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
        )
        
        assert wrapper is None

    @pytest.mark.asyncio
    async def test_finalize_by_key(self):
        """Verifica finalização de instância específica."""
        cancel_event = asyncio.Event()
        
        key = await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_event=cancel_event,
        )
        
        await AsyncOnDemandRequestFactory.finalize_by_key(key)
        
        wrapper = await AsyncOnDemandRequestFactory.get_instance_by_key(key)
        assert wrapper is None

    @pytest.mark.asyncio
    async def test_finalize_all(self):
        """Verifica finalização de todas as instâncias."""
        cancel_event = asyncio.Event()
        
        # Cria múltiplas instâncias
        for i in range(3):
            await AsyncOnDemandRequestFactory.create_instance(
                entity_type=FactoryTestEntity,
                service=ServiceName.CRUD_SAVE,
                cancel_event=cancel_event,
            )
        
        assert await AsyncOnDemandRequestFactory.get_instance_count() == 3
        
        await AsyncOnDemandRequestFactory.finalize_all()
        
        assert await AsyncOnDemandRequestFactory.get_instance_count() == 0

    @pytest.mark.asyncio
    async def test_flush_by_key(self):
        """Verifica flush de instância específica."""
        cancel_event = asyncio.Event()
        
        key = await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SAVE,
            cancel_event=cancel_event,
        )
        
        wrapper = await AsyncOnDemandRequestFactory.get_instance_by_key(key)
        assert wrapper is not None
        
        # Não deve lançar exceção
        await AsyncOnDemandRequestFactory.flush_by_key(key)



# =============================================================================
# Sessão dedicada (.NET OnDemandRequestWrapper.cs:144-165, SankhyaContext.cs:112-116)
# =============================================================================


def _session_context(*tokens) -> MagicMock:
    """Contexto simulado cujas novas sessões recebem os tokens informados."""
    context = MagicMock()
    context.acquire_new_session.side_effect = list(tokens)
    return context


class TestOnDemandRequestFactorySession:
    """A sessão adquirida pela factory é finalizada com o wrapper."""

    def setup_method(self):
        """Limpa o factory antes de cada teste."""
        OnDemandRequestFactory.clear()

    def teardown_method(self):
        """Limpa o factory após cada teste."""
        OnDemandRequestFactory.finalize_all()
        OnDemandRequestFactory.clear()

    def test_finalize_by_key_releases_dedicated_session(self):
        """finalize_by_key encerra a sessão on-demand criada pela factory."""
        token = uuid4()
        context = _session_context(token)

        key = OnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SERVICE_SAVE,
            cancel_token=threading.Event(),
            context=context,
        )

        context.acquire_new_session.assert_called_once_with(
            ServiceRequestType.ON_DEMAND_CRUD
        )
        context.detach_on_demand_request_wrapper.assert_not_called()

        OnDemandRequestFactory.finalize_by_key(key)

        context.detach_on_demand_request_wrapper.assert_called_once_with(token)

    def test_finalize_all_releases_every_dedicated_session(self):
        """finalize_all encerra a sessão de cada wrapper criado."""
        tokens = [uuid4(), uuid4()]
        context = _session_context(*tokens)
        for _ in tokens:
            OnDemandRequestFactory.create_instance(
                entity_type=FactoryTestEntity,
                service=ServiceName.CRUD_SERVICE_SAVE,
                cancel_token=threading.Event(),
                context=context,
            )

        OnDemandRequestFactory.finalize_all()

        context.detach_on_demand_request_wrapper.assert_has_calls(
            [call(token) for token in tokens], any_order=True
        )
        assert context.detach_on_demand_request_wrapper.call_count == 2

    def test_session_is_released_if_wrapper_creation_fails(self):
        """Se o wrapper não pode ser criado, a sessão adquirida é encerrada."""
        token = uuid4()
        context = _session_context(token)

        with patch(
            "sankhya_sdk.request_wrappers.on_demand_request_factory."
            "OnDemandRequestWrapper",
            side_effect=RuntimeError("falha ao criar wrapper"),
        ):
            with pytest.raises(RuntimeError):
                OnDemandRequestFactory.create_instance(
                    entity_type=FactoryTestEntity,
                    service=ServiceName.CRUD_SERVICE_SAVE,
                    cancel_token=threading.Event(),
                    context=context,
                )

        context.detach_on_demand_request_wrapper.assert_called_once_with(token)
        assert OnDemandRequestFactory.get_instance_count() == 0


class TestAsyncOnDemandRequestFactorySession:
    """A sessão adquirida pela factory assíncrona é finalizada com o wrapper."""

    @pytest_asyncio.fixture(autouse=True)
    async def cleanup(self):
        """Limpa o factory antes e após cada teste."""
        await AsyncOnDemandRequestFactory.clear()
        yield
        await AsyncOnDemandRequestFactory.finalize_all()
        await AsyncOnDemandRequestFactory.clear()

    @pytest.mark.asyncio
    async def test_finalize_by_key_releases_dedicated_session(self):
        """finalize_by_key encerra a sessão on-demand criada pela factory."""
        token = uuid4()
        context = _session_context(token)

        key = await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SERVICE_SAVE,
            cancel_event=asyncio.Event(),
            context=context,
        )

        context.acquire_new_session.assert_called_once_with(
            ServiceRequestType.ON_DEMAND_CRUD
        )
        context.detach_on_demand_request_wrapper.assert_not_called()

        await AsyncOnDemandRequestFactory.finalize_by_key(key)

        context.detach_on_demand_request_wrapper.assert_called_once_with(token)

    @pytest.mark.asyncio
    async def test_finalize_all_releases_every_dedicated_session(self):
        """finalize_all encerra a sessão de cada wrapper criado."""
        tokens = [uuid4(), uuid4()]
        context = _session_context(*tokens)
        for _ in tokens:
            await AsyncOnDemandRequestFactory.create_instance(
                entity_type=FactoryTestEntity,
                service=ServiceName.CRUD_SERVICE_SAVE,
                cancel_event=asyncio.Event(),
                context=context,
            )

        await AsyncOnDemandRequestFactory.finalize_all()

        context.detach_on_demand_request_wrapper.assert_has_calls(
            [call(token) for token in tokens], any_order=True
        )
        assert context.detach_on_demand_request_wrapper.call_count == 2

    @pytest.mark.asyncio
    async def test_session_is_released_if_wrapper_creation_fails(self):
        """Se o wrapper não pode ser criado, a sessão adquirida é encerrada."""
        token = uuid4()
        context = _session_context(token)

        with patch(
            "sankhya_sdk.request_wrappers.async_on_demand_request_factory."
            "AsyncOnDemandRequestWrapper",
            side_effect=RuntimeError("falha ao criar wrapper"),
        ):
            with pytest.raises(RuntimeError):
                await AsyncOnDemandRequestFactory.create_instance(
                    entity_type=FactoryTestEntity,
                    service=ServiceName.CRUD_SERVICE_SAVE,
                    cancel_event=asyncio.Event(),
                    context=context,
                )

        context.detach_on_demand_request_wrapper.assert_called_once_with(token)
        assert await AsyncOnDemandRequestFactory.get_instance_count() == 0

    @pytest.mark.asyncio
    async def test_dedicated_session_login_and_logout_run_off_the_event_loop(self):
        """Login e logout da sessão dedicada (HTTP bloqueante) rodam fora do loop."""
        token = uuid4()
        context = MagicMock()
        session_threads: dict = {}

        def acquire(request_type):
            session_threads["acquire"] = threading.get_ident()
            return token

        def detach(session_token):
            session_threads["detach"] = threading.get_ident()

        context.acquire_new_session.side_effect = acquire
        context.detach_on_demand_request_wrapper.side_effect = detach

        key = await AsyncOnDemandRequestFactory.create_instance(
            entity_type=FactoryTestEntity,
            service=ServiceName.CRUD_SERVICE_SAVE,
            cancel_event=asyncio.Event(),
            context=context,
        )
        await AsyncOnDemandRequestFactory.finalize_by_key(key)

        context.acquire_new_session.assert_called_once_with(
            ServiceRequestType.ON_DEMAND_CRUD
        )
        context.detach_on_demand_request_wrapper.assert_called_once_with(token)
        loop_thread = threading.get_ident()
        assert session_threads["acquire"] != loop_thread
        assert session_threads["detach"] != loop_thread

    @pytest.mark.asyncio
    async def test_session_release_after_creation_failure_runs_off_the_event_loop(
        self,
    ):
        """O logout após falha na criação do wrapper também roda fora do loop."""
        token = uuid4()
        context = _session_context(token)
        detach_threads = []
        context.detach_on_demand_request_wrapper.side_effect = (
            lambda session_token: detach_threads.append(threading.get_ident())
        )

        with patch(
            "sankhya_sdk.request_wrappers.async_on_demand_request_factory."
            "AsyncOnDemandRequestWrapper",
            side_effect=RuntimeError("falha ao criar wrapper"),
        ):
            with pytest.raises(RuntimeError):
                await AsyncOnDemandRequestFactory.create_instance(
                    entity_type=FactoryTestEntity,
                    service=ServiceName.CRUD_SERVICE_SAVE,
                    cancel_event=asyncio.Event(),
                    context=context,
                )

        context.detach_on_demand_request_wrapper.assert_called_once_with(token)
        assert len(detach_threads) == 1
        assert detach_threads[0] != threading.get_ident()


# =============================================================================
# Flush pela factory na thread worker
# =============================================================================


class TestOnDemandRequestFactoryFlushFromWorker:
    """flush_all() em um handler de falha (thread worker) não trava."""

    def setup_method(self):
        """Limpa o factory antes de cada teste."""
        OnDemandRequestFactory.clear()

    def teardown_method(self):
        """Limpa o factory após cada teste."""
        OnDemandRequestFactory.finalize_all()
        OnDemandRequestFactory.clear()

    def test_flush_all_from_failure_handler_returns(self):
        """O handler que chama flush_all() retorna e o flush externo também."""
        from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
        from sankhya_sdk.models.transport.partner import Partner

        wait_timeout = 10.0
        key = OnDemandRequestFactory.create_instance(
            entity_type=Partner,
            service=ServiceName.CRUD_SERVICE_SAVE,
            cancel_token=threading.Event(),
        )
        wrapper = OnDemandRequestFactory.get_instance_by_key(key)
        original = Partner(name="A")
        handler_flush_returned = threading.Event()

        def handler(event: OnDemandRequestFailureEvent) -> None:
            # Sem contexto todo envio falha; só a falha de "A" reenfileira
            if event.entity is original:
                wrapper.add(Partner(name="A2"))
                OnDemandRequestFactory.flush_all()
                handler_flush_returned.set()

        EventBus.subscribe(OnDemandRequestFailureEvent, handler)
        try:
            wrapper.add(original)
            flusher = threading.Thread(target=wrapper.flush, daemon=True)
            flusher.start()
            flusher.join(wait_timeout)

            assert not flusher.is_alive(), "flush() externo travou"
            assert handler_flush_returned.is_set()
        finally:
            EventBus.unsubscribe(OnDemandRequestFailureEvent, handler)

    def test_flush_all_from_failure_handler_with_two_failing_wrappers(self):
        """
        Dois wrappers falhando, com handler que só chama flush_all(), não travam.

        Cada worker, no handler, chama o flush do outro enquanto o lote do
        outro está em andamento: nenhum dos dois pode aguardar o outro.
        """
        from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
        from sankhya_sdk.models.transport.partner import Partner

        wait_timeout = 10.0
        wrappers = []
        for _ in range(2):
            key = OnDemandRequestFactory.create_instance(
                entity_type=Partner,
                service=ServiceName.CRUD_SERVICE_SAVE,
                cancel_token=threading.Event(),
                throughput=10,
            )
            wrappers.append(OnDemandRequestFactory.get_instance_by_key(key))
        failures = []
        handler_lock = threading.Lock()

        def handler(event: OnDemandRequestFailureEvent) -> None:
            # Sem contexto todo envio falha (ex.: servidor fora do ar)
            with handler_lock:
                failures.append(event.entity.name)
            OnDemandRequestFactory.flush_all()

        EventBus.subscribe(OnDemandRequestFailureEvent, handler)
        try:
            wrappers[0].add(Partner(name="A"))
            wrappers[1].add(Partner(name="B"))
            flusher = threading.Thread(target=wrappers[0].flush, daemon=True)
            flusher.start()
            flusher.join(wait_timeout)

            assert not flusher.is_alive(), "flush() externo travou"

            # O flush pedido pelo handler do primeiro worker envia "B"
            finalizer = threading.Thread(
                target=OnDemandRequestFactory.finalize_all, daemon=True
            )
            finalizer.start()
            finalizer.join(wait_timeout)

            assert not finalizer.is_alive(), "finalize_all() travou"
            assert [w._worker.is_alive() for w in wrappers] == [False, False]
            assert sorted(failures) == ["A", "B"]
        finally:
            EventBus.unsubscribe(OnDemandRequestFailureEvent, handler)
