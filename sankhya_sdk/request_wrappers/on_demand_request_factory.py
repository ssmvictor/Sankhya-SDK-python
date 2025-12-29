# -*- coding: utf-8 -*-
"""
Factory para gerenciamento centralizado de OnDemandRequestWrappers.

Implementa padrão factory com gerenciamento thread-safe de instâncias.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/OnDemandRequestFactory.cs
"""

from __future__ import annotations

import logging
import threading
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    Optional,
    Type,
    TypeVar,
)
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from sankhya_sdk.core.context import SankhyaContext

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.request_wrappers.interfaces import IOnDemandRequestWrapper
from sankhya_sdk.request_wrappers.on_demand_request_wrapper import OnDemandRequestWrapper
from sankhya_sdk.value_objects.on_demand_request_instance import OnDemandRequestInstance


logger = logging.getLogger(__name__)

# TypeVar para entidades genéricas
TEntity = TypeVar("TEntity", bound=EntityBase)


class OnDemandRequestFactory:
    """
    Factory para criação e gerenciamento de OnDemandRequestWrappers.
    
    Gerencia instâncias de forma centralizada e thread-safe,
    permitindo criar, buscar, flush e finalizar wrappers.
    
    Todas as operações são thread-safe usando locks.
    
    Example:
        >>> cancel_token = threading.Event()
        >>> key = OnDemandRequestFactory.create_instance(
        ...     Partner,
        ...     ServiceName.CRUD_SERVICE_SAVE,
        ...     cancel_token,
        ...     context
        ... )
        >>> wrapper = OnDemandRequestFactory.get_instance_by_key(key)
        >>> wrapper.add(partner)
        >>> OnDemandRequestFactory.flush_all()
        >>> OnDemandRequestFactory.finalize_all()
    """

    # Class-level attributes
    _instances: ClassVar[Dict[UUID, OnDemandRequestInstance]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def create_instance(
        cls,
        entity_type: Type[TEntity],
        service: ServiceName,
        cancel_token: threading.Event,
        context: Optional["SankhyaContext"] = None,
        throughput: int = 10,
        allow_above_throughput: bool = True,
    ) -> UUID:
        """
        Cria uma nova instância de wrapper e retorna seu UUID.
        
        Args:
            entity_type: Tipo da entidade a ser processada
            service: Nome do serviço a usar
            cancel_token: Evento para sinalizar cancelamento
            context: Contexto Sankhya (cria nova sessão se fornecido)
            throughput: Número máximo de entidades por lote
            allow_above_throughput: Se True, processa antes de atingir throughput
            
        Returns:
            UUID identificador da instância criada
            
        Example:
            >>> key = OnDemandRequestFactory.create_instance(
            ...     Partner,
            ...     ServiceName.CRUD_SERVICE_SAVE,
            ...     cancel_token
            ... )
        """
        # Cria sessão dedicada se contexto fornecido
        session_token: Optional[UUID] = None
        if context:
            session_token = context.acquire_new_session(
                ServiceRequestType.ON_DEMAND_CRUD
            )
        
        # Cria wrapper
        wrapper: OnDemandRequestWrapper[TEntity] = OnDemandRequestWrapper(
            service=service,
            cancel_token=cancel_token,
            throughput=throughput,
            allow_above_throughput=allow_above_throughput,
            context=context,
            session_token=session_token,
        )
        
        # Gera chave única
        key = uuid4()
        
        # Cria instância de registro
        instance = OnDemandRequestInstance(
            key=key,
            service=service,
            entity_type=entity_type,
            instance=wrapper,
            is_async=False,
        )
        
        # Registra com lock
        with cls._lock:
            cls._instances[key] = instance
        
        logger.info(
            f"OnDemandRequestWrapper criado: key={key}, "
            f"entity_type={entity_type.__name__}, "
            f"service={service.name}"
        )
        
        return key

    @classmethod
    def get_instance_for_service(
        cls,
        entity_type: Type[TEntity],
        service: ServiceName,
    ) -> Optional[IOnDemandRequestWrapper]:
        """
        Busca uma instância existente para o serviço e tipo de entidade.
        
        Args:
            entity_type: Tipo da entidade
            service: Nome do serviço
            
        Returns:
            Instância do wrapper ou None se não encontrada
            
        Example:
            >>> wrapper = OnDemandRequestFactory.get_instance_for_service(
            ...     Partner,
            ...     ServiceName.CRUD_SERVICE_SAVE
            ... )
        """
        with cls._lock:
            for instance in cls._instances.values():
                if (
                    instance.entity_type == entity_type and
                    instance.service == service and
                    not instance.is_async
                ):
                    return instance.instance
        return None

    @classmethod
    def get_instance_by_key(cls, key: UUID) -> Optional[IOnDemandRequestWrapper]:
        """
        Busca uma instância pelo seu UUID.
        
        Args:
            key: UUID da instância
            
        Returns:
            Instância do wrapper ou None se não encontrada
            
        Example:
            >>> wrapper = OnDemandRequestFactory.get_instance_by_key(key)
        """
        with cls._lock:
            instance = cls._instances.get(key)
            if instance and not instance.is_async:
                return instance.instance
        return None

    @classmethod
    def flush_by_key(cls, key: UUID) -> None:
        """
        Força flush em uma instância específica.
        
        Args:
            key: UUID da instância
            
        Example:
            >>> OnDemandRequestFactory.flush_by_key(key)
        """
        with cls._lock:
            instance = cls._instances.get(key)
        
        if instance and not instance.is_async:
            instance.instance.flush()
            logger.debug(f"Flush executado: key={key}")

    @classmethod
    def flush_all(cls) -> None:
        """
        Força flush em todas as instâncias síncronas.
        
        Example:
            >>> OnDemandRequestFactory.flush_all()
        """
        with cls._lock:
            instances = [
                inst for inst in cls._instances.values()
                if not inst.is_async
            ]
        
        for instance in instances:
            try:
                instance.instance.flush()
            except Exception as e:
                logger.warning(f"Erro ao fazer flush: {e}")
        
        logger.debug(f"Flush executado em {len(instances)} instâncias")

    @classmethod
    def finalize_by_key(cls, key: UUID) -> None:
        """
        Finaliza e remove uma instância específica.
        
        Args:
            key: UUID da instância
            
        Example:
            >>> OnDemandRequestFactory.finalize_by_key(key)
        """
        with cls._lock:
            instance = cls._instances.pop(key, None)
        
        if instance and not instance.is_async:
            try:
                instance.instance.dispose()
                logger.debug(f"Instância finalizada: key={key}")
            except Exception as e:
                logger.warning(f"Erro ao finalizar instância: {e}")

    @classmethod
    def finalize_all(cls) -> None:
        """
        Finaliza e remove todas as instâncias síncronas.
        
        Example:
            >>> OnDemandRequestFactory.finalize_all()
        """
        with cls._lock:
            # Separa instâncias síncronas
            sync_keys = [
                key for key, inst in cls._instances.items()
                if not inst.is_async
            ]
            sync_instances = [cls._instances.pop(key) for key in sync_keys]
        
        for instance in sync_instances:
            try:
                instance.instance.dispose()
            except Exception as e:
                logger.warning(f"Erro ao finalizar instância: {e}")
        
        logger.info(f"Finalizadas {len(sync_instances)} instâncias síncronas")

    @classmethod
    def get_instance_count(cls) -> int:
        """Retorna o número de instâncias registradas."""
        with cls._lock:
            return len([i for i in cls._instances.values() if not i.is_async])

    @classmethod
    def clear(cls) -> None:
        """
        Remove todas as instâncias sem chamar dispose.
        
        Use apenas para testes ou limpeza emergencial.
        """
        with cls._lock:
            cls._instances.clear()
        logger.warning("Todas as instâncias foram removidas (sem dispose)")


__all__ = ["OnDemandRequestFactory"]
