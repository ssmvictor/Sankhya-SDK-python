"""Unit tests for EntityValidation class.

Tests the regex patterns used for parsing API error messages.
Uses parametrized tests to cover multiple matching scenarios.
"""

import pytest

from sankhya_sdk.validations.entity_validation import EntityValidation


class TestReferenceFieldsFirstLevelPattern:
    """Tests for REFERENCE_FIELDS_FIRST_LEVEL_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_entity,expected_field",
        [
            ("Parceiro_NOMEPARC", "Parceiro", "NOMEPARC"),
            ("Produto_DESCRPROD", "Produto", "DESCRPROD"),
            ("Cidade_NOMECID", "Cidade", "NOMECID"),
            ("Estado_UF", "Estado", "UF"),
            ("NotaFiscal_NUMNOTA", "NotaFiscal", "NUMNOTA"),
        ],
    )
    def test_matches_valid_first_level_references(
        self, text: str, expected_entity: str, expected_field: str
    ) -> None:
        """Pattern matches valid first-level reference fields."""
        match = EntityValidation.match_reference_first_level(text)
        assert match is not None
        assert match.group("entity") == expected_entity
        assert match.group("field") == expected_field

    @pytest.mark.parametrize(
        "text",
        [
            "AD_SOMETHING",  # Starts with AD - excluded
            # Note: "lowercase_field" matches because IGNORECASE is used
            "NoUnderscore",  # No underscore separator
            "",  # Empty string
        ],
    )
    def test_does_not_match_invalid_references(self, text: str) -> None:
        """Pattern does not match invalid first-level references."""
        match = EntityValidation.match_reference_first_level(text)
        assert match is None


class TestReferenceFieldsSecondLevelPattern:
    """Tests for REFERENCE_FIELDS_SECOND_LEVEL_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_parent,expected_entity,expected_field",
        [
            ("NotaFiscal_Parceiro_NOMEPARC", "NotaFiscal", "Parceiro", "NOMEPARC"),
            ("Pedido_Produto_DESCRPROD", "Pedido", "Produto", "DESCRPROD"),
            ("Venda_Cliente_RAZAOSOCIAL", "Venda", "Cliente", "RAZAOSOCIAL"),
        ],
    )
    def test_matches_valid_second_level_references(
        self, text: str, expected_parent: str, expected_entity: str, expected_field: str
    ) -> None:
        """Pattern matches valid second-level reference fields."""
        match = EntityValidation.match_reference_second_level(text)
        assert match is not None
        assert match.group("parentEntity") == expected_parent
        assert match.group("entity") == expected_entity
        assert match.group("field") == expected_field

    @pytest.mark.parametrize(
        "text",
        [
            "AD_Entity_Field",  # Starts with AD
            "Single_Field",  # Only one level
            # Note: "no_uppercase_here" matches because IGNORECASE is used
            "",  # Empty string
        ],
    )
    def test_does_not_match_invalid_references(self, text: str) -> None:
        """Pattern does not match invalid second-level references."""
        match = EntityValidation.match_reference_second_level(text)
        assert match is None


class TestPropertyValueErrorPattern:
    """Tests for PROPERTY_VALUE_ERROR_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_property",
        [
            ("erro ao obter valor da propriedade 'NOMEPARC'", "NOMEPARC"),
            ("erro ao obter valor da propriedade 'CODPROD->DESCRPROD'", "CODPROD->DESCRPROD"),
            ("erro ao obter valor da propriedade 'FIELD-&gt;SUBFIELD'", "FIELD-&gt;SUBFIELD"),
        ],
    )
    def test_matches_property_value_errors(
        self, text: str, expected_property: str
    ) -> None:
        """Pattern matches property value error messages."""
        match = EntityValidation.match_property_value_error(text)
        assert match is not None
        assert match.group("propertyName") == expected_property

    def test_does_not_match_other_errors(self) -> None:
        """Pattern does not match unrelated error messages."""
        match = EntityValidation.match_property_value_error("Some other error message")
        assert match is None


class TestPropertyNameErrorPattern:
    """Tests for PROPERTY_NAME_ERROR_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_property",
        [
            ("Descritor do campo 'NOMEPARC' inválido", "NOMEPARC"),
            ("Descritor do campo 'CODPROD' inválido", "CODPROD"),
            ("Descritor do campo 'UF' inválido", "UF"),
        ],
    )
    def test_matches_property_name_errors(
        self, text: str, expected_property: str
    ) -> None:
        """Pattern matches field descriptor error messages."""
        match = EntityValidation.match_property_name_error(text)
        assert match is not None
        assert match.group("propertyName") == expected_property


class TestPropertyNameAssociationErrorPattern:
    """Tests for PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_entity,expected_property",
        [
            (
                'O identificador de várias partes "PARCEIRO.NOMEPARC" não pôde ser associado',
                "PARCEIRO",
                "NOMEPARC",
            ),
            (
                'O identificador de várias partes "PRODUTO.DESCRPROD" não pôde ser associado',
                "PRODUTO",
                "DESCRPROD",
            ),
        ],
    )
    def test_matches_association_errors(
        self, text: str, expected_entity: str, expected_property: str
    ) -> None:
        """Pattern matches multi-part identifier association errors."""
        match = EntityValidation.PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN.search(text)
        assert match is not None
        assert match.group("entity") == expected_entity
        assert match.group("propertyName") == expected_property


class TestPropertyNotFoundPattern:
    """Tests for PROPERTY_NOT_FOUND_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_entity,expected_property",
        [
            ("Campo não existe: PARCEIRO->NOMEPARC", "PARCEIRO", "NOMEPARC"),
            ("Campo não existe: PRODUTO->CODPROD", "PRODUTO", "CODPROD"),
            ("Campo não existe: NOTAFISCAL->NUMNOTA", "NOTAFISCAL", "NUMNOTA"),
        ],
    )
    def test_matches_property_not_found_errors(
        self, text: str, expected_entity: str, expected_property: str
    ) -> None:
        """Pattern matches field not found error messages."""
        match = EntityValidation.match_property_not_found(text)
        assert match is not None
        assert match.group("entity") == expected_entity
        assert match.group("propertyName") == expected_property


class TestPropertyNameInvalidErrorPattern:
    """Tests for PROPERTY_NAME_INVALID_ERROR_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_property",
        [
            ("Nome de coluna 'NOMEPARC' inválido", "NOMEPARC"),
            ("Nome de coluna 'Campo Inválido' inválido", "Campo Inválido"),
            ("Nome de coluna '123ABC' inválido", "123ABC"),
        ],
    )
    def test_matches_invalid_column_name_errors(
        self, text: str, expected_property: str
    ) -> None:
        """Pattern matches invalid column name error messages."""
        match = EntityValidation.PROPERTY_NAME_INVALID_ERROR_PATTERN.search(text)
        assert match is not None
        assert match.group("propertyName") == expected_property


class TestPropertyWidthErrorPattern:
    """Tests for PROPERTY_WIDTH_ERROR_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_property,expected_current,expected_allowed",
        [
            (
                "Propriedade 'NOMEPARC' com largura acima do limite: (150 > 100)",
                "NOMEPARC",
                "150",
                "100",
            ),
            (
                "Propriedade 'DESCRPROD' com largura acima do limite: (500 > 255)",
                "DESCRPROD",
                "500",
                "255",
            ),
        ],
    )
    def test_matches_property_width_errors(
        self,
        text: str,
        expected_property: str,
        expected_current: str,
        expected_allowed: str,
    ) -> None:
        """Pattern matches property width limit error messages."""
        match = EntityValidation.match_property_width_error(text)
        assert match is not None
        assert match.group("propertyName") == expected_property
        assert match.group("currentWidth") == expected_current
        assert match.group("widthAllowed") == expected_allowed


class TestPropertyForeignKeyRestrictionPattern:
    """Tests for PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN."""

    def test_matches_foreign_key_error(self) -> None:
        """Pattern matches foreign key constraint violation."""
        text = (
            'conflito com a restrição FOREIGN KEY "FK_PARCEIRO_CIDADE". '
            'O conflito ocorreu no banco de dados "SANKHYA", '
            "tabela \"TGFPAR\", column 'CODCID'"
        )
        match = EntityValidation.match_foreign_key_restriction(text)
        assert match is not None
        assert match.group("constraintName") == "FK_PARCEIRO_CIDADE"
        assert match.group("database") == "SANKHYA"
        assert match.group("table") == "TGFPAR"
        assert match.group("column") == "CODCID"

    def test_matches_foreign_key_error_without_column(self) -> None:
        """Pattern matches foreign key error without column specification."""
        text = (
            'conflito com a restrição FOREIGN KEY "FK_PRODUTO_GRUPO". '
            'O conflito ocorreu no banco de dados "SANKHYA", '
            'tabela "TGFPRO"'
        )
        match = EntityValidation.match_foreign_key_restriction(text)
        assert match is not None
        assert match.group("constraintName") == "FK_PRODUTO_GRUPO"
        assert match.group("column") is None


class TestDuplicatedDocumentPattern:
    """Tests for DUPLICATED_DOCUMENT_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_name",
        [
            ("CNPJ/CPF já existente para o parceiro: 'João da Silva'", "João da Silva"),
            ("CNPJ/CPF já existente para o parceiro: 'Empresa LTDA'", "Empresa LTDA"),
            ("CNPJ/CPF já existente para o parceiro: 'Cliente 123'", "Cliente 123"),
        ],
    )
    def test_matches_duplicated_document_errors(
        self, text: str, expected_name: str
    ) -> None:
        """Pattern matches duplicate CNPJ/CPF error messages."""
        match = EntityValidation.match_duplicated_document(text)
        assert match is not None
        assert match.group("name") == expected_name


class TestBusinessRuleRestrictionPattern:
    """Tests for BUSINESS_RULE_RESTRICTION_PATTERN."""

    def test_matches_business_rule_error(self) -> None:
        """Pattern matches business rule restriction errors."""
        text = (
            'A regra "Validação de Crédito" não permitiu a operação.\n'
            "Cliente com limite de crédito excedido."
        )
        match = EntityValidation.match_business_rule_restriction(text)
        assert match is not None
        assert match.group("ruleName") == "Validação de Crédito"
        assert match.group("errorMessage") == "Cliente com limite de crédito excedido."

    def test_matches_business_rule_error_with_crlf(self) -> None:
        """Pattern matches business rule with Windows line endings."""
        text = (
            'A regra "Regra de Estoque" não permitiu a operação.\r\n'
            "Produto sem estoque disponível."
        )
        match = EntityValidation.match_business_rule_restriction(text)
        assert match is not None
        assert match.group("ruleName") == "Regra de Estoque"


class TestFullTransactionLogsPattern:
    """Tests for FULL_TRANSACTION_LOGS_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_database",
        [
            ("Log de transações do banco de dados 'SANKHYA' cheio", "SANKHYA"),
            (" Log de transações do banco de dados 'PRODUCAO' cheio", "PRODUCAO"),
            ("Log de transações do banco de dados 'teste_db' cheio", "teste_db"),
        ],
    )
    def test_matches_full_transaction_log_errors(
        self, text: str, expected_database: str
    ) -> None:
        """Pattern matches transaction log full error messages."""
        match = EntityValidation.match_full_transaction_logs(text)
        assert match is not None
        assert match.group("database") == expected_database


class TestMissingRelationPattern:
    """Tests for MISSING_RELATION_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_relation,expected_entity",
        [
            (
                "Relacionamento: 'Cidade' não encontrado em: 'Parceiro'",
                "Cidade",
                "Parceiro",
            ),
            (
                "Relacionamento: 'Grupo' não encontrado em: 'Produto'",
                "Grupo",
                "Produto",
            ),
        ],
    )
    def test_matches_missing_relation_errors(
        self, text: str, expected_relation: str, expected_entity: str
    ) -> None:
        """Pattern matches missing relationship error messages."""
        match = EntityValidation.match_missing_relation(text)
        assert match is not None
        assert match.group("missingRelation") == expected_relation
        assert match.group("entity") == expected_entity


class TestMissingAttributePattern:
    """Tests for MISSING_ATTRIBUTE_PATTERN."""

    @pytest.mark.parametrize(
        "text,expected_attribute",
        [
            ("É necessário informar o atributo 'NOMEPARC'", "NOMEPARC"),
            ("É necessário informar o atributo 'CODPROD'", "CODPROD"),
            ("É necessário informar o atributo 'Data de Nascimento'", "Data de Nascimento"),
        ],
    )
    def test_matches_missing_attribute_errors(
        self, text: str, expected_attribute: str
    ) -> None:
        """Pattern matches missing required attribute error messages."""
        match = EntityValidation.match_missing_attribute(text)
        assert match is not None
        assert match.group("attributeName") == expected_attribute


class TestPatternCaseSensitivity:
    """Tests for case-insensitive matching."""

    def test_property_name_error_case_insensitive(self) -> None:
        """Property name error pattern is case insensitive."""
        text_lower = "descritor do campo 'TESTE' inválido"
        text_upper = "DESCRITOR DO CAMPO 'TESTE' INVÁLIDO"

        match_lower = EntityValidation.PROPERTY_NAME_ERROR_PATTERN.search(text_lower)
        match_upper = EntityValidation.PROPERTY_NAME_ERROR_PATTERN.search(text_upper)

        assert match_lower is not None
        assert match_upper is not None

    def test_duplicated_document_case_insensitive(self) -> None:
        """Duplicated document pattern is case insensitive."""
        text = "cnpj/cpf já existente para o parceiro: 'Teste'"
        match = EntityValidation.match_duplicated_document(text)
        assert match is not None
