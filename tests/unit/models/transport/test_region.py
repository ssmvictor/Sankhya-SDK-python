"""
Testes unitários para a entidade Region.

Testa serialização/deserialização XML, conversão booleana S/N,
rastreamento de campos, igualdade e hash.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.transport.region import Region


class TestRegionCreation:
    """Testes de criação de instâncias Region."""
    
    def test_create_with_required_field(self):
        """Testa criação com campo obrigatório (code)."""
        region = Region(code=1)
        
        assert region.code == 1
        assert "code" in region._fields_set
    
    def test_create_with_all_fields(self):
        """Testa criação com todos os campos."""
        region = Region(
            code=1,
            code_region_father=0,
            code_price_table=10,
            code_seller=100,
            active_internal="S",
            name="Sudeste"
        )
        
        assert region.code == 1
        assert region.code_region_father == 0
        assert region.code_price_table == 10
        assert region.code_seller == 100
        assert region.active_internal == "S"
        assert region.name == "Sudeste"
    
    def test_optional_fields_default_none(self):
        """Testa que campos opcionais são None por padrão."""
        region = Region(code=1)
        
        assert region.code_region_father is None
        assert region.code_price_table is None
        assert region.code_seller is None
        assert region.active_internal is None
        assert region.name is None
        assert region.seller is None


class TestRegionActiveProperty:
    """Testes da propriedade active (conversão S/N <-> bool)."""
    
    def test_active_getter_true(self):
        """Testa que active retorna True quando active_internal é 'S'."""
        region = Region(code=1, active_internal="S")
        
        assert region.active is True
    
    def test_active_getter_false(self):
        """Testa que active retorna False quando active_internal é 'N'."""
        region = Region(code=1, active_internal="N")
        
        assert region.active is False
    
    def test_active_getter_none(self):
        """Testa que active retorna False quando active_internal é None."""
        region = Region(code=1)
        
        assert region.active is False
    
    def test_active_setter_true(self):
        """Testa que definir active como True define active_internal como 'S'."""
        region = Region(code=1)
        region.active = True
        
        assert region.active_internal == "S"
        assert region.active is True
    
    def test_active_setter_false(self):
        """Testa que definir active como False define active_internal como 'N'."""
        region = Region(code=1)
        region.active = False
        
        assert region.active_internal == "N"
        assert region.active is False
    
    def test_active_lowercase_s(self):
        """Testa que 's' minúsculo também é interpretado como True."""
        region = Region(code=1, active_internal="s")
        
        assert region.active is True
    
    def test_active_lowercase_n(self):
        """Testa que 'n' minúsculo também é interpretado como False."""
        region = Region(code=1, active_internal="n")
        
        assert region.active is False


class TestRegionFieldTracking:
    """Testes de rastreamento de campos modificados."""
    
    def test_fields_set_on_creation(self):
        """Testa que _fields_set contém apenas campos definidos na criação."""
        region = Region(code=1, name="Sudeste")
        
        assert "code" in region._fields_set
        assert "name" in region._fields_set
        assert "code_seller" not in region._fields_set
        assert "active_internal" not in region._fields_set
    
    def test_fields_set_when_setting_active(self):
        """Testa que active_internal é adicionado a _fields_set ao definir active."""
        region = Region(code=1)
        
        assert "active_internal" not in region._fields_set
        
        region.active = True
        
        assert "active_internal" in region._fields_set


class TestRegionSerialization:
    """Testes de serialização XML."""
    
    def test_to_xml_basic(self):
        """Testa serialização básica para XML."""
        region = Region(code=123)
        xml = region.to_xml()
        
        assert xml.tag == "Regiao"
        assert xml.find("CODREG").text == "123"
    
    def test_to_xml_with_active(self):
        """Testa serialização do campo active como S/N."""
        region = Region(code=1, active_internal="S", name="Teste")
        xml = region.to_xml()
        
        assert xml.find("CODREG").text == "1"
        assert xml.find("ATIVA").text == "S"
        assert xml.find("NOMEREG").text == "Teste"
    
    def test_to_xml_omits_unset_fields(self):
        """Testa que campos não definidos não aparecem no XML."""
        region = Region(code=1)
        xml = region.to_xml()
        
        assert xml.find("CODREG") is not None
        assert xml.find("ATIVA") is None
        assert xml.find("NOMEREG") is None
        assert xml.find("CODVEND") is None
    
    def test_to_xml_string(self):
        """Testa conversão para string XML."""
        region = Region(code=1, name="Sudeste")
        xml_string = region.to_xml_string()
        
        assert "<Regiao>" in xml_string
        assert "<CODREG>1</CODREG>" in xml_string
        assert "<NOMEREG>Sudeste</NOMEREG>" in xml_string


class TestRegionDeserialization:
    """Testes de deserialização XML."""
    
    def test_from_xml_basic(self):
        """Testa deserialização básica de XML."""
        xml_str = """
        <Regiao>
            <CODREG>1</CODREG>
        </Regiao>
        """
        elem = etree.fromstring(xml_str)
        region = Region.from_xml(elem)
        
        assert region.code == 1
    
    def test_from_xml_with_active_s(self):
        """Testa deserialização de XML com ATIVA='S'."""
        xml_str = """
        <Regiao>
            <CODREG>1</CODREG>
            <ATIVA>S</ATIVA>
            <NOMEREG>Sudeste</NOMEREG>
        </Regiao>
        """
        elem = etree.fromstring(xml_str)
        region = Region.from_xml(elem)
        
        assert region.code == 1
        assert region.active_internal == "S"
        assert region.active is True
        assert region.name == "Sudeste"
    
    def test_from_xml_with_active_n(self):
        """Testa deserialização de XML com ATIVA='N'."""
        xml_str = """
        <Regiao>
            <CODREG>2</CODREG>
            <ATIVA>N</ATIVA>
        </Regiao>
        """
        elem = etree.fromstring(xml_str)
        region = Region.from_xml(elem)
        
        assert region.code == 2
        assert region.active is False
    
    def test_from_xml_all_fields(self):
        """Testa deserialização de XML com todos os campos."""
        xml_str = """
        <Regiao>
            <CODREG>1</CODREG>
            <CODREGPAI>0</CODREGPAI>
            <CODTAB>10</CODTAB>
            <CODVEND>100</CODVEND>
            <ATIVA>S</ATIVA>
            <NOMEREG>Região Sul</NOMEREG>
        </Regiao>
        """
        elem = etree.fromstring(xml_str)
        region = Region.from_xml(elem)
        
        assert region.code == 1
        assert region.code_region_father == 0
        assert region.code_price_table == 10
        assert region.code_seller == 100
        assert region.active is True
        assert region.name == "Região Sul"


class TestRegionEquality:
    """Testes de igualdade entre instâncias."""
    
    def test_equal_regions(self):
        """Testa igualdade entre regiões iguais."""
        region1 = Region(code=1, name="Sudeste")
        region2 = Region(code=1, name="sudeste")  # case-insensitive
        
        assert region1 == region2
    
    def test_not_equal_different_code(self):
        """Testa desigualdade entre regiões com códigos diferentes."""
        region1 = Region(code=1, name="Sudeste")
        region2 = Region(code=2, name="Sudeste")
        
        assert region1 != region2
    
    def test_not_equal_different_active(self):
        """Testa desigualdade entre regiões com active diferente."""
        region1 = Region(code=1, active_internal="S")
        region2 = Region(code=1, active_internal="N")
        
        assert region1 != region2
    
    def test_not_equal_none(self):
        """Testa desigualdade com None."""
        region = Region(code=1)
        
        assert region != None


class TestRegionHash:
    """Testes de hash."""
    
    def test_hash_equal_regions(self):
        """Testa que regiões iguais têm mesmo hash."""
        region1 = Region(code=1, name="SUDESTE")
        region2 = Region(code=1, name="sudeste")
        
        assert hash(region1) == hash(region2)
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        region = Region(code=1, name="Sudeste")
        h1 = hash(region)
        h2 = hash(region)
        
        assert h1 == h2


class TestRegionRoundTrip:
    """Testes de round-trip (objeto -> XML -> objeto)."""
    
    def test_round_trip_with_active(self):
        """Testa round-trip com campo active."""
        original = Region(code=1, active_internal="S", name="Sudeste")
        
        xml_string = original.to_xml_string()
        restored = Region.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.active == original.active
        assert restored.name == original.name
    
    def test_round_trip_using_active_setter(self):
        """Testa round-trip definindo active via setter."""
        original = Region(code=1, name="Norte")
        original.active = True
        
        xml_string = original.to_xml_string()
        restored = Region.from_xml_string(xml_string)
        
        assert restored.active is True
        assert restored.active_internal == "S"
