"""
Testes unitários para QueryCriteria e QueryBuilder.

Garante que os tipos de valor usam apenas membros existentes de ParameterType.
"""

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
