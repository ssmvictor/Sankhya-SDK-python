"""
Entidade Partner (Parceiro) para o SDK Sankhya.

Representa um parceiro (cliente, fornecedor, vendedor, etc.) no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/Partner.cs
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from .base import TransportEntityBase
from .neighborhood import Neighborhood
from .partner_complement import PartnerComplement
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_custom_data,
)
from ...enums.fiscal_person_type import FiscalPersonType
from ...enums.fiscal_classification import FiscalClassification

if TYPE_CHECKING:
    from .address import Address
    from .city import City
    from .region import Region


@entity("Parceiro")
class Partner(TransportEntityBase):
    """
    Representa um parceiro no sistema Sankhya.
    
    Mapeia para a entidade "Parceiro" no XML.
    
    Attributes:
        code: Código do parceiro (chave primária - CODPARC)
        name: Nome do parceiro (NOMEPARC)
        company_name: Razão social (RAZAOSOCIAL)
        fiscal_type: Tipo de pessoa fiscal (TIPPESSOA)
        fiscal_classification: Classificação fiscal (CLASSIFICMS)
        email_address: Email (EMAIL)
        email_address_fiscal_invoice: Email para NFe (EMAILNFE)
        is_active: Se está ativo (ATIVO)
        is_client: Se é cliente (CLIENTE)
        is_seller: Se é vendedor (VENDEDOR)
        is_user: Se é usuário (USUARIO)
        is_supplier: Se é fornecedor (FORNECEDOR)
        document: CPF/CNPJ (CGC_CPF)
        identity: RG/Inscrição estadual (IDENTINSCESTAD)
        state_inscription: Inscrição estadual em outra UF (INSCESTADNAUF)
        zip_code: CEP (CEP)
        code_address: Código do endereço (CODEND)
        address_number: Número do endereço (NUMEND)
        address_complement: Complemento do endereço (COMPLEMENTO)
        code_neighborhood: Código do bairro (CODBAI)
        code_city: Código da cidade (CODCID)
        code_region: Código da região (CODREG)
        telephone: Telefone (TELEFONE)
        telephone_extension_line: Ramal (RAMAL)
        mobile_phone: Fax/Celular (FAX)
        date_created: Data de cadastro (DTCAD)
        date_changed: Data de alteração (DTALTER)
        send_fiscal_invoice_by_email: Enviar DANFE por email (EMAILDANFE)
        authorization_group: Grupo de autorização (GRUPOAUTOR)
        latitude: Latitude (LATITUDE)
        longitude: Longitude (LONGITUDE)
        notes: Observações (OBSERVACOES)
        address: Referência ao endereço
        neighborhood: Referência ao bairro
        city: Referência à cidade
        region: Referência à região
        complement: Referência ao complemento do parceiro
    """
    
    # Campos básicos
    code: int = entity_key(
        entity_element("CODPARC", default=0)
    )
    
    name: Optional[str] = entity_element(
        "NOMEPARC",
        default=None
    )
    
    company_name: Optional[str] = entity_element(
        "RAZAOSOCIAL",
        default=None
    )
    
    # Enums
    fiscal_type: Optional[FiscalPersonType] = entity_element(
        "TIPPESSOA",
        default=None
    )
    
    fiscal_classification: Optional[FiscalClassification] = entity_element(
        "CLASSIFICMS",
        default=None
    )
    
    # Contato
    email_address: Optional[str] = entity_element(
        "EMAIL",
        default=None
    )
    
    email_address_fiscal_invoice: Optional[str] = entity_element(
        "EMAILNFE",
        default=None
    )
    
    # Flags booleanas
    is_active: Optional[bool] = entity_element(
        "ATIVO",
        default=None
    )
    
    is_client: Optional[bool] = entity_element(
        "CLIENTE",
        default=None
    )
    
    is_seller: Optional[bool] = entity_element(
        "VENDEDOR",
        default=None
    )
    
    is_user: Optional[bool] = entity_element(
        "USUARIO",
        default=None
    )
    
    is_supplier: Optional[bool] = entity_element(
        "FORNECEDOR",
        default=None
    )
    
    send_fiscal_invoice_by_email: Optional[bool] = entity_element(
        "EMAILDANFE",
        default=None
    )
    
    # Documentos
    document: Optional[str] = entity_element(
        "CGC_CPF",
        default=None
    )
    
    identity: Optional[str] = entity_element(
        "IDENTINSCESTAD",
        default=None
    )
    
    state_inscription: Optional[str] = entity_element(
        "INSCESTADNAUF",
        default=None
    )
    
    # Endereço
    zip_code: Optional[str] = entity_element(
        "CEP",
        default=None
    )
    
    code_address: Optional[int] = entity_element(
        "CODEND",
        default=None
    )
    
    address_number: Optional[str] = entity_element(
        "NUMEND",
        default=None
    )
    
    address_complement: Optional[str] = entity_custom_data(
        max_length=30,
        field=entity_element("COMPLEMENTO", default=None)
    )
    
    code_neighborhood: Optional[int] = entity_element(
        "CODBAI",
        default=None
    )
    
    code_city: Optional[int] = entity_element(
        "CODCID",
        default=None
    )
    
    code_region: Optional[int] = entity_element(
        "CODREG",
        default=None
    )
    
    # Telefones
    telephone: Optional[str] = entity_element(
        "TELEFONE",
        default=None
    )
    
    telephone_extension_line: Optional[str] = entity_element(
        "RAMAL",
        default=None
    )
    
    mobile_phone: Optional[str] = entity_element(
        "FAX",
        default=None
    )
    
    # Datas
    date_created: Optional[datetime] = entity_element(
        "DTCAD",
        default=None
    )
    
    date_changed: Optional[datetime] = entity_element(
        "DTALTER",
        default=None
    )
    
    # Outros
    authorization_group: Optional[str] = entity_element(
        "GRUPOAUTOR",
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
    
    notes: Optional[str] = entity_element(
        "OBSERVACOES",
        default=None
    )
    
    # Relacionamentos
    address: Optional["Address"] = entity_reference(default=None)
    neighborhood: Optional[Neighborhood] = entity_reference(default=None)
    city: Optional["City"] = entity_reference(default=None)
    region: Optional["Region"] = entity_reference(default=None)
    complement: Optional[PartnerComplement] = entity_reference(default=None)
    
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
        Compara duas instâncias de Partner.
        
        Strings são comparadas de forma case-insensitive.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, Partner):
            return False
        
        return (
            self.code == other.code
            and ("code" in self._fields_set) == ("code" in other._fields_set)
            and self._compare_optional_str_ci(self.name, other.name)
            and ("name" in self._fields_set) == ("name" in other._fields_set)
            and self._compare_optional_str_ci(self.company_name, other.company_name)
            and ("company_name" in self._fields_set) == ("company_name" in other._fields_set)
            and self.fiscal_type == other.fiscal_type
            and ("fiscal_type" in self._fields_set) == ("fiscal_type" in other._fields_set)
            and self.fiscal_classification == other.fiscal_classification
            and ("fiscal_classification" in self._fields_set) == ("fiscal_classification" in other._fields_set)
            and self._compare_optional_str_ci(self.email_address, other.email_address)
            and ("email_address" in self._fields_set) == ("email_address" in other._fields_set)
            and self._compare_optional_str_ci(self.email_address_fiscal_invoice, other.email_address_fiscal_invoice)
            and ("email_address_fiscal_invoice" in self._fields_set) == ("email_address_fiscal_invoice" in other._fields_set)
            and self.is_active == other.is_active
            and ("is_active" in self._fields_set) == ("is_active" in other._fields_set)
            and self.is_client == other.is_client
            and ("is_client" in self._fields_set) == ("is_client" in other._fields_set)
            and self.is_seller == other.is_seller
            and ("is_seller" in self._fields_set) == ("is_seller" in other._fields_set)
            and self.is_user == other.is_user
            and ("is_user" in self._fields_set) == ("is_user" in other._fields_set)
            and self.is_supplier == other.is_supplier
            and ("is_supplier" in self._fields_set) == ("is_supplier" in other._fields_set)
            and self._compare_optional_str_ci(self.document, other.document)
            and ("document" in self._fields_set) == ("document" in other._fields_set)
            and self._compare_optional_str_ci(self.identity, other.identity)
            and ("identity" in self._fields_set) == ("identity" in other._fields_set)
            and self._compare_optional_str_ci(self.state_inscription, other.state_inscription)
            and ("state_inscription" in self._fields_set) == ("state_inscription" in other._fields_set)
            and self._compare_optional_str_ci(self.zip_code, other.zip_code)
            and ("zip_code" in self._fields_set) == ("zip_code" in other._fields_set)
            and self.code_address == other.code_address
            and ("code_address" in self._fields_set) == ("code_address" in other._fields_set)
            and self._compare_optional_str_ci(self.address_number, other.address_number)
            and ("address_number" in self._fields_set) == ("address_number" in other._fields_set)
            and self._compare_optional_str_ci(self.address_complement, other.address_complement)
            and ("address_complement" in self._fields_set) == ("address_complement" in other._fields_set)
            and self.code_neighborhood == other.code_neighborhood
            and ("code_neighborhood" in self._fields_set) == ("code_neighborhood" in other._fields_set)
            and self.code_city == other.code_city
            and ("code_city" in self._fields_set) == ("code_city" in other._fields_set)
            and self.code_region == other.code_region
            and ("code_region" in self._fields_set) == ("code_region" in other._fields_set)
            and self._compare_optional_str_ci(self.telephone, other.telephone)
            and ("telephone" in self._fields_set) == ("telephone" in other._fields_set)
            and self._compare_optional_str_ci(self.telephone_extension_line, other.telephone_extension_line)
            and ("telephone_extension_line" in self._fields_set) == ("telephone_extension_line" in other._fields_set)
            and self._compare_optional_str_ci(self.mobile_phone, other.mobile_phone)
            and ("mobile_phone" in self._fields_set) == ("mobile_phone" in other._fields_set)
            and self.date_created == other.date_created
            and ("date_created" in self._fields_set) == ("date_created" in other._fields_set)
            and self.date_changed == other.date_changed
            and ("date_changed" in self._fields_set) == ("date_changed" in other._fields_set)
            and self.send_fiscal_invoice_by_email == other.send_fiscal_invoice_by_email
            and ("send_fiscal_invoice_by_email" in self._fields_set) == ("send_fiscal_invoice_by_email" in other._fields_set)
            and self._compare_optional_str_ci(self.authorization_group, other.authorization_group)
            and ("authorization_group" in self._fields_set) == ("authorization_group" in other._fields_set)
            and self._compare_optional_str_ci(self.latitude, other.latitude)
            and ("latitude" in self._fields_set) == ("latitude" in other._fields_set)
            and self._compare_optional_str_ci(self.longitude, other.longitude)
            and ("longitude" in self._fields_set) == ("longitude" in other._fields_set)
            and self._compare_optional_str_ci(self.notes, other.notes)
            and ("notes" in self._fields_set) == ("notes" in other._fields_set)
            and self.address == other.address
            and ("address" in self._fields_set) == ("address" in other._fields_set)
            and self.neighborhood == other.neighborhood
            and ("neighborhood" in self._fields_set) == ("neighborhood" in other._fields_set)
            and self.city == other.city
            and ("city" in self._fields_set) == ("city" in other._fields_set)
            and self.region == other.region
            and ("region" in self._fields_set) == ("region" in other._fields_set)
            and self.complement == other.complement
            and ("complement" in self._fields_set) == ("complement" in other._fields_set)
        )
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa o mesmo algoritmo do SDK .NET para compatibilidade.
        """
        hash_code = self.code
        hash_code = (hash_code * 397) ^ hash("code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.name.lower()) if self.name else 0
        )
        hash_code = (hash_code * 397) ^ hash("name" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.company_name.lower()) if self.company_name else 0
        )
        hash_code = (hash_code * 397) ^ hash("company_name" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.fiscal_type.value) if self.fiscal_type else 0
        )
        hash_code = (hash_code * 397) ^ hash("fiscal_type" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.fiscal_classification.value) if self.fiscal_classification else 0
        )
        hash_code = (hash_code * 397) ^ hash("fiscal_classification" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.email_address.lower()) if self.email_address else 0
        )
        hash_code = (hash_code * 397) ^ hash("email_address" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.email_address_fiscal_invoice.lower()) 
            if self.email_address_fiscal_invoice else 0
        )
        hash_code = (hash_code * 397) ^ hash("email_address_fiscal_invoice" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_active or False)
        hash_code = (hash_code * 397) ^ hash("is_active" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_client or False)
        hash_code = (hash_code * 397) ^ hash("is_client" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_seller or False)
        hash_code = (hash_code * 397) ^ hash("is_seller" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_user or False)
        hash_code = (hash_code * 397) ^ hash("is_user" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.is_supplier or False)
        hash_code = (hash_code * 397) ^ hash("is_supplier" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.document.lower()) if self.document else 0
        )
        hash_code = (hash_code * 397) ^ hash("document" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.identity.lower()) if self.identity else 0
        )
        hash_code = (hash_code * 397) ^ hash("identity" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.state_inscription.lower()) if self.state_inscription else 0
        )
        hash_code = (hash_code * 397) ^ hash("state_inscription" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.zip_code.lower()) if self.zip_code else 0
        )
        hash_code = (hash_code * 397) ^ hash("zip_code" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_address or 0)
        hash_code = (hash_code * 397) ^ hash("code_address" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.address_number.lower()) if self.address_number else 0
        )
        hash_code = (hash_code * 397) ^ hash("address_number" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.address_complement.lower()) if self.address_complement else 0
        )
        hash_code = (hash_code * 397) ^ hash("address_complement" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_neighborhood or 0)
        hash_code = (hash_code * 397) ^ hash("code_neighborhood" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_city or 0)
        hash_code = (hash_code * 397) ^ hash("code_city" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_region or 0)
        hash_code = (hash_code * 397) ^ hash("code_region" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.telephone.lower()) if self.telephone else 0
        )
        hash_code = (hash_code * 397) ^ hash("telephone" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.telephone_extension_line.lower()) 
            if self.telephone_extension_line else 0
        )
        hash_code = (hash_code * 397) ^ hash("telephone_extension_line" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.mobile_phone.lower()) if self.mobile_phone else 0
        )
        hash_code = (hash_code * 397) ^ hash("mobile_phone" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.date_created) if self.date_created else 0
        )
        hash_code = (hash_code * 397) ^ hash("date_created" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.date_changed) if self.date_changed else 0
        )
        hash_code = (hash_code * 397) ^ hash("date_changed" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.send_fiscal_invoice_by_email or False)
        hash_code = (hash_code * 397) ^ hash("send_fiscal_invoice_by_email" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.authorization_group.lower()) if self.authorization_group else 0
        )
        hash_code = (hash_code * 397) ^ hash("authorization_group" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.latitude.lower()) if self.latitude else 0
        )
        hash_code = (hash_code * 397) ^ hash("latitude" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.longitude.lower()) if self.longitude else 0
        )
        hash_code = (hash_code * 397) ^ hash("longitude" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.notes.lower()) if self.notes else 0
        )
        hash_code = (hash_code * 397) ^ hash("notes" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.address) if self.address else 0)
        hash_code = (hash_code * 397) ^ hash("address" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.neighborhood) if self.neighborhood else 0)
        hash_code = (hash_code * 397) ^ hash("neighborhood" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.city) if self.city else 0)
        hash_code = (hash_code * 397) ^ hash("city" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.region) if self.region else 0)
        hash_code = (hash_code * 397) ^ hash("region" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.complement) if self.complement else 0)
        hash_code = (hash_code * 397) ^ hash("complement" in self._fields_set)
        
        return hash_code
