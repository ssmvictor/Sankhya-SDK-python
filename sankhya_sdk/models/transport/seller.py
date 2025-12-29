"""
Entidade Seller (Vendedor) para o SDK Sankhya.

Representa um vendedor no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/Seller.cs
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from .base import TransportEntityBase
from ..service.xml_serialization import serialize_bool, deserialize_bool
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_ignore,
)
from ...enums import SellerType

# Forward reference para evitar import circular
if TYPE_CHECKING:
    pass  # Partner would be imported here when implemented


@entity("Vendedor")
class Seller(TransportEntityBase):
    """
    Representa um vendedor no sistema Sankhya.
    
    Mapeia para a entidade "Vendedor" no XML, com campos como código,
    código do usuário, código do parceiro, status ativo, apelido, email,
    tipo de vendedor e data de alteração.
    
    Os campos `is_active` e `type` são propriedades computadas que convertem
    de/para valores internos de serialização.
    
    Attributes:
        code: Código do vendedor (chave primária - CODVEND)
        code_user: Código do usuário (CODUSU)
        code_partner: Código do parceiro (CODPARC)
        is_active_internal: Status ativo como string "S"/"N" (ATIVO)
        nickname: Apelido do vendedor (APELIDO)
        email: Email do vendedor (EMAIL)
        type_internal: Tipo de vendedor como string (TIPVEND)
        date_changed: Data de alteração (DTALTER)
    """
    
    code: int = entity_key(
        entity_element("CODVEND", default=0)
    )
    
    code_user: Optional[int] = entity_element(
        "CODUSU",
        default=None
    )
    
    code_partner: Optional[int] = entity_element(
        "CODPARC",
        default=None
    )
    
    # Campo interno para serialização - NÃO usar diretamente
    is_active_internal: Optional[str] = entity_element(
        "ATIVO",
        default=None
    )
    
    nickname: Optional[str] = entity_element(
        "APELIDO",
        default=None
    )
    
    email: Optional[str] = entity_element(
        "EMAIL",
        default=None
    )
    
    # Campo interno para tipo - NÃO usar diretamente
    type_internal: Optional[str] = entity_element(
        "TIPVEND",
        default=None
    )
    
    date_changed: Optional[datetime] = entity_element(
        "DTALTER",
        default=None
    )
    
    @property
    def is_active(self) -> bool:
        """
        Retorna o status ativo como booleano.
        
        Converte de "S"/"N" para True/False.
        """
        if self.is_active_internal is None:
            return False
        return deserialize_bool(self.is_active_internal, "S|N")
    
    @is_active.setter
    def is_active(self, value: bool) -> None:
        """
        Define o status ativo.
        
        Converte o booleano para "S" ou "N" e armazena em is_active_internal.
        """
        self.is_active_internal = serialize_bool(value, "S|N")
    
    @property
    def type(self) -> SellerType:
        """
        Retorna o tipo do vendedor como SellerType.
        
        Converte do valor interno para o enum.
        """
        if self.type_internal is None:
            return SellerType.NONE
        # Busca o enum pelo valor interno
        for member in SellerType:
            if member.internal_value == self.type_internal:
                return member
        return SellerType.NONE
    
    @type.setter
    def type(self, value: SellerType) -> None:
        """
        Define o tipo do vendedor.
        
        Converte o enum para o valor interno e armazena em type_internal.
        """
        self.type_internal = value.internal_value
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas instâncias de Seller.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, Seller):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self.code_user == other.code_user
            and ("code_user" in self._fields_set) == ("code_user" in other._fields_set)
            and self.code_partner == other.code_partner
            and ("code_partner" in self._fields_set) == (
                "code_partner" in other._fields_set
            )
            and self.is_active == other.is_active
            and ("is_active_internal" in self._fields_set) == (
                "is_active_internal" in other._fields_set
            )
            and self._compare_optional_str_ci(self.nickname, other.nickname)
            and ("nickname" in self._fields_set) == ("nickname" in other._fields_set)
            and self._compare_optional_str_ci(self.email, other.email)
            and ("email" in self._fields_set) == ("email" in other._fields_set)
            and self.type == other.type
            and ("type_internal" in self._fields_set) == (
                "type_internal" in other._fields_set
            )
            and self.date_changed == other.date_changed
            and ("date_changed" in self._fields_set) == (
                "date_changed" in other._fields_set
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
        
        hash_code = (hash_code * 397) ^ (self.code_user or 0)
        hash_code = (hash_code * 397) ^ hash("code_user" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_partner or 0)
        hash_code = (hash_code * 397) ^ hash("code_partner" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_active)
        hash_code = (hash_code * 397) ^ hash(
            "is_active_internal" in self._fields_set
        )
        
        hash_code = (hash_code * 397) ^ (
            hash(self.nickname.lower()) if self.nickname else 0
        )
        hash_code = (hash_code * 397) ^ hash("nickname" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.email.lower()) if self.email else 0
        )
        hash_code = (hash_code * 397) ^ hash("email" in self._fields_set)
        
        # Use the ordinal value of the enum for hash
        hash_code = (hash_code * 397) ^ hash(self.type.name)
        hash_code = (hash_code * 397) ^ hash("type_internal" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.date_changed) if self.date_changed else 0
        )
        hash_code = (hash_code * 397) ^ hash("date_changed" in self._fields_set)
        
        return hash_code
