# -*- coding: utf-8 -*-
"""
Testes unitários para service_request_extensions.py
"""

import pytest
from unittest.mock import Mock, MagicMock

from sankhya_sdk.helpers.service_request_extensions import (
    ServiceRequestExtensions,
    ParsePropertyModel,
    EntityResolverResult,
    resolve,
    _reference_level_to_int,
    _int_to_reference_level,
)
from sankhya_sdk.enums.reference_level import ReferenceLevel


class TestParsePropertyModel:
    """Testes para ParsePropertyModel."""

    def test_initialization(self):
        """Verifica inicialização do modelo."""
        model = ParsePropertyModel()
        
        assert model.property_name == ""
        assert model.is_ignored is False
        assert model.is_entity_key is False
        assert model.is_entity_reference is False
        assert model.is_entity_reference_inline is False
        assert model.ignore_entity_reference_inline is False
        assert model.custom_relation_name == ""
        assert model.is_criteria is False
        assert model.custom_data is None


class TestEntityResolverResult:
    """Testes para EntityResolverResult."""

    def test_initialization(self):
        """Verifica inicialização do resultado."""
        result = EntityResolverResult("TestEntity")
        
        assert result.name == "TestEntity"
        assert result.fields == []
        assert result.keys == []
        assert result.criteria == []
        assert result.references == {}
        assert result.literal_criteria == ""


class TestReferenceLevelConversion:
    """Testes para conversão de ReferenceLevel."""

    def test_level_to_int(self):
        """Verifica conversão de ReferenceLevel para int."""
        assert _reference_level_to_int(ReferenceLevel.NONE) == 0
        assert _reference_level_to_int(ReferenceLevel.FIRST) == 1
        assert _reference_level_to_int(ReferenceLevel.SECOND) == 2
        assert _reference_level_to_int(ReferenceLevel.THIRD) == 3
        assert _reference_level_to_int(ReferenceLevel.FOURTH) == 4
        assert _reference_level_to_int(ReferenceLevel.FIFTH) == 5
        assert _reference_level_to_int(ReferenceLevel.SIXTH) == 6

    def test_int_to_level(self):
        """Verifica conversão de int para ReferenceLevel."""
        assert _int_to_reference_level(0) == ReferenceLevel.NONE
        assert _int_to_reference_level(1) == ReferenceLevel.FIRST
        assert _int_to_reference_level(2) == ReferenceLevel.SECOND
        assert _int_to_reference_level(3) == ReferenceLevel.THIRD
        assert _int_to_reference_level(4) == ReferenceLevel.FOURTH
        assert _int_to_reference_level(5) == ReferenceLevel.FIFTH
        assert _int_to_reference_level(6) == ReferenceLevel.SIXTH


class TestServiceRequestExtensions:
    """Testes para ServiceRequestExtensions."""

    def test_get_unix_timestamp_returns_string(self):
        """Verifica que _get_unix_timestamp retorna string."""
        timestamp = ServiceRequestExtensions._get_unix_timestamp()
        
        assert isinstance(timestamp, str)
        assert timestamp.isdigit()


# ---------------------------------------------------------------------------
# Montagem das requisições (porta de HandleService / Resolve do .NET)
# ---------------------------------------------------------------------------

from lxml import etree

from sankhya_sdk.enums.parameter_type import ParameterType
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import InvalidServiceRequestOperationException
from sankhya_sdk.helpers.filter_expression import LiteralCriteria as FilterLiteralCriteria
from sankhya_sdk.models.service.basic_types import (
    LiteralCriteria,
    LiteralCriteriaSql,
    Parameter,
)
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.transport.neighborhood import Neighborhood
from sankhya_sdk.models.transport.partner import Partner


FIXED_TIMESTAMP = "1700000000"


@pytest.fixture
def fixed_timestamp(monkeypatch):
    """Fixa o timestamp usado no datasetid."""
    monkeypatch.setattr(
        ServiceRequestExtensions,
        "_get_unix_timestamp",
        staticmethod(lambda: FIXED_TIMESTAMP),
    )


def _body(request: ServiceRequest) -> etree._Element:
    """Serializa a requisição (ServiceRequest/RequestBody.to_xml) e retorna o requestBody."""
    root = etree.fromstring(request.to_xml_bytes())
    body = root.find("requestBody")
    assert body is not None
    return body


@pytest.mark.usefixtures("fixed_timestamp")
class TestHandleServiceCrudServiceFind:
    """CRUDServiceProvider.loadRecords (.NET HandleService, CrudServiceFind)."""

    def test_find_by_key_builds_data_set(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        ServiceRequestExtensions.resolve_with_entity(request, Partner(code=123))

        data_set = _body(request).find("dataSet")
        assert data_set is not None
        assert data_set.get("rootEntity") == "Parceiro"
        assert data_set.get("includePresentationFields") == "N"
        assert data_set.get("parallelLoader") == "true"
        assert data_set.get("datasetid") == f"{FIXED_TIMESTAMP}_1"
        assert data_set.findtext("criteria/expression") == "CODPARC = 123"

        root_entity = data_set.findall("entity")[0]
        assert root_entity.get("path") == ""
        assert "name" not in root_entity.attrib
        field_list = root_entity.find("fieldset").get("list").split(",")
        assert field_list[:2] == ["CODPARC", "NOMEPARC"]
        assert "CODCID" in field_list

    def test_find_with_reference_adds_entity_per_reference(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        partner = Partner(code=1, neighborhood=Neighborhood(code=2, name="Centro"))

        ServiceRequestExtensions.resolve_with_entity(request, partner)

        entities = _body(request).find("dataSet").findall("entity")
        by_path = {e.get("path"): e.find("fieldset").get("list") for e in entities}
        assert by_path["Bairro"].split(",")[:2] == ["CODBAI", "NOMEBAI"]

    def test_find_without_criteria_sends_empty_criteria(self):
        """O .NET sempre atribui result.LiteralCriteria (vazio) no HandleService."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        ServiceRequestExtensions.resolve_with_entity(request, Partner())

        criteria = _body(request).find("dataSet/criteria")
        assert criteria is not None
        assert criteria.find("expression") is None

    def test_resolve_generic_does_not_set_criteria(self):
        """Resolve<T>() do .NET não define LiteralCriteria."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        ServiceRequestExtensions.resolve_generic(request, Partner)

        data_set = _body(request).find("dataSet")
        assert data_set.find("criteria") is None
        assert data_set.findall("entity")[0].get("path") == ""


@pytest.mark.usefixtures("fixed_timestamp")
class TestHandleServiceCrudServiceSave:
    """CRUDServiceProvider.saveRecord (.NET HandleService, CrudServiceSave)."""

    def test_update_builds_data_row(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)

        ServiceRequestExtensions.resolve_with_entity(
            request, Partner(code=123, name="Cliente")
        )

        data_set = _body(request).find("dataSet")
        assert data_set.get("rootEntity") == "Parceiro"
        assert data_set.get("includePresentationFields") == "N"
        assert data_set.get("parallelLoader") == "true"
        assert data_set.get("datasetid") == f"{FIXED_TIMESTAMP}_1"
        entity = data_set.find("entity")
        assert entity.get("path") == ""
        assert entity.find("fieldset").get("list") == "*"
        data_rows = data_set.findall("dataRow")
        assert len(data_rows) == 1
        assert data_rows[0].findtext("key/CODPARC") == "123"
        local_fields = data_rows[0].find("localFields")
        assert {child.tag: child.text for child in local_fields} == {"NOMEPARC": "Cliente"}

    def test_insert_without_key_sends_empty_key(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)

        ServiceRequestExtensions.resolve_with_entity(request, Partner(name="Novo"))

        data_row = _body(request).find("dataSet/dataRow")
        assert data_row.findtext("localFields/NOMEPARC") == "Novo"
        key = data_row.find("key")
        assert key is not None
        assert len(key) == 0

    def test_batch_save_builds_one_data_row_per_entity(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)

        ServiceRequestExtensions.resolve_with_collection(
            request, [Partner(name="A"), Partner(code=2, name="B")]
        )

        data_rows = _body(request).find("dataSet").findall("dataRow")
        assert [r.findtext("localFields/NOMEPARC") for r in data_rows] == ["A", "B"]
        assert [r.findtext("key/CODPARC") for r in data_rows] == [None, "2"]


@pytest.mark.usefixtures("fixed_timestamp")
class TestHandleServiceCrudServiceRemove:
    """CRUDServiceProvider.removeRecord (.NET HandleService, CrudServiceRemove)."""

    def test_remove_builds_entity_with_ids(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_REMOVE)

        ServiceRequestExtensions.resolve_with_entity(request, Partner(code=123))

        entity = _body(request).find("entity")
        assert entity is not None
        assert "name" not in entity.attrib
        assert entity.get("rootEntity") == "Parceiro"
        assert entity.get("datasetid") == f"{FIXED_TIMESTAMP}_2"
        assert [i.findtext("CODPARC") for i in entity.findall("id")] == ["123"]

    def test_batch_remove_builds_one_id_per_entity(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_REMOVE)

        ServiceRequestExtensions.resolve_with_entities(
            request, [Partner(code=1), Partner(code=2)]
        )

        entity = _body(request).find("entity")
        assert [i.findtext("CODPARC") for i in entity.findall("id")] == ["1", "2"]

    def test_batch_unsupported_service_raises(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        with pytest.raises(InvalidServiceRequestOperationException):
            ServiceRequestExtensions.resolve_with_collection(request, [Partner(code=1)])


class TestHandleServiceLegacyCrud:
    """crud.find / crud.save / crud.remove (.NET HandleService)."""

    def test_crud_find_builds_entity(self):
        request = ServiceRequest(service=ServiceName.CRUD_FIND)

        ServiceRequestExtensions.resolve_with_entity(request, Partner(code=1))

        entity = _body(request).find("entity")
        assert entity.get("name") == "Parceiro"
        assert entity.get("getPresentations") == "false"
        assert entity.find("fields/field").get("name") == "CODPARC"
        # Critérios como <criterio> diretos (Entity.cs: XmlElement "criterio")
        assert entity.find("criteria") is None
        assert [c.get("nome") for c in entity.findall("criterio")] == ["CODPARC"]

    def test_crud_find_with_reference_adds_reference_fetch(self):
        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        partner = Partner(code=1, neighborhood=Neighborhood(code=2))

        ServiceRequestExtensions.resolve_with_entity(request, partner)

        references = request.request_body.entity.references_fetch
        assert "Bairro" in [ref.entity_name for ref in references]

    def test_crud_save_builds_campos(self):
        request = ServiceRequest(service=ServiceName.CRUD_SAVE)

        ServiceRequestExtensions.resolve_with_entity(
            request, Partner(code=1, name="Cliente")
        )

        entity = _body(request).find("entity")
        assert entity.get("name") == "Parceiro"
        # Campos = FieldValues (inclui a chave definida, como no .NET)
        assert [(c.get("nome"), c.text) for c in entity.findall("campo")] == [
            ("CODPARC", "1"),
            ("NOMEPARC", "Cliente"),
        ]

    def test_crud_remove_builds_campos_with_key(self):
        request = ServiceRequest(service=ServiceName.CRUD_REMOVE)

        ServiceRequestExtensions.resolve_with_entity(request, Partner(code=7))

        entity = _body(request).find("entity")
        assert [(c.get("nome"), c.text) for c in entity.findall("campo")] == [
            ("CODPARC", "7"),
        ]

    def test_unsupported_service_raises(self):
        request = ServiceRequest(service=ServiceName.LOGIN)

        with pytest.raises(InvalidServiceRequestOperationException):
            ServiceRequestExtensions.resolve_with_entity(request, Partner(code=1))


class TestResolveWithOptions:
    """Resolve<T>(T, EntityQueryOptions) do .NET."""

    def test_crud_find_options(self):
        from sankhya_sdk.helpers.entity_query_options import EntityQueryOptions

        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        options = EntityQueryOptions(
            include_presentation_fields=True,
            include_references=False,
            max_results=10,
        )

        ServiceRequestExtensions.resolve_with_options(
            request, Partner(code=1, neighborhood=Neighborhood(code=2)), options
        )

        entity = _body(request).find("entity")
        assert entity.get("getPresentations") == "true"
        assert entity.get("rowsLimit") == "10"
        assert entity.find("referenceFetch") is None

    def test_crud_service_find_options(self):
        from sankhya_sdk.helpers.entity_query_options import EntityQueryOptions

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        options = EntityQueryOptions(
            include_presentation_fields=True,
            include_references=False,
        )

        ServiceRequestExtensions.resolve_with_options(
            request, Partner(code=1, neighborhood=Neighborhood(code=2)), options
        )

        data_set = _body(request).find("dataSet")
        assert data_set.get("includePresentationFields") == "S"
        assert [e.get("path") for e in data_set.findall("entity")] == [""]


class TestResolveWithLiteralCriteria:
    """Resolve<T>(ILiteralCriteria) do .NET (ServiceRequestExtensions.cs:727-749)."""

    def test_crud_service_find_with_filter_expression(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        ServiceRequestExtensions.resolve_with_literal_criteria(
            request, Partner, FilterLiteralCriteria.equals("CODPARC", 42)
        )

        literal = request.request_body.data_set.literal_criteria
        assert isinstance(literal, LiteralCriteria)
        assert literal.expression == "CODPARC = 42"
        criteria = _body(request).find("dataSet/criteria")
        assert criteria.findtext("expression") == "CODPARC = 42"

    def test_crud_find_with_filter_expression(self):
        request = ServiceRequest(service=ServiceName.CRUD_FIND)

        ServiceRequestExtensions.resolve_with_literal_criteria(
            request, Partner, FilterLiteralCriteria("NOMEPARC LIKE '%A%'")
        )

        assert isinstance(request.request_body.entity.literal_criteria, LiteralCriteria)
        entity = _body(request).find("entity")
        assert entity.findtext("literalCriteria/expression") == "NOMEPARC LIKE '%A%'"

    def test_model_literal_criteria_keeps_parameters(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        criteria = LiteralCriteria(
            expression="CODPARC > ?",
            parameters=[Parameter(type=ParameterType.INTEGER, value="0")],
        )

        ServiceRequestExtensions.resolve_with_literal_criteria(request, Partner, criteria)

        xml_criteria = _body(request).find("dataSet/criteria")
        assert xml_criteria.findtext("expression") == "CODPARC > ?"
        assert [p.text for p in xml_criteria.findall("parameter")] == ["0"]

    def test_query_builder_parameters(self):
        """
        Expressão de um builder vai sem parâmetros.

        Equivale a ``Resolve<T>(StringBuilder)`` do .NET
        (ServiceRequestExtensions.cs:751-760), que cria
        ``new LiteralCriteria(builder.ToString())``. O QueryBuilder embute
        os valores na expressão (sem '?'), então enviar ``<parameter>``
        geraria binds sem placeholder.
        """
        from sankhya_sdk.models.service.query_types import QueryBuilder

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        builder = (
            QueryBuilder("Parceiro")
            .where("CODPARC", 5, ">", ParameterType.INTEGER)
            .where("NOMEPARC", "Fulano")
        )

        ServiceRequestExtensions.resolve_with_literal_criteria(request, Partner, builder)

        literal = request.request_body.data_set.literal_criteria
        assert literal.expression == "CODPARC > 5 AND NOMEPARC = 'Fulano'"
        assert literal.parameters == []
        criteria = _body(request).find("dataSet/criteria")
        assert criteria.findtext("expression") == "CODPARC > 5 AND NOMEPARC = 'Fulano'"
        assert criteria.findall("parameter") == []

    def test_literal_criteria_sql_on_crud_find(self):
        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        criteria = LiteralCriteriaSql(expression="CODPARC = 1")

        ServiceRequestExtensions.resolve_with_literal_criteria(request, Partner, criteria)

        assert request.request_body.entity.literal_criteria_sql is criteria
        entity = _body(request).find("entity")
        assert entity.findtext("criterioLiteral/expressao") == "CODPARC = 1"

    def test_literal_criteria_sql_on_crud_service_find_raises(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        with pytest.raises(InvalidServiceRequestOperationException):
            ServiceRequestExtensions.resolve_with_literal_criteria(
                request, Partner, LiteralCriteriaSql(expression="CODPARC = 1")
            )


class TestFieldValueFormat:
    """
    Valores enviados no formato do .NET.

    As propriedades serializadas de booleanos e enums no .NET são as
    ``*Internal`` (Partner.cs: IsActiveInternal -> "S"/"N",
    FiscalTypeInternal -> valor interno).
    """

    def test_bool_criteria_uses_s_n_and_is_quoted(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        ServiceRequestExtensions.resolve_with_entity(
            request, Partner(code=1, is_active=True)
        )

        expression = request.request_body.data_set.literal_criteria.expression
        assert expression == "CODPARC = 1 AND ATIVO = 'S'"

    def test_save_bool_and_enum_values(self):
        from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)

        ServiceRequestExtensions.resolve_with_entity(
            request,
            Partner(
                code=1,
                is_active=False,
                fiscal_type=FiscalPersonType.CORPORATION,
            ),
        )

        local_fields = request.request_body.data_set.data_rows[0].local_fields
        assert local_fields == {"TIPPESSOA": "J", "ATIVO": "N"}


class TestIgnoreInlineReference:
    """EntityElement(..., IgnoreInlineReference = true) do .NET."""

    def test_element_with_underscore_is_a_regular_field(self):
        from typing import Optional

        from sankhya_sdk.attributes.decorators import (
            entity,
            entity_element,
            entity_key,
        )
        from sankhya_sdk.models.transport.base import TransportEntityBase

        @entity("Documento")
        class _Document(TransportEntityBase):
            code: int = entity_key(entity_element("CODDOC", default=0))
            document: Optional[str] = entity_element(
                "CGC_CPF", ignore_inline_reference=True, default=None
            )
            inline: Optional[str] = entity_element("Cidade_NOMECID", default=None)

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)

        ServiceRequestExtensions.resolve_with_entity(
            request, _Document(code=1, document="01234567890")
        )

        data_set = request.request_body.data_set
        assert data_set.data_rows[0].local_fields == {"CGC_CPF": "01234567890"}

        find_request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        ServiceRequestExtensions.resolve_with_entity(find_request, _Document(code=1))

        entities = find_request.request_body.data_set.entities
        assert entities[0].fieldset.list == "CODDOC,CGC_CPF"
        # Sem IgnoreInlineReference, o padrão Entidade_CAMPO continua sendo
        # tratado como referência inline
        assert [(e.path, e.fieldset.list) for e in entities[1:]] == [
            ("Cidade", "NOMECID"),
        ]
