"""
Entidade Address (Endereço) para o SDK Sankhya.

Representa um endereço no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/Address.cs
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import TransportEntityBase
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_custom_data,
)


@entity("Endereco")
class Address(TransportEntityBase):
    """
    Representa um endereço no sistema Sankhya.
    
    Mapeia para a entidade "Endereco" no XML, com campos como código,
    tipo, nome, descrição do correio e data de alteração.
    
    Attributes:
        code: Código do endereço (chave primária - CODEND)
        type: Tipo do endereço (TIPO)
        name: Nome do endereço, max 60 caracteres (NOMEEND)
        description_correios: Descrição do correio (DESCRICAOCORREIO)
        date_changed: Data de alteração (DTALTER)
    """
    
    code: int = entity_key(
        entity_element("CODEND", default=0)
    )
    
    type: Optional[str] = entity_element(
        "TIPO",
        default=None
    )
    
    name: Optional[str] = entity_custom_data(
        max_length=60,
        field=entity_element("NOMEEND", default=None)
    )
    
    description_correios: Optional[str] = entity_element(
        "DESCRICAOCORREIO",
        default=None
    )
    
    date_changed: Optional[datetime] = entity_element(
        "DTALTER",
        default=None
    )
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas instâncias de Address.
        
        Strings são comparadas de forma case-insensitive para manter
        compatibilidade com o SDK .NET.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, Address):
            return False
        
        # Compara code e flags de set
        if self.code != other.code:
            return False
        if ("code" in self._fields_set) != ("code" in other._fields_set):
            return False
        
        # Compara type case-insensitive
        if not self._compare_optional_str(self.type, other.type):
            return False
        if ("type" in self._fields_set) != ("type" in other._fields_set):
            return False
        
        # Compara name case-insensitive
        if not self._compare_optional_str(self.name, other.name):
            return False
        if ("name" in self._fields_set) != ("name" in other._fields_set):
            return False
        
        # Compara description_correios case-insensitive
        if not self._compare_optional_str(
            self.description_correios, 
            other.description_correios
        ):
            return False
        if ("description_correios" in self._fields_set) != (
            "description_correios" in other._fields_set
        ):
            return False
        
        # Compara date_changed
        if self.date_changed != other.date_changed:
            return False
        if ("date_changed" in self._fields_set) != (
            "date_changed" in other._fields_set
        ):
            return False
        
        return True
    
    @staticmethod
    def _compare_optional_str(a: Optional[str], b: Optional[str]) -> bool:
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
        
        hash_code = (hash_code * 397) ^ (
            hash(self.type.lower()) if self.type else 0
        )
        hash_code = (hash_code * 397) ^ hash("type" in self._fields_set)
        
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
