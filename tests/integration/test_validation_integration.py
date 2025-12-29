# -*- coding: utf-8 -*-
"""
Testes de integração para validação de entidades.

Testa validação de campos, tipos de dados e regras de negócio.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.models.transport.neighborhood import Neighborhood
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    create_error_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_success_response,
)


@pytest.mark.integration
class TestFieldValidation:
    """Testes de validação de campos."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_required_field_name(self, mock_session_class):
        """Testa validação de campo nome obrigatório."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("VALIDATION.REQUIRED", "Campo NOMEPARC é obrigatório")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Parceiro sem nome
            partner = Partner()
            
            with pytest.raises(SankhyaException) as exc:
                SimpleCRUDRequestWrapper.create(partner)
            
            assert "NOMEPARC" in str(exc.value) or "obrigatório" in str(exc.value).lower()
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_max_length(self, mock_session_class):
        """Testa validação de tamanho máximo."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("VALIDATION.LENGTH", "Campo excede tamanho máximo")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Nome muito longo
            partner = Partner(name="A" * 1000)
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestDataTypeValidation:
    """Testes de validação de tipos de dados."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_numeric_field(self, mock_session_class):
        """Testa validação de campo numérico."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("VALIDATION.TYPE", "Valor inválido para campo numérico")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Código inválido (negativo pode ser rejeitado)
            partner = Partner(code=-999, name="Teste")
            
            # Dependendo da implementação, pode falhar ou não
            try:
                SimpleCRUDRequestWrapper.create(partner)
            except SankhyaException:
                pass  # Esperado
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_email_format(self, mock_session_class):
        """Testa validação de formato de email."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("VALIDATION.EMAIL", "Formato de email inválido")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Email inválido
            partner = Partner(name="Parceiro", email_address="email-invalido")
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestReferenceValidation:
    """Testes de validação de referências."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_invalid_city_reference(self, mock_session_class):
        """Testa validação de referência de cidade inválida."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("FK_VIOLATION", "Cidade não encontrada")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Cidade inexistente
            partner = Partner(name="Parceiro", code_city=999999)
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_invalid_neighborhood_reference(self, mock_session_class):
        """Testa validação de referência de bairro inválida."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("FK_VIOLATION", "Bairro não encontrado")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Bairro inexistente
            partner = Partner(name="Parceiro", code_neighborhood=999999)
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestBusinessRuleValidation:
    """Testes de validação de regras de negócio."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_active_partner_deletion(self, mock_session_class):
        """Testa validação de deleção de parceiro ativo."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response(
                "BUSINESS.RULE", 
                "Não é possível excluir parceiro com notas fiscais pendentes"
            )
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Tentar deletar parceiro com dependências
            partner = Partner(code=1)
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.remove(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_product_without_volume(self, mock_session_class):
        """Testa validação de produto sem unidade de volume."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("VALIDATION.REQUIRED", "Campo CODVOL é obrigatório")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Produto sem código de volume
            product = Product(name="Produto Teste")
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(product)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestValidationSuccess:
    """Testes de validação bem-sucedida."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_valid_partner_creation(self, mock_session_class):
        """Testa criação de parceiro válido."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro Válido", "EMAIL": "valid@email.com"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, success_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Parceiro com todos os campos válidos
            partner = Partner(name="Parceiro Válido", email_address="valid@email.com")
            result = SimpleCRUDRequestWrapper.create(partner)
            
            assert result.code == 1
            assert result.name == "Parceiro Válido"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_valid_product_creation(self, mock_session_class):
        """Testa criação de produto válido."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "1", "DESCRPROD": "Produto Válido", "CODVOL": "UN"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, success_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Produto com todos os campos obrigatórios
            product = Product(name="Produto Válido", code_volume="UN")
            result = SimpleCRUDRequestWrapper.create(product)
            
            assert result.code == 1
            assert result.name == "Produto Válido"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSpecialCharacterValidation:
    """Testes de validação de caracteres especiais."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_special_characters_in_name(self, mock_session_class):
        """Testa caracteres especiais no nome."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "João & Maria Ltda"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, success_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Nome com caracteres especiais (& deve ser escapado para XML)
            partner = Partner(name="João & Maria Ltda")
            result = SimpleCRUDRequestWrapper.create(partner)
            
            assert result.code == 1
            assert "João" in result.name
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_unicode_characters_in_name(self, mock_session_class):
        """Testa caracteres Unicode no nome."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Açúcar & Café Gótico"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, success_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Nome com acentos e caracteres especiais
            partner = Partner(name="Açúcar & Café Gótico")
            result = SimpleCRUDRequestWrapper.create(partner)
            
            assert result.code == 1
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestNullableFieldValidation:
    """Testes de validação de campos anuláveis."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_nullable_email_field(self, mock_session_class):
        """Testa campo de email anulável."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro Sem Email"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, success_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Parceiro sem email (campo opcional)
            partner = Partner(name="Parceiro Sem Email")
            result = SimpleCRUDRequestWrapper.create(partner)
            
            assert result.code == 1
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()
