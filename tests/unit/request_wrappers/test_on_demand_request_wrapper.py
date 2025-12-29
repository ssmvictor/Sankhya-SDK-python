# -*- coding: utf-8 -*-
"""
Unit tests para OnDemandRequestWrapper e AsyncOnDemandRequestWrapper.

Testes básicos de inicialização e propriedades, evitando bloqueios de threads.
"""

import asyncio
import threading
import time
from typing import Optional
import pytest

from pydantic import Field

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
from sankhya_sdk.models.base import EntityBase


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
