"""
Testes unitários para a entidade State.

Testa serialização/deserialização XML, rastreamento de campos,
igualdade e hash.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.transport.state import State


class TestStateCreation:
    """Testes de criação de instâncias State."""
    
    def test_create_with_required_field(self):
        """Testa criação com campo obrigatório (code)."""
        state = State(code=1)
        
        assert state.code == 1
        assert "code" in state._fields_set
    
    def test_create_with_all_fields(self):
        """Testa criação com todos os campos."""
        state = State(
            code=35,
            initials="SP",
            name="São Paulo",
            code_country=1058,
            code_partner_secretary_of_state_revenue=100,
            code_ibge=35,
            code_revenue=200,
            code_revenue_detailing=300,
            code_product=400,
            agreement_protocol="PROT123"
        )
        
        assert state.code == 35
        assert state.initials == "SP"
        assert state.name == "São Paulo"
        assert state.code_country == 1058
        assert state.code_partner_secretary_of_state_revenue == 100
        assert state.code_ibge == 35
        assert state.code_revenue == 200
        assert state.code_revenue_detailing == 300
        assert state.code_product == 400
        assert state.agreement_protocol == "PROT123"
    
    def test_optional_fields_default_none(self):
        """Testa que campos opcionais são None por padrão."""
        state = State(code=1)
        
        assert state.initials is None
        assert state.name is None
        assert state.code_country is None
        assert state.code_ibge is None


class TestStateFieldTracking:
    """Testes de rastreamento de campos modificados."""
    
    def test_fields_set_on_creation(self):
        """Testa que _fields_set contém apenas campos definidos na criação."""
        state = State(code=35, initials="SP")
        
        assert "code" in state._fields_set
        assert "initials" in state._fields_set
        assert "name" not in state._fields_set
        assert "code_country" not in state._fields_set
    
    def test_should_serialize_field(self):
        """Testa should_serialize_field retorna True apenas para campos definidos."""
        state = State(code=35, initials="SP", code_ibge=35)
        
        assert state.should_serialize_field("code") is True
        assert state.should_serialize_field("initials") is True
        assert state.should_serialize_field("code_ibge") is True
        assert state.should_serialize_field("name") is False
        assert state.should_serialize_field("code_country") is False


class TestStateSerialization:
    """Testes de serialização XML."""
    
    def test_to_xml_basic(self):
        """Testa serialização básica para XML."""
        state = State(code=35)
        xml = state.to_xml()
        
        assert xml.tag == "UnidadeFederativa"
        assert xml.find("CODUF").text == "35"
    
    def test_to_xml_multiple_fields(self):
        """Testa serialização com múltiplos campos."""
        state = State(
            code=35,
            initials="SP",
            name="São Paulo",
            code_ibge=35
        )
        xml = state.to_xml()
        
        assert xml.find("CODUF").text == "35"
        assert xml.find("UF").text == "SP"
        assert xml.find("DESCRICAO").text == "São Paulo"
        assert xml.find("CODIBGE").text == "35"
    
    def test_to_xml_omits_unset_fields(self):
        """Testa que campos não definidos não aparecem no XML."""
        state = State(code=35, initials="SP")
        xml = state.to_xml()
        
        assert xml.find("CODUF") is not None
        assert xml.find("UF") is not None
        assert xml.find("DESCRICAO") is None
        assert xml.find("CODPAIS") is None
    
    def test_to_xml_string(self):
        """Testa conversão para string XML."""
        state = State(code=35, initials="SP")
        xml_string = state.to_xml_string()
        
        assert "<UnidadeFederativa>" in xml_string
        assert "<CODUF>35</CODUF>" in xml_string
        assert "<UF>SP</UF>" in xml_string


class TestStateDeserialization:
    """Testes de deserialização XML."""
    
    def test_from_xml_basic(self):
        """Testa deserialização básica de XML."""
        xml_str = """
        <UnidadeFederativa>
            <CODUF>35</CODUF>
        </UnidadeFederativa>
        """
        elem = etree.fromstring(xml_str)
        state = State.from_xml(elem)
        
        assert state.code == 35
    
    def test_from_xml_all_fields(self):
        """Testa deserialização de XML com todos os campos."""
        xml_str = """
        <UnidadeFederativa>
            <CODUF>35</CODUF>
            <UF>SP</UF>
            <DESCRICAO>São Paulo</DESCRICAO>
            <CODPAIS>1058</CODPAIS>
            <CODIBGE>35</CODIBGE>
        </UnidadeFederativa>
        """
        elem = etree.fromstring(xml_str)
        state = State.from_xml(elem)
        
        assert state.code == 35
        assert state.initials == "SP"
        assert state.name == "São Paulo"
        assert state.code_country == 1058
        assert state.code_ibge == 35
    
    def test_from_xml_partial(self):
        """Testa deserialização de XML parcial."""
        xml_str = """
        <UnidadeFederativa>
            <CODUF>33</CODUF>
            <UF>RJ</UF>
        </UnidadeFederativa>
        """
        elem = etree.fromstring(xml_str)
        state = State.from_xml(elem)
        
        assert state.code == 33
        assert state.initials == "RJ"
        assert state.name is None
        assert state.code_country is None


class TestStateEquality:
    """Testes de igualdade entre instâncias."""
    
    def test_equal_states(self):
        """Testa igualdade entre estados iguais."""
        state1 = State(code=35, initials="SP")
        state2 = State(code=35, initials="SP")
        
        assert state1 == state2
    
    def test_not_equal_different_code(self):
        """Testa desigualdade entre estados com códigos diferentes."""
        state1 = State(code=35, initials="SP")
        state2 = State(code=33, initials="SP")
        
        assert state1 != state2
    
    def test_not_equal_different_fields_set(self):
        """Testa desigualdade quando _fields_set é diferente."""
        state1 = State(code=35)
        state2 = State(code=35, initials="SP")
        
        assert state1 != state2
    
    def test_not_equal_none(self):
        """Testa desigualdade com None."""
        state = State(code=35)
        
        assert state != None
    
    def test_same_instance(self):
        """Testa igualdade com mesma instância."""
        state = State(code=35)
        
        assert state == state


class TestStateHash:
    """Testes de hash."""
    
    def test_hash_equal_states(self):
        """Testa que estados iguais têm mesmo hash."""
        state1 = State(code=35, initials="SP")
        state2 = State(code=35, initials="SP")
        
        assert hash(state1) == hash(state2)
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        state = State(code=35, initials="SP")
        h1 = hash(state)
        h2 = hash(state)
        
        assert h1 == h2


class TestStateRoundTrip:
    """Testes de round-trip (objeto -> XML -> objeto)."""
    
    def test_round_trip_basic(self):
        """Testa round-trip básico."""
        original = State(code=35, initials="SP", name="São Paulo")
        
        xml_string = original.to_xml_string()
        restored = State.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.initials == original.initials
        assert restored.name == original.name
    
    def test_round_trip_all_numeric_fields(self):
        """Testa round-trip com todos os campos numéricos."""
        original = State(
            code=35,
            code_country=1058,
            code_ibge=35,
            code_revenue=200,
            code_revenue_detailing=300,
            code_product=400
        )
        
        xml_string = original.to_xml_string()
        restored = State.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.code_country == original.code_country
        assert restored.code_ibge == original.code_ibge
        assert restored.code_revenue == original.code_revenue
        assert restored.code_revenue_detailing == original.code_revenue_detailing
        assert restored.code_product == original.code_product
