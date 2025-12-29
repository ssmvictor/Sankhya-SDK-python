"""
Testes unitários para tipos básicos de serviço Sankhya.

Testa serialização/deserialização XML de classes básicas.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.service.basic_types import (
    FieldValue,
    Field,
    Criteria,
    Parameter,
    LiteralCriteria,
    LiteralCriteriaSql,
    DataRow,
    ReferenceFetch,
    Prop,
    Path,
    Paths,
)
from sankhya_sdk.enums.parameter_type import ParameterType


class TestFieldValue:
    """Testes para a classe FieldValue."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        fv = FieldValue(name="CODPROD", value="123")
        xml = fv.to_xml()
        
        assert xml.tag == "campo"
        assert xml.get("nome") == "CODPROD"
        assert xml.text == "123"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = '<campo nome="CODPROD">123</campo>'
        elem = etree.fromstring(xml_str)
        fv = FieldValue.from_xml(elem)
        
        assert fv.name == "CODPROD"
        assert fv.value == "123"

    def test_equality(self):
        """Testa igualdade case-insensitive."""
        fv1 = FieldValue(name="CODPROD", value="123")
        fv2 = FieldValue(name="codprod", value="456")
        
        assert fv1 == fv2

    def test_hash(self):
        """Testa hash case-insensitive."""
        fv1 = FieldValue(name="CODPROD", value="123")
        fv2 = FieldValue(name="codprod", value="456")
        
        assert hash(fv1) == hash(fv2)


class TestField:
    """Testes para a classe Field."""

    def test_to_xml_basic(self):
        """Testa serialização básica para XML."""
        field = Field(name="CODPROD")
        xml = field.to_xml()
        
        assert xml.tag == "field"
        assert xml.get("name") == "CODPROD"
        assert xml.get("list") is None

    def test_to_xml_with_attributes(self):
        """Testa serialização com todos os atributos."""
        field = Field(name="DESCRPROD", list="Lista", except_=True, value="Produto")
        xml = field.to_xml()
        
        assert xml.get("name") == "DESCRPROD"
        assert xml.get("list") == "Lista"
        assert xml.get("except") == "true"
        assert xml.text == "Produto"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = '<field name="CODPROD" list="Lista" except="true">Valor</field>'
        elem = etree.fromstring(xml_str)
        field = Field.from_xml(elem)
        
        assert field.name == "CODPROD"
        assert field.list == "Lista"
        assert field.except_ is True
        assert field.value == "Valor"


class TestCriteria:
    """Testes para a classe Criteria."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        crit = Criteria(name="CODPROD", value="123")
        xml = crit.to_xml()
        
        assert xml.tag == "criterio"
        assert xml.get("nome") == "CODPROD"
        assert xml.text == "123"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = '<criterio nome="CODPROD">123</criterio>'
        elem = etree.fromstring(xml_str)
        crit = Criteria.from_xml(elem)
        
        assert crit.name == "CODPROD"
        assert crit.value == "123"


class TestParameter:
    """Testes para a classe Parameter."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        param = Parameter(type=ParameterType.TEXT, value="teste")
        xml = param.to_xml()
        
        assert xml.tag == "parameter"
        assert xml.get("type") == "S"
        assert xml.text == "teste"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = '<parameter type="I">123</parameter>'
        elem = etree.fromstring(xml_str)
        param = Parameter.from_xml(elem)
        
        assert param.type == ParameterType.NUMERIC
        assert param.value == "123"


class TestLiteralCriteria:
    """Testes para a classe LiteralCriteria."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        crit = LiteralCriteria(
            expression="CODPROD = ?",
            parameters=[Parameter(type=ParameterType.NUMERIC, value="123")]
        )
        xml = crit.to_xml()
        
        assert xml.tag == "literalCriteria"
        expr = xml.find("expression")
        assert expr is not None
        assert expr.text == "CODPROD = ?"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = """
        <literalCriteria>
            <expression>CODPROD = ?</expression>
            <parameters>
                <parameter type="I">123</parameter>
            </parameters>
        </literalCriteria>
        """
        elem = etree.fromstring(xml_str)
        crit = LiteralCriteria.from_xml(elem)
        
        assert crit.expression == "CODPROD = ?"
        assert len(crit.parameters) == 1
        assert crit.parameters[0].value == "123"


class TestLiteralCriteriaSql:
    """Testes para a classe LiteralCriteriaSql (português)."""

    def test_to_xml(self):
        """Testa serialização para XML com tags em português."""
        crit = LiteralCriteriaSql(
            expression="CODPROD = ?",
            parameters=[Parameter(type=ParameterType.NUMERIC, value="123")]
        )
        xml = crit.to_xml()
        
        assert xml.tag == "criterioLiteralSql"
        expr = xml.find("expressao")
        assert expr is not None
        assert expr.text == "CODPROD = ?"


class TestDataRow:
    """Testes para a classe DataRow."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        row = DataRow(fields={"CODPROD": "123", "DESCRPROD": "Produto"})
        xml = row.to_xml()
        
        assert xml.tag == "row"
        assert xml.find("CODPROD").text == "123"
        assert xml.find("DESCRPROD").text == "Produto"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = """
        <row id="1">
            <CODPROD>123</CODPROD>
            <DESCRPROD>Produto</DESCRPROD>
        </row>
        """
        elem = etree.fromstring(xml_str)
        row = DataRow.from_xml(elem)
        
        assert row["id"] == "1"
        assert row["CODPROD"] == "123"
        assert row["DESCRPROD"] == "Produto"

    def test_dict_access(self):
        """Testa acesso como dicionário."""
        row = DataRow(fields={"CODPROD": "123"})
        
        assert row["CODPROD"] == "123"
        assert row.get("INEXISTENTE", "default") == "default"
        
        row["NOVO"] = "valor"
        assert row["NOVO"] == "valor"


class TestReferenceFetch:
    """Testes para a classe ReferenceFetch."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        ref = ReferenceFetch(
            mode="all", 
            entity_name="Produto", 
            fields=["CODPROD", "DESCRPROD"]
        )
        xml = ref.to_xml()
        
        assert xml.tag == "referenceFetch"
        assert xml.get("mode") == "all"
        assert xml.get("entityName") == "Produto"
        fields = xml.findall("field")
        assert len(fields) == 2

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = """
        <referenceFetch mode="all" entityName="Produto">
            <field>CODPROD</field>
            <field>DESCRPROD</field>
        </referenceFetch>
        """
        elem = etree.fromstring(xml_str)
        ref = ReferenceFetch.from_xml(elem)
        
        assert ref.mode == "all"
        assert ref.entity_name == "Produto"
        assert ref.fields == ["CODPROD", "DESCRPROD"]


class TestProp:
    """Testes para a classe Prop."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        prop = Prop(name="config", value="valor")
        xml = prop.to_xml()
        
        assert xml.tag == "prop"
        assert xml.get("name") == "config"
        assert xml.text == "valor"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = '<prop name="config">valor</prop>'
        elem = etree.fromstring(xml_str)
        prop = Prop.from_xml(elem)
        
        assert prop.name == "config"
        assert prop.value == "valor"


class TestPath:
    """Testes para a classe Path."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        path = Path(value="/caminho/arquivo.pdf", type="pdf")
        xml = path.to_xml()
        
        assert xml.tag == "path"
        assert xml.get("type") == "pdf"
        assert xml.text == "/caminho/arquivo.pdf"

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = '<path type="pdf">/caminho/arquivo.pdf</path>'
        elem = etree.fromstring(xml_str)
        path = Path.from_xml(elem)
        
        assert path.value == "/caminho/arquivo.pdf"
        assert path.type == "pdf"


class TestPaths:
    """Testes para a classe Paths."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        paths = Paths(items=[
            Path(value="/caminho1.pdf"),
            Path(value="/caminho2.pdf"),
        ])
        xml = paths.to_xml()
        
        assert xml.tag == "paths"
        assert len(xml.findall("path")) == 2

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = """
        <paths>
            <path>/caminho1.pdf</path>
            <path>/caminho2.pdf</path>
        </paths>
        """
        elem = etree.fromstring(xml_str)
        paths = Paths.from_xml(elem)
        
        assert len(paths.items) == 2
        assert paths.items[0].value == "/caminho1.pdf"
