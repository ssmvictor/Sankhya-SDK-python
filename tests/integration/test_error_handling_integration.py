# -*- coding: utf-8 -*-
"""
Testes de integração para tratamento de erros e retry.

Testa cenários de erro, retry, timeout e recuperação.
"""

from __future__ import annotations

import gc
from unittest.mock import MagicMock, call, patch

import pytest
import requests
from lxml import etree

from sankhya_sdk.core.constants import MAX_RETRY_COUNT
from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestCompetitionException,
)
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.request_helpers import RequestRetryDelay
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    FakeSankhyaServer,
    create_error_response,
    entities_response,
    http_response,
    simple_crud_session,
)


# Tentativas totais de uma requisição que falha sempre: 1 + retries
MAX_ATTEMPTS = 1 + MAX_RETRY_COUNT


# =============================================================================
# Testes
# =============================================================================


@pytest.mark.integration
class TestTimeoutHandling:
    """Testes de tratamento de timeout."""

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_timeout_with_successful_retry(self, mock_session_class, mock_sleep):
        """Testa timeout seguido de retry bem-sucedido."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            # Primeira tentativa: timeout
            requests.exceptions.Timeout("Connection timed out"),
            # Segunda tentativa: sucesso
            http_response(200, entities_response(
                {"CODPARC": 1, "NOMEPARC": "Parceiro Recuperado"}
            )),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        # Deve ter recuperado após retry
        assert result is not None
        assert result.code == 1
        assert result.name == "Parceiro Recuperado"
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 2

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_multiple_timeouts_exhausts_retries(self, mock_session_class, mock_sleep):
        """Testa múltiplos timeouts que esgotam retries."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Todas as tentativas: timeout
        server = FakeSankhyaServer([
            requests.exceptions.Timeout("Connection timed out")
            for _ in range(MAX_ATTEMPTS)
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises((requests.exceptions.Timeout, SankhyaException)):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == MAX_ATTEMPTS


@pytest.mark.integration
class TestConnectionErrors:
    """Testes de erros de conexão."""

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_connection_error_during_operation(self, mock_session_class, mock_sleep):
        """Testa erro de conexão durante operação."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Erro de conexão persistente (todas as tentativas)
        server = FakeSankhyaServer([
            requests.exceptions.ConnectionError("Connection refused")
            for _ in range(MAX_ATTEMPTS)
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises((requests.exceptions.ConnectionError, SankhyaException)):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == MAX_ATTEMPTS

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_connection_recovery(self, mock_session_class, mock_sleep):
        """Testa recuperação após erro de conexão."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            # Primeiro: erro de conexão
            requests.exceptions.ConnectionError("Connection refused"),
            # Segundo: sucesso
            http_response(200, entities_response(
                {"CODPARC": 1, "NOMEPARC": "Parceiro"}
            )),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert result is not None
        assert result.name == "Parceiro"
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 2


@pytest.mark.integration
class TestServerErrors:
    """Testes de erros do servidor."""

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_server_internal_error(self, mock_session_class, mock_sleep):
        """Testa erro interno do servidor (500)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Resposta 500 persistente
        server = FakeSankhyaServer([
            http_response(500, b"Internal Server Error")
            for _ in range(MAX_ATTEMPTS)
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises(
                (requests.exceptions.HTTPError, SankhyaException)
            ) as exc_info:
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        if isinstance(exc_info.value, requests.exceptions.HTTPError):
            assert exc_info.value.response.status_code == 500
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == MAX_ATTEMPTS

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_service_unavailable(self, mock_session_class, mock_sleep):
        """Testa serviço indisponível (503)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Resposta 503 persistente
        server = FakeSankhyaServer([
            http_response(503, b"Service Unavailable")
            for _ in range(MAX_ATTEMPTS)
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises(
                (requests.exceptions.HTTPError, SankhyaException)
            ) as exc_info:
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        if isinstance(exc_info.value, requests.exceptions.HTTPError):
            assert exc_info.value.response.status_code == 503
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == MAX_ATTEMPTS


@pytest.mark.integration
class TestBusinessErrors:
    """
    Testes de erros de negócio.

    A criação de registros usa ``SimpleCRUDRequestWrapper.update``
    (CRUDServiceProvider.saveRecord), como no SDK .NET: não existe
    operação ``create`` separada.
    """

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_duplicate_key_error(self, mock_session_class):
        """Testa erro de chave duplicada."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            http_response(200, create_error_response("DUPLICATE_KEY", "Chave duplicada")),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises(SankhyaException) as exc:
                SimpleCRUDRequestWrapper.update(Partner(code=1, name="Duplicado"))

        assert "duplicada" in str(exc.value).lower() or "DUPLICATE" in str(exc.value)
        # Erro de negócio não deve ser retentado
        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 1

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_foreign_key_violation(self, mock_session_class):
        """Testa violação de chave estrangeira."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            http_response(200, create_error_response("FK_VIOLATION", "Referência inválida")),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.update(
                    Partner(name="Parceiro", code_city=99999)  # Cidade inexistente
                )

        # Erro de negócio não deve ser retentado
        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 1

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_required_field_missing(self, mock_session_class):
        """Testa campo obrigatório faltando."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            http_response(200, create_error_response(
                "REQUIRED_FIELD", "Campo obrigatório: NOMEPARC"
            )),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.update(Partner())  # Sem nome

        # Erro de negócio não deve ser retentado
        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 1


@pytest.mark.integration
class TestConcurrencyErrors:
    """Testes de erros de concorrência."""

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_deadlock_detection_and_retry(self, mock_session_class, mock_sleep):
        """
        Testa detecção de deadlock e retry.

        Em serviço de consulta (não transacional) o deadlock é retentado
        após o atraso STABLE, sem reautenticar (SankhyaWrapper.cs,
        HandleExceptionInternal).
        """
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            # Primeiro: deadlock
            http_response(200, create_error_response("DEADLOCK", "Transaction deadlock")),
            # Segundo: sucesso
            http_response(200, entities_response(
                {"CODPARC": 1, "NOMEPARC": "Parceiro"}
            )),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            logins_before = server.logins
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert result is not None
        assert result.name == "Parceiro"
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 2
        assert server.logins == logins_before
        assert mock_sleep.call_args_list == [call(RequestRetryDelay.STABLE)]

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_competition_error(self, mock_session_class, mock_sleep):
        """
        Testa erro de competição de recursos.

        "situação de concorrência" identifica a competição; em serviço
        transacional (saveRecord) ela não é retentada, para não repetir
        a gravação (SankhyaWrapper.cs, HandleException).
        """
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            http_response(200, create_error_response(
                "COMPETITION",
                "Não foi possível gravar o registro: situação de concorrência",
            )),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises(ServiceRequestCompetitionException):
                SimpleCRUDRequestWrapper.update(Partner(code=1, name="Locked"))

        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 1


@pytest.mark.integration
class TestSessionErrors:
    """Testes de erros de sessão."""

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_session_expired_during_operation(self, mock_session_class, mock_sleep):
        """
        Testa sessão expirada durante operação.

        "Não autorizado" invalida a sessão: o wrapper faz logout, autentica
        novamente e repete a requisição.
        """
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            # Operação retorna sessão inválida
            http_response(200, create_error_response("SESSION.INVALID", "Não autorizado.")),
            # Retry com sucesso após o re-login
            http_response(200, entities_response(
                {"CODPARC": 1, "NOMEPARC": "Parceiro"}
            )),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            logins_before = server.logins
            logouts_before = server.logouts
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
            relogins = server.logins - logins_before
            session_logouts = server.logouts - logouts_before

        assert result is not None
        assert result.name == "Parceiro"
        assert relogins == 1
        assert session_logouts == 1
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 2


@pytest.mark.integration
class TestXMLParsingErrors:
    """Testes de erros de parsing XML."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_malformed_xml_response(self, mock_session_class):
        """Testa resposta XML malformada."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # XML inválido
        server = FakeSankhyaServer([
            http_response(200, b"<invalid><not-closed>"),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises((etree.XMLSyntaxError, SankhyaException)):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 1

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_empty_response(self, mock_session_class):
        """Testa resposta vazia."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([http_response(200, b"")])
        mock_session.request.side_effect = server

        with simple_crud_session():
            with pytest.raises((etree.XMLSyntaxError, SankhyaException)):
                SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 1


@pytest.mark.integration
class TestSharedStateIsolation:
    """
    Isolamento entre testes do estado de classe do SankhyaContext.

    Causa da intermitência de ``test_malformed_xml_response``: um
    SankhyaContext vazado por outro teste, quando finalizado pelo coletor
    cíclico, executa ``dispose()`` e remove do registro de classe as sessões
    de todos os contextos, inclusive a sessão dedicada do
    SimpleCRUDRequestWrapper do teste em execução ("Wrapper não encontrado
    para token").
    """

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_leaked_context_does_not_drop_running_test_session(self, mock_session_class):
        """Contexto vazado não derruba a sessão do teste em execução."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([
            http_response(200, entities_response({"CODPARC": 1, "NOMEPARC": "Parceiro"})),
        ])
        mock_session.request.side_effect = server

        with simple_crud_session():
            # Contexto não descartado preso num ciclo de referências, como o
            # de um teste que falhou antes do dispose (frames do traceback)
            leaked_wrapper = SankhyaWrapper(host="http://test.local", port=8180)
            leaked_wrapper.authenticate("user", "pass")
            leaked_context = SankhyaContext(wrapper=leaked_wrapper)
            leaked_context.reference_cycle = leaked_context
            del leaked_context, leaked_wrapper

            # Alocações suficientes para disparar várias coletas automáticas
            # das gerações jovens, onde está o ciclo recém-criado
            allocations = [[] for _ in range(20 * gc.get_threshold()[0])]
            del allocations

            result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

        assert result is not None
        assert result.name == "Parceiro"
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 1
