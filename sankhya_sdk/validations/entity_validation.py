"""Entity validation patterns for API error messages.

This module provides compiled regular expression patterns for parsing
and validating error messages returned by the Sankhya API.

Migrated from: Sankhya-SDK-dotnet/Src/Sankhya/Validations/EntityValidation.cs

Note on Regex Timeouts:
    Python 3.11+ supports a `timeout` parameter, but only for regex operations
    like `re.search()`, `re.match()`, `re.findall()`, etc. — NOT for `re.compile()`.
    The compiled pattern objects do not store timeout; instead, pass `timeout`
    directly to the search/match call if running on Python 3.11+.
    For compatibility with Python <3.11, timeout is not applied here.
"""

import re
from typing import Pattern


class EntityValidation:
    """Static class containing compiled regex patterns for API error validation.

    These patterns are used to parse and extract information from error messages
    returned by the Sankhya API, allowing for programmatic error handling and
    recovery.

    All patterns are compiled with IGNORECASE and MULTILINE flags for
    consistent matching across different error message formats.

    Attributes:
        REFERENCE_FIELDS_FIRST_LEVEL_PATTERN: Matches first-level reference fields.
        REFERENCE_FIELDS_SECOND_LEVEL_PATTERN: Matches second-level reference fields.
        PROPERTY_VALUE_ERROR_PATTERN: Matches property value errors.
        PROPERTY_NAME_ERROR_PATTERN: Matches invalid field descriptor errors.
        PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN: Matches identifier association errors.
        PROPERTY_NOT_FOUND_PATTERN: Matches field not found errors.
        PROPERTY_NAME_INVALID_ERROR_PATTERN: Matches invalid column name errors.
        PROPERTY_WIDTH_ERROR_PATTERN: Matches property width limit errors.
        PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN: Matches foreign key conflicts.
        DUPLICATED_DOCUMENT_PATTERN: Matches duplicate CNPJ/CPF errors.
        BUSINESS_RULE_RESTRICTION_PATTERN: Matches business rule violations.
        FULL_TRANSACTION_LOGS_PATTERN: Matches transaction log full errors.
        MISSING_RELATION_PATTERN: Matches missing relationship errors.
        MISSING_ATTRIBUTE_PATTERN: Matches missing required attribute errors.
    """

    # Flags used for all patterns
    _FLAGS: int = re.IGNORECASE | re.MULTILINE

    # Reference field patterns
    REFERENCE_FIELDS_FIRST_LEVEL_PATTERN: Pattern[str] = re.compile(
        r"^(?!AD)(?P<entity>[A-Z].+)_(?P<field>.+)$",
        _FLAGS
    )
    """Matches first-level reference fields like 'Entity_Field'.

    Named groups:
        - entity: The entity name
        - field: The field name
    """

    REFERENCE_FIELDS_SECOND_LEVEL_PATTERN: Pattern[str] = re.compile(
        r"^(?!AD)(?P<parentEntity>[A-Z].+)_(?P<entity>[A-Z].+)_(?P<field>.+)$",
        _FLAGS
    )
    """Matches second-level reference fields like 'ParentEntity_Entity_Field'.

    Named groups:
        - parentEntity: The parent entity name
        - entity: The child entity name
        - field: The field name
    """

    # Property error patterns
    PROPERTY_VALUE_ERROR_PATTERN: Pattern[str] = re.compile(
        r"erro ao obter valor da propriedade '(?P<propertyName>(?:(?:[A-Z]+)(?:-(?:>|&gt;))?)+)",
        _FLAGS
    )
    """Matches property value retrieval errors.

    Named groups:
        - propertyName: The property name that failed
    """

    PROPERTY_NAME_ERROR_PATTERN: Pattern[str] = re.compile(
        r"Descritor do campo '(?P<propertyName>[A-Z]+)' inválido",
        _FLAGS
    )
    """Matches invalid field descriptor errors.

    Named groups:
        - propertyName: The invalid field name
    """

    PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN: Pattern[str] = re.compile(
        r'O identificador de várias partes "(?P<entity>[A-Z]+)\.(?P<propertyName>[A-Z]+)" não pôde ser associado',
        _FLAGS
    )
    """Matches multi-part identifier association errors.

    Named groups:
        - entity: The entity name
        - propertyName: The property name
    """

    PROPERTY_NOT_FOUND_PATTERN: Pattern[str] = re.compile(
        r"Campo não existe: (?P<entity>[A-Z]+)->(?P<propertyName>[A-Z]+)",
        _FLAGS
    )
    """Matches field not found errors.

    Named groups:
        - entity: The entity name
        - propertyName: The missing property name
    """

    PROPERTY_NAME_INVALID_ERROR_PATTERN: Pattern[str] = re.compile(
        r"Nome de coluna '(?P<propertyName>.+?)' inválido",
        _FLAGS
    )
    """Matches invalid column name errors.

    Named groups:
        - propertyName: The invalid column name
    """

    PROPERTY_WIDTH_ERROR_PATTERN: Pattern[str] = re.compile(
        r"^Propriedade '(?P<propertyName>.+?)' com largura acima do limite: \((?P<currentWidth>\d+) > (?P<widthAllowed>\d+)\)$",
        _FLAGS
    )
    """Matches property width limit errors.

    Named groups:
        - propertyName: The property name
        - currentWidth: The current value width
        - widthAllowed: The maximum allowed width
    """

    PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN: Pattern[str] = re.compile(
        r"conflito com a restrição FOREIGN KEY \"(?P<constraintName>.+?)\"\.?\s*"
        r"O conflito ocorreu no banco de dados \"(?P<database>.+?)\",\s*"
        r"tabela \"(?P<table>.+?)\"(?:,\s*column '(?P<column>.+?)')?",
        _FLAGS
    )
    """Matches foreign key constraint violation errors.

    Named groups:
        - constraintName: The constraint name
        - database: The database name
        - table: The table name
        - column: The column name (optional)
    """

    DUPLICATED_DOCUMENT_PATTERN: Pattern[str] = re.compile(
        r"CNPJ/CPF já existente para o parceiro: '(?P<name>.+?)'$",
        _FLAGS
    )
    """Matches duplicate CNPJ/CPF document errors.

    Named groups:
        - name: The partner name with duplicate document
    """

    BUSINESS_RULE_RESTRICTION_PATTERN: Pattern[str] = re.compile(
        r'^A regra "(?P<ruleName>.+?)" não permitiu a operação\.(?:\r?\n)*(?P<errorMessage>.+?)$',
        _FLAGS
    )
    """Matches business rule restriction errors.

    Named groups:
        - ruleName: The name of the business rule
        - errorMessage: The detailed error message
    """

    FULL_TRANSACTION_LOGS_PATTERN: Pattern[str] = re.compile(
        r"^\s*Log de transações do banco de dados '(?P<database>.+?)' cheio",
        _FLAGS
    )
    """Matches transaction log full errors.

    Named groups:
        - database: The database name
    """

    MISSING_RELATION_PATTERN: Pattern[str] = re.compile(
        r"^Relacionamento: '(?P<missingRelation>.+?)' não encontrado em: '(?P<entity>.+?)'",
        _FLAGS
    )
    """Matches missing relationship errors.

    Named groups:
        - missingRelation: The missing relationship name
        - entity: The entity name
    """

    MISSING_ATTRIBUTE_PATTERN: Pattern[str] = re.compile(
        r"^É necessário informar o atributo '(?P<attributeName>.+?)'$",
        _FLAGS
    )
    """Matches missing required attribute errors.

    Named groups:
        - attributeName: The name of the required attribute
    """

    @staticmethod
    def match_reference_first_level(text: str) -> re.Match[str] | None:
        """Match first-level reference field pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(text)

    @staticmethod
    def match_reference_second_level(text: str) -> re.Match[str] | None:
        """Match second-level reference field pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(text)

    @staticmethod
    def match_property_value_error(text: str) -> re.Match[str] | None:
        """Match property value error pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.PROPERTY_VALUE_ERROR_PATTERN.search(text)

    @staticmethod
    def match_property_name_error(text: str) -> re.Match[str] | None:
        """Match property name error pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.PROPERTY_NAME_ERROR_PATTERN.search(text)

    @staticmethod
    def match_property_not_found(text: str) -> re.Match[str] | None:
        """Match property not found pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.PROPERTY_NOT_FOUND_PATTERN.search(text)

    @staticmethod
    def match_property_width_error(text: str) -> re.Match[str] | None:
        """Match property width error pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.PROPERTY_WIDTH_ERROR_PATTERN.match(text)

    @staticmethod
    def match_business_rule_restriction(text: str) -> re.Match[str] | None:
        """Match business rule restriction pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.BUSINESS_RULE_RESTRICTION_PATTERN.match(text)

    @staticmethod
    def match_duplicated_document(text: str) -> re.Match[str] | None:
        """Match duplicated document pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.DUPLICATED_DOCUMENT_PATTERN.search(text)

    @staticmethod
    def match_missing_relation(text: str) -> re.Match[str] | None:
        """Match missing relation pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.MISSING_RELATION_PATTERN.match(text)

    @staticmethod
    def match_missing_attribute(text: str) -> re.Match[str] | None:
        """Match missing attribute pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.MISSING_ATTRIBUTE_PATTERN.match(text)

    @staticmethod
    def match_full_transaction_logs(text: str) -> re.Match[str] | None:
        """Match full transaction logs pattern.

        Args:
            text: Text to match against.

        Returns:
            Match object if pattern matches, None otherwise.
        """
        return EntityValidation.FULL_TRANSACTION_LOGS_PATTERN.match(text)

    @staticmethod
    def match_foreign_key_restriction(text: str) -> re.Match[str] | None:
        """Match foreign key restriction pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN.search(text)

    @staticmethod
    def match_property_name_association(text: str) -> re.Match[str] | None:
        """Match multi-part identifier association error pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN.search(text)

    @staticmethod
    def match_property_name_invalid(text: str) -> re.Match[str] | None:
        """Match invalid column name error pattern.

        Args:
            text: Text to search for the pattern.

        Returns:
            Match object if pattern found, None otherwise.
        """
        return EntityValidation.PROPERTY_NAME_INVALID_ERROR_PATTERN.search(text)
