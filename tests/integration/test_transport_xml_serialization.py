"""
Testes de integração para serialização XML de entidades de transporte.

Testa round-trip completo e compatibilidade com XMLs do SDK .NET.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.transport.address import Address
from sankhya_sdk.models.transport.state import State
from sankhya_sdk.models.transport.region import Region
from sankhya_sdk.models.transport.city import City


class TestComplexXmlSerialization:
    """Testes de serialização XML com entidades complexas."""
    
    def test_city_with_all_relationships(self):
        """Testa serialização de City com State e Region relacionados."""
        # Cria as entidades relacionadas
        state = State(
            code=35,
            initials="SP",
            name="São Paulo",
            code_country=1058,
            code_ibge=35
        )
        
        region = Region(
            code=1,
            name="Sudeste",
            active_internal="S"
        )
        
        # Cria a cidade com relacionamentos
        city = City(
            code=123,
            code_state=35,
            code_region=1,
            code_fiscal=3550308,
            name="São Paulo",
            description_correios="SAO PAULO",
            area_code=11,
            latitude="-23.5505",
            longitude="-46.6333",
            state=state,
            region=region
        )
        
        # Serializa para XML
        xml = city.to_xml()
        
        # Verifica estrutura XML
        assert xml.tag == "Cidade"
        assert xml.find("CODCID").text == "123"
        assert xml.find("UF").text == "35"
        assert xml.find("CODREG").text == "1"
        assert xml.find("NOMECID").text == "São Paulo"
        
        # Verifica entidades relacionadas
        state_elem = xml.find("UnidadeFederativa")
        assert state_elem is not None
        assert state_elem.find("CODUF").text == "35"
        assert state_elem.find("UF").text == "SP"
        
        region_elem = xml.find("Regiao")
        assert region_elem is not None
        assert region_elem.find("CODREG").text == "1"
        assert region_elem.find("NOMEREG").text == "Sudeste"
    
    def test_deserialize_complex_xml(self):
        """Testa deserialização de XML complexo."""
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
            <UnidadeFederativa>
                <CODUF>35</CODUF>
                <UF>SP</UF>
                <DESCRICAO>São Paulo</DESCRICAO>
                <CODPAIS>1058</CODPAIS>
                <CODIBGE>35</CODIBGE>
            </UnidadeFederativa>
            <Regiao>
                <CODREG>1</CODREG>
                <NOMEREG>Sudeste</NOMEREG>
                <ATIVA>S</ATIVA>
            </Regiao>
        </Cidade>
        """
        
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        # Verifica campos básicos
        assert city.code == 123
        assert city.code_state == 35
        assert city.code_region == 1
        assert city.code_fiscal == 3550308
        assert city.name == "São Paulo"
        assert city.area_code == 11
        
        # Verifica relacionamento State
        assert city.state is not None
        assert city.state.code == 35
        assert city.state.initials == "SP"
        assert city.state.name == "São Paulo"
        assert city.state.code_country == 1058
        assert city.state.code_ibge == 35
        
        # Verifica relacionamento Region
        assert city.region is not None
        assert city.region.code == 1
        assert city.region.name == "Sudeste"
        assert city.region.active is True


class TestRoundTripPreservation:
    """Testes de round-trip (objeto -> XML -> objeto)."""
    
    def test_round_trip_city_with_relationships(self):
        """Testa round-trip de City com relacionamentos."""
        # Cria as entidades
        state = State(code=35, initials="SP", name="São Paulo")
        region = Region(code=1, name="Sudeste", active_internal="S")
        
        original = City(
            code=123,
            code_state=35,
            name="São Paulo",
            state=state,
            region=region
        )
        
        # Round-trip
        xml_string = original.to_xml_string()
        restored = City.from_xml_string(xml_string)
        
        # Verifica dados preservados
        assert restored.code == original.code
        assert restored.code_state == original.code_state
        assert restored.name == original.name
        
        # Verifica relacionamentos preservados
        assert restored.state is not None
        assert restored.state.code == 35
        assert restored.state.initials == "SP"
        
        assert restored.region is not None
        assert restored.region.code == 1
        assert restored.region.name == "Sudeste"
        assert restored.region.active is True
    
    def test_round_trip_all_entities(self):
        """Testa round-trip de todas as entidades."""
        # Address
        address = Address(
            code=1,
            type="Residencial",
            name="Rua Principal",
            description_correios="Descrição"
        )
        xml_str = address.to_xml_string()
        restored_address = Address.from_xml_string(xml_str)
        assert restored_address.code == address.code
        assert restored_address.type == address.type
        assert restored_address.name == address.name
        
        # State
        state = State(
            code=35,
            initials="SP",
            name="São Paulo",
            code_ibge=35
        )
        xml_str = state.to_xml_string()
        restored_state = State.from_xml_string(xml_str)
        assert restored_state.code == state.code
        assert restored_state.initials == state.initials
        assert restored_state.code_ibge == state.code_ibge
        
        # Region
        region = Region(
            code=1,
            name="Sudeste",
            active_internal="S",
            code_price_table=10
        )
        xml_str = region.to_xml_string()
        restored_region = Region.from_xml_string(xml_str)
        assert restored_region.code == region.code
        assert restored_region.name == region.name
        assert restored_region.active is True
        assert restored_region.code_price_table == region.code_price_table
        
        # City
        city = City(
            code=123,
            code_state=35,
            name="São Paulo",
            area_code=11,
            latitude="-23.5505",
            longitude="-46.6333"
        )
        xml_str = city.to_xml_string()
        restored_city = City.from_xml_string(xml_str)
        assert restored_city.code == city.code
        assert restored_city.code_state == city.code_state
        assert restored_city.name == city.name
        assert restored_city.latitude == city.latitude


class TestFieldSetPreservation:
    """Testes de preservação de _fields_set."""
    
    def test_fields_set_preserved_after_deserialization(self):
        """Testa que campos desserializados estão em _fields_set."""
        xml_str = """
        <Cidade>
            <CODCID>123</CODCID>
            <NOMECID>São Paulo</NOMECID>
        </Cidade>
        """
        
        elem = etree.fromstring(xml_str)
        city = City.from_xml(elem)
        
        # Campos presentes no XML devem estar em _fields_set
        assert "code" in city._fields_set
        assert "name" in city._fields_set
        
        # Campos ausentes no XML não devem estar em _fields_set
        assert "code_state" not in city._fields_set
        assert "area_code" not in city._fields_set


class TestDotNetCompatibility:
    """Testes de compatibilidade com XML gerado pelo SDK .NET."""
    
    def test_parse_dotnet_address_xml(self):
        """Testa parsing de XML de Address no formato .NET."""
        # XML típico gerado pelo SDK .NET
        xml_str = """
        <Endereco>
            <CODEND>1</CODEND>
            <TIPO>Residencial</TIPO>
            <NOMEEND>Rua Principal</NOMEEND>
            <DESCRICAOCORREIO>DESC CORREIOS</DESCRICAOCORREIO>
        </Endereco>
        """
        
        address = Address.from_xml_string(xml_str)
        
        assert address.code == 1
        assert address.type == "Residencial"
        assert address.name == "Rua Principal"
        assert address.description_correios == "DESC CORREIOS"
    
    def test_parse_dotnet_state_xml(self):
        """Testa parsing de XML de State no formato .NET."""
        xml_str = """
        <UnidadeFederativa>
            <CODUF>35</CODUF>
            <UF>SP</UF>
            <DESCRICAO>São Paulo</DESCRICAO>
            <CODPAIS>1058</CODPAIS>
            <CODIBGE>35</CODIBGE>
            <CODSTGNRE>200</CODSTGNRE>
            <CODDETGNRE>300</CODDETGNRE>
            <CODPRODGNRE>400</CODPRODGNRE>
        </UnidadeFederativa>
        """
        
        state = State.from_xml_string(xml_str)
        
        assert state.code == 35
        assert state.initials == "SP"
        assert state.name == "São Paulo"
        assert state.code_country == 1058
        assert state.code_ibge == 35
        assert state.code_revenue == 200
        assert state.code_revenue_detailing == 300
        assert state.code_product == 400
    
    def test_parse_dotnet_region_with_active(self):
        """Testa parsing de XML de Region com campo ATIVA no formato .NET."""
        xml_str = """
        <Regiao>
            <CODREG>1</CODREG>
            <CODREGPAI>0</CODREGPAI>
            <CODTAB>10</CODTAB>
            <CODVEND>100</CODVEND>
            <ATIVA>S</ATIVA>
            <NOMEREG>Sudeste</NOMEREG>
        </Regiao>
        """
        
        region = Region.from_xml_string(xml_str)
        
        assert region.code == 1
        assert region.code_region_father == 0
        assert region.code_price_table == 10
        assert region.code_seller == 100
        assert region.active is True
        assert region.active_internal == "S"
        assert region.name == "Sudeste"
    
    def test_parse_dotnet_city_full(self):
        """Testa parsing de XML de City completo no formato .NET."""
        xml_str = """
        <Cidade>
            <CODCID>3550308</CODCID>
            <UF>35</UF>
            <CODREG>1</CODREG>
            <CODMUNFIS>3550308</CODMUNFIS>
            <NOMECID>São Paulo</NOMECID>
            <DESCRICAOCORREIO>SAO PAULO</DESCRICAOCORREIO>
            <DDD>11</DDD>
            <LATITUDE>-23.5505199</LATITUDE>
            <LONGITUDE>-46.6333094</LONGITUDE>
        </Cidade>
        """
        
        city = City.from_xml_string(xml_str)
        
        assert city.code == 3550308
        assert city.code_state == 35
        assert city.code_region == 1
        assert city.code_fiscal == 3550308
        assert city.name == "São Paulo"
        assert city.description_correios == "SAO PAULO"
        assert city.area_code == 11
        assert city.latitude == "-23.5505199"
        assert city.longitude == "-46.6333094"


class TestXmlStructure:
    """Testes de estrutura XML."""
    
    def test_xml_element_names_match_dotnet(self):
        """Testa que nomes dos elementos XML correspondem ao SDK .NET."""
        # Address
        address = Address(code=1)
        xml = address.to_xml()
        assert xml.tag == "Endereco"
        assert xml.find("CODEND") is not None
        
        # State
        state = State(code=35, initials="SP")
        xml = state.to_xml()
        assert xml.tag == "UnidadeFederativa"
        assert xml.find("CODUF") is not None
        assert xml.find("UF") is not None
        
        # Region
        region = Region(code=1, name="Teste", active_internal="S")
        xml = region.to_xml()
        assert xml.tag == "Regiao"
        assert xml.find("CODREG") is not None
        assert xml.find("ATIVA") is not None
        assert xml.find("NOMEREG") is not None
        
        # City
        city = City(code=123, code_state=35, area_code=11)
        xml = city.to_xml()
        assert xml.tag == "Cidade"
        assert xml.find("CODCID") is not None
        assert xml.find("UF") is not None
        assert xml.find("DDD") is not None
    
    def test_nested_entities_structure(self):
        """Testa estrutura de entidades aninhadas."""
        state = State(code=35, initials="SP")
        region = Region(code=1, name="Sudeste")
        city = City(code=1, state=state, region=region)
        
        xml = city.to_xml()
        
        # Verifica que entidades aninhadas estão presentes
        assert xml.find("UnidadeFederativa") is not None
        assert xml.find("Regiao") is not None
        
        # Verifica que estão no nível correto (filhos diretos de Cidade)
        state_elem = xml.find("UnidadeFederativa")
        assert state_elem.getparent() == xml
        
        region_elem = xml.find("Regiao")
        assert region_elem.getparent() == xml
