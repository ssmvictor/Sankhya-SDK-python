"""
Módulo de entidades de transporte Sankhya.

Contém classes que representam entidades de domínio do sistema Sankhya,
com suporte a serialização/deserialização XML e rastreamento de campos.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/
"""

from .base import TransportEntityBase
from .address import Address
from .state import State
from .seller import Seller
from .neighborhood import Neighborhood
from .region import Region
from .city import City
from .partner_complement import PartnerComplement
from .product_cost import ProductCost
from .code_bars import CodeBars
from .partner import Partner
from .product import Product
from .invoice_header import InvoiceHeader
from .product_suggested_sale import ProductSuggestedSale
from .service_file import ServiceFile
from .enum_helpers import serialize_enum, deserialize_enum, get_enum_by_internal_value

# Rebuild models to resolve forward references
# This is required because we use TYPE_CHECKING imports for circular dependencies
Region.model_rebuild()
City.model_rebuild()
PartnerComplement.model_rebuild()
Partner.model_rebuild()
Product.model_rebuild()
InvoiceHeader.model_rebuild()
ProductSuggestedSale.model_rebuild()
ServiceFile.model_rebuild()

__all__ = [
    "TransportEntityBase",
    "Address",
    "State",
    "Region",
    "City",
    "Seller",
    "Neighborhood",
    "PartnerComplement",
    "ProductCost",
    "CodeBars",
    "Partner",
    "Product",
    "InvoiceHeader",
    "ProductSuggestedSale",
    "ServiceFile",
    "serialize_enum",
    "deserialize_enum",
    "get_enum_by_internal_value",
]
