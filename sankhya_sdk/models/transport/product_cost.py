"""
Entidade ProductCost (Custo) para o SDK Sankhya.

Representa o custo de um produto no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/ProductCost.cs
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from .base import TransportEntityBase
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
)


@entity("Custo")
class ProductCost(TransportEntityBase):
    """
    Representa o custo de um produto no sistema Sankhya.
    
    Mapeia para a entidade "Custo" no XML.
    
    Attributes:
        code_product: Código do produto (chave primária - CODPROD)
        code_company: Código da empresa (CODEMP)
        date: Data de atualização (chave primária - DTATUAL)
        code_local: Código do local (chave primária - CODLOCAL)
        control: Controle (chave primária - CONTROLE)
        single_number: Número único (chave primária - NUNOTA)
        sequence: Sequência (chave primária - SEQUENCIA)
        cost_replacement: Custo de reposição (CUSREP)
    """
    
    code_product: int = entity_key(
        entity_element("CODPROD", default=0)
    )
    
    code_company: Optional[int] = entity_element(
        "CODEMP",
        default=None
    )
    
    date: Optional[datetime] = entity_key(
        entity_element("DTATUAL", default=None)
    )
    
    code_local: Optional[int] = entity_key(
        entity_element("CODLOCAL", default=None)
    )
    
    control: Optional[str] = entity_key(
        entity_element("CONTROLE", default=None)
    )
    
    single_number: Optional[int] = entity_key(
        entity_element("NUNOTA", default=None)
    )
    
    sequence: Optional[int] = entity_key(
        entity_element("SEQUENCIA", default=None)
    )
    
    cost_replacement: Optional[Decimal] = entity_element(
        "CUSREP",
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
        Compara duas instâncias de ProductCost.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, ProductCost):
            return False
        
        return (
            self.code_product == other.code_product
            and ("code_product" in self._fields_set) == (
                "code_product" in other._fields_set
            )
            and self.code_company == other.code_company
            and ("code_company" in self._fields_set) == (
                "code_company" in other._fields_set
            )
            and self.date == other.date
            and ("date" in self._fields_set) == ("date" in other._fields_set)
            and self.code_local == other.code_local
            and ("code_local" in self._fields_set) == (
                "code_local" in other._fields_set
            )
            and self._compare_optional_str_ci(self.control, other.control)
            and ("control" in self._fields_set) == (
                "control" in other._fields_set
            )
            and self.single_number == other.single_number
            and ("single_number" in self._fields_set) == (
                "single_number" in other._fields_set
            )
            and self.sequence == other.sequence
            and ("sequence" in self._fields_set) == (
                "sequence" in other._fields_set
            )
            and self.cost_replacement == other.cost_replacement
            and ("cost_replacement" in self._fields_set) == (
                "cost_replacement" in other._fields_set
            )
        )
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa o mesmo algoritmo do SDK .NET para compatibilidade.
        """
        hash_code = self.code_product
        hash_code = (hash_code * 397) ^ hash("code_product" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_company or 0)
        hash_code = (hash_code * 397) ^ hash("code_company" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.date) if self.date else 0)
        hash_code = (hash_code * 397) ^ hash("date" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_local or 0)
        hash_code = (hash_code * 397) ^ hash("code_local" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.control.lower()) if self.control else 0
        )
        hash_code = (hash_code * 397) ^ hash("control" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.single_number or 0)
        hash_code = (hash_code * 397) ^ hash("single_number" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.sequence or 0)
        hash_code = (hash_code * 397) ^ hash("sequence" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.cost_replacement) if self.cost_replacement else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "cost_replacement" in self._fields_set
        )
        
        return hash_code
