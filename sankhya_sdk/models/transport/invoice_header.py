"""
Entidade InvoiceHeader (CabecalhoNota) para o SDK Sankhya.

Representa o cabeçalho de uma nota fiscal no sistema Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/InvoiceHeader.cs
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from .base import TransportEntityBase
from .partner import Partner
from .seller import Seller
from ...attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
)
from ...enums.movement_type import MovementType
from ...enums.freight_type import FreightType
from ...enums.invoice_status import InvoiceStatus
from ...enums.invoice_freight_type import InvoiceFreightType
from ...enums.fiscal_invoice_status import FiscalInvoiceStatus

if TYPE_CHECKING:
    pass


@entity("CabecalhoNota")
class InvoiceHeader(TransportEntityBase):
    """
    Representa o cabeçalho de uma nota fiscal no sistema Sankhya.
    
    Mapeia para a entidade "CabecalhoNota" no XML.
    
    Attributes:
        single_number: Número único da nota (chave primária - NUNOTA)
        code_company: Código da empresa (CODEMP)
        code_partner: Código do parceiro (CODPARC)
        code_partner_destination: Código do parceiro destino (CODPARCDEST)
        code_contact: Código do contato (CODCONTATO)
        operation_type: Tipo de operação (CODTIPOPER)
        code_trade_type: Tipo de venda (CODTIPVENDA)
        invoice_number: Número da nota (NUMNOTA)
        code_seller: Código do vendedor (CODVEND)
        date_traded: Data da negociação (DTNEG)
        date_imported: Data de entrada/saída (DTENTSAI)
        date_billed: Data de faturamento (DTFATUR)
        date_expected_delivery: Data prevista de entrega (DTPREVENT)
        date_changed: Data de alteração (DTALTER)
        code_result_center: Centro de resultado (CODCENCUS)
        code_nature: Natureza (CODNAT)
        movement_type: Tipo de movimento (TIPMOV)
        freight_value: Valor do frete (VLRFRETE)
        note: Observação (OBSERVACAO)
        freight_type: Tipo de frete CIF/FOB (CIF_FOB)
        invoice_status: Status da nota (STATUSNOTA)
        invoice_freight_type: Tipo de frete da nota (TIPFRETE)
        code_partner_carrier: Código do transportador (CODPARCTRANSP)
        fiscal_invoice_status: Status da NFe (STATUSNFE)
        confirmed: Confirmada (CONFIRMADA)
        pending: Pendente (PENDENTE)
        fiscal_invoice_key: Chave da NFe (CHAVENFE)
        movement_time: Hora do movimento (HRMOV)
        invoice_value: Valor da nota (VLRNOTA)
        partner: Parceiro
        partner_destination: Parceiro destino
        partner_carrier: Transportadora
        partner_royalties: Parceiro royalties
        seller: Vendedor
    """
    
    # Campos básicos - chave primária
    single_number: Optional[int] = entity_key(
        entity_element("NUNOTA", default=None)
    )
    
    # Códigos inteiros
    code_company: Optional[int] = entity_element(
        "CODEMP",
        default=None
    )
    
    code_partner: Optional[int] = entity_element(
        "CODPARC",
        default=None
    )
    
    code_partner_destination: Optional[int] = entity_element(
        "CODPARCDEST",
        default=None
    )
    
    code_contact: Optional[int] = entity_element(
        "CODCONTATO",
        default=None
    )
    
    operation_type: Optional[int] = entity_element(
        "CODTIPOPER",
        default=None
    )
    
    code_trade_type: Optional[int] = entity_element(
        "CODTIPVENDA",
        default=None
    )
    
    invoice_number: Optional[int] = entity_element(
        "NUMNOTA",
        default=None
    )
    
    code_seller: Optional[int] = entity_element(
        "CODVEND",
        default=None
    )
    
    code_result_center: Optional[int] = entity_element(
        "CODCENCUS",
        default=None
    )
    
    code_nature: Optional[int] = entity_element(
        "CODNAT",
        default=None
    )
    
    code_partner_carrier: Optional[int] = entity_element(
        "CODPARCTRANSP",
        default=None
    )
    
    # Datas
    date_traded: Optional[datetime] = entity_element(
        "DTNEG",
        default=None
    )
    
    date_imported: Optional[datetime] = entity_element(
        "DTENTSAI",
        default=None
    )
    
    date_billed: Optional[datetime] = entity_element(
        "DTFATUR",
        default=None
    )
    
    date_expected_delivery: Optional[datetime] = entity_element(
        "DTPREVENT",
        default=None
    )
    
    date_changed: Optional[datetime] = entity_element(
        "DTALTER",
        default=None
    )
    
    # Valores decimais
    freight_value: Optional[Decimal] = entity_element(
        "VLRFRETE",
        default=None
    )
    
    invoice_value: Optional[Decimal] = entity_element(
        "VLRNOTA",
        default=None
    )
    
    # Strings
    note: Optional[str] = entity_element(
        "OBSERVACAO",
        default=None
    )
    
    fiscal_invoice_key: Optional[str] = entity_element(
        "CHAVENFE",
        default=None
    )
    
    # Enums
    movement_type: Optional[MovementType] = entity_element(
        "TIPMOV",
        default=None
    )
    
    freight_type: Optional[FreightType] = entity_element(
        "CIF_FOB",
        default=None
    )
    
    invoice_status: Optional[InvoiceStatus] = entity_element(
        "STATUSNOTA",
        default=None
    )
    
    invoice_freight_type: Optional[InvoiceFreightType] = entity_element(
        "TIPFRETE",
        default=None
    )
    
    fiscal_invoice_status: Optional[FiscalInvoiceStatus] = entity_element(
        "STATUSNFE",
        default=None
    )
    
    # Booleanos
    confirmed: Optional[bool] = entity_element(
        "CONFIRMADA",
        default=None
    )
    
    pending: Optional[bool] = entity_element(
        "PENDENTE",
        default=None
    )
    
    # Hora do movimento (HHMMSS)
    movement_time: Optional[timedelta] = entity_element(
        "HRMOV",
        default=None
    )
    
    # Relacionamentos
    partner: Optional[Partner] = entity_reference(default=None)
    partner_destination: Optional[Partner] = entity_reference(default=None)
    partner_carrier: Optional[Partner] = entity_reference(
        "Transportadora",
        default=None
    )
    partner_royalties: Optional[Partner] = entity_reference(
        "Parceiro_AD001",
        default=None
    )
    seller: Optional[Seller] = entity_reference(default=None)
    
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
        Compara duas instâncias de InvoiceHeader.
        
        Strings são comparadas de forma case-insensitive.
        """
        if other is None:
            return False
        
        if self is other:
            return True
        
        if not isinstance(other, InvoiceHeader):
            return False
        
        return (
            self.code_company == other.code_company
            and ("code_company" in self._fields_set) == ("code_company" in other._fields_set)
            and self.code_contact == other.code_contact
            and ("code_contact" in self._fields_set) == ("code_contact" in other._fields_set)
            and self.code_nature == other.code_nature
            and ("code_nature" in self._fields_set) == ("code_nature" in other._fields_set)
            and self.code_partner == other.code_partner
            and ("code_partner" in self._fields_set) == ("code_partner" in other._fields_set)
            and self.code_partner_carrier == other.code_partner_carrier
            and ("code_partner_carrier" in self._fields_set) == ("code_partner_carrier" in other._fields_set)
            and self.code_partner_destination == other.code_partner_destination
            and ("code_partner_destination" in self._fields_set) == ("code_partner_destination" in other._fields_set)
            and self.code_result_center == other.code_result_center
            and ("code_result_center" in self._fields_set) == ("code_result_center" in other._fields_set)
            and self.code_seller == other.code_seller
            and ("code_seller" in self._fields_set) == ("code_seller" in other._fields_set)
            and self.code_trade_type == other.code_trade_type
            and ("code_trade_type" in self._fields_set) == ("code_trade_type" in other._fields_set)
            and self.confirmed == other.confirmed
            and ("confirmed" in self._fields_set) == ("confirmed" in other._fields_set)
            and self.date_billed == other.date_billed
            and ("date_billed" in self._fields_set) == ("date_billed" in other._fields_set)
            and self.date_changed == other.date_changed
            and ("date_changed" in self._fields_set) == ("date_changed" in other._fields_set)
            and self.date_expected_delivery == other.date_expected_delivery
            and ("date_expected_delivery" in self._fields_set) == ("date_expected_delivery" in other._fields_set)
            and self.date_imported == other.date_imported
            and ("date_imported" in self._fields_set) == ("date_imported" in other._fields_set)
            and self.date_traded == other.date_traded
            and ("date_traded" in self._fields_set) == ("date_traded" in other._fields_set)
            and self._compare_optional_str_ci(self.fiscal_invoice_key, other.fiscal_invoice_key)
            and ("fiscal_invoice_key" in self._fields_set) == ("fiscal_invoice_key" in other._fields_set)
            and self.fiscal_invoice_status == other.fiscal_invoice_status
            and ("fiscal_invoice_status" in self._fields_set) == ("fiscal_invoice_status" in other._fields_set)
            and self.freight_type == other.freight_type
            and ("freight_type" in self._fields_set) == ("freight_type" in other._fields_set)
            and self.freight_value == other.freight_value
            and ("freight_value" in self._fields_set) == ("freight_value" in other._fields_set)
            and self.invoice_freight_type == other.invoice_freight_type
            and ("invoice_freight_type" in self._fields_set) == ("invoice_freight_type" in other._fields_set)
            and self.invoice_number == other.invoice_number
            and ("invoice_number" in self._fields_set) == ("invoice_number" in other._fields_set)
            and self.invoice_status == other.invoice_status
            and ("invoice_status" in self._fields_set) == ("invoice_status" in other._fields_set)
            and self.invoice_value == other.invoice_value
            and ("invoice_value" in self._fields_set) == ("invoice_value" in other._fields_set)
            and self.movement_type == other.movement_type
            and ("movement_type" in self._fields_set) == ("movement_type" in other._fields_set)
            and self._compare_optional_str_ci(self.note, other.note)
            and ("note" in self._fields_set) == ("note" in other._fields_set)
            and self.operation_type == other.operation_type
            and ("operation_type" in self._fields_set) == ("operation_type" in other._fields_set)
            and self.partner == other.partner
            and ("partner" in self._fields_set) == ("partner" in other._fields_set)
            and self.partner_carrier == other.partner_carrier
            and ("partner_carrier" in self._fields_set) == ("partner_carrier" in other._fields_set)
            and self.partner_destination == other.partner_destination
            and ("partner_destination" in self._fields_set) == ("partner_destination" in other._fields_set)
            and self.partner_royalties == other.partner_royalties
            and ("partner_royalties" in self._fields_set) == ("partner_royalties" in other._fields_set)
            and self.pending == other.pending
            and ("pending" in self._fields_set) == ("pending" in other._fields_set)
            and self.seller == other.seller
            and ("seller" in self._fields_set) == ("seller" in other._fields_set)
            and self.single_number == other.single_number
            and ("single_number" in self._fields_set) == ("single_number" in other._fields_set)
            and self.movement_time == other.movement_time
            and ("movement_time" in self._fields_set) == ("movement_time" in other._fields_set)
        )
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa o mesmo algoritmo do SDK .NET para compatibilidade.
        """
        hash_code = self.code_company or 0
        hash_code = (hash_code * 397) ^ hash("code_company" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_contact or 0)
        hash_code = (hash_code * 397) ^ hash("code_contact" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_nature or 0)
        hash_code = (hash_code * 397) ^ hash("code_nature" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_partner or 0)
        hash_code = (hash_code * 397) ^ hash("code_partner" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_partner_carrier or 0)
        hash_code = (hash_code * 397) ^ hash("code_partner_carrier" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_partner_destination or 0)
        hash_code = (hash_code * 397) ^ hash("code_partner_destination" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_result_center or 0)
        hash_code = (hash_code * 397) ^ hash("code_result_center" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_seller or 0)
        hash_code = (hash_code * 397) ^ hash("code_seller" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.code_trade_type or 0)
        hash_code = (hash_code * 397) ^ hash("code_trade_type" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.confirmed or False)
        hash_code = (hash_code * 397) ^ hash("confirmed" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.date_billed) if self.date_billed else 0)
        hash_code = (hash_code * 397) ^ hash("date_billed" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.date_changed) if self.date_changed else 0)
        hash_code = (hash_code * 397) ^ hash("date_changed" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.date_expected_delivery) if self.date_expected_delivery else 0)
        hash_code = (hash_code * 397) ^ hash("date_expected_delivery" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.date_imported) if self.date_imported else 0)
        hash_code = (hash_code * 397) ^ hash("date_imported" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.date_traded) if self.date_traded else 0)
        hash_code = (hash_code * 397) ^ hash("date_traded" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.fiscal_invoice_key.lower()) if self.fiscal_invoice_key else 0
        )
        hash_code = (hash_code * 397) ^ hash("fiscal_invoice_key" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.fiscal_invoice_status.value) if self.fiscal_invoice_status else 0)
        hash_code = (hash_code * 397) ^ hash("fiscal_invoice_status" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.freight_type.value) if self.freight_type else 0)
        hash_code = (hash_code * 397) ^ hash("freight_type" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.freight_value) if self.freight_value else 0)
        hash_code = (hash_code * 397) ^ hash("freight_value" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.invoice_freight_type.value) if self.invoice_freight_type else 0)
        hash_code = (hash_code * 397) ^ hash("invoice_freight_type" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.invoice_number or 0)
        hash_code = (hash_code * 397) ^ hash("invoice_number" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.invoice_status.value) if self.invoice_status else 0)
        hash_code = (hash_code * 397) ^ hash("invoice_status" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.invoice_value) if self.invoice_value else 0)
        hash_code = (hash_code * 397) ^ hash("invoice_value" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.movement_type.value) if self.movement_type else 0)
        hash_code = (hash_code * 397) ^ hash("movement_type" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.note.lower()) if self.note else 0
        )
        hash_code = (hash_code * 397) ^ hash("note" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.operation_type or 0)
        hash_code = (hash_code * 397) ^ hash("operation_type" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.partner) if self.partner else 0)
        hash_code = (hash_code * 397) ^ hash("partner" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.partner_carrier) if self.partner_carrier else 0)
        hash_code = (hash_code * 397) ^ hash("partner_carrier" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.partner_destination) if self.partner_destination else 0)
        hash_code = (hash_code * 397) ^ hash("partner_destination" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.partner_royalties) if self.partner_royalties else 0)
        hash_code = (hash_code * 397) ^ hash("partner_royalties" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ hash(self.pending or False)
        hash_code = (hash_code * 397) ^ hash("pending" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (hash(self.seller) if self.seller else 0)
        hash_code = (hash_code * 397) ^ hash("seller" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (self.single_number or 0)
        hash_code = (hash_code * 397) ^ hash("single_number" in self._fields_set)
        
        hash_code = (hash_code * 397) ^ (
            hash(self.movement_time.total_seconds()) if self.movement_time else 0
        )
        hash_code = (hash_code * 397) ^ hash("movement_time" in self._fields_set)
        
        return hash_code
