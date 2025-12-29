"""
Entidade State (Unidade Federativa) para o SDK Sankhya.

Representa um estado/UF no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/State.cs
"""

from __future__ import annotations

from typing import Optional

from .base import TransportEntityBase
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
)


@entity("UnidadeFederativa")
class State(TransportEntityBase):
    """
    Representa uma unidade federativa (estado) no sistema Sankhya.
    
    Mapeia para a entidade "UnidadeFederativa" no XML, com campos como
    código, sigla, nome, código do país e informações fiscais.
    
    Attributes:
        code: Código da UF (chave primária - CODUF)
        initials: Sigla do estado (UF)
        name: Nome/descrição do estado (DESCRICAO)
        code_country: Código do país (CODPAIS)
        code_partner_secretary_of_state_revenue: Código do parceiro da secretaria estadual (CODPARCSECRECEST)
        code_ibge: Código IBGE do estado (CODIBGE)
        code_revenue: Código de receita GNRE (CODSTGNRE)
        code_revenue_detailing: Código de detalhamento GNRE (CODDETGNRE)
        code_product: Código de produto GNRE (CODPRODGNRE)
        agreement_protocol: Protocolo de convênio (PROTOCOLOCONVENIO)
    """
    
    code: int = entity_key(
        entity_element("CODUF", default=0)
    )
    
    initials: Optional[str] = entity_element(
        "UF",
        default=None
    )
    
    name: Optional[str] = entity_element(
        "DESCRICAO",
        default=None
    )
    
    code_country: Optional[int] = entity_element(
        "CODPAIS",
        default=None
    )
    
    code_partner_secretary_of_state_revenue: Optional[int] = entity_element(
        "CODPARCSECRECEST",
        default=None
    )
    
    code_ibge: Optional[int] = entity_element(
        "CODIBGE",
        default=None
    )
    
    code_revenue: Optional[int] = entity_element(
        "CODSTGNRE",
        default=None
    )
    
    code_revenue_detailing: Optional[int] = entity_element(
        "CODDETGNRE",
        default=None
    )
    
    code_product: Optional[int] = entity_element(
        "CODPRODGNRE",
        default=None
    )
    
    agreement_protocol: Optional[str] = entity_element(
        "PROTOCOLOCONVENIO",
        default=None
    )
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas instâncias de State.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, State):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self.initials == other.initials
            and ("initials" in self._fields_set) == ("initials" in other._fields_set)
            and self.name == other.name
            and ("name" in self._fields_set) == ("name" in other._fields_set)
            and self.code_country == other.code_country
            and ("code_country" in self._fields_set) == ("code_country" in other._fields_set)
            and self.code_partner_secretary_of_state_revenue == other.code_partner_secretary_of_state_revenue
            and ("code_partner_secretary_of_state_revenue" in self._fields_set) == (
                "code_partner_secretary_of_state_revenue" in other._fields_set
            )
            and self.code_ibge == other.code_ibge
            and ("code_ibge" in self._fields_set) == ("code_ibge" in other._fields_set)
            and self.code_revenue == other.code_revenue
            and ("code_revenue" in self._fields_set) == ("code_revenue" in other._fields_set)
            and self.code_revenue_detailing == other.code_revenue_detailing
            and ("code_revenue_detailing" in self._fields_set) == (
                "code_revenue_detailing" in other._fields_set
            )
            and self.code_product == other.code_product
            and ("code_product" in self._fields_set) == ("code_product" in other._fields_set)
            and self.agreement_protocol == other.agreement_protocol
            and ("agreement_protocol" in self._fields_set) == (
                "agreement_protocol" in other._fields_set
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
            hash(self.initials) if self.initials else 0
        )
        hash_code = (hash_code * 397) ^ hash("initials" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.name) if self.name else 0
        )
        hash_code = (hash_code * 397) ^ hash("name" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_country or 0)
        hash_code = (hash_code * 397) ^ hash("code_country" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            self.code_partner_secretary_of_state_revenue or 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "code_partner_secretary_of_state_revenue" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_ibge or 0)
        hash_code = (hash_code * 397) ^ hash("code_ibge" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_revenue or 0)
        hash_code = (hash_code * 397) ^ hash("code_revenue" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_revenue_detailing or 0)
        hash_code = (hash_code * 397) ^ hash(
            "code_revenue_detailing" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (self.code_product or 0)
        hash_code = (hash_code * 397) ^ hash("code_product" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.agreement_protocol) if self.agreement_protocol else 0
        )
        hash_code = (hash_code * 397) ^ hash(
            "agreement_protocol" in self._fields_set
        )
        
        return hash_code
