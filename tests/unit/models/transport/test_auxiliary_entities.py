"""
Testes unitários para entidades auxiliares de transporte.

Testa Neighborhood, PartnerComplement, ProductCost e CodeBars.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from lxml import etree

from sankhya_sdk.models.transport import (
    Neighborhood,
    PartnerComplement,
    ProductCost,
    CodeBars,
)


class TestNeighborhood:
    """Testes para a entidade Neighborhood."""
    
    def test_create_instance(self):
        """Testa criação de instância básica."""
        neighborhood = Neighborhood(code=1, name="Centro")
        
        assert neighborhood.code == 1
        assert neighborhood.name == "Centro"
        assert "code" in neighborhood._fields_set
        assert "name" in neighborhood._fields_set
    
    def test_fields_set_tracking(self):
        """Testa rastreamento de campos definidos."""
        neighborhood = Neighborhood(code=1)
        
        assert "code" in neighborhood._fields_set
        assert "name" not in neighborhood._fields_set
        assert "description_correios" not in neighborhood._fields_set
    
    def test_equality_same_values(self):
        """Testa igualdade com mesmos valores."""
        n1 = Neighborhood(code=1, name="Centro")
        n2 = Neighborhood(code=1, name="Centro")
        
        assert n1 == n2
    
    def test_equality_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        n1 = Neighborhood(code=1, name="CENTRO")
        n2 = Neighborhood(code=1, name="centro")
        
        assert n1 == n2
    
    def test_inequality_different_code(self):
        """Testa desigualdade com códigos diferentes."""
        n1 = Neighborhood(code=1, name="Centro")
        n2 = Neighborhood(code=2, name="Centro")
        
        assert n1 != n2
    
    def test_inequality_different_fields_set(self):
        """Testa desigualdade com _fields_set diferente."""
        n1 = Neighborhood(code=1, name="Centro")
        n2 = Neighborhood(code=1)  # name not set
        
        assert n1 != n2
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        n1 = Neighborhood(code=1, name="Centro")
        n2 = Neighborhood(code=1, name="Centro")
        
        assert hash(n1) == hash(n2)
    
    def test_xml_serialization(self):
        """Testa serialização XML."""
        neighborhood = Neighborhood(code=1, name="Centro")
        xml = neighborhood.to_xml()
        
        assert xml.tag == "Bairro"
        assert xml.find("CODBAI").text == "1"
        assert xml.find("NOMEBAI").text == "Centro"
    
    def test_xml_deserialization(self):
        """Testa deserialização XML."""
        xml_string = """
        <Bairro>
            <CODBAI>1</CODBAI>
            <NOMEBAI>Centro</NOMEBAI>
            <DESCRICAOCORREIO>Centro Histórico</DESCRICAOCORREIO>
        </Bairro>
        """
        element = etree.fromstring(xml_string)
        neighborhood = Neighborhood.from_xml(element)
        
        assert neighborhood.code == 1
        assert neighborhood.name == "Centro"
        assert neighborhood.description_correios == "Centro Histórico"


class TestPartnerComplement:
    """Testes para a entidade PartnerComplement."""
    
    def test_create_instance(self):
        """Testa criação de instância básica."""
        complement = PartnerComplement(
            code=123,
            zip_code_delivery="12345-678",
            code_city_delivery=1
        )
        
        assert complement.code == 123
        assert complement.zip_code_delivery == "12345-678"
        assert complement.code_city_delivery == 1
    
    def test_equality_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        p1 = PartnerComplement(code=1, zip_code_delivery="12345-678")
        p2 = PartnerComplement(code=1, zip_code_delivery="12345-678")
        
        assert p1 == p2
    
    def test_xml_serialization(self):
        """Testa serialização XML."""
        complement = PartnerComplement(code=123, zip_code_delivery="12345-678")
        xml = complement.to_xml()
        
        assert xml.tag == "ComplementoParc"
        assert xml.find("CODPARC").text == "123"
        assert xml.find("CEPENTREGA").text == "12345-678"


class TestProductCost:
    """Testes para a entidade ProductCost."""
    
    def test_create_instance(self):
        """Testa criação de instância básica."""
        cost = ProductCost(
            code_product=1,
            code_company=1,
            cost_replacement=Decimal("100.50")
        )
        
        assert cost.code_product == 1
        assert cost.code_company == 1
        assert cost.cost_replacement == Decimal("100.50")
    
    def test_equality(self):
        """Testa igualdade."""
        c1 = ProductCost(code_product=1, cost_replacement=Decimal("100.50"))
        c2 = ProductCost(code_product=1, cost_replacement=Decimal("100.50"))
        
        assert c1 == c2
    
    def test_xml_serialization(self):
        """Testa serialização XML."""
        cost = ProductCost(code_product=1, cost_replacement=Decimal("100.50"))
        xml = cost.to_xml()
        
        assert xml.tag == "Custo"
        assert xml.find("CODPROD").text == "1"
        assert xml.find("CUSREP").text == "100.50"


class TestCodeBars:
    """Testes para a entidade CodeBars."""
    
    def test_create_instance(self):
        """Testa criação de instância básica."""
        code_bars = CodeBars(code="7891234567890", code_product=123)
        
        assert code_bars.code == "7891234567890"
        assert code_bars.code_product == 123
    
    def test_equality_case_insensitive(self):
        """Testa igualdade case-insensitive para código de barras."""
        cb1 = CodeBars(code="ABC123", code_product=1)
        cb2 = CodeBars(code="abc123", code_product=1)
        
        assert cb1 == cb2
    
    def test_xml_serialization(self):
        """Testa serialização XML."""
        code_bars = CodeBars(code="7891234567890", code_product=123)
        xml = code_bars.to_xml()
        
        assert xml.tag == "CodigoBarras"
        assert xml.find("CODBARRA").text == "7891234567890"
        assert xml.find("CODPROD").text == "123"
    
    def test_xml_deserialization(self):
        """Testa deserialização XML."""
        xml_string = """
        <CodigoBarras>
            <CODBARRA>7891234567890</CODBARRA>
            <CODPROD>123</CODPROD>
            <CODUSU>1</CODUSU>
        </CodigoBarras>
        """
        element = etree.fromstring(xml_string)
        code_bars = CodeBars.from_xml(element)
        
        assert code_bars.code == "7891234567890"
        assert code_bars.code_product == 123
        assert code_bars.code_user == 1
