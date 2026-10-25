"""
Testes unitários para QueryCriteria e QueryBuilder.

Garante que os tipos de valor usam apenas membros existentes de ParameterType.
"""

from decimal import Decimal

import pytest

from sankhya_sdk.enums.parameter_type import ParameterType
from sankhya_sdk.models.service.query_types import QueryBuilder, QueryCriteria


class TestQueryCriteria:
    """Testes para a classe QueryCriteria."""

    def test_to_sql_string_is_quoted_and_escaped(self):
        """Testa que valores STRING são citados e têm aspas escapadas."""
        crit = QueryCriteria(field="NOMEPARC", value="O'Brien", value_type=ParameterType.STRING)

        assert crit.to_sql() == "NOMEPARC = 'O''Brien'"

    def test_to_sql_datetime_is_quoted(self):
        """Testa que valores DATETIME são citados."""
        crit = QueryCriteria(field="DTNEG", operator=">=", value="01/01/2024", value_type=ParameterType.DATETIME)

        assert crit.to_sql() == "DTNEG >= '01/01/2024'"

    def test_to_sql_integer_is_not_quoted(self):
        """Testa que valores INTEGER não são citados."""
        crit = QueryCriteria(field="CODPARC", operator=">", value="10", value_type=ParameterType.INTEGER)

        assert crit.to_sql() == "CODPARC > 10"

    def test_to_sql_integer_rejects_non_integer_value(self):
        """Testa que um valor INTEGER nao numerico nao e inserido cru no SQL."""
        crit = QueryCriteria(
            field="CODPARC", value="1 OR 1=1", value_type=ParameterType.INTEGER
        )

        with pytest.raises(ValueError):
            crit.to_sql()

    def test_to_sql_integer_normalizes_value(self):
        """Testa que espacos e sinal sao normalizados no valor INTEGER."""
        crit = QueryCriteria(field="CODPARC", value=" -12 ", value_type=ParameterType.INTEGER)

        assert crit.to_sql() == "CODPARC = -12"

    def test_to_sql_without_type_infers(self):
        """Testa a inferência de tipo quando value_type não é informado."""
        assert QueryCriteria(field="CODPARC", value="10").to_sql() == "CODPARC = 10"
        assert QueryCriteria(field="ATIVO", value="S").to_sql() == "ATIVO = 'S'"


class TestQueryBuilder:
    """Testes para a classe QueryBuilder."""

    def test_build_expression(self):
        """Testa a construção da expressão com critérios tipados."""
        builder = (
            QueryBuilder("Parceiro")
            .where("CODPARC", 10, ">", ParameterType.INTEGER)
            .where("ATIVO", "S", value_type=ParameterType.STRING)
            .where_null("DTALTER")
        )

        assert builder.build_expression() == "CODPARC > 10 AND ATIVO = 'S' AND DTALTER IS NULL"

    def test_build_parameters_defaults_to_string(self):
        """Testa que critérios sem tipo geram parâmetros STRING e nulos são ignorados."""
        builder = (
            QueryBuilder("Parceiro")
            .where("CODPARC", 10, value_type=ParameterType.INTEGER)
            .where("NOMEPARC", "Cliente")
            .where_null("DTALTER")
        )

        params = builder.build_parameters()

        assert [(p.type, p.value) for p in params] == [
            (ParameterType.INTEGER, "10"),
            (ParameterType.STRING, "Cliente"),
        ]
        assert [p.to_xml().get("type") for p in params] == ["I", "S"]


class TestWhereIn:
    """
    QueryBuilder.where_in e critérios IN/NOT IN.

    Sem equivalente no .NET: a expressão vai como literal criteria sem
    alteração (Resolve<T>(StringBuilder), ServiceRequestExtensions.cs:751-760),
    então o builder precisa gerar uma lista IN válida.
    """

    def test_integers_are_not_quoted(self):
        builder = QueryBuilder("Parceiro").where_in("CODCID", [1, 2])

        assert builder.build_expression() == "CODCID IN (1, 2)"

    def test_strings_are_quoted_and_escaped(self):
        builder = QueryBuilder("Parceiro").where_in("NOMEPARC", ["O'Neil", "A"])

        assert builder.build_expression() == "NOMEPARC IN ('O''Neil', 'A')"

    def test_mixed_values(self):
        builder = (
            QueryBuilder("Parceiro")
            .where_in("CODIGO", [-5, Decimal("1.50"), None, "1", True])
            .where("CODPARC", 5, value_type=ParameterType.INTEGER)
        )

        assert builder.build_expression() == (
            "CODIGO IN (-5, 1.50, NULL, '1', 'True') AND CODPARC = 5"
        )

    def test_injection_attempt_stays_inside_string_literal(self):
        builder = QueryBuilder("Parceiro").where_in(
            "NOMEPARC", ["x') OR 1=1 --"]
        )

        assert builder.build_expression() == "NOMEPARC IN ('x'') OR 1=1 --')"

    def test_non_finite_decimal_is_rejected(self):
        with pytest.raises(ValueError):
            QueryBuilder("Parceiro").where_in("VLR", [Decimal("NaN")])

    def test_empty_values_add_no_criteria(self):
        assert QueryBuilder("Parceiro").where_in("CODCID", []).build_expression() == ""

    def test_literal_criteria_expression(self):
        from sankhya_sdk.enums.service_name import ServiceName
        from sankhya_sdk.helpers.service_request_extensions import (
            ServiceRequestExtensions,
        )
        from sankhya_sdk.models.service.service_request import ServiceRequest
        from sankhya_sdk.models.transport import Partner

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        builder = QueryBuilder("Parceiro").where_in("CODCID", [1, 2])

        ServiceRequestExtensions.resolve_with_literal_criteria(request, Partner, builder)

        assert request.request_body.data_set.literal_criteria.expression == (
            "CODCID IN (1, 2)"
        )

    @pytest.mark.parametrize("operator", ["IN", "NOT IN", "not  in"])
    def test_query_criteria_set_operator_keeps_list(self, operator):
        crit = QueryCriteria(field="CODCID", operator=operator, value="(1, 'A''B', NULL)")

        assert crit.to_sql() == f"CODCID {operator} (1, 'A''B', NULL)"

    @pytest.mark.parametrize(
        "value",
        [
            "1, 2",
            "(1, 2) OR 1=1",
            "(1); DELETE FROM TGFPAR",
            "('a' || 'b')",
            "('unterminated)",
            "()",
            "(SELECT CODCID FROM TSICID)",
        ],
    )
    def test_query_criteria_invalid_list_is_rejected(self, value):
        crit = QueryCriteria(field="CODCID", operator="IN", value=value)

        with pytest.raises(ValueError):
            crit.to_sql()
