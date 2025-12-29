"""
Entidade Region (Região) para o SDK Sankhya.

Representa uma região no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/Region.cs
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .seller import Seller

from .base import TransportEntityBase
from ..service.xml_serialization import serialize_bool, deserialize_bool
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_ignore,
)


@entity("Regiao")
class Region(TransportEntityBase):
    """
    Representa uma região no sistema Sankhya.
    
    Mapeia para a entidade "Regiao" no XML, com campos como código,
    código da região pai, código da tabela de preços, código do vendedor,
    status ativo e nome.
    
    O campo `active` é uma propriedade computada que converte de/para
    `active_internal` (string "S" ou "N").
    
    Attributes:
        code: Código da região (chave primária - CODREG)
        code_region_father: Código da região pai (CODREGPAI)
        code_price_table: Código da tabela de preços (CODTAB)
        code_seller: Código do vendedor (CODVEND)
        active_internal: Status ativo como string "S"/"N" (ATIVA)
        name: Nome da região (NOMEREG)
        seller: Referência ao vendedor
    """
    
    code: int = entity_key(
        entity_element("CODREG", default=0)
    )
    
    code_region_father: Optional[int] = entity_element(
        "CODREGPAI",
        default=None
    )
    
    code_price_table: Optional[int] = entity_element(
        "CODTAB",
        default=None
    )
    
    code_seller: Optional[int] = entity_element(
        "CODVEND",
        default=None
    )
    
    # Campo interno para serialização - NÃO usar diretamente
    active_internal: Optional[str] = entity_element(
        "ATIVA",
        default=None
    )
    
    name: Optional[str] = entity_element(
        "NOMEREG",
        default=None
    )
    
    # Referência ao vendedor - usa string literal para evitar import circular
    seller: Optional["Seller"] = entity_reference(default=None)
    
    @property
    def active(self) -> bool:
        """
        Retorna o status ativo como booleano.
        
        Converte de "S"/"N" para True/False.
        """
        if self.active_internal is None:
            return False
        return deserialize_bool(self.active_internal, "S|N")
    
    @active.setter
    def active(self, value: bool) -> None:
        """
        Define o status ativo.
        
        Converte o booleano para "S" ou "N" e armazena em active_internal.
        """
        self.active_internal = serialize_bool(value, "S|N")
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas instâncias de Region.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, Region):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self.code_region_father == other.code_region_father
            and ("code_region_father" in self._fields_set) == (
                "code_region_father" in other._fields_set
            )
            and self.code_price_table == other.code_price_table
            and ("code_price_table" in self._fields_set) == (
                "code_price_table" in other._fields_set
            )
            and self.code_seller == other.code_seller
            and ("code_seller" in self._fields_set) == (
                "code_seller" in other._fields_set
            )
            and self.active == other.active
            and ("active_internal" in self._fields_set) == (
                "active_internal" in other._fields_set
            )
            and self._compare_optional_str_ci(self.name, other.name)
            and ("name" in self._fields_set) == ("name" in other._fields_set)
            and self.seller == other.seller
            and ("seller" in self._fields_set) == ("seller" in other._fields_set)
        )
    
    @staticmethod
    def _compare_optional_str_ci(a: Optional[str], b: Optional[str]) -> bool:
        """Compara duas strings opcionais de forma case-insensitive."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return a.lower() == b.lower()
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa o mesmo algoritmo do SDK .NET para compatibilidade.
        """
        hash_code = self.code
        hash_code = (hash_code * 397) ^ hash("code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_region_father or 0)
        hash_code = (hash_code * 397) ^ hash(
            "code_region_father" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_price_table or 0)
        hash_code = (hash_code * 397) ^ hash(
            "code_price_table" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_seller or 0)
        hash_code = (hash_code * 397) ^ hash("code_seller" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.active)
        hash_code = (hash_code * 397) ^ hash(
            "active_internal" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.name.lower()) if self.name else 0
        )
        hash_code = (hash_code * 397) ^ hash("name" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.seller) if self.seller else 0
        )
        hash_code = (hash_code * 397) ^ hash("seller" in self._fields_set)
        
        return hash_code
