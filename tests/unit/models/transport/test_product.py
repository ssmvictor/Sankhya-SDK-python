"""
Testes unitários para a entidade Product.
"""

import pytest
from decimal import Decimal
from lxml import etree

from sankhya_sdk.models.transport import Product, ProductCost, CodeBars
from sankhya_sdk.enums.product_source import ProductSource
from sankhya_sdk.enums.product_use import ProductUse


class TestProduct:
    """Testes para a entidade Product."""
    
    def test_create_instance_basic(self):
        """Testa criação de instância com campos básicos."""
        product = Product(
            code=1,
            name="Produto ABC",
            is_active=True
        )
        
        assert product.code == 1
        assert product.name == "Produto ABC"
        assert product.is_active is True
        assert "code" in product._fields_set
    
    def test_decimal_fields(self):
        """Testa campos Decimal."""
        product = Product(
            code=1,
            net_weight=Decimal("1.5"),
            gross_weight=Decimal("2.0"),
            width=Decimal("10.5")
        )
        
        assert product.net_weight == Decimal("1.5")
        assert product.gross_weight == Decimal("2.0")
        assert product.width == Decimal("10.5")
    
    def test_enum_fields(self):
        """Testa campos de enum."""
        product = Product(
            code=1,
            source=ProductSource.NATIONAL,
            use=ProductUse.RESALE
        )
        
        assert product.source == ProductSource.NATIONAL
        assert product.use == ProductUse.RESALE
    
    def test_collections_default_empty(self):
        """Testa que coleções são inicializadas como listas vazias."""
        product = Product(code=1)
        
        assert product.components == []
        assert product.codes_bars == []
    
    def test_collections_with_values(self):
        """Testa coleções com valores."""
        code_bars = [
            CodeBars(code="7891234567890", code_product=1),
            CodeBars(code="7891234567891", code_product=1)
        ]
        product = Product(code=1, codes_bars=code_bars)
        
        assert len(product.codes_bars) == 2
        assert product.codes_bars[0].code == "7891234567890"
    
    def test_self_reference(self):
        """Testa auto-referência (produto pai)."""
        product_father = Product(code=1, name="Produto Pai")
        product = Product(
            code=2,
            name="Produto Filho",
            product_father=product_father
        )
        
        assert product.product_father == product_father
        assert product.product_father.code == 1
    
    def test_equality_same_values(self):
        """Testa igualdade com mesmos valores."""
        p1 = Product(code=1, name="Produto ABC")
        p2 = Product(code=1, name="Produto ABC")
        
        assert p1 == p2
    
    def test_equality_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        p1 = Product(code=1, name="PRODUTO ABC")
        p2 = Product(code=1, name="produto abc")
        
        assert p1 == p2
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        p1 = Product(code=1, name="Produto ABC")
        p2 = Product(code=1, name="Produto ABC")
        
        assert hash(p1) == hash(p2)
    
    def test_xml_serialization_basic(self):
        """Testa serialização XML básica."""
        product = Product(
            code=1,
            name="Produto ABC",
            is_active=True,
            net_weight=Decimal("1.5")
        )
        xml = product.to_xml()
        
        assert xml.tag == "Produto"
        assert xml.find("CODPROD").text == "1"
        assert xml.find("DESCRPROD").text == "Produto ABC"
        assert xml.find("ATIVO").text == "S"
        assert xml.find("PESOLIQ").text == "1.5"
    
    def test_xml_serialization_enum(self):
        """Testa serialização XML de enum."""
        product = Product(
            code=1,
            source=ProductSource.NATIONAL
        )
        xml = product.to_xml()
        
        # ProductSource.NATIONAL has internal_value "0"
        assert xml.find("ORIGPROD") is not None
    
    def test_xml_deserialization(self):
        """Testa deserialização XML."""
        xml_string = """
        <Produto>
            <CODPROD>1</CODPROD>
            <DESCRPROD>Produto ABC</DESCRPROD>
            <ATIVO>S</ATIVO>
            <PESOLIQ>1.5</PESOLIQ>
            <NCM>12345678</NCM>
        </Produto>
        """
        element = etree.fromstring(xml_string)
        product = Product.from_xml(element)
        
        assert product.code == 1
        assert product.name == "Produto ABC"
        assert product.is_active is True
        assert product.ncm == "12345678"
    
    def test_product_father_xml_wrapper_tag(self):
        """Testa que product_father é serializado com wrapper Produto_AD001."""
        product_father = Product(code=1, name="Produto Pai")
        product = Product(
            code=2,
            name="Produto Filho",
            product_father=product_father
        )
        
        xml = product.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        # Deve conter o wrapper Produto_AD001
        assert "Produto_AD001" in xml_string
        # Deve conter o Produto interno
        assert "<Produto>" in xml_string
    
    def test_product_father_xml_roundtrip(self):
        """Testa roundtrip de product_father com alias."""
        product_father = Product(code=1, name="Produto Pai")
        original = Product(
            code=2,
            name="Produto Filho",
            product_father=product_father
        )
        
        xml = original.to_xml()
        xml_string = etree.tostring(xml, encoding="unicode")
        
        element = etree.fromstring(xml_string)
        deserialized = Product.from_xml(element)
        
        assert deserialized.code == original.code
        assert deserialized.name.lower() == original.name.lower()
        assert deserialized.product_father is not None
        assert deserialized.product_father.code == product_father.code
