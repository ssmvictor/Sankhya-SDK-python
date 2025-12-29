"""
Testes unitários para a entidade Partner.
"""

import pytest
from datetime import datetime
from lxml import etree

from sankhya_sdk.models.transport import Partner, Neighborhood
from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType
from sankhya_sdk.enums.fiscal_classification import FiscalClassification


class TestPartner:
    """Testes para a entidade Partner."""
    
    def test_create_instance_basic(self):
        """Testa criação de instância com campos básicos."""
        partner = Partner(
            code=1,
            name="Empresa ABC",
            document="12.345.678/0001-90"
        )
        
        assert partner.code == 1
        assert partner.name == "Empresa ABC"
        assert partner.document == "12.345.678/0001-90"
        assert "code" in partner._fields_set
        assert "name" in partner._fields_set
        assert "document" in partner._fields_set
    
    def test_boolean_fields(self):
        """Testa campos booleanos."""
        partner = Partner(
            code=1,
            is_active=True,
            is_client=True,
            is_supplier=False
        )
        
        assert partner.is_active is True
        assert partner.is_client is True
        assert partner.is_supplier is False
    
    def test_enum_fields(self):
        """Testa campos de enum."""
        partner = Partner(
            code=1,
            fiscal_type=FiscalPersonType.CORPORATION
        )
        
        assert partner.fiscal_type == FiscalPersonType.CORPORATION
        assert "fiscal_type" in partner._fields_set
    
    def test_equality_same_values(self):
        """Testa igualdade com mesmos valores."""
        p1 = Partner(code=1, name="Empresa ABC")
        p2 = Partner(code=1, name="Empresa ABC")
        
        assert p1 == p2
    
    def test_equality_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        p1 = Partner(code=1, name="EMPRESA ABC")
        p2 = Partner(code=1, name="empresa abc")
        
        assert p1 == p2
    
    def test_inequality_different_code(self):
        """Testa desigualdade com códigos diferentes."""
        p1 = Partner(code=1, name="Empresa ABC")
        p2 = Partner(code=2, name="Empresa ABC")
        
        assert p1 != p2
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        p1 = Partner(code=1, name="Empresa ABC")
        p2 = Partner(code=1, name="Empresa ABC")
        
        assert hash(p1) == hash(p2)
    
    def test_xml_serialization_basic(self):
        """Testa serialização XML básica."""
        partner = Partner(code=1, name="Empresa ABC", is_active=True)
        xml = partner.to_xml()
        
        assert xml.tag == "Parceiro"
        assert xml.find("CODPARC").text == "1"
        assert xml.find("NOMEPARC").text == "Empresa ABC"
        assert xml.find("ATIVO").text == "S"
    
    def test_xml_serialization_enum(self):
        """Testa serialização XML de enum."""
        partner = Partner(
            code=1,
            fiscal_type=FiscalPersonType.CORPORATION
        )
        xml = partner.to_xml()
        
        assert xml.find("TIPPESSOA").text == "J"
    
    def test_xml_deserialization(self):
        """Testa deserialização XML."""
        xml_string = """
        <Parceiro>
            <CODPARC>1</CODPARC>
            <NOMEPARC>Empresa ABC</NOMEPARC>
            <CGC_CPF>12.345.678/0001-90</CGC_CPF>
            <ATIVO>S</ATIVO>
            <CLIENTE>S</CLIENTE>
            <TIPPESSOA>J</TIPPESSOA>
        </Parceiro>
        """
        element = etree.fromstring(xml_string)
        partner = Partner.from_xml(element)
        
        assert partner.code == 1
        assert partner.name == "Empresa ABC"
        assert partner.document == "12.345.678/0001-90"
        assert partner.is_active is True
        assert partner.is_client is True
        assert partner.fiscal_type == FiscalPersonType.CORPORATION
    
    def test_relationship_with_neighborhood(self):
        """Testa relacionamento com Neighborhood."""
        neighborhood = Neighborhood(code=1, name="Centro")
        partner = Partner(
            code=1,
            name="Empresa ABC",
            neighborhood=neighborhood
        )
        
        assert partner.neighborhood == neighborhood
        assert partner.neighborhood.name == "Centro"
