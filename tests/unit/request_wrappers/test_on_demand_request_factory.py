# -*- coding: utf-8 -*-
"""
Unit tests para OnDemandRequestFactory e AsyncOnDemandRequestFactory.
"""

import asyncio
import threading
from typing import Optional
from unittest.mock import MagicMock, patch
import pytest

from pydantic import Field

from sankhya_sdk.enums.service_name import ServiceName
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

    @pytest.fixture(autouse=True)
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
