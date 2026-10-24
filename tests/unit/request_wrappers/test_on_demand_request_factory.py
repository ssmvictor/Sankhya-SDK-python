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
