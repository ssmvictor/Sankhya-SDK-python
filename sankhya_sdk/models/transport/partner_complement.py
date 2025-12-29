"""
Entidade PartnerComplement (ComplementoParc) para o SDK Sankhya.

Representa dados complementares de um parceiro no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/PartnerComplement.cs
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TransportEntityBase
from .neighborhood import Neighborhood
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_custom_data,
)

if TYPE_CHECKING:
    from .address import Address
    from .city import City


@entity("ComplementoParc")
class PartnerComplement(TransportEntityBase):
    """
    Representa dados complementares de um parceiro no sistema Sankhya.
    
    Mapeia para a entidade "ComplementoParc" no XML, com campos para
    endereço de entrega.
    
    Attributes:
        code: Código do parceiro (chave primária - CODPARC)
        zip_code_delivery: CEP de entrega (CEPENTREGA)
        code_address_delivery: Código do endereço de entrega (CODENDENTREGA)
        address_number_delivery: Número do endereço de entrega (NUMENTREGA)
        address_complement_delivery: Complemento do endereço (COMPLENTREGA)
        code_neighborhood_delivery: Código do bairro de entrega (CODBAIENTREGA)
        code_city_delivery: Código da cidade de entrega (CODCIDENTREGA)
        latitude_delivery: Latitude de entrega (LATITUDEENTREGA)
        longitude_delivery: Longitude de entrega (LONGITUDEENTREGA)
        address_delivery: Referência ao endereço de entrega
        neighborhood_delivery: Referência ao bairro de entrega
        city_delivery: Referência à cidade de entrega
    """
    
    code: int = entity_key(
        entity_element("CODPARC", default=0)
    )
    
    zip_code_delivery: Optional[str] = entity_element(
        "CEPENTREGA",
        default=None
    )
    
    code_address_delivery: Optional[int] = entity_element(
        "CODENDENTREGA",
        default=None
    )
    
    address_number_delivery: Optional[str] = entity_element(
        "NUMENTREGA",
        default=None
    )
    
    address_complement_delivery: Optional[str] = entity_custom_data(
        max_length=30,
        field=entity_element("COMPLENTREGA", default=None)
    )
    
    code_neighborhood_delivery: Optional[int] = entity_element(
        "CODBAIENTREGA",
        default=None
    )
    
    code_city_delivery: Optional[int] = entity_element(
        "CODCIDENTREGA",
        default=None
    )
    
    latitude_delivery: Optional[str] = entity_element(
        "LATITUDEENTREGA",
        default=None
    )
    
    longitude_delivery: Optional[str] = entity_element(
        "LONGITUDEENTREGA",
        default=None
    )
    
    # Relacionamentos
    address_delivery: Optional["Address"] = entity_reference(default=None)
    neighborhood_delivery: Optional[Neighborhood] = entity_reference(default=None)
    city_delivery: Optional["City"] = entity_reference(default=None)
    
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
        Compara duas instâncias de PartnerComplement.
        
        Strings são comparadas de forma case-insensitive.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, PartnerComplement):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self._compare_optional_str_ci(
                self.zip_code_delivery, other.zip_code_delivery
            )
            and ("zip_code_delivery" in self._fields_set) == (
                "zip_code_delivery" in other._fields_set
            )
            and self.code_address_delivery == other.code_address_delivery
            and ("code_address_delivery" in self._fields_set) == (
                "code_address_delivery" in other._fields_set
            )
            and self._compare_optional_str_ci(
                self.address_number_delivery, other.address_number_delivery
            )
            and ("address_number_delivery" in self._fields_set) == (
                "address_number_delivery" in other._fields_set
            )
            and self._compare_optional_str_ci(
                self.address_complement_delivery, other.address_complement_delivery
            )
            and ("address_complement_delivery" in self._fields_set) == (
                "address_complement_delivery" in other._fields_set
            )
            and self.code_neighborhood_delivery == other.code_neighborhood_delivery
            and ("code_neighborhood_delivery" in self._fields_set) == (
                "code_neighborhood_delivery" in other._fields_set
            )
            and self.code_city_delivery == other.code_city_delivery
            and ("code_city_delivery" in self._fields_set) == (
                "code_city_delivery" in other._fields_set
            )
            and self._compare_optional_str_ci(
                self.latitude_delivery, other.latitude_delivery
            )
            and ("latitude_delivery" in self._fields_set) == (
                "latitude_delivery" in other._fields_set
            )
            and self._compare_optional_str_ci(
                self.longitude_delivery, other.longitude_delivery
            )
            and ("longitude_delivery" in self._fields_set) == (
                "longitude_delivery" in other._fields_set
            )
            and self.address_delivery == other.address_delivery
            and ("address_delivery" in self._fields_set) == (
                "address_delivery" in other._fields_set
            )
            and self.neighborhood_delivery == other.neighborhood_delivery
            and ("neighborhood_delivery" in self._fields_set) == (
                "neighborhood_delivery" in other._fields_set
            )
            and self.city_delivery == other.city_delivery
            and ("city_delivery" in self._fields_set) == (
                "city_delivery" in other._fields_set
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
            hash(self.zip_code_delivery.lower()) 
            if self.zip_code_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "zip_code_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_address_delivery or 0)
        hash_code = (hash_code * 397) ^ hash(
            "code_address_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.address_number_delivery.lower()) 
            if self.address_number_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "address_number_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.address_complement_delivery.lower()) 
            if self.address_complement_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "address_complement_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_neighborhood_delivery or 0)
        hash_code = (hash_code * 397) ^ hash(
            "code_neighborhood_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_city_delivery or 0)
        hash_code = (hash_code * 397) ^ hash(
            "code_city_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.latitude_delivery.lower()) 
            if self.latitude_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "latitude_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.longitude_delivery.lower()) 
            if self.longitude_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "longitude_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.address_delivery) if self.address_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "address_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.neighborhood_delivery) if self.neighborhood_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "neighborhood_delivery" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.city_delivery) if self.city_delivery else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "city_delivery" in self._fields_set
        )
        
        return hash_code
