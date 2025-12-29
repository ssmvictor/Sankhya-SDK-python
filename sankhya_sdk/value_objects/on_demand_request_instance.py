# -*- coding: utf-8 -*-
"""
Value Object para instâncias de OnDemandRequestWrapper.

Armazena informações sobre instâncias de wrappers gerenciadas pelo factory.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/OnDemandRequestFactory.cs
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Type, Union
from uuid import UUID

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.base import EntityBase

if TYPE_CHECKING:
    from sankhya_sdk.request_wrappers.interfaces import (
        IOnDemandRequestWrapper,
        IAsyncOnDemandRequestWrapper,
    )


@dataclass(frozen=True, slots=True)
class OnDemandRequestInstance:
    """
    Representa uma instância de wrapper de requisição on-demand.
    
    Armazena metadados sobre a instância para gerenciamento pelo factory.
    
    Attributes:
        key: Identificador único da instância (UUID).
        service: Nome do serviço associado.
        entity_type: Tipo da entidade processada pelo wrapper.
        instance: Referência à instância do wrapper.
        is_async: Indica se é uma instância assíncrona.
    """

    key: UUID
    service: ServiceName
    entity_type: Type[EntityBase]
    instance: Union["IOnDemandRequestWrapper", "IAsyncOnDemandRequestWrapper"]
    is_async: bool = False

    def __repr__(self) -> str:
        return (
            f"OnDemandRequestInstance("
            f"key={self.key!r}, "
            f"service={self.service.name}, "
            f"entity_type={self.entity_type.__name__}, "
            f"is_async={self.is_async})"
        )


__all__ = ["OnDemandRequestInstance"]
