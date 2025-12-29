"""
Entidade ServiceFile para o SDK Sankhya.

Representa um arquivo de serviço (imagem, documento).

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/ServiceFile.cs
"""

from __future__ import annotations

from typing import Optional

from .base import TransportEntityBase
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
)


@entity("ArquivoServico")
class ServiceFile(TransportEntityBase):
    """
    Representa um arquivo de serviço (imagem, documento).
    
    Mapeia para a entidade "ArquivoServico" no XML.
    """
    
    code: int = entity_key(
        entity_element("CODARQUIVO", default=0)
    )
    
    name: Optional[str] = entity_element(
        "NOME",
        default=None
    )
    
    extension: Optional[str] = entity_element(
        "EXTENSAO",
        default=None
    )
    
    path: Optional[str] = entity_element(
        "CAMINHO",
        default=None
    )
    
    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if self is other:
            return True
        if not isinstance(other, ServiceFile):
            return False
        
        return (
            self.code == other.code
            and self.name == other.name
            and self.extension == other.extension
            and self.path == other.path
        )
    
    def __hash__(self) -> int:
        return hash((self.code, self.name))
