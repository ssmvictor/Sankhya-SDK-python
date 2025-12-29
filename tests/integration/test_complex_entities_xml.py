"""
Testes de integração XML para entidades complexas.

Testa serialização/deserialização round-trip e compatibilidade.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from lxml import etree

from sankhya_sdk.models.transport import (
    Partner,
    Product,
    InvoiceHeader,
    Neighborhood,
    CodeBars,
)
from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType
from sankhya_sdk.enums.product_source import ProductSource
from sankhya_sdk.enums.movement_type import MovementType
from sankhya_sdk.enums.freight_type import FreightType


class TestCompletePartnerRoundTrip:
    """Testes de round-trip para Partner completo."""
    
    def test_partner_complete_round_trip(self):
        """Testa serialização e deserialização completa de Partner."""
        neighborhood = Neighborhood(code=10, name="Centro")
        
        original = Partner(
            code=123,
            name="Empresa ABC LTDA",
            company_name="Empresa ABC",
            fiscal_type=FiscalPersonType.CORPORATION,
            email_address="contato@empresa.com",
            is_active=True,
            is_client=True,
            is_supplier=False,
            document="12.345.678/0001-90",
            zip_code="12345-678",
            telephone="(11) 1234-5678",
            neighborhood=neighborhood
        )
        
        # Serialize
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        # Verify XML structure
        assert "CODPARC" in xml_string
        assert "NOMEPARC" in xml_string
        assert "Empresa ABC LTDA" in xml_string
        
        # Deserialize
        element = etree.fromstring(xml_string)
        deserialized = Partner.from_xml(element)
        
        # Verify fields
        assert deserialized.code == original.code
        assert deserialized.name.lower() == original.name.lower()
        assert deserialized.is_active == original.is_active


class TestCompleteProductRoundTrip:
    """Testes de round-trip para Product completo."""
    
    def test_product_complete_round_trip(self):
        """Testa serialização e deserialização completa de Product."""
        code_bars = [
            CodeBars(code="7891234567890", code_product=100),
            CodeBars(code="7891234567891", code_product=100)
        ]
        
        original = Product(
            code=100,
            name="Produto Premium",
            complement="Com garantia estendida",
            is_active=True,
            net_weight=Decimal("2.5"),
            gross_weight=Decimal("3.0"),
            brand="MarcaXYZ",
            ncm="12345678",
            source=ProductSource.NATIONAL,
            codes_bars=code_bars
        )
        
        # Serialize
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        # Verify XML structure
        assert "CODPROD" in xml_string
        assert "DESCRPROD" in xml_string
        assert "Produto Premium" in xml_string
        
        # Deserialize
        element = etree.fromstring(xml_string)
        deserialized = Product.from_xml(element)
        
        # Verify fields
        assert deserialized.code == original.code
        assert deserialized.name.lower() == original.name.lower()
        assert deserialized.is_active == original.is_active
        assert deserialized.ncm == original.ncm


class TestCompleteInvoiceHeaderRoundTrip:
    """Testes de round-trip para InvoiceHeader completo."""
    
    def test_invoice_header_complete_round_trip(self):
        """Testa serialização e deserialização completa de InvoiceHeader."""
        partner = Partner(code=100, name="Cliente XYZ")
        
        original = InvoiceHeader(
            single_number=12345,
            code_company=1,
            code_partner=100,
            invoice_number=1001,
            movement_type=MovementType.OUTPUT,
            freight_type=FreightType.COST_INSURANCE_FREIGHT,
            freight_value=Decimal("150.00"),
            invoice_value=Decimal("1500.00"),
            note="Nota de venda",
            confirmed=True,
            pending=False,
            partner=partner
        )
        
        # Serialize
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        # Verify XML structure
        assert "NUNOTA" in xml_string
        assert "12345" in xml_string
        
        # Deserialize
        element = etree.fromstring(xml_string)
        deserialized = InvoiceHeader.from_xml(element)
        
        # Verify fields
        assert deserialized.single_number == original.single_number
        assert deserialized.invoice_value == original.invoice_value
        assert deserialized.confirmed == original.confirmed


class TestEnumSerialization:
    """Testes específicos para serialização de enums."""
    
    def test_fiscal_person_type_serialization(self):
        """Testa serialização de FiscalPersonType."""
        partner = Partner(code=1, fiscal_type=FiscalPersonType.CORPORATION)
        xml = partner.to_xml()
        
        # FiscalPersonType.CORPORATION should serialize to "J"
        tippessoa = xml.find("TIPPESSOA")
        assert tippessoa is not None
        assert tippessoa.text == "J"
    
    def test_movement_type_serialization(self):
        """Testa serialização de MovementType."""
        invoice = InvoiceHeader(
            single_number=1,
            movement_type=MovementType.OUTPUT
        )
        xml = invoice.to_xml()
        
        tipmov = xml.find("TIPMOV")
        assert tipmov is not None


class TestBooleanSerialization:
    """Testes específicos para serialização de booleanos."""
    
    def test_boolean_true_serialization(self):
        """Testa serialização de booleano True."""
        partner = Partner(code=1, is_active=True)
        xml = partner.to_xml()
        
        assert xml.find("ATIVO").text == "S"
    
    def test_boolean_false_serialization(self):
        """Testa serialização de booleano False."""
        partner = Partner(code=1, is_supplier=False)
        xml = partner.to_xml()
        
        assert xml.find("FORNECEDOR").text == "N"
    
    def test_boolean_deserialization(self):
        """Testa deserialização de booleano."""
        xml_string = """
        <Parceiro>
            <CODPARC>1</CODPARC>
            <ATIVO>S</ATIVO>
            <CLIENTE>N</CLIENTE>
        </Parceiro>
        """
        element = etree.fromstring(xml_string)
        partner = Partner.from_xml(element)
        
        assert partner.is_active is True
        assert partner.is_client is False


class TestDecimalSerialization:
    """Testes específicos para serialização de Decimal."""
    
    def test_decimal_serialization(self):
        """Testa serialização de Decimal."""
        product = Product(
            code=1,
            net_weight=Decimal("10.555"),
            width=Decimal("0.5")
        )
        xml = product.to_xml()
        
        assert xml.find("PESOLIQ").text == "10.555"
        assert xml.find("LARGURA").text == "0.5"
    
    def test_decimal_deserialization(self):
        """Testa deserialização de Decimal."""
        xml_string = """
        <Produto>
            <CODPROD>1</CODPROD>
            <PESOLIQ>10.555</PESOLIQ>
            <ALTURA>2.5</ALTURA>
        </Produto>
        """
        element = etree.fromstring(xml_string)
        product = Product.from_xml(element)
        
        assert product.net_weight == Decimal("10.555")
        assert product.height == Decimal("2.5")


class TestCollectionSerialization:
    """Testes de serialização de coleções."""
    
    def test_product_codes_bars_serialization(self):
        """Testa serialização de coleção codes_bars."""
        code_bars = [
            CodeBars(code="7891234567890", code_product=100),
            CodeBars(code="7891234567891", code_product=100)
        ]
        product = Product(code=100, codes_bars=code_bars)
        
        xml = product.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        # Deve conter múltiplos elementos CodigoBarras
        assert xml_string.count("<CodigoBarras>") == 2
        assert "7891234567890" in xml_string
        assert "7891234567891" in xml_string
    
    def test_product_codes_bars_deserialization(self):
        """Testa deserialização de coleção codes_bars."""
        xml_string = """
        <Produto>
            <CODPROD>100</CODPROD>
            <CodigoBarras>
                <CODBARRA>7891234567890</CODBARRA>
                <CODPROD>100</CODPROD>
            </CodigoBarras>
            <CodigoBarras>
                <CODBARRA>7891234567891</CODBARRA>
                <CODPROD>100</CODPROD>
            </CodigoBarras>
        </Produto>
        """
        element = etree.fromstring(xml_string)
        product = Product.from_xml(element)
        
        assert product.code == 100
        assert len(product.codes_bars) == 2
        assert product.codes_bars[0].code == "7891234567890"
        assert product.codes_bars[1].code == "7891234567891"
    
    def test_product_collection_roundtrip(self):
        """Testa roundtrip de coleção."""
        code_bars = [
            CodeBars(code="123", code_product=1),
            CodeBars(code="456", code_product=1)
        ]
        original = Product(code=1, name="Test", codes_bars=code_bars)
        
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        element = etree.fromstring(xml_string)
        deserialized = Product.from_xml(element)
        
        assert len(deserialized.codes_bars) == 2
        assert deserialized.codes_bars[0].code == "123"
        assert deserialized.codes_bars[1].code == "456"


class TestEntityReferenceAlias:
    """Testes de alias de referência de entidade."""
    
    def test_product_father_wrapper_alias(self):
        """Testa que product_father usa wrapper Produto_AD001."""
        father = Product(code=1, name="Pai")
        child = Product(code=2, name="Filho", product_father=father)
        
        xml = child.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        # Estrutura esperada: <Produto_AD001><Produto>...</Produto></Produto_AD001>
        assert "<Produto_AD001>" in xml_string
        assert "</Produto_AD001>" in xml_string
    
    def test_product_father_alias_roundtrip(self):
        """Testa roundtrip com alias."""
        father = Product(code=1, name="Pai")
        original = Product(code=2, name="Filho", product_father=father)
        
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        element = etree.fromstring(xml_string)
        
        deserialized = Product.from_xml(element)
        
        assert deserialized.product_father is not None
        assert deserialized.product_father.code == 1
        assert deserialized.product_father.name.lower() == "pai"
