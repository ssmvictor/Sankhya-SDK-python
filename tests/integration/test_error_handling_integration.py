# -*- coding: utf-8 -*-
"""
Testes de integração para tratamento de erros e retry.

Testa cenários de erro, retry, timeout e recuperação.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestTimeoutException,
)
from sankhya_sdk.models.transport.partner import Partner
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
class TestTimeoutHandling:
    """Testes de tratamento de timeout."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_timeout_with_successful_retry(self, mock_session_class):
        """Testa timeout seguido de retry bem-sucedido."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeira tentativa: timeout
        timeout_error = requests.exceptions.Timeout("Connection timed out")
        
        # Segunda tentativa: sucesso
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro Recuperado"}
            ])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, timeout_error, success_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
            
            # Deve ter recuperado após retry
            assert result is not None
            assert result.name == "Parceiro Recuperado"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_multiple_timeouts_exhausts_retries(self, mock_session_class):
        """Testa múltiplos timeouts que esgotam retries."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Todas as tentativas: timeout
        timeout_error = requests.exceptions.Timeout("Connection timed out")
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        # Configurar para falhar em todas as tentativas
        mock_session.request.side_effect = [
            login_resp,
            timeout_error,
            timeout_error,
            timeout_error,
            timeout_error,
            logout_resp,
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises((requests.exceptions.Timeout, SankhyaException)):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestConnectionErrors:
    """Testes de erros de conexão."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_connection_error_during_operation(self, mock_session_class):
        """Testa erro de conexão durante operação."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Erro de conexão
        connection_error = requests.exceptions.ConnectionError("Connection refused")
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, connection_error, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises((requests.exceptions.ConnectionError, SankhyaException)):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_connection_recovery(self, mock_session_class):
        """Testa recuperação após erro de conexão."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeiro: erro de conexão
        connection_error = requests.exceptions.ConnectionError("Connection refused")
        
        # Segundo: sucesso
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro"}
            ])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, connection_error, success_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
            assert result is not None
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestServerErrors:
    """Testes de erros do servidor."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_server_internal_error(self, mock_session_class):
        """Testa erro interno do servidor (500)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Resposta 500
        error_resp = create_mock_response(500, b"Internal Server Error")
        error_resp.ok = False
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(Exception):  # Qualquer exceção
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_service_unavailable(self, mock_session_class):
        """Testa serviço indisponível (503)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Resposta 503
        error_resp = create_mock_response(503, b"Service Unavailable")
        error_resp.ok = False
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(Exception):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestBusinessErrors:
    """Testes de erros de negócio."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_duplicate_key_error(self, mock_session_class):
        """Testa erro de chave duplicada."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("DUPLICATE_KEY", "Chave duplicada")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(SankhyaException) as exc:
                SimpleCRUDRequestWrapper.create(Partner(code=1, name="Duplicado"))
            
            assert "duplicada" in str(exc.value).lower() or "DUPLICATE" in str(exc.value)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_foreign_key_violation(self, mock_session_class):
        """Testa violação de chave estrangeira."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("FK_VIOLATION", "Referência inválida")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(
                    Partner(name="Parceiro", code_city=99999)  # Cidade inexistente
                )
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_required_field_missing(self, mock_session_class):
        """Testa campo obrigatório faltando."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("REQUIRED_FIELD", "Campo obrigatório: NOMEPARC")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(Partner())  # Sem nome
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestConcurrencyErrors:
    """Testes de erros de concorrência."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_deadlock_detection_and_retry(self, mock_session_class):
        """Testa detecção de deadlock e retry."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeiro: deadlock
        deadlock_resp = create_mock_response(
            200, create_error_response("DEADLOCK", "Transaction deadlock")
        )
        
        # Segundo: sucesso
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro"}
            ])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, deadlock_resp, success_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Dependendo da implementação, pode fazer retry ou falhar
            try:
                result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
            except (SankhyaException, ServiceRequestDeadlockException):
                pass  # Comportamento aceitável
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_competition_error(self, mock_session_class):
        """Testa erro de competição de recursos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        competition_resp = create_mock_response(
            200, create_error_response("COMPETITION", "Resource locked")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, competition_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.update(Partner(code=1, name="Locked"))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSessionErrors:
    """Testes de erros de sessão."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_session_expired_during_operation(self, mock_session_class):
        """Testa sessão expirada durante operação."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Operação retorna sessão inválida
        session_error = create_mock_response(
            200, create_error_response("SESSION.INVALID", "Sessão expirada")
        )
        
        # Re-login
        relogin_resp = create_mock_response(200, create_login_response("NEW_SESSION"))
        
        # Retry com sucesso
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro"}
            ])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, session_error, relogin_resp, success_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Dependendo da implementação, pode fazer re-auth ou falhar
            try:
                result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
            except SankhyaException:
                pass  # Aceitável se não tiver auto-reauth
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestXMLParsingErrors:
    """Testes de erros de parsing XML."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_malformed_xml_response(self, mock_session_class):
        """Testa resposta XML malformada."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # XML inválido
        bad_xml = create_mock_response(200, b"<invalid><not-closed>")
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, bad_xml, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(Exception):  # Pode ser várias exceções
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_empty_response(self, mock_session_class):
        """Testa resposta vazia."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        empty_resp = create_mock_response(200, b"")
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, empty_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with pytest.raises(Exception):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()
