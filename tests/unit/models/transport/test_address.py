"""
Testes unitários para a entidade Address.

Testa serialização/deserialização XML, rastreamento de campos,
comparação case-insensitive e validação.
"""

import pytest
from datetime import datetime
from lxml import etree

from sankhya_sdk.models.transport.address import Address


class TestAddressCreation:
    """Testes de criação de instâncias Address."""
    
    def test_create_with_required_field(self):
        """Testa criação com campo obrigatório (code)."""
        address = Address(code=1)
        
        assert address.code == 1
        assert "code" in address._fields_set
    
    def test_create_with_all_fields(self):
        """Testa criação com todos os campos."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        address = Address(
            code=1,
            type="Residencial",
            name="Rua Principal",
            description_correios="Descrição Correios",
            date_changed=dt
        )
        
        assert address.code == 1
        assert address.type == "Residencial"
        assert address.name == "Rua Principal"
        assert address.description_correios == "Descrição Correios"
        assert address.date_changed == dt
    
    def test_optional_fields_default_none(self):
        """Testa que campos opcionais são None por padrão."""
        address = Address(code=1)
        
        assert address.type is None
        assert address.name is None
        assert address.description_correios is None
        assert address.date_changed is None


class TestAddressFieldTracking:
    """Testes de rastreamento de campos modificados."""
    
    def test_fields_set_on_creation(self):
        """Testa que _fields_set contém apenas campos definidos na criação."""
        address = Address(code=1, name="Teste")
        
        assert "code" in address._fields_set
        assert "name" in address._fields_set
        assert "type" not in address._fields_set
        assert "date_changed" not in address._fields_set
    
    def test_fields_set_on_assignment(self):
        """Testa que _fields_set é atualizado ao atribuir valor."""
        address = Address(code=1)
        
        assert "type" not in address._fields_set
        
        address.type = "Comercial"
        
        assert "type" in address._fields_set
        assert address.type == "Comercial"
    
    def test_should_serialize_field(self):
        """Testa should_serialize_field retorna True apenas para campos definidos."""
        address = Address(code=1, name="Teste")
        
        assert address.should_serialize_field("code") is True
        assert address.should_serialize_field("name") is True
        assert address.should_serialize_field("type") is False
        assert address.should_serialize_field("description_correios") is False


class TestAddressSerialization:
    """Testes de serialização XML."""
    
    def test_to_xml_basic(self):
        """Testa serialização básica para XML."""
        address = Address(code=123)
        xml = address.to_xml()
        
        assert xml.tag == "Endereco"
        assert xml.find("CODEND").text == "123"
    
    def test_to_xml_all_fields(self):
        """Testa serialização com todos os campos."""
        address = Address(
            code=123,
            type="Residencial",
            name="Rua Principal",
            description_correios="Descrição"
        )
        xml = address.to_xml()
        
        assert xml.find("CODEND").text == "123"
        assert xml.find("TIPO").text == "Residencial"
        assert xml.find("NOMEEND").text == "Rua Principal"
        assert xml.find("DESCRICAOCORREIO").text == "Descrição"
    
    def test_to_xml_omits_unset_fields(self):
        """Testa que campos não definidos não aparecem no XML."""
        address = Address(code=123)
        xml = address.to_xml()
        
        assert xml.find("CODEND") is not None
        assert xml.find("TIPO") is None
        assert xml.find("NOMEEND") is None
    
    def test_to_xml_string(self):
        """Testa conversão para string XML."""
        address = Address(code=123, name="Teste")
        xml_string = address.to_xml_string()
        
        assert "<Endereco>" in xml_string
        assert "<CODEND>123</CODEND>" in xml_string
        assert "<NOMEEND>Teste</NOMEEND>" in xml_string
    
    def test_to_xml_string_pretty_print(self):
        """Testa conversão para string XML com formatação."""
        address = Address(code=123, name="Teste")
        xml_string = address.to_xml_string(pretty_print=True)
        
        assert "\n" in xml_string


class TestAddressDeserialization:
    """Testes de deserialização XML."""
    
    def test_from_xml_basic(self):
        """Testa deserialização básica de XML."""
        xml_str = """
        <Endereco>
            <CODEND>123</CODEND>
        </Endereco>
        """
        elem = etree.fromstring(xml_str)
        address = Address.from_xml(elem)
        
        assert address.code == 123
    
    def test_from_xml_all_fields(self):
        """Testa deserialização de XML com todos os campos."""
        xml_str = """
        <Endereco>
            <CODEND>123</CODEND>
            <TIPO>Residencial</TIPO>
            <NOMEEND>Rua Principal</NOMEEND>
            <DESCRICAOCORREIO>Descrição</DESCRICAOCORREIO>
        </Endereco>
        """
        elem = etree.fromstring(xml_str)
        address = Address.from_xml(elem)
        
        assert address.code == 123
        assert address.type == "Residencial"
        assert address.name == "Rua Principal"
        assert address.description_correios == "Descrição"
    
    def test_from_xml_string(self):
        """Testa deserialização de string XML."""
        xml_str = "<Endereco><CODEND>456</CODEND><TIPO>Comercial</TIPO></Endereco>"
        address = Address.from_xml_string(xml_str)
        
        assert address.code == 456
        assert address.type == "Comercial"
    
    def test_from_xml_partial(self):
        """Testa deserialização de XML parcial."""
        xml_str = """
        <Endereco>
            <CODEND>789</CODEND>
            <NOMEEND>Avenida</NOMEEND>
        </Endereco>
        """
        elem = etree.fromstring(xml_str)
        address = Address.from_xml(elem)
        
        assert address.code == 789
        assert address.name == "Avenida"
        assert address.type is None


class TestAddressEquality:
    """Testes de igualdade entre instâncias."""
    
    def test_equal_addresses(self):
        """Testa igualdade entre endereços iguais."""
        addr1 = Address(code=1, name="Rua A")
        addr2 = Address(code=1, name="Rua A")
        
        assert addr1 == addr2
    
    def test_equal_case_insensitive(self):
        """Testa igualdade case-insensitive para strings."""
        addr1 = Address(code=1, name="RUA PRINCIPAL")
        addr2 = Address(code=1, name="rua principal")
        
        assert addr1 == addr2
    
    def test_not_equal_different_code(self):
        """Testa desigualdade entre endereços com códigos diferentes."""
        addr1 = Address(code=1, name="Rua A")
        addr2 = Address(code=2, name="Rua A")
        
        assert addr1 != addr2
    
    def test_not_equal_different_fields_set(self):
        """Testa desigualdade quando _fields_set é diferente."""
        addr1 = Address(code=1)
        addr2 = Address(code=1, name="Teste")
        
        assert addr1 != addr2
    
    def test_not_equal_none(self):
        """Testa desigualdade com None."""
        addr = Address(code=1)
        
        assert addr != None
    
    def test_same_instance(self):
        """Testa igualdade com mesma instância."""
        addr = Address(code=1)
        
        assert addr == addr


class TestAddressHash:
    """Testes de hash."""
    
    def test_hash_equal_addresses(self):
        """Testa que endereços iguais têm mesmo hash."""
        addr1 = Address(code=1, name="RUA A")
        addr2 = Address(code=1, name="rua a")
        
        assert hash(addr1) == hash(addr2)
    
    def test_hash_consistency(self):
        """Testa consistência do hash."""
        addr = Address(code=1, name="Teste")
        h1 = hash(addr)
        h2 = hash(addr)
        
        assert h1 == h2
    
    def test_hash_different_addresses(self):
        """Testa que endereços diferentes geralmente têm hash diferente."""
        addr1 = Address(code=1, name="Rua A")
        addr2 = Address(code=2, name="Rua B")
        
        # Não garantido, mas altamente provável
        assert hash(addr1) != hash(addr2)


class TestAddressValidation:
    """Testes de validação."""
    
    def test_max_length_validation(self):
        """Testa validação de max_length no campo name."""
        # Nome com 60 caracteres (limite)
        long_name = "A" * 60
        address = Address(code=1, name=long_name)
        assert address.name == long_name
        
        # Nome com 61 caracteres (excede limite) - deve levantar exceção
        too_long_name = "A" * 61
        with pytest.raises(ValueError):
            Address(code=1, name=too_long_name)


class TestAddressRoundTrip:
    """Testes de round-trip (objeto -> XML -> objeto)."""
    
    def test_round_trip_basic(self):
        """Testa round-trip básico."""
        original = Address(code=123, type="Residencial", name="Rua A")
        
        xml_string = original.to_xml_string()
        restored = Address.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.type == original.type
        assert restored.name == original.name
    
    def test_round_trip_preserves_values(self):
        """Testa que round-trip preserva todos os valores."""
        original = Address(
            code=456,
            type="Comercial",
            name="Avenida B",
            description_correios="Desc"
        )
        
        xml_string = original.to_xml_string()
        restored = Address.from_xml_string(xml_string)
        
        assert restored.code == original.code
        assert restored.type == original.type
        assert restored.name == original.name
        assert restored.description_correios == original.description_correios
