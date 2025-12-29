# -*- coding: utf-8 -*-
"""
Factory assíncrono para gerenciamento de AsyncOnDemandRequestWrappers.

Implementa padrão factory com gerenciamento thread-safe de instâncias assíncronas.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/OnDemandRequestFactory.cs
"""

from __future__ import annotations

import asyncio
import logging
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
from sankhya_sdk.request_wrappers.async_on_demand_request_wrapper import (
    AsyncOnDemandRequestWrapper,
)
from sankhya_sdk.request_wrappers.interfaces import IAsyncOnDemandRequestWrapper
from sankhya_sdk.value_objects.on_demand_request_instance import OnDemandRequestInstance


logger = logging.getLogger(__name__)

# TypeVar para entidades genéricas
TEntity = TypeVar("TEntity", bound=EntityBase)


class AsyncOnDemandRequestFactory:
    """
    Factory para criação e gerenciamento de AsyncOnDemandRequestWrappers.
    
    Gerencia instâncias assíncronas de forma centralizada,
    permitindo criar, buscar, flush e finalizar wrappers.
    
    Usa asyncio.Lock para operações thread-safe em contexto assíncrono.
    
    Example:
        >>> cancel_event = asyncio.Event()
        >>> key = await AsyncOnDemandRequestFactory.create_instance(
        ...     Partner,
        ...     ServiceName.CRUD_SERVICE_SAVE,
        ...     cancel_event,
        ...     context
        ... )
        >>> wrapper = await AsyncOnDemandRequestFactory.get_instance_by_key(key)
        >>> await wrapper.add(partner)
        >>> await AsyncOnDemandRequestFactory.flush_all()
        >>> await AsyncOnDemandRequestFactory.finalize_all()
    """

    # Class-level attributes
    _instances: ClassVar[Dict[UUID, OnDemandRequestInstance]] = {}
    _lock: ClassVar[Optional[asyncio.Lock]] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Obtém ou cria o lock assíncrono."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def create_instance(
        cls,
        entity_type: Type[TEntity],
        service: ServiceName,
        cancel_event: asyncio.Event,
        context: Optional["SankhyaContext"] = None,
        throughput: int = 10,
        allow_above_throughput: bool = True,
    ) -> UUID:
        """
        Cria uma nova instância de wrapper assíncrono e retorna seu UUID.
        
        Args:
            entity_type: Tipo da entidade a ser processada
            service: Nome do serviço a usar
            cancel_event: Evento asyncio para sinalizar cancelamento
            context: Contexto Sankhya (cria nova sessão se fornecido)
            throughput: Número máximo de entidades por lote
            allow_above_throughput: Se True, processa antes de atingir throughput
            
        Returns:
            UUID identificador da instância criada
            
        Example:
            >>> key = await AsyncOnDemandRequestFactory.create_instance(
            ...     Partner,
            ...     ServiceName.CRUD_SERVICE_SAVE,
            ...     cancel_event
            ... )
        """
        # Cria sessão dedicada se contexto fornecido
        session_token: Optional[UUID] = None
        if context:
            session_token = context.acquire_new_session(
                ServiceRequestType.ON_DEMAND_CRUD
            )
        
        # Cria wrapper
        wrapper: AsyncOnDemandRequestWrapper[TEntity] = AsyncOnDemandRequestWrapper(
            service=service,
            cancel_event=cancel_event,
            throughput=throughput,
            allow_above_throughput=allow_above_throughput,
            context=context,
            session_token=session_token,
        )
        
        # Inicia worker task
        await wrapper.start()
        
        # Gera chave única
        key = uuid4()
        
        # Cria instância de registro
        instance = OnDemandRequestInstance(
            key=key,
            service=service,
            entity_type=entity_type,
            instance=wrapper,
            is_async=True,
        )
        
        # Registra com lock
        async with cls._get_lock():
            cls._instances[key] = instance
        
        logger.info(
            f"AsyncOnDemandRequestWrapper criado: key={key}, "
            f"entity_type={entity_type.__name__}, "
            f"service={service.name}"
        )
        
        return key

    @classmethod
    async def get_instance_for_service(
        cls,
        entity_type: Type[TEntity],
        service: ServiceName,
    ) -> Optional[IAsyncOnDemandRequestWrapper]:
        """
        Busca uma instância existente para o serviço e tipo de entidade.
        
        Args:
            entity_type: Tipo da entidade
            service: Nome do serviço
            
        Returns:
            Instância do wrapper ou None se não encontrada
        """
        async with cls._get_lock():
            for instance in cls._instances.values():
                if (
                    instance.entity_type == entity_type and
                    instance.service == service and
                    instance.is_async
                ):
                    return instance.instance  # type: ignore
        return None

    @classmethod
    async def get_instance_by_key(
        cls, key: UUID
    ) -> Optional[IAsyncOnDemandRequestWrapper]:
        """
        Busca uma instância pelo seu UUID.
        
        Args:
            key: UUID da instância
            
        Returns:
            Instância do wrapper ou None se não encontrada
        """
        async with cls._get_lock():
            instance = cls._instances.get(key)
            if instance and instance.is_async:
                return instance.instance  # type: ignore
        return None

    @classmethod
    async def flush_by_key(cls, key: UUID) -> None:
        """
        Força flush em uma instância específica.
        
        Args:
            key: UUID da instância
        """
        async with cls._get_lock():
            instance = cls._instances.get(key)
        
        if instance and instance.is_async:
            await instance.instance.flush()  # type: ignore
            logger.debug(f"Flush executado: key={key}")

    @classmethod
    async def flush_all(cls) -> None:
        """Força flush em todas as instâncias assíncronas."""
        async with cls._get_lock():
            instances = [
                inst for inst in cls._instances.values()
                if inst.is_async
            ]
        
        for instance in instances:
            try:
                await instance.instance.flush()  # type: ignore
            except Exception as e:
                logger.warning(f"Erro ao fazer flush: {e}")
        
        logger.debug(f"Flush executado em {len(instances)} instâncias assíncronas")

    @classmethod
    async def finalize_by_key(cls, key: UUID) -> None:
        """
        Finaliza e remove uma instância específica.
        
        Args:
            key: UUID da instância
        """
        async with cls._get_lock():
            instance = cls._instances.pop(key, None)
        
        if instance and instance.is_async:
            try:
                await instance.instance.dispose()  # type: ignore
                logger.debug(f"Instância assíncrona finalizada: key={key}")
            except Exception as e:
                logger.warning(f"Erro ao finalizar instância: {e}")

    @classmethod
    async def finalize_all(cls) -> None:
        """Finaliza e remove todas as instâncias assíncronas."""
        async with cls._get_lock():
            # Separa instâncias assíncronas
            async_keys = [
                key for key, inst in cls._instances.items()
                if inst.is_async
            ]
            async_instances = [cls._instances.pop(key) for key in async_keys]
        
        for instance in async_instances:
            try:
                await instance.instance.dispose()  # type: ignore
            except Exception as e:
                logger.warning(f"Erro ao finalizar instância: {e}")
        
        logger.info(f"Finalizadas {len(async_instances)} instâncias assíncronas")

    @classmethod
    async def get_instance_count(cls) -> int:
        """Retorna o número de instâncias assíncronas registradas."""
        async with cls._get_lock():
            return len([i for i in cls._instances.values() if i.is_async])

    @classmethod
    async def clear(cls) -> None:
        """
        Remove todas as instâncias assíncronas sem chamar dispose.
        
        Use apenas para testes ou limpeza emergencial.
        """
        async with cls._get_lock():
            cls._instances = {
                k: v for k, v in cls._instances.items()
                if not v.is_async
            }
        logger.warning("Todas as instâncias assíncronas foram removidas (sem dispose)")


__all__ = ["AsyncOnDemandRequestFactory"]
