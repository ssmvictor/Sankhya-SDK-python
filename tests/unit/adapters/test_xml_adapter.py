"""Unit tests for XmlAdapter."""

import pytest
from sankhya_sdk.adapters.xml_adapter import XmlAdapter


class TestXmlToJson:
    """Tests for xml_to_json conversion."""
    
    @pytest.fixture
    def adapter(self):
        return XmlAdapter()
    
    def test_simple_element(self, adapter):
        xml = "<root>value</root>"
        result = adapter.xml_to_json(xml)
        assert result == "value"
    
    def test_element_with_children(self, adapter):
        xml = "<root><child>value</child></root>"
        result = adapter.xml_to_json(xml)
        assert result == {"child": "value"}
    
    def test_element_with_attributes(self, adapter):
        xml = '<root attr="val"><child>text</child></root>'
        result = adapter.xml_to_json(xml)
        assert result["@attributes"]["attr"] == "val"
        assert result["child"] == "text"
    
    def test_multiple_same_children_becomes_list(self, adapter):
        xml = "<root><item>1</item><item>2</item></root>"
        result = adapter.xml_to_json(xml)
        assert isinstance(result["item"], list)
        assert result["item"] == ["1", "2"]
    
    def test_malformed_xml_raises_error(self, adapter):
        with pytest.raises(ValueError, match="Malformed XML"):
            adapter.xml_to_json("<root><unclosed>")


class TestJsonToXml:
    """Tests for json_to_xml conversion."""
    
    @pytest.fixture
    def adapter(self):
        return XmlAdapter()
    
    def test_simple_dict(self, adapter):
        data = {"message": "hello"}
        result = adapter.json_to_xml(data)
        assert "<message>hello</message>" in result
    
    def test_nested_dict(self, adapter):
        data = {"outer": {"inner": "value"}}
        result = adapter.json_to_xml(data)
        assert "<outer>" in result
        assert "<inner>value</inner>" in result
    
    def test_with_attributes(self, adapter):
        data = {"@attributes": {"id": "123"}, "name": "test"}
        result = adapter.json_to_xml(data)
        assert 'id="123"' in result
    
    def test_with_text_content(self, adapter):
        data = {"$": "text value", "child": "other"}
        result = adapter.json_to_xml(data)
        assert "text value" in result
    
    def test_list_values(self, adapter):
        data = {"items": [{"name": "a"}, {"name": "b"}]}
        result = adapter.json_to_xml(data)
        assert result.count("<items>") == 2


class TestWrapLegacyRequest:
    """Tests for wrap_legacy_request method."""
    
    @pytest.fixture
    def adapter(self):
        return XmlAdapter()
    
    def test_wraps_correctly(self, adapter):
        result = adapter.wrap_legacy_request(
            "CRUDServiceProvider.loadRecords",
            {"dataSet": {"rootEntity": "Parceiro"}}
        )
        
        assert result["serviceName"] == "CRUDServiceProvider.loadRecords"
        assert result["requestBody"]["dataSet"]["rootEntity"] == "Parceiro"


class TestExtractLegacyResponse:
    """Tests for extract_legacy_response method."""
    
    @pytest.fixture
    def adapter(self):
        return XmlAdapter()
    
    def test_extracts_response_body(self, adapter):
        response = {"responseBody": {"data": "value"}, "status": "ok"}
        result = adapter.extract_legacy_response(response)
        assert result == {"data": "value"}
    
    def test_extracts_entities(self, adapter):
        response = {"entities": [{"id": 1}], "total": 1}
        result = adapter.extract_legacy_response(response)
        assert result == {"entities": [{"id": 1}]}
    
    def test_returns_original_if_no_known_structure(self, adapter):
        response = {"custom": "data"}
        result = adapter.extract_legacy_response(response)
        assert result == {"custom": "data"}


class TestConvertFieldFormat:
    """Tests for convert_field_format method."""
    
    @pytest.fixture
    def adapter(self):
        return XmlAdapter()
    
    def test_to_sankhya_format(self, adapter):
        fields = {"NOMEPARC": "Teste", "ATIVO": "S"}
        result = adapter.convert_field_format(fields, to_sankhya=True)
        
        assert result["NOMEPARC"]["$"] == "Teste"
        assert result["ATIVO"]["$"] == "S"
    
    def test_from_sankhya_format(self, adapter):
        fields = {"NOMEPARC": {"$": "Teste"}, "ATIVO": {"$": "S"}}
        result = adapter.convert_field_format(fields, to_sankhya=False)
        
        assert result["NOMEPARC"] == "Teste"
        assert result["ATIVO"] == "S"
    
    def test_preserves_already_formatted(self, adapter):
        fields = {"NOMEPARC": {"$": "Teste"}}
        result = adapter.convert_field_format(fields, to_sankhya=True)
        
        assert result["NOMEPARC"]["$"] == "Teste"
