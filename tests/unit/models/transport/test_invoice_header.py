"""
Testes unitários para a entidade InvoiceHeader.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from lxml import etree

from sankhya_sdk.models.transport import InvoiceHeader, Partner
from sankhya_sdk.enums.movement_type import MovementType
from sankhya_sdk.enums.freight_type import FreightType
from sankhya_sdk.enums.invoice_status import InvoiceStatus


class TestInvoiceHeader:
    """Testes para a entidade InvoiceHeader."""
    
    def test_create_instance_basic(self):
        """Testa criação de instância com campos básicos."""
        invoice = InvoiceHeader(
            single_number=12345,
            code_company=1,
            code_partner=100
        )
        
        assert invoice.single_number == 12345
        assert invoice.code_company == 1
        assert invoice.code_partner == 100
    
    def test_decimal_fields(self):
        """Testa campos Decimal."""
        invoice = InvoiceHeader(
            single_number=12345,
            freight_value=Decimal("150.50"),
            invoice_value=Decimal("1500.00")
        )
        
        assert invoice.freight_value == Decimal("150.50")
        assert invoice.invoice_value == Decimal("1500.00")
    
    def test_datetime_fields(self):
        """Testa campos de data/hora."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        invoice = InvoiceHeader(
            single_number=12345,
            date_traded=dt,
            date_billed=dt
        )
        
        assert invoice.date_traded == dt
        assert invoice.date_billed == dt
    
    def test_enum_fields(self):
        """Testa campos de enum."""
        invoice = InvoiceHeader(
            single_number=12345,
            movement_type=MovementType.OUTPUT,
            freight_type=FreightType.COST_INSURANCE_FREIGHT
        )
        
        assert invoice.movement_type == MovementType.OUTPUT
        assert invoice.freight_type == FreightType.COST_INSURANCE_FREIGHT
    
    def test_boolean_fields(self):
        """Testa campos booleanos."""
        invoice = InvoiceHeader(
            single_number=12345,
            confirmed=True,
            pending=False
        )
        
        assert invoice.confirmed is True
        assert invoice.pending is False
    
    def test_relationship_with_partner(self):
        """Testa relacionamento com Partner."""
        partner = Partner(code=100, name="Empresa ABC")
        invoice = InvoiceHeader(
            single_number=12345,
            partner=partner
        )
        
        assert invoice.partner == partner
        assert invoice.partner.name == "Empresa ABC"
    
    def test_multiple_partner_relationships(self):
        """Testa múltiplos relacionamentos com Partner."""
        partner = Partner(code=100, name="Cliente")
        carrier = Partner(code=200, name="Transportadora")
        
        invoice = InvoiceHeader(
            single_number=12345,
            partner=partner,
            partner_carrier=carrier
        )
        
        assert invoice.partner.name == "Cliente"
        assert invoice.partner_carrier.name == "Transportadora"
    
    def test_equality_same_values(self):
        """Testa igualdade com mesmos valores."""
        inv1 = InvoiceHeader(single_number=12345, code_company=1)
        inv2 = InvoiceHeader(single_number=12345, code_company=1)
        
        assert inv1 == inv2
    
    def test_equality_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        inv1 = InvoiceHeader(single_number=12345, note="OBSERVAÇÃO")
        inv2 = InvoiceHeader(single_number=12345, note="observação")
        
        assert inv1 == inv2
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        inv1 = InvoiceHeader(single_number=12345, code_company=1)
        inv2 = InvoiceHeader(single_number=12345, code_company=1)
        
        assert hash(inv1) == hash(inv2)
    
    def test_xml_serialization_basic(self):
        """Testa serialização XML básica."""
        invoice = InvoiceHeader(
            single_number=12345,
            code_company=1,
            invoice_value=Decimal("1500.00")
        )
        xml = invoice.to_xml()
        
        assert xml.tag == "CabecalhoNota"
        assert xml.find("NUNOTA").text == "12345"
        assert xml.find("CODEMP").text == "1"
        assert xml.find("VLRNOTA").text == "1500.00"
    
    def test_xml_serialization_boolean(self):
        """Testa serialização XML de booleanos."""
        invoice = InvoiceHeader(
            single_number=12345,
            confirmed=True,
            pending=False
        )
        xml = invoice.to_xml()
        
        assert xml.find("CONFIRMADA").text == "S"
        assert xml.find("PENDENTE").text == "N"
    
    def test_xml_deserialization(self):
        """Testa deserialização XML."""
        xml_string = """
        <CabecalhoNota>
            <NUNOTA>12345</NUNOTA>
            <CODEMP>1</CODEMP>
            <CODPARC>100</CODPARC>
            <VLRNOTA>1500.00</VLRNOTA>
            <OBSERVACAO>Nota de teste</OBSERVACAO>
            <CONFIRMADA>S</CONFIRMADA>
            <PENDENTE>N</PENDENTE>
        </CabecalhoNota>
        """
        element = etree.fromstring(xml_string)
        invoice = InvoiceHeader.from_xml(element)
        
        assert invoice.single_number == 12345
        assert invoice.code_company == 1
        assert invoice.code_partner == 100
        assert invoice.invoice_value == Decimal("1500.00")
        assert invoice.note == "Nota de teste"
        assert invoice.confirmed is True
        assert invoice.pending is False
    
    def test_movement_time_field(self):
        """Testa campo movement_time (timedelta)."""
        mt = timedelta(hours=14, minutes=30, seconds=45)
        invoice = InvoiceHeader(
            single_number=12345,
            movement_time=mt
        )
        
        assert invoice.movement_time == mt
    
    def test_movement_time_serialization(self):
        """Testa serialização de movement_time para HHMMSS."""
        mt = timedelta(hours=14, minutes=30, seconds=45)
        invoice = InvoiceHeader(
            single_number=12345,
            movement_time=mt
        )
        
        xml = invoice.to_xml()
        hrmov = xml.find("HRMOV")
        
        assert hrmov is not None
        assert hrmov.text == "143045"
    
    def test_movement_time_deserialization(self):
        """Testa deserialização de HRMOV para timedelta."""
        xml_string = """
        <CabecalhoNota>
            <NUNOTA>12345</NUNOTA>
            <HRMOV>143045</HRMOV>
        </CabecalhoNota>
        """
        element = etree.fromstring(xml_string)
        invoice = InvoiceHeader.from_xml(element)
        
        assert invoice.movement_time is not None
        assert invoice.movement_time.total_seconds() == (14 * 3600 + 30 * 60 + 45)
    
    def test_movement_time_roundtrip(self):
        """Testa roundtrip de movement_time."""
        mt = timedelta(hours=9, minutes=15, seconds=30)
        original = InvoiceHeader(
            single_number=12345,
            movement_time=mt
        )
        
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        element = etree.fromstring(xml_string)
        deserialized = InvoiceHeader.from_xml(element)
        
        assert deserialized.movement_time == original.movement_time
    
    def test_movement_time_equality(self):
        """Testa igualdade com movement_time."""
        mt = timedelta(hours=10, minutes=0, seconds=0)
        inv1 = InvoiceHeader(single_number=12345, movement_time=mt)
        inv2 = InvoiceHeader(single_number=12345, movement_time=mt)
        
        assert inv1 == inv2
    
    def test_movement_time_hash(self):
        """Testa hash com movement_time."""
        mt = timedelta(hours=10, minutes=0, seconds=0)
        inv1 = InvoiceHeader(single_number=12345, movement_time=mt)
        inv2 = InvoiceHeader(single_number=12345, movement_time=mt)
        
        assert hash(inv1) == hash(inv2)
