"""
Testes unitários para a entidade City.

Testa serialização/deserialização XML com relacionamentos,
rastreamento de campos, igualdade e hash.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.transport.city import City
from sankhya_sdk.models.transport.state import State
from sankhya_sdk.models.transport.region import Region


class TestCityCreation:
    """Testes de criação de instâncias City."""
    
    def test_create_with_required_field(self):
        """Testa criação com campo obrigatório (code)."""
        city = City(code=1)
        
        assert city.code == 1
        assert "code" in city._fields_set
    
    def test_create_with_all_fields(self):
        """Testa criação com todos os campos."""
        city = City(
            code=123,
            code_state=35,
            code_region=1,
            code_fiscal=3550308,
            name="São Paulo",
            description_correios="SAO PAULO",
            area_code=11,
            latitude="-23.5505",
            longitude="-46.6333"
        )
        
        assert city.code == 123
        assert city.code_state == 35
        assert city.code_region == 1
        assert city.code_fiscal == 3550308
        assert city.name == "São Paulo"
        assert city.description_correios == "SAO PAULO"
        assert city.area_code == 11
        assert city.latitude == "-23.5505"
        assert city.longitude == "-46.6333"
    
    def test_optional_fields_default_none(self):
        """Testa que campos opcionais são None por padrão."""
        city = City(code=1)
        
        assert city.code_state is None
        assert city.code_region is None
        assert city.code_fiscal is None
        assert city.name is None
        assert city.description_correios is None
        assert city.area_code is None
        assert city.latitude is None
        assert city.longitude is None
        assert city.state is None
        assert city.region is None


class TestCityRelationships:
    """Testes de relacionamentos com State e Region."""
    
    def test_create_with_state_relationship(self):
        """Testa criação com relacionamento State."""
        state = State(code=35, initials="SP", name="São Paulo")
        city = City(code=1, name="São Paulo", state=state)
        
        assert city.state is not None
        assert city.state.code == 35
        assert city.state.initials == "SP"
    
    def test_create_with_region_relationship(self):
        """Testa criação com relacionamento Region."""
        region = Region(code=1, name="Sudeste")
        city = City(code=1, name="São Paulo", region=region)
        
        assert city.region is not None
        assert city.region.code == 1
        assert city.region.name == "Sudeste"
    
    def test_create_with_both_relationships(self):
        """Testa criação com ambos os relacionamentos."""
        state = State(code=35, initials="SP")
        region = Region(code=1, name="Sudeste")
        city = City(
            code=1,
            name="São Paulo",
            state=state,
            region=region
        )
        
        assert city.state is not None
        assert city.region is not None


class TestCityFieldTracking:
    """Testes de rastreamento de campos modificados."""
    
    def test_fields_set_on_creation(self):
        """Testa que _fields_set contém apenas campos definidos na criação."""
        city = City(code=1, name="São Paulo")
        
        assert "code" in city._fields_set
        assert "name" in city._fields_set
        assert "code_state" not in city._fields_set
        assert "state" not in city._fields_set
    
    def test_fields_set_includes_relationships(self):
        """Testa que relacionamentos são rastreados em _fields_set."""
        state = State(code=35)
        city = City(code=1, state=state)
        
        assert "code" in city._fields_set
        assert "state" in city._fields_set


class TestCitySerialization:
    """Testes de serialização XML."""
    
    def test_to_xml_basic(self):
        """Testa serialização básica para XML."""
        city = City(code=123)
        xml = city.to_xml()
        
        assert xml.tag == "Cidade"
        assert xml.find("CODCID").text == "123"
    
    def test_to_xml_all_fields(self):
        """Testa serialização com todos os campos."""
        city = City(
            code=123,
            code_state=35,
            code_region=1,
            name="São Paulo",
            description_correios="SAO PAULO",
            area_code=11,
            latitude="-23.5505",
            longitude="-46.6333"
        )
        xml = city.to_xml()
        
        assert xml.find("CODCID").text == "123"
        assert xml.find("UF").text == "35"
        assert xml.find("CODREG").text == "1"
        assert xml.find("NOMECID").text == "São Paulo"
        assert xml.find("DESCRICAOCORREIO").text == "SAO PAULO"
        assert xml.find("DDD").text == "11"
        assert xml.find("LATITUDE").text == "-23.5505"
        assert xml.find("LONGITUDE").text == "-46.6333"
    
    def test_to_xml_omits_unset_fields(self):
        """Testa que campos não definidos não aparecem no XML."""
        city = City(code=123)
        xml = city.to_xml()
        
        assert xml.find("CODCID") is not None
        assert xml.find("UF") is None
        assert xml.find("NOMECID") is None
        assert xml.find("LATITUDE") is None
    
    def test_to_xml_with_state_relationship(self):
        """Testa serialização com relacionamento State."""
        state = State(code=35, initials="SP")
        city = City(code=1, name="São Paulo", state=state)
        xml = city.to_xml()
        
        # Verifica campos da cidade
        assert xml.find("CODCID").text == "1"
        assert xml.find("NOMECID").text == "São Paulo"
        
        # Verifica elemento do state relacionado
        state_elem = xml.find("UnidadeFederativa")
        assert state_elem is not None
        assert state_elem.find("CODUF").text == "35"
        assert state_elem.find("UF").text == "SP"
    
    def test_to_xml_string(self):
        """Testa conversão para string XML."""
        city = City(code=123, name="São Paulo")
        xml_string = city.to_xml_string()
        
        assert "<Cidade>" in xml_string
        assert "<CODCID>123</CODCID>" in xml_string
        assert "<NOMECID>São Paulo</NOMECID>" in xml_string


class TestCityDeserialization:
    """Testes de deserialização XML."""
    
    def test_from_xml_basic(self):
        """Testa deserialização básica de XML."""
        xml_str = """
        <Cidade>
            <CODCID>123</CODCID>
        </Cidade>
        """
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        assert city.code == 123
    
    def test_from_xml_all_fields(self):
        """Testa deserialização de XML com todos os campos."""
        xml_str = """
        <Cidade>
            <CODCID>123</CODCID>
            <UF>35</UF>
            <CODREG>1</CODREG>
            <CODMUNFIS>3550308</CODMUNFIS>
            <NOMECID>São Paulo</NOMECID>
            <DESCRICAOCORREIO>SAO PAULO</DESCRICAOCORREIO>
            <DDD>11</DDD>
            <LATITUDE>-23.5505</LATITUDE>
            <LONGITUDE>-46.6333</LONGITUDE>
        </Cidade>
        """
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        assert city.code == 123
        assert city.code_state == 35
        assert city.code_region == 1
        assert city.code_fiscal == 3550308
        assert city.name == "São Paulo"
        assert city.description_correios == "SAO PAULO"
        assert city.area_code == 11
        assert city.latitude == "-23.5505"
        assert city.longitude == "-46.6333"
    
    def test_from_xml_with_state_relationship(self):
        """Testa deserialização de XML com State aninhado."""
        xml_str = """
        <Cidade>
            <CODCID>1</CODCID>
            <NOMECID>São Paulo</NOMECID>
            <UnidadeFederativa>
                <CODUF>35</CODUF>
                <UF>SP</UF>
                <DESCRICAO>São Paulo</DESCRICAO>
            </UnidadeFederativa>
        </Cidade>
        """
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        assert city.code == 1
        assert city.name == "São Paulo"
        assert city.state is not None
        assert city.state.code == 35
        assert city.state.initials == "SP"
    
    def test_from_xml_with_region_relationship(self):
        """Testa deserialização de XML com Region aninhado."""
        xml_str = """
        <Cidade>
            <CODCID>1</CODCID>
            <NOMECID>São Paulo</NOMECID>
            <Regiao>
                <CODREG>1</CODREG>
                <NOMEREG>Sudeste</NOMEREG>
            </Regiao>
        </Cidade>
        """
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        assert city.code == 1
        assert city.region is not None
        assert city.region.code == 1
        assert city.region.name == "Sudeste"
    
    def test_from_xml_without_relationships(self):
        """Testa deserialização de XML sem relacionamentos."""
        xml_str = """
        <Cidade>
            <CODCID>789</CODCID>
            <NOMECID>Campinas</NOMECID>
        </Cidade>
        """
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        assert city.code == 789
        assert city.name == "Campinas"
        assert city.state is None
        assert city.region is None


class TestCityEquality:
    """Testes de igualdade entre instâncias."""
    
    def test_equal_cities(self):
        """Testa igualdade entre cidades iguais."""
        city1 = City(code=1, name="São Paulo")
        city2 = City(code=1, name="São Paulo")
        
        assert city1 == city2
    
    def test_equal_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        city1 = City(code=1, name="SÃO PAULO")
        city2 = City(code=1, name="são paulo")
        
        assert city1 == city2
    
    def test_not_equal_different_code(self):
        """Testa desigualdade entre cidades com códigos diferentes."""
        city1 = City(code=1, name="São Paulo")
        city2 = City(code=2, name="São Paulo")
        
        assert city1 != city2
    
    def test_equal_with_relationships(self):
        """Testa igualdade considerando relacionamentos."""
        state = State(code=35, initials="SP")
        city1 = City(code=1, state=state)
        city2 = City(code=1, state=state)
        
        assert city1 == city2
    
    def test_not_equal_different_relationships(self):
        """Testa desigualdade quando relacionamentos são diferentes."""
        state1 = State(code=35, initials="SP")
        state2 = State(code=33, initials="RJ")
        city1 = City(code=1, state=state1)
        city2 = City(code=1, state=state2)
        
        assert city1 != city2
    
    def test_not_equal_none(self):
        """Testa desigualdade com None."""
        city = City(code=1)
        
        assert city != None


class TestCityHash:
    """Testes de hash."""
    
    def test_hash_equal_cities(self):
        """Testa que cidades iguais têm mesmo hash."""
        city1 = City(code=1, name="SÃO PAULO")
        city2 = City(code=1, name="são paulo")
        
        assert hash(city1) == hash(city2)
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        city = City(code=1, name="São Paulo")
        h1 = hash(city)
        h2 = hash(city)
        
        assert h1 == h2


class TestCityCoordinates:
    """Testes de coordenadas geográficas."""
    
    def test_latitude_longitude_as_strings(self):
        """Testa que latitude e longitude são strings."""
        city = City(
            code=1,
            latitude="-23.5505",
            longitude="-46.6333"
        )
        
        assert isinstance(city.latitude, str)
        assert isinstance(city.longitude, str)
        assert city.latitude == "-23.5505"
        assert city.longitude == "-46.6333"
    
    def test_round_trip_coordinates(self):
        """Testa round-trip de coordenadas."""
        original = City(
            code=1,
            latitude="-23.5505199",
            longitude="-46.6333094"
        )
        
        xml_string = original.to_xml_string()
        restored = City.from_xml_string(xml_string)
        
        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude


class TestCityRoundTrip:
    """Testes de round-trip (objeto -> XML -> objeto)."""
    
    def test_round_trip_basic(self):
        """Testa round-trip básico."""
        original = City(code=123, name="São Paulo")
        
        xml_string = original.to_xml_string()
        restored = City.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.name == original.name
    
    def test_round_trip_with_relationship(self):
        """Testa round-trip com relacionamento."""
        state = State(code=35, initials="SP")
        original = City(code=1, name="São Paulo", state=state)
        
        xml_string = original.to_xml_string()
        restored = City.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.name == original.name
        assert restored.state is not None
        assert restored.state.code == 35
        assert restored.state.initials == "SP"
    
    def test_round_trip_all_fields(self):
        """Testa round-trip com todos os campos."""
        original = City(
            code=123,
            code_state=35,
            code_region=1,
            code_fiscal=3550308,
            name="São Paulo",
            description_correios="SAO PAULO",
            area_code=11,
            latitude="-23.5505",
            longitude="-46.6333"
        )
        
        xml_string = original.to_xml_string()
        restored = City.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.code_state == original.code_state
        assert restored.code_region == original.code_region
        assert restored.code_fiscal == original.code_fiscal
        assert restored.name == original.name
        assert restored.description_correios == original.description_correios
        assert restored.area_code == original.area_code
        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude
