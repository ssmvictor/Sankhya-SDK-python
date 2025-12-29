# -*- coding: utf-8 -*-
"""
Sistema de eventos para o Sankhya SDK.

Fornece um EventBus simples para publicação e assinatura de eventos,
utilizado principalmente para notificação de falhas em operações on-demand.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Events/
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Protocol, Type, TypeVar, runtime_checkable


TEvent = TypeVar("TEvent")


@runtime_checkable
class EventHandler(Protocol[TEvent]):
    """Protocolo para handlers de eventos."""

    def __call__(self, event: TEvent) -> None:
        """Processa o evento."""
        ...


class EventBus:
    """
    Barramento de eventos singleton para publicação e assinatura.
    
    Permite desacoplamento entre componentes que geram eventos
    e handlers que os processam.
    
    Thread-safe usando locks para operações de registro/publicação.
    
    Exemplo de uso:
        >>> def on_failure(event: OnDemandRequestFailureEvent) -> None:
        ...     print(f"Failed: {event.entity}")
        ...
        >>> EventBus.subscribe(OnDemandRequestFailureEvent, on_failure)
        >>> EventBus.publish(OnDemandRequestFailureEvent(entity=entity, exception=ex))
    """

    _instance: "EventBus | None" = None
    _lock: threading.Lock = threading.Lock()
    _handlers: Dict[Type[Any], List[Callable[[Any], None]]]

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._handlers = {}
                    cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls) -> "EventBus":
        """Retorna a instância singleton do EventBus."""
        return cls()

    @classmethod
    def subscribe(
        cls,
        event_type: Type[TEvent],
        handler: Callable[[TEvent], None],
    ) -> None:
        """
        Registra um handler para um tipo de evento.
        
        Args:
            event_type: Tipo do evento a ser assinado.
            handler: Função que será chamada quando o evento for publicado.
        """
        instance = cls.get_instance()
        with cls._lock:
            if event_type not in instance._handlers:
                instance._handlers[event_type] = []
            instance._handlers[event_type].append(handler)

    @classmethod
    def unsubscribe(
        cls,
        event_type: Type[TEvent],
        handler: Callable[[TEvent], None],
    ) -> bool:
        """
        Remove um handler de um tipo de evento.
        
        Args:
            event_type: Tipo do evento.
            handler: Handler a ser removido.
            
        Returns:
            True se o handler foi removido, False caso contrário.
        """
        instance = cls.get_instance()
        with cls._lock:
            if event_type in instance._handlers:
                try:
                    instance._handlers[event_type].remove(handler)
                    return True
                except ValueError:
                    return False
        return False

    @classmethod
    def publish(cls, event: TEvent) -> None:
        """
        Publica um evento para todos os handlers registrados.
        
        Args:
            event: Evento a ser publicado.
            
        Note:
            Erros em handlers são propagados silenciosamente para
            não interromper outros handlers.
        """
        instance = cls.get_instance()
        event_type = type(event)
        handlers: List[Callable[[Any], None]] = []
        
        with cls._lock:
            if event_type in instance._handlers:
                handlers = instance._handlers[event_type].copy()
        
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Log silenciosamente para não interromper processamento
                pass

    @classmethod
    def clear(cls, event_type: Type[TEvent] | None = None) -> None:
        """
        Remove todos os handlers de um tipo de evento ou todos os handlers.
        
        Args:
            event_type: Tipo do evento a limpar, ou None para limpar todos.
        """
        instance = cls.get_instance()
        with cls._lock:
            if event_type is None:
                instance._handlers.clear()
            elif event_type in instance._handlers:
                del instance._handlers[event_type]

    @classmethod
    def has_handlers(cls, event_type: Type[TEvent]) -> bool:
        """Verifica se há handlers registrados para um tipo de evento."""
        instance = cls.get_instance()
        with cls._lock:
            return event_type in instance._handlers and len(instance._handlers[event_type]) > 0

    @classmethod
    def handler_count(cls, event_type: Type[TEvent]) -> int:
        """Retorna o número de handlers registrados para um tipo de evento."""
        instance = cls.get_instance()
        with cls._lock:
            if event_type in instance._handlers:
                return len(instance._handlers[event_type])
            return 0


# Re-export for convenience
from .on_demand_request_failure_event import OnDemandRequestFailureEvent


__all__ = [
    "TEvent",
    "EventHandler",
    "EventBus",
    "OnDemandRequestFailureEvent",
]
