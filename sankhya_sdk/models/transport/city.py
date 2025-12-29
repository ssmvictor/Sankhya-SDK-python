"""
Entidade City (Cidade) para o SDK Sankhya.

Representa uma cidade no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/City.cs
"""

from __future__ import annotations

from typing import Optional

from .base import TransportEntityBase
from .state import State
from .region import Region
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
)


@entity("Cidade")
class City(TransportEntityBase):
    """
    Representa uma cidade no sistema Sankhya.
    
    Mapeia para a entidade "Cidade" no XML, com campos como código,
    código do estado, código da região, código fiscal, nome, descrição
    do correio, DDD e coordenadas geográficas.
    
    Inclui relacionamentos com State e Region.
    
    Attributes:
        code: Código da cidade (chave primária - CODCID)
        code_state: Código do estado/UF (UF)
        code_region: Código da região (CODREG)
        code_fiscal: Código fiscal do município (CODMUNFIS)
        name: Nome da cidade (NOMECID)
        description_correios: Descrição do correio (DESCRICAOCORREIO)
        area_code: Código de área/DDD (DDD)
        latitude: Latitude da cidade (LATITUDE)
        longitude: Longitude da cidade (LONGITUDE)
        state: Referência ao estado
        region: Referência à região
    """
    
    code: int = entity_key(
        entity_element("CODCID", default=0)
    )
    
    code_state: Optional[int] = entity_element(
        "UF",
        default=None
    )
    
    code_region: Optional[int] = entity_element(
        "CODREG",
        default=None
    )
    
    code_fiscal: Optional[int] = entity_element(
        "CODMUNFIS",
        default=None
    )
    
    name: Optional[str] = entity_element(
        "NOMECID",
        default=None
    )
    
    description_correios: Optional[str] = entity_element(
        "DESCRICAOCORREIO",
        default=None
    )
    
    area_code: Optional[int] = entity_element(
        "DDD",
        default=None
    )
    
    latitude: Optional[str] = entity_element(
        "LATITUDE",
        default=None
    )
    
    longitude: Optional[str] = entity_element(
        "LONGITUDE",
        default=None
    )
    
    # Relacionamentos
    state: Optional[State] = entity_reference(default=None)
    region: Optional[Region] = entity_reference(default=None)
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas instâncias de City.
        
        Strings são comparadas de forma case-insensitive para manter
        compatibilidade com o SDK .NET.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, City):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self.code_state == other.code_state
            and ("code_state" in self._fields_set) == (
                "code_state" in other._fields_set
            )
            and self.code_region == other.code_region
            and ("code_region" in self._fields_set) == (
                "code_region" in other._fields_set
            )
            and self.code_fiscal == other.code_fiscal
            and ("code_fiscal" in self._fields_set) == (
                "code_fiscal" in other._fields_set
            )
            and self._compare_optional_str_ci(self.name, other.name)
            and ("name" in self._fields_set) == ("name" in other._fields_set)
            and self._compare_optional_str_ci(
                self.description_correios, 
                other.description_correios
            )
            and ("description_correios" in self._fields_set) == (
                "description_correios" in other._fields_set
            )
            and self.state == other.state
            and ("state" in self._fields_set) == ("state" in other._fields_set)
            and self.region == other.region
            and ("region" in self._fields_set) == (
                "region" in other._fields_set
            )
            and self.area_code == other.area_code
            and ("area_code" in self._fields_set) == (
                "area_code" in other._fields_set
            )
            and self._compare_optional_str_ci(self.latitude, other.latitude)
            and ("latitude" in self._fields_set) == (
                "latitude" in other._fields_set
            )
            and self._compare_optional_str_ci(self.longitude, other.longitude)
            and ("longitude" in self._fields_set) == (
                "longitude" in other._fields_set
            )
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
        
        hash_code = (hash_code * 397) ^ (self.code_state or 0)
        hash_code = (hash_code * 397) ^ hash("code_state" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_region or 0)
        hash_code = (hash_code * 397) ^ hash("code_region" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_fiscal or 0)
        hash_code = (hash_code * 397) ^ hash("code_fiscal" in self._fields_set)
        
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
            hash(self.state) if self.state else 0
        )
        hash_code = (hash_code * 397) ^ hash("state" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.region) if self.region else 0
        )
        hash_code = (hash_code * 397) ^ hash("region" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.area_code or 0)
        hash_code = (hash_code * 397) ^ hash("area_code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.latitude.lower()) if self.latitude else 0
        )
        hash_code = (hash_code * 397) ^ hash("latitude" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.longitude.lower()) if self.longitude else 0
        )
        hash_code = (hash_code * 397) ^ hash("longitude" in self._fields_set)
        
        return hash_code
