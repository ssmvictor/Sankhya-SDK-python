# -*- coding: utf-8 -*-
"""
Testes de integração para validação de entidades.

Testa validação de campos, tipos de dados e regras de negócio.

Criação usa ``SimpleCRUDRequestWrapper.update``, que invoca
``CRUDServiceProvider.saveRecord`` (Create/Update), como no SDK .NET.

O SimpleCRUDRequestWrapper usa uma sessão dedicada (novo login), como
``Context.AcquireNewSession(SimpleCrud)`` no .NET; o ``FakeSankhyaServer``
responde login/logout/DWR e entrega a resposta de validação apenas à
chamada de serviço, registrando o XML enviado.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple
from unittest.mock import patch

import pytest

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    FakeSankhyaServer,
    create_error_response,
    create_success_response,
    http_response,
    save_data_row,
    simple_crud_session,
)


SAVE = ServiceName.CRUD_SERVICE_SAVE
REMOVE = ServiceName.CRUD_SERVICE_REMOVE


def _install(mock_session_class, server: FakeSankhyaServer) -> None:
    """Instala o servidor simulado no transporte HTTP do SDK."""
    mock_session_class.return_value.request.side_effect = server


def _assert_save_rejected(
    mock_session_class,
    entity: EntityBase,
    error_code: str,
    message: str,
) -> SankhyaException:
    """
    Envia ``entity`` via saveRecord com o servidor rejeitando a gravação.

    A mensagem de erro do servidor deve chegar ao chamador como
    SankhyaException, sem nova tentativa (mensagem sem tratamento
    específico no StatusMessageHelper).
    """
    server = FakeSankhyaServer([
        http_response(200, create_error_response(error_code, message)),
    ])
    _install(mock_session_class, server)

    with simple_crud_session():
        with pytest.raises(SankhyaException) as exc_info:
            SimpleCRUDRequestWrapper.update(entity)

    assert message in str(exc_info.value)
    assert server.calls_to(SAVE) == 1
    return exc_info.value


def _save_accepted(
    mock_session_class,
    entity: EntityBase,
    response_row: Dict[str, Any],
) -> Tuple[EntityBase, str]:
    """
    Envia ``entity`` via saveRecord com o servidor aceitando a gravação.

    Returns:
        Tupla (entidade devolvida, corpo XML do saveRecord enviado)
    """
    server = FakeSankhyaServer([
        http_response(200, create_success_response([response_row])),
    ])
    _install(mock_session_class, server)

    with simple_crud_session():
        result = SimpleCRUDRequestWrapper.update(entity)

    (body,) = server.bodies(SAVE)
    return result, body


@pytest.mark.integration
class TestFieldValidation:
    """Testes de validação de campos."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_required_field_name(self, mock_session_class):
        """Testa validação de campo nome obrigatório."""
        # Parceiro sem nome
        error = _assert_save_rejected(
            mock_session_class,
            Partner(),
            "VALIDATION.REQUIRED",
            "Campo NOMEPARC é obrigatório",
        )
        
        assert "NOMEPARC" in str(error) or "obrigatório" in str(error).lower()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_max_length(self, mock_session_class):
        """Testa validação de tamanho máximo."""
        # Nome muito longo
        _assert_save_rejected(
            mock_session_class,
            Partner(name="A" * 1000),
            "VALIDATION.LENGTH",
            "Campo excede tamanho máximo",
        )


@pytest.mark.integration
class TestDataTypeValidation:
    """Testes de validação de tipos de dados."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_numeric_field(self, mock_session_class):
        """Testa validação de campo numérico."""
        # Código inválido (negativo pode ser rejeitado): o servidor (mock)
        # rejeita o valor e o erro deve ser propagado
        _assert_save_rejected(
            mock_session_class,
            Partner(code=-999, name="Teste"),
            "VALIDATION.TYPE",
            "Valor inválido para campo numérico",
        )

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_email_format(self, mock_session_class):
        """Testa validação de formato de email."""
        # Email inválido
        _assert_save_rejected(
            mock_session_class,
            Partner(name="Parceiro", email_address="email-invalido"),
            "VALIDATION.EMAIL",
            "Formato de email inválido",
        )


@pytest.mark.integration
class TestReferenceValidation:
    """Testes de validação de referências."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_invalid_city_reference(self, mock_session_class):
        """Testa validação de referência de cidade inválida."""
        # Cidade inexistente
        _assert_save_rejected(
            mock_session_class,
            Partner(name="Parceiro", code_city=999999),
            "FK_VIOLATION",
            "Cidade não encontrada",
        )

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_invalid_neighborhood_reference(self, mock_session_class):
        """Testa validação de referência de bairro inválida."""
        # Bairro inexistente
        _assert_save_rejected(
            mock_session_class,
            Partner(name="Parceiro", code_neighborhood=999999),
            "FK_VIOLATION",
            "Bairro não encontrado",
        )


@pytest.mark.integration
class TestBusinessRuleValidation:
    """Testes de validação de regras de negócio."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_active_partner_deletion(self, mock_session_class):
        """Testa validação de deleção de parceiro ativo."""
        message = "Não é possível excluir parceiro com notas fiscais pendentes"
        server = FakeSankhyaServer([
            http_response(200, create_error_response("BUSINESS.RULE", message)),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Tentar deletar parceiro com dependências
            partner = Partner(code=1)
            
            with pytest.raises(SankhyaException) as exc_info:
                SimpleCRUDRequestWrapper.remove(partner)
        
        assert message in str(exc_info.value)
        assert server.calls_to(REMOVE) == 1

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_validate_product_without_volume(self, mock_session_class):
        """Testa validação de produto sem unidade de volume."""
        # Produto sem código de volume
        _assert_save_rejected(
            mock_session_class,
            Product(name="Produto Teste"),
            "VALIDATION.REQUIRED",
            "Campo CODVOL é obrigatório",
        )


@pytest.mark.integration
class TestValidationSuccess:
    """Testes de validação bem-sucedida."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_valid_partner_creation(self, mock_session_class):
        """Testa criação de parceiro válido."""
        # Parceiro com todos os campos válidos
        result, body = _save_accepted(
            mock_session_class,
            Partner(name="Parceiro Válido", email_address="valid@email.com"),
            {"CODPARC": "1", "NOMEPARC": "Parceiro Válido", "EMAIL": "valid@email.com"},
        )
        
        assert result.code == 1
        assert result.name == "Parceiro Válido"
        assert save_data_row(body) == (
            {}, {"NOMEPARC": "Parceiro Válido", "EMAIL": "valid@email.com"}
        )

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_valid_product_creation(self, mock_session_class):
        """Testa criação de produto válido."""
        # Produto com todos os campos obrigatórios
        result, body = _save_accepted(
            mock_session_class,
            Product(name="Produto Válido", code_volume="UN"),
            {"CODPROD": "1", "DESCRPROD": "Produto Válido", "CODVOL": "UN"},
        )
        
        assert result.code == 1
        assert result.name == "Produto Válido"
        assert save_data_row(body) == (
            {}, {"DESCRPROD": "Produto Válido", "CODVOL": "UN"}
        )


@pytest.mark.integration
class TestSpecialCharacterValidation:
    """Testes de validação de caracteres especiais."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_special_characters_in_name(self, mock_session_class):
        """Testa caracteres especiais no nome."""
        # Nome com caracteres especiais (& deve ser escapado para XML)
        result, body = _save_accepted(
            mock_session_class,
            Partner(name="João & Maria Ltda"),
            {"CODPARC": "1", "NOMEPARC": "João & Maria Ltda"},
        )
        
        assert result.code == 1
        assert "João" in result.name
        # O XML enviado é válido e o valor chega intacto ao servidor
        assert "João &amp; Maria Ltda" in body
        assert save_data_row(body)[1] == {"NOMEPARC": "João & Maria Ltda"}

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_unicode_characters_in_name(self, mock_session_class):
        """Testa caracteres Unicode no nome."""
        # Nome com acentos e caracteres especiais
        result, body = _save_accepted(
            mock_session_class,
            Partner(name="Açúcar & Café Gótico"),
            {"CODPARC": "1", "NOMEPARC": "Açúcar & Café Gótico"},
        )
        
        assert result.code == 1
        assert save_data_row(body)[1] == {"NOMEPARC": "Açúcar & Café Gótico"}


@pytest.mark.integration
class TestNullableFieldValidation:
    """Testes de validação de campos anuláveis."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_nullable_email_field(self, mock_session_class):
        """Testa campo de email anulável."""
        # Parceiro sem email (campo opcional)
        result, body = _save_accepted(
            mock_session_class,
            Partner(name="Parceiro Sem Email"),
            {"CODPARC": "1", "NOMEPARC": "Parceiro Sem Email"},
        )
        
        assert result.code == 1
        # Campo não preenchido não é enviado
        assert save_data_row(body)[1] == {"NOMEPARC": "Parceiro Sem Email"}
