# -*- coding: utf-8 -*-
"""
Evento de falha para requisições on-demand.

Disparado quando uma entidade falha ao ser processada individualmente
após falha do processamento em lote.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Events/OnDemandRequestFailureEventArgs.cs
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from sankhya_sdk.models.base import EntityBase


@dataclass(frozen=True, slots=True)
class OnDemandRequestFailureEvent:
    """
    Evento disparado quando uma entidade falha no processamento on-demand.
    
    Usado para notificar handlers sobre falhas em entidades individuais
    quando o processamento em lote falha e o fallback individual também falha.
    
    Attributes:
        entity: A entidade que falhou ao ser processada.
        is_update: True se a operação era uma atualização, False se era criação.
        exception: A exceção que causou a falha.
        error_message: Mensagem de erro opcional para contexto adicional.
        retry_count: Número de tentativas que foram feitas.
    """

    entity: Any  # EntityBase, usando Any para evitar import circular
    is_update: bool
    exception: BaseException
    error_message: Optional[str] = None
    retry_count: int = 0

    def __repr__(self) -> str:
        entity_repr = (
            f"{type(self.entity).__name__}"
            if hasattr(self.entity, "__class__")
            else str(self.entity)
        )
        return (
            f"OnDemandRequestFailureEvent("
            f"entity={entity_repr}, "
            f"is_update={self.is_update}, "
            f"exception={type(self.exception).__name__}: {self.exception}, "
            f"retry_count={self.retry_count})"
        )

    @property
    def operation_type(self) -> str:
        """Retorna o tipo de operação como string legível."""
        return "update" if self.is_update else "create"


__all__ = ["OnDemandRequestFailureEvent"]
