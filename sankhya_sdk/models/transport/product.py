"""
Entidade Product (Produto) para o SDK Sankhya.

Representa um produto no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/Product.cs
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import Field

from .base import TransportEntityBase
from .code_bars import CodeBars
from .product_cost import ProductCost
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_ignore,
)
from ...enums.product_source import ProductSource
from ...enums.product_use import ProductUse

if TYPE_CHECKING:
    from .product_suggested_sale import ProductSuggestedSale
    from .service_file import ServiceFile


@entity("Produto")
class Product(TransportEntityBase):
    """
    Representa um produto no sistema Sankhya.
    
    Mapeia para a entidade "Produto" no XML.
    
    Attributes:
        code: Código do produto (chave primária - CODPROD)
        is_active: Se está ativo (ATIVO)
        name: Descrição do produto (DESCRPROD)
        complement: Complemento da descrição (COMPLDESC)
        description: Características (CARACTERISTICAS)
        code_volume: Código do volume (CODVOL)
        code_volume_component: Código do volume componente (ignorado)
        code_group: Código do grupo de produtos (CODGRUPOPROD)
        net_weight: Peso líquido (PESOLIQ)
        gross_weight: Peso bruto (PESOBRUTO)
        quantity: Quantidade (ignorado)
        brand: Marca (MARCA)
        reference: Referência (REFERENCIA)
        width: Largura (LARGURA)
        height: Altura (ALTURA)
        length: Espessura (ESPESSURA)
        ncm: NCM (NCM)
        source: Origem do produto (ORIGPROD)
        use: Uso do produto (USOPROD)
        is_sale_allowed_outside_kit: Venda individual permitida (VENCOMPINDIV)
        product_father: Produto pai
        product_replacement: Produto substituto
        cost: Custo do produto (ignorado)
        components: Lista de componentes do produto
        codes_bars: Lista de códigos de barras
    """
    
    # Campos básicos
    code: int = entity_key(
        entity_element("CODPROD", default=0)
    )
    
    is_active: Optional[bool] = entity_element(
        "ATIVO",
        default=None
    )
    
    name: Optional[str] = entity_element(
        "DESCRPROD",
        default=None
    )
    
    complement: Optional[str] = entity_element(
        "COMPLDESC",
        default=None
    )
    
    description: Optional[str] = entity_element(
        "CARACTERISTICAS",
        default=None
    )
    
    code_volume: Optional[str] = entity_element(
        "CODVOL",
        default=None
    )
    
    code_volume_component: Optional[str] = entity_ignore(default=None)
    
    code_group: Optional[int] = entity_element(
        "CODGRUPOPROD",
        default=None
    )
    
    net_weight: Optional[Decimal] = entity_element(
        "PESOLIQ",
        default=None
    )
    
    gross_weight: Optional[Decimal] = entity_element(
        "PESOBRUTO",
        default=None
    )
    
    quantity: Optional[Decimal] = entity_ignore(default=None)
    
    brand: Optional[str] = entity_element(
        "MARCA",
        default=None
    )
    
    reference: Optional[str] = entity_element(
        "REFERENCIA",
        default=None
    )
    
    width: Optional[Decimal] = entity_element(
        "LARGURA",
        default=None
    )
    
    height: Optional[Decimal] = entity_element(
        "ALTURA",
        default=None
    )
    
    length: Optional[Decimal] = entity_element(
        "ESPESSURA",
        default=None
    )
    
    ncm: Optional[str] = entity_element(
        "NCM",
        default=None
    )
    
    # Enums
    source: Optional[ProductSource] = entity_element(
        "ORIGPROD",
        default=None
    )
    
    use: Optional[ProductUse] = entity_element(
        "USOPROD",
        default=None
    )
    
    is_sale_allowed_outside_kit: Optional[bool] = entity_element(
        "VENCOMPINDIV",
        default=None
    )
    
    # Relacionamentos - self-reference usando forward reference
    product_father: Optional["Product"] = entity_reference(
        "Produto_AD001",
        default=None
    )
    
    product_replacement: Optional["Product"] = entity_reference(
        "Produto_AD002",
        default=None
    )
    
    # Custo - ignorado na serialização
    cost: Optional[ProductCost] = entity_ignore(default=None)
    
    components: List["Product"] = Field(default_factory=list)
    codes_bars: List[CodeBars] = Field(default_factory=list)
    
    # Coleções adicionais
    suggestions: List["ProductSuggestedSale"] = Field(default_factory=list)
    alternative_images: List["ServiceFile"] = Field(default_factory=list)
    
    # Imagem principal - ignorada na serialização por enquanto
    image: Optional["ServiceFile"] = entity_ignore(default=None)
    
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
        Compara duas instâncias de Product.
        
        Strings são comparadas de forma case-insensitive.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, Product):
            return False
        
        # Compare primitive fields
        if not (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self.is_active == other.is_active
            and ("is_active" in self._fields_set) == ("is_active" in other._fields_set)
            and self._compare_optional_str_ci(self.name, other.name)
            and ("name" in self._fields_set) == ("name" in other._fields_set)
            and self._compare_optional_str_ci(self.complement, other.complement)
            and ("complement" in self._fields_set) == ("complement" in other._fields_set)
            and self._compare_optional_str_ci(self.description, other.description)
            and ("description" in self._fields_set) == ("description" in other._fields_set)
            and self._compare_optional_str_ci(self.code_volume, other.code_volume)
            and ("code_volume" in self._fields_set) == ("code_volume" in other._fields_set)
            and self._compare_optional_str_ci(self.code_volume_component, other.code_volume_component)
            and ("code_volume_component" in self._fields_set) == ("code_volume_component" in other._fields_set)
            and self.code_group == other.code_group
            and ("code_group" in self._fields_set) == ("code_group" in other._fields_set)
            and self.net_weight == other.net_weight
            and ("net_weight" in self._fields_set) == ("net_weight" in other._fields_set)
            and self.gross_weight == other.gross_weight
            and ("gross_weight" in self._fields_set) == ("gross_weight" in other._fields_set)
            and self.quantity == other.quantity
            and ("quantity" in self._fields_set) == ("quantity" in other._fields_set)
            and self._compare_optional_str_ci(self.brand, other.brand)
            and ("brand" in self._fields_set) == ("brand" in other._fields_set)
            and self._compare_optional_str_ci(self.reference, other.reference)
            and ("reference" in self._fields_set) == ("reference" in other._fields_set)
            and self.width == other.width
            and ("width" in self._fields_set) == ("width" in other._fields_set)
            and self.height == other.height
            and ("height" in self._fields_set) == ("height" in other._fields_set)
            and self.length == other.length
            and ("length" in self._fields_set) == ("length" in other._fields_set)
            and self.source == other.source
            and ("source" in self._fields_set) == ("source" in other._fields_set)
            and self.is_sale_allowed_outside_kit == other.is_sale_allowed_outside_kit
            and ("is_sale_allowed_outside_kit" in self._fields_set) == ("is_sale_allowed_outside_kit" in other._fields_set)
            and self._compare_optional_str_ci(self.ncm, other.ncm)
            and ("ncm" in self._fields_set) == ("ncm" in other._fields_set)
            and self.use == other.use
            and ("use" in self._fields_set) == ("use" in other._fields_set)
        ):
            return False
        
        # Compare relationships
        if not (
            self.product_father == other.product_father
            and ("product_father" in self._fields_set) == ("product_father" in other._fields_set)
            and self.product_replacement == other.product_replacement
            and ("product_replacement" in self._fields_set) == ("product_replacement" in other._fields_set)
            and self.cost == other.cost
            and ("cost" in self._fields_set) == ("cost" in other._fields_set)
        ):
            return False
        
        # Compare collections
        return (
            self.components == other.components
            and self.codes_bars == other.codes_bars
        )
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa o mesmo algoritmo do SDK .NET para compatibilidade.
        """
        hash_code = self.code
        hash_code = (hash_code * 397) ^ hash("code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_active or False)
        hash_code = (hash_code * 397) ^ hash("is_active" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.name.lower()) if self.name else 0
        )
        hash_code = (hash_code * 397) ^ hash("name" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.complement.lower()) if self.complement else 0
        )
        hash_code = (hash_code * 397) ^ hash("complement" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.description.lower()) if self.description else 0
        )
        hash_code = (hash_code * 397) ^ hash("description" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.code_volume.lower()) if self.code_volume else 0
        )
        hash_code = (hash_code * 397) ^ hash("code_volume" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.code_volume_component.lower()) if self.code_volume_component else 0
        )
        hash_code = (hash_code * 397) ^ hash("code_volume_component" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_group or 0)
        hash_code = (hash_code * 397) ^ hash("code_group" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.net_weight) if self.net_weight else 0)
        hash_code = (hash_code * 397) ^ hash("net_weight" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.gross_weight) if self.gross_weight else 0)
        hash_code = (hash_code * 397) ^ hash("gross_weight" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.quantity) if self.quantity else 0)
        hash_code = (hash_code * 397) ^ hash("quantity" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.brand.lower()) if self.brand else 0
        )
        hash_code = (hash_code * 397) ^ hash("brand" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.reference.lower()) if self.reference else 0
        )
        hash_code = (hash_code * 397) ^ hash("reference" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.width) if self.width else 0)
        hash_code = (hash_code * 397) ^ hash("width" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.height) if self.height else 0)
        hash_code = (hash_code * 397) ^ hash("height" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.length) if self.length else 0)
        hash_code = (hash_code * 397) ^ hash("length" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.source.value) if self.source else 0)
        hash_code = (hash_code * 397) ^ hash("source" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_sale_allowed_outside_kit or False)
        hash_code = (hash_code * 397) ^ hash("is_sale_allowed_outside_kit" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.ncm.lower()) if self.ncm else 0
        )
        hash_code = (hash_code * 397) ^ hash("ncm" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.use.value) if self.use else 0)
        hash_code = (hash_code * 397) ^ hash("use" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.product_father) if self.product_father else 0)
        hash_code = (hash_code * 397) ^ hash("product_father" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.product_replacement) if self.product_replacement else 0)
        hash_code = (hash_code * 397) ^ hash("product_replacement" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.cost) if self.cost else 0)
        hash_code = (hash_code * 397) ^ hash("cost" in self._fields_set)
        
        # Collections
        hash_code = (hash_code * 397) ^ (hash(tuple(self.components)) if self.components else 0)
        hash_code = (hash_code * 397) ^ (hash(tuple(self.codes_bars)) if self.codes_bars else 0)
        
        return hash_code
