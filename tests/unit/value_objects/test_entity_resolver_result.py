from sankhya_sdk.value_objects.entity_resolver import EntityResolverResult
from sankhya_sdk.models.service.basic_types import LiteralCriteria, Parameter
from sankhya_sdk.enums.parameter_type import ParameterType


def test_entity_resolver_result_creation():
    result = EntityResolverResult(entity_name="TestEntity")
    assert result.entity_name == "TestEntity"
    assert len(result.field_values) == 0
    assert len(result.keys) == 0
    assert len(result.criteria) == 0
    assert len(result.fields) == 0
    assert len(result.references) == 0
    assert result.literal_criteria is None


def test_entity_resolver_result_add_field_value():
    result = EntityResolverResult(entity_name="Test")
    result.add_field_value("CODIGO", "123")
    assert len(result.field_values) == 1
    assert result.field_values[0].name == "CODIGO"
    assert result.field_values[0].value == "123"


def test_entity_resolver_result_add_key():
    result = EntityResolverResult(entity_name="Test")
    result.add_key("ID", "1")
    assert len(result.keys) == 1
    assert result.keys[0].name == "ID"
    assert result.keys[0].value == "1"


def test_entity_resolver_result_add_criteria():
    result = EntityResolverResult(entity_name="Test")
    result.add_criteria("NOME", "Teste")
    assert len(result.criteria) == 1
    assert result.criteria[0].name == "NOME"
    assert result.criteria[0].value == "Teste"


def test_entity_resolver_result_add_field():
    result = EntityResolverResult(entity_name="Test")
    result.add_field("DESCRICAO")
    assert len(result.fields) == 1
    assert result.fields[0].name == "DESCRICAO"


def test_entity_resolver_result_add_reference():
    result = EntityResolverResult(entity_name="Test")
    result.add_reference("Parceiro", "CODPARC")
    result.add_reference("Parceiro", "NOMEPARC")

    assert "Parceiro" in result.references
    assert len(result.references["Parceiro"]) == 2
    assert result.references["Parceiro"][0].name == "CODPARC"
    assert result.references["Parceiro"][1].name == "NOMEPARC"


def test_entity_resolver_result_literal_criteria():
    result = EntityResolverResult(entity_name="Test")
    params = [Parameter(type=ParameterType.INTEGER, value="10")]
    lc = LiteralCriteria(expression="ID > ?", parameters=params)
    result.literal_criteria = lc

    assert result.literal_criteria.expression == "ID > ?"
    assert len(result.literal_criteria.parameters) == 1
    assert result.literal_criteria.parameters[0].value == "10"


def test_entity_resolver_result_collections_independence():
    res1 = EntityResolverResult(entity_name="E1")
    res2 = EntityResolverResult(entity_name="E2")

    res1.add_field("F1")
    assert len(res1.fields) == 1
    assert len(res2.fields) == 0
