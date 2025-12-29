"""
Entidade CodeBars (CodigoBarras) para o SDK Sankhya.

Representa um código de barras de produto no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/CodeBars.cs
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


@entity("CodigoBarras")
class CodeBars(TransportEntityBase):
    """
    Representa um código de barras de produto no sistema Sankhya.
    
    Mapeia para a entidade "CodigoBarras" no XML.
    
    Attributes:
        code: Código de barras (chave primária - CODBARRA)
        code_product: Código do produto (CODPROD)
        code_user: Código do usuário (CODUSU)
        code_volume: Código do volume (CODVOL)
        date_changed: Data de alteração (DHALTER)
    """
    
    code: Optional[str] = entity_key(
        entity_element("CODBARRA", default=None)
    )
    
    code_product: Optional[int] = entity_element(
        "CODPROD",
        default=None
    )
    
    code_user: Optional[int] = entity_element(
        "CODUSU",
        default=None
    )
    
    code_volume: Optional[str] = entity_element(
        "CODVOL",
        default=None
    )
    
    date_changed: Optional[datetime] = entity_element(
        "DHALTER",
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
        Compara duas instâncias de CodeBars.
        
        Strings são comparadas de forma case-insensitive.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, CodeBars):
            return False
        
        return (
            self._compare_optional_str_ci(self.code, other.code)
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self.code_product == other.code_product
            and ("code_product" in self._fields_set) == (
                "code_product" in other._fields_set
            )
            and self.code_user == other.code_user
            and ("code_user" in self._fields_set) == (
                "code_user" in other._fields_set
            )
            and self._compare_optional_str_ci(self.code_volume, other.code_volume)
            and ("code_volume" in self._fields_set) == (
                "code_volume" in other._fields_set
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
        hash_code = hash(self.code.lower()) if self.code else 0
        hash_code = (hash_code * 397) ^ hash("code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_product or 0)
        hash_code = (hash_code * 397) ^ hash("code_product" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_user or 0)
        hash_code = (hash_code * 397) ^ hash("code_user" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.code_volume.lower()) if self.code_volume else 0
        )
        hash_code = (hash_code * 397) ^ hash("code_volume" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.date_changed) if self.date_changed else 0
        )
        hash_code = (hash_code * 397) ^ hash("date_changed" in self._fields_set)
        
        return hash_code
