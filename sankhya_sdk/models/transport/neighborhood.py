"""
Entidade Neighborhood (Bairro) para o SDK Sankhya.

Representa um bairro no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/Neighborhood.cs
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import TransportEntityBase
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
)


@entity("Bairro")
class Neighborhood(TransportEntityBase):
    """
    Representa um bairro no sistema Sankhya.
    
    Mapeia para a entidade "Bairro" no XML.
    
    Attributes:
        code: Código do bairro (chave primária - CODBAI)
        name: Nome do bairro (NOMEBAI)
        description_correios: Descrição do correio (DESCRICAOCORREIO)
        date_changed: Data de alteração (DTALTER)
    """
    
    code: int = entity_key(
        entity_element("CODBAI", default=0)
    )
    
    name: Optional[str] = entity_element(
        "NOMEBAI",
        default=None
    )
    
    description_correios: Optional[str] = entity_element(
        "DESCRICAOCORREIO",
        default=None
    )
    
    date_changed: Optional[datetime] = entity_element(
        "DTALTER",
        default=None
    )
    
    @staticmethod
    def _compare_optional_str_ci(a: Optional[str], b: Optional[str]) -> bool:
        """Compara duas strings opcionais de forma case-insensitive."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return a.lower() == b.lower()
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas instâncias de Neighborhood.
        
        Strings são comparadas de forma case-insensitive para manter
        compatibilidade com o SDK .NET.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, Neighborhood):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self._compare_optional_str_ci(self.name, other.name)
            and ("name" in self._fields_set) == ("name" in other._fields_set)
            and self._compare_optional_str_ci(
                self.description_correios, 
                other.description_correios
            )
            and ("description_correios" in self._fields_set) == (
                "description_correios" in other._fields_set
            )
            and self.date_changed == other.date_changed
            and ("date_changed" in self._fields_set) == (
                "date_changed" in other._fields_set
            )
        )
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa o mesmo algoritmo do SDK .NET para compatibilidade.
        """
        hash_code = self.code
        hash_code = (hash_code * 397) ^ hash("code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.name.lower()) if self.name else 0
        )
        hash_code = (hash_code * 397) ^ hash("name" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.description_correios.lower()) 
            if self.description_correios else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "description_correios" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.date_changed) if self.date_changed else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "date_changed" in self._fields_set
        )
        
        return hash_code
