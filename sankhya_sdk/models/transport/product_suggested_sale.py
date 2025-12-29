"""
Entidade ProductSuggestedSale para o SDK Sankhya.

Representa uma sugestão de venda de produto.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/ProductSuggestedSale.cs
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from .base import TransportEntityBase
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
)


@entity("SugestaoVenda")
class ProductSuggestedSale(TransportEntityBase):
    """
    Representa uma sugestão de venda de produto.
    
    Mapeia para a entidade "SugestaoVenda" no XML.
    """
    
    code: int = entity_key(
        entity_element("CODSUGESTAO", default=0)
    )
    
    code_product: Optional[int] = entity_element(
        "CODPROD",
        default=None
    )
    
    code_product_suggested: Optional[int] = entity_element(
        "CODPRODSUGERIDO",
        default=None
    )
    
    quantity: Optional[Decimal] = entity_element(
        "QTDSUGERIDA",
        default=None
    )
    
    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if self is other:
            return True
        if not isinstance(other, ProductSuggestedSale):
            return False
        
        return (
            self.code == other.code
            and self.code_product == other.code_product
            and self.code_product_suggested == other.code_product_suggested
            and self.quantity == other.quantity
        )
    
    def __hash__(self) -> int:
        return hash((self.code, self.code_product, self.code_product_suggested))
