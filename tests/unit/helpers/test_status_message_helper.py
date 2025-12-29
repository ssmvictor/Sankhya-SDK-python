# -*- coding: utf-8 -*-
"""
Testes unitários para status_message_helper.py
"""

import pytest
from unittest.mock import Mock, MagicMock

from sankhya_sdk.helpers.status_message_helper import (
    StatusMessageHelper,
    PROPERTY_VALUE_ERROR_PATTERN,
    PROPERTY_NAME_ERROR_PATTERN,
    REFERENCE_FIELDS_FIRST_LEVEL_PATTERN,
    REFERENCE_FIELDS_SECOND_LEVEL_PATTERN,
)


class TestStatusMessageHelper:
    """Testes para StatusMessageHelper."""

    @pytest.fixture
    def mock_request(self):
        """Cria mock de ServiceRequest."""
        return Mock()

    @pytest.fixture
    def mock_response(self):
        """Cria mock de ServiceResponse."""
        response = Mock()
        response.status_message = None
        return response

    @pytest.fixture
    def mock_service(self):
        """Cria mock de ServiceName."""
        return Mock()

    def test_no_status_message_does_nothing(
        self, mock_service, mock_request, mock_response
    ):
        """Não deve lançar exceção se não houver status_message."""
        mock_response.status_message = None
        
        # Não deve lançar exceção
        StatusMessageHelper.process_status_message(
            mock_service, mock_request, mock_response
        )

    def test_empty_status_message_does_nothing(
        self, mock_service, mock_request, mock_response
    ):
        """Não deve lançar exceção se status_message estiver vazio."""
        mock_response.status_message = Mock(decoded_value="")
        
        StatusMessageHelper.process_status_message(
            mock_service, mock_request, mock_response
        )


class TestRegexPatterns:
    """Testes para padrões regex."""

    def test_property_value_error_pattern(self):
        """Testa padrão de erro de valor de propriedade."""
        text = "O valor do campo 'CODPARC' é inválido"
        match = PROPERTY_VALUE_ERROR_PATTERN.search(text)
        
        assert match is not None
        assert match.group("propertyName") == "CODPARC"

    def test_property_name_error_pattern(self):
        """Testa padrão de erro de nome de propriedade."""
        text = "O campo 'XPTO' não existe"
        match = PROPERTY_NAME_ERROR_PATTERN.search(text)
        
        assert match is not None
        assert match.group("propertyName") == "XPTO"

    def test_reference_first_level_pattern(self):
        """Testa padrão de referência primeiro nível."""
        text = "Parceiro_NomeParceiro"
        match = REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(text)
        
        assert match is not None
        assert match.group("entity") == "Parceiro"
        assert match.group("field") == "NomeParceiro"

    def test_reference_second_level_pattern(self):
        """Testa padrão de referência segundo nível."""
        text = "Produto_Familia_Descricao"
        match = REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(text)
        
        assert match is not None
        assert match.group("parentEntity") == "Produto"
        assert match.group("entity") == "Familia"
        assert match.group("field") == "Descricao"

    def test_first_level_pattern_no_match_for_simple_field(self):
        """Padrão primeiro nível não deve casar com campo simples."""
        text = "CODPARC"
        match = REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(text)
        
        assert match is None

    def test_second_level_pattern_no_match_for_first_level(self):
        """Padrão segundo nível não deve casar com primeiro nível."""
        text = "Parceiro_Nome"
        match = REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(text)
        
        assert match is None
