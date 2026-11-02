# -*- coding: utf-8 -*-
"""
Testes unitários para SimpleCRUDRequestWrapper.

Testa operações CRUD, gerenciamento de sessão e processamento de resposta.
"""

import threading
import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

from sankhya_sdk.config import SankhyaSettings
from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.exceptions import (
    ServiceRequestTooManyResultsException,
    ServiceRequestUnexpectedResultException,
)
from sankhya_sdk.helpers.filter_expression import LiteralCriteria
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

# =============================================================================
# Test Entity
# =============================================================================


class MockEntity(EntityBase):
    """Entidade mock para testes."""

    code: int = 0
    name: str = ""
    active: str = "S"


# =============================================================================
# Respostas reais (XML do protocolo Sankhya)
# =============================================================================


# Resposta de CRUDServiceProvider com <metadata> e chaves posicionais f0..fN
PARTNER_METADATA_ENTITIES_XML = (
    '<entities total="1" totalPages="1">'
    "<metadata><fields>"
    '<field name="CODPARC"/><field name="NOMEPARC"/><field name="CGC_CPF"/>'
    '<field name="CEP"/><field name="ATIVO"/><field name="CLIENTE"/>'
    '<field name="TIPPESSOA"/>'
    "</fields></metadata>"
    "<entity><f0>123</f0><f1>Cliente</f1><f2>01234567890</f2>"
    "<f3>01001000</f3><f4>S</f4><f5>N</f5><f6>F</f6></entity>"
    "</entities>"
)


def _service_response(
    body_xml: str,
    service: str = "CRUDServiceProvider.loadRecords",
) -> ServiceResponse:
    """Desserializa uma resposta Sankhya real a partir do XML do corpo."""
    return ServiceResponse.from_xml_string(
        f'<serviceResponse serviceName="{service}" status="1" '
        'pendingPrinting="false" transactionId="TX-1">'
        f"<responseBody>{body_xml}</responseBody>"
        "</serviceResponse>"
    )


def _partner_entities_xml(*codes: int) -> str:
    """Gera <entities> com chaves nomeadas para os códigos informados."""
    rows = "".join(
        f"<entity><CODPARC>{code}</CODPARC>"
        f"<NOMEPARC>Parceiro {code}</NOMEPARC></entity>"
        for code in codes
    )
    return f'<entities total="{len(codes)}">{rows}</entities>'


def _mock_entities_xml(*entities: "MockEntity") -> str:
    """Gera <entities> com os campos de MockEntity (chaves nomeadas)."""
    rows = "".join(
        f"<entity><code>{entity.code}</code><name>{entity.name}</name>"
        f"<active>{entity.active}</active></entity>"
        for entity in entities
    )
    return f'<entities total="{len(entities)}">{rows}</entities>'


def _assert_typed_partner(partner: Partner) -> None:
    """Valida a conversão tipada de PARTNER_METADATA_ENTITIES_XML."""
    assert isinstance(partner, Partner)
    assert partner.code == 123
    assert partner.name == "Cliente"
    # Zeros à esquerda preservados (valores chegam como texto bruto)
    assert partner.document == "01234567890"
    assert partner.zip_code == "01001000"
    # S/N convertidos para bool e TIPPESSOA para enum por convert_to_type
    assert partner.is_active is True
    assert partner.is_client is False
    assert partner.fiscal_type is FiscalPersonType.INDIVIDUAL


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_wrapper():
    """Reseta o estado do wrapper antes de cada teste."""
    SimpleCRUDRequestWrapper._context = None
    SimpleCRUDRequestWrapper._session_token = None
    SimpleCRUDRequestWrapper._owns_context = False
    SimpleCRUDRequestWrapper._initialized = False
    yield
    SimpleCRUDRequestWrapper._context = None
    SimpleCRUDRequestWrapper._session_token = None
    SimpleCRUDRequestWrapper._owns_context = False
    SimpleCRUDRequestWrapper._initialized = False


@pytest.fixture
def mock_context():
    """Cria um contexto mock."""
    context = MagicMock()
    context.token = uuid.uuid4()
    context.acquire_new_session.return_value = uuid.uuid4()
    return context


@pytest.fixture
def mock_entity():
    """Cria uma entidade mock."""
    return MockEntity(code=123, name="Test Entity", active="S")


def _http_response(content: bytes, content_type: str = "text/xml;charset=UTF-8") -> requests.Response:
    """Cria uma resposta HTTP real (requests.Response) com status 200."""
    response = requests.Response()
    response.status_code = 200
    response._content = content
    response.headers["Content-Type"] = content_type
    response.encoding = "utf-8"
    return response


class _SessionHttpStub:
    """
    Simula o servidor Sankhya como ``side_effect`` de ``requests.Session.request``.

    Responde login (um JSESSIONID por login), logout e o registro de user
    agent (DWR), contando logins e logouts. Thread-safe.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.logins = 0
        self.logouts = 0

    def __call__(self, method: str, url: str, **kwargs) -> requests.Response:
        with self._lock:
            if "serviceName=MobileLoginSP.login" in url:
                self.logins += 1
                return _http_response(
                    '<serviceResponse status="1"><responseBody>'
                    f"<jsessionid>SESSION_{uuid.uuid4().hex}</jsessionid>"
                    "</responseBody></serviceResponse>".encode("utf-8")
                )
            if "serviceName=MobileLoginSP.logout" in url:
                self.logouts += 1
                return _http_response(b'<serviceResponse status="1"></serviceResponse>')
            if "DWRController" in url:
                return _http_response(b"", "text/html")
        raise AssertionError(f"Requisição inesperada: {method} {url}")


@pytest.fixture
def http_stub():
    """
    Instala o servidor simulado no transporte HTTP do SDK e configura as
    SankhyaSettings usadas por ``SankhyaContext.from_settings()``.
    """
    stub = _SessionHttpStub()
    settings = SankhyaSettings(
        SANKHYA_URL="http://test.local",
        SANKHYA_PORT=8180,
        SANKHYA_USERNAME="user",
        SANKHYA_PASSWORD="pass",
    )
    with patch("sankhya_sdk.core.low_level_wrapper.requests.Session") as session_cls, \
            patch("sankhya_sdk.config.settings", settings):
        session_cls.return_value.request.side_effect = stub
        yield stub


def _authenticated_context() -> SankhyaContext:
    """Cria um SankhyaContext real autenticado contra o servidor simulado."""
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    return SankhyaContext(wrapper=wrapper)


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInitialization:
    """Testes de inicialização do wrapper."""

    def test_initialize_with_context(self, mock_context):
        """Inicializa com contexto existente adquirindo sessão dedicada (.NET)."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        assert SimpleCRUDRequestWrapper._initialized is True
        assert SimpleCRUDRequestWrapper._context is mock_context
        mock_context.acquire_new_session.assert_called_once_with(
            ServiceRequestType.SIMPLE_CRUD
        )
        assert (
            SimpleCRUDRequestWrapper._session_token
            == mock_context.acquire_new_session.return_value
        )
        assert SimpleCRUDRequestWrapper._session_token != mock_context.token

    def test_dispose_finalizes_acquired_session(self, mock_context):
        """dispose finaliza a sessão dedicada, não a sessão principal do contexto."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        acquired_token = mock_context.acquire_new_session.return_value

        SimpleCRUDRequestWrapper.dispose()

        mock_context.finalize_session.assert_called_once_with(acquired_token)

    # SankhyaContext é importado localmente em initialize(); o patch deve
    # ser aplicado no módulo de origem (sankhya_sdk.core.context).
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_initialize_without_context(self, mock_ctx_class):
        """Inicializa criando novo contexto."""
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        mock_ctx_class.from_settings.return_value = mock_ctx

        SimpleCRUDRequestWrapper.initialize()

        assert SimpleCRUDRequestWrapper._initialized is True
        assert SimpleCRUDRequestWrapper._context is mock_ctx
        mock_ctx_class.from_settings.assert_called_once()
        mock_ctx.acquire_new_session.assert_called_once_with(
            ServiceRequestType.SIMPLE_CRUD
        )
        assert (
            SimpleCRUDRequestWrapper._session_token
            == mock_ctx.acquire_new_session.return_value
        )

    def test_initialize_already_initialized(self, mock_context):
        """Inicialização duplicada é ignorada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        SimpleCRUDRequestWrapper.initialize(mock_context)  # Segunda chamada

        # Não deve lançar exceção
        assert SimpleCRUDRequestWrapper._initialized is True

    def test_dispose(self, mock_context):
        """Libera recursos corretamente."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        SimpleCRUDRequestWrapper.dispose()

        assert SimpleCRUDRequestWrapper._initialized is False
        assert SimpleCRUDRequestWrapper._context is None
        assert SimpleCRUDRequestWrapper._session_token is None

    def test_dispose_not_initialized(self):
        """Dispose sem inicialização não falha."""
        SimpleCRUDRequestWrapper.dispose()  # Não deve lançar exceção

        assert SimpleCRUDRequestWrapper._initialized is False

    def test_ensure_initialized_raises(self):
        """Lança exceção se não inicializado."""
        with pytest.raises(RuntimeError, match="não inicializado"):
            SimpleCRUDRequestWrapper._ensure_initialized()


# =============================================================================
# Internal Context Tests (initialize() sem contexto)
# =============================================================================


class TestInternalContext:
    """
    Contexto criado pelo próprio wrapper em initialize() sem contexto.

    No .NET o contexto vem do ServiceLocator e pertence à aplicação, que o
    descarta (SimpleCRUDRequestWrapper.cs:17-21). Aqui o wrapper cria o
    contexto e é o único a referenciá-lo, então dispose() deve encerrar a
    sessão principal desse contexto sem afetar sessões de outros contextos.
    Apenas o transporte HTTP é simulado.
    """

    def test_context_manager_releases_internal_context_sessions(self, http_stub):
        """Sai do bloco with sem deixar sessões autenticadas do contexto interno."""
        with SimpleCRUDRequestWrapper():
            internal_context = SimpleCRUDRequestWrapper._context
            session_token = SimpleCRUDRequestWrapper._session_token
            # Sessão principal do contexto interno + sessão dedicada SIMPLE_CRUD
            assert http_stub.logins == 2

        assert http_stub.logouts == 2
        assert internal_context.token not in SankhyaContext._wrappers
        assert session_token not in SankhyaContext._wrappers
        assert SimpleCRUDRequestWrapper._owns_context is False

    def test_dispose_keeps_sessions_of_other_contexts(self, http_stub):
        """Encerra só o contexto interno: o contexto da aplicação segue ativo."""
        app_context = _authenticated_context()
        try:
            SimpleCRUDRequestWrapper.initialize()
            internal_context = SimpleCRUDRequestWrapper._context
            SimpleCRUDRequestWrapper.dispose()

            assert http_stub.logins == 3
            assert http_stub.logouts == 2
            assert internal_context.token not in SankhyaContext._wrappers
            assert SankhyaContext._wrappers[app_context.token] is app_context.wrapper
        finally:
            app_context.dispose()

    def test_dispose_does_not_release_provided_context(self, http_stub):
        """Com contexto informado, dispose() só finaliza a sessão dedicada."""
        context = _authenticated_context()
        try:
            SimpleCRUDRequestWrapper.initialize(context)
            SimpleCRUDRequestWrapper.dispose()

            assert http_stub.logins == 2
            assert http_stub.logouts == 1
            assert SankhyaContext._wrappers[context.token] is context.wrapper
        finally:
            context.dispose()

    def test_initialize_releases_internal_context_when_session_fails(self, http_stub):
        """Falha ao adquirir a sessão dedicada não deixa o contexto interno autenticado."""
        created: List[SankhyaContext] = []
        real_from_settings = SankhyaContext.from_settings

        def from_settings() -> SankhyaContext:
            created.append(real_from_settings())
            return created[-1]

        with patch.object(SankhyaContext, "from_settings", side_effect=from_settings), \
                patch.object(
                    SankhyaContext,
                    "acquire_new_session",
                    side_effect=RuntimeError("falha no login"),
                ):
            with pytest.raises(RuntimeError, match="falha no login"):
                SimpleCRUDRequestWrapper.initialize()

        assert len(created) == 1
        assert created[0].token not in SankhyaContext._wrappers
        assert http_stub.logins == 1
        assert http_stub.logouts == 1
        assert SimpleCRUDRequestWrapper._initialized is False
        assert SimpleCRUDRequestWrapper._context is None


# =============================================================================
# Concurrent Initialization Tests
# =============================================================================


class _OtherThreadRunsFirst:
    """
    Lock que simula outra thread executando ``action`` enquanto o chamador
    espera para entrar na seção crítica (apenas na primeira entrada).
    """

    def __init__(self, action) -> None:
        self._lock = threading.Lock()
        self._action = action
        self._raced = False

    def __enter__(self) -> "_OtherThreadRunsFirst":
        if not self._raced:
            self._raced = True
            self._action()
        self._lock.acquire()
        return self

    def __exit__(self, *exc_info) -> bool:
        self._lock.release()
        return False


class TestConcurrentInitialization:
    """
    initialize() e dispose() concorrentes.

    No .NET a sessão é adquirida uma única vez pelo inicializador estático
    da classe (SimpleCRUDRequestWrapper.cs:17-21), que o CLR executa uma vez
    e de forma thread-safe. Aqui initialize() é serializado por um lock de
    classe: chamadas concorrentes adquirem uma única sessão e nenhuma sessão
    em uso é liberada.
    """

    def test_concurrent_initialize_acquires_single_session(self, mock_context):
        """Oito threads inicializando juntas adquirem uma única sessão."""
        threads_count = 8
        start = threading.Barrier(threads_count)
        acquired: List[uuid.UUID] = []
        lock_held: List[bool] = []
        errors: List[BaseException] = []

        def acquire_new_session(request_type: ServiceRequestType) -> uuid.UUID:
            lock = getattr(SimpleCRUDRequestWrapper, "_lock", None)
            lock_held.append(lock is not None and lock.locked())
            token = uuid.uuid4()
            acquired.append(token)
            return token

        mock_context.acquire_new_session.side_effect = acquire_new_session

        def run() -> None:
            try:
                start.wait(timeout=10)
                SimpleCRUDRequestWrapper.initialize(mock_context)
            except BaseException as e:  # pragma: no cover - diagnosticado pelo assert
                errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(threads_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert not any(thread.is_alive() for thread in threads)
        assert errors == []
        assert len(acquired) == 1
        assert lock_held == [True]
        assert SimpleCRUDRequestWrapper._session_token == acquired[0]

        SimpleCRUDRequestWrapper.dispose()

        mock_context.finalize_session.assert_called_once_with(acquired[0])

    def test_initialize_rechecks_state_after_waiting_for_lock(self, mock_context):
        """
        Quem esperava o lock enquanto outra thread inicializava não adquire
        outra sessão nem libera a sessão já adquirida.
        """
        other_context = MagicMock()
        other_context.acquire_new_session.return_value = uuid.uuid4()
        lock = _OtherThreadRunsFirst(
            lambda: SimpleCRUDRequestWrapper.initialize(other_context)
        )

        with patch.object(SimpleCRUDRequestWrapper, "_lock", lock, create=True):
            SimpleCRUDRequestWrapper.initialize(mock_context)

        mock_context.acquire_new_session.assert_not_called()
        assert SimpleCRUDRequestWrapper._context is other_context
        assert (
            SimpleCRUDRequestWrapper._session_token
            == other_context.acquire_new_session.return_value
        )
        other_context.finalize_session.assert_not_called()

    def test_dispose_during_finalize_does_not_finalize_twice(self, mock_context):
        """dispose() chamado enquanto outro dispose() finaliza a sessão não a finaliza de novo."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        token = SimpleCRUDRequestWrapper._session_token
        # Outra thread chama dispose() durante o logout da sessão dedicada
        mock_context.finalize_session.side_effect = (
            lambda _token: SimpleCRUDRequestWrapper.dispose()
        )

        SimpleCRUDRequestWrapper.dispose()

        mock_context.finalize_session.assert_called_once_with(token)
        assert SimpleCRUDRequestWrapper._initialized is False


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Testes do context manager."""

    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_context_manager_sync(self, mock_ctx_class):
        """Usa como context manager síncrono."""
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        mock_ctx_class.from_settings.return_value = mock_ctx

        with SimpleCRUDRequestWrapper():
            assert SimpleCRUDRequestWrapper._initialized is True

        assert SimpleCRUDRequestWrapper._initialized is False
        mock_ctx.finalize_session.assert_called_once_with(
            mock_ctx.acquire_new_session.return_value
        )

    @pytest.mark.asyncio
    @patch("sankhya_sdk.core.context.SankhyaContext")
    async def test_context_manager_async(self, mock_ctx_class):
        """Usa como context manager assíncrono."""
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        mock_ctx_class.from_settings.return_value = mock_ctx

        async with SimpleCRUDRequestWrapper():
            assert SimpleCRUDRequestWrapper._initialized is True

        assert SimpleCRUDRequestWrapper._initialized is False
        mock_ctx.finalize_session.assert_called_once_with(
            mock_ctx.acquire_new_session.return_value
        )


# =============================================================================
# Find Operations Tests (mocking internal methods)
# =============================================================================


class TestFindOperations:
    """Testes de operações de busca."""

    def test_try_find_returns_entity(self, mock_context, mock_entity):
        """try_find retorna entidade quando encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_internal",
            return_value=mock_entity,
        ):
            entity = MockEntity(code=123)
            result = SimpleCRUDRequestWrapper.try_find(entity)

            assert result is not None
            assert result.code == 123

    def test_try_find_returns_none(self, mock_context):
        """try_find retorna None quando não encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_internal",
            return_value=None,
        ):
            entity = MockEntity(code=999)
            result = SimpleCRUDRequestWrapper.try_find(entity)

            assert result is None

    def test_find_returns_entity(self, mock_context, mock_entity):
        """find retorna entidade quando encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        # Como MustFindInternal (.NET), find monta e envia a própria
        # requisição (não passa por try_find): simula-se o transporte.
        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service",
            return_value=_service_response(_mock_entities_xml(mock_entity)),
        ):
            entity = MockEntity(code=123)
            result = SimpleCRUDRequestWrapper.find(entity)

            assert result is not None
            assert result.code == 123

    def test_find_raises_when_not_found(self, mock_context):
        """find lança exceção quando não encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service",
            return_value=response,
        ) as invoke:
            entity = MockEntity(code=999)

            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                SimpleCRUDRequestWrapper.find(entity)

        assert exc_info.value.request is invoke.call_args[0][0]
        assert exc_info.value.response is response

    def test_find_all_returns_list(self, mock_context, mock_entity):
        """find_all retorna lista de entidades."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        entities = [mock_entity, MockEntity(code=456, name="Second")]

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_find_all_internal",
            return_value=entities,
        ):
            entity = MockEntity(active="S")
            results = SimpleCRUDRequestWrapper.find_all(entity)

            assert isinstance(results, list)
            assert len(results) == 2

    def test_find_all_returns_empty_list(self, mock_context):
        """find_all retorna lista vazia quando não há resultados."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_find_all_internal",
            return_value=[],
        ):
            entity = MockEntity(active="X")
            results = SimpleCRUDRequestWrapper.find_all(entity)

            assert results == []


# =============================================================================
# Find with Criteria Tests
# =============================================================================


class TestFindWithCriteria:
    """Testes de busca com critérios literais."""

    def test_try_find_with_criteria(self, mock_context, mock_entity):
        """try_find_with_criteria retorna entidade."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_with_criteria_internal",
            return_value=mock_entity,
        ):
            criteria = LiteralCriteria.equals("code", 123)
            result = SimpleCRUDRequestWrapper.try_find_with_criteria(
                MockEntity, criteria
            )

            assert result is not None

    def test_find_with_criteria_raises_when_not_found(self, mock_context):
        """find_with_criteria lança exceção quando não encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service",
            return_value=response,
        ) as invoke:
            criteria = LiteralCriteria.equals("code", 999)

            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                SimpleCRUDRequestWrapper.find_with_criteria(MockEntity, criteria)

        assert exc_info.value.request is invoke.call_args[0][0]
        assert exc_info.value.response is response


# =============================================================================
# Update & Remove Tests
# =============================================================================


class TestUpdateAndRemove:
    """Testes de operações de atualização e remoção."""

    def test_update_returns_entity(self, mock_context, mock_entity):
        """update retorna entidade atualizada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service",
            return_value=MagicMock(),
        ), patch.object(
            SimpleCRUDRequestWrapper,
            "_process_single_response",
            return_value=mock_entity,
        ), patch(
            "sankhya_sdk.request_wrappers.simple_crud_request_wrapper."
            "ServiceRequestExtensions.resolve_with_entity"
        ):
            entity = MockEntity(code=123, name="Updated")
            result = SimpleCRUDRequestWrapper.update(entity)

            assert result is not None

    def test_remove_succeeds(self, mock_context):
        """remove executa sem exceção."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service",
            return_value=MagicMock(),
        ), patch(
            "sankhya_sdk.request_wrappers.simple_crud_request_wrapper."
            "ServiceRequestExtensions.resolve_with_entity"
        ):
            entity = MockEntity(code=123)
            SimpleCRUDRequestWrapper.remove(entity)  # Não deve lançar exceção


# =============================================================================
# Async Operations Tests
# =============================================================================


class TestAsyncOperations:
    """Testes de operações assíncronas."""

    @pytest.mark.asyncio
    async def test_try_find_async(self, mock_context, mock_entity):
        """try_find_async retorna entidade."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_internal_async",
            new_callable=AsyncMock,
            return_value=mock_entity,
        ):
            entity = MockEntity(code=123)
            result = await SimpleCRUDRequestWrapper.try_find_async(entity)

            assert result is not None

    @pytest.mark.asyncio
    async def test_find_async_raises_when_not_found(self, mock_context):
        """find_async lança exceção quando não encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service_async",
            new_callable=AsyncMock,
            return_value=response,
        ) as invoke:
            entity = MockEntity(code=999)

            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                await SimpleCRUDRequestWrapper.find_async(entity)

        assert exc_info.value.request is invoke.call_args[0][0]
        assert exc_info.value.response is response

    @pytest.mark.asyncio
    async def test_update_async(self, mock_context, mock_entity):
        """update_async retorna entidade."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service_async",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ), patch.object(
            SimpleCRUDRequestWrapper,
            "_process_single_response",
            return_value=mock_entity,
        ), patch(
            "sankhya_sdk.request_wrappers.simple_crud_request_wrapper."
            "ServiceRequestExtensions.resolve_with_entity"
        ):
            entity = MockEntity(code=123, name="Updated")
            result = await SimpleCRUDRequestWrapper.update_async(entity)

            assert result is not None

    @pytest.mark.asyncio
    async def test_remove_async(self, mock_context):
        """remove_async executa sem exceção."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        with patch.object(
            SimpleCRUDRequestWrapper,
            "_invoke_service_async",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ), patch(
            "sankhya_sdk.request_wrappers.simple_crud_request_wrapper."
            "ServiceRequestExtensions.resolve_with_entity"
        ):
            entity = MockEntity(code=123)
            await SimpleCRUDRequestWrapper.remove_async(entity)


# =============================================================================
# Response Processing Tests
# =============================================================================


class TestResponseProcessing:
    """Testes de processamento de resposta."""

    def test_extract_entities_from_entities_field(self, mock_context):
        """
        Extrai entidades de uma ServiceResponse real (ServiceResponse.Entities).

        No .NET o SimpleCrudRequestWrapper lê ``response.Entities``
        (CrudServiceEntities ou CrudServiceProviderEntities); os valores
        permanecem como texto bruto (zeros à esquerda preservados).
        """
        SimpleCRUDRequestWrapper.initialize(mock_context)

        response = _service_response(
            '<entities total="1"><entity>'
            "<CODPARC>123</CODPARC><NOMEPARC>Cliente</NOMEPARC>"
            "<CGC_CPF>01234567890</CGC_CPF>"
            "</entity></entities>"
        )

        entities = SimpleCRUDRequestWrapper._extract_entities_from_response(response)

        assert len(entities) == 1
        assert entities[0].dictionary == {
            "CODPARC": "123",
            "NOMEPARC": "Cliente",
            "CGC_CPF": "01234567890",
        }

    def test_extract_entities_renamed_by_response_metadata(self, mock_context):
        """Entidades f0..fN chegam com os nomes do <metadata> da resposta."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        response = _service_response(PARTNER_METADATA_ENTITIES_XML)

        entities = SimpleCRUDRequestWrapper._extract_entities_from_response(response)

        assert [entity.dictionary for entity in entities] == [
            {
                "CODPARC": "123",
                "NOMEPARC": "Cliente",
                "CGC_CPF": "01234567890",
                "CEP": "01001000",
                "ATIVO": "S",
                "CLIENTE": "N",
                "TIPPESSOA": "F",
            }
        ]

    def test_extract_entities_from_crud_find_entidades(self, mock_context):
        """Entidades de crud.find (<entidades>/<entidade>) também são extraídas."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        response = _service_response(
            '<entidades nome="Parceiro"><entidade>'
            "<CODPARC>7</CODPARC><NOMEPARC>Parceiro 7</NOMEPARC>"
            "</entidade></entidades>",
            service="crud.find",
        )

        entities = SimpleCRUDRequestWrapper._extract_entities_from_response(response)

        assert [entity.dictionary for entity in entities] == [
            {"CODPARC": "7", "NOMEPARC": "Parceiro 7"}
        ]

    def test_extract_entities_from_empty_response(self, mock_context):
        """Retorna lista vazia para resposta sem body."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

        response = MagicMock()
        response.response_body = None

        entities = SimpleCRUDRequestWrapper._extract_entities_from_response(response)

        assert entities == []


# =============================================================================
# End-to-end com ServiceResponse desserializada (SimpleCrudRequestWrapper.cs)
# =============================================================================


class TestParsedServiceResponse:
    """
    Operações públicas com respostas reais desserializadas do XML.

    Apenas o transporte (``SankhyaContext.service_invoker_with_token`` /
    ``service_invoker_async_with_token``) é simulado; a montagem da
    requisição, a extração das entidades e a conversão tipada são reais.
    """

    @pytest.fixture
    def session_token(self, mock_context):
        """Inicializa o wrapper e retorna o token da sessão dedicada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        return mock_context.acquire_new_session.return_value

    def test_try_find_converts_parsed_entity(self, session_token):
        """try_find converte a entidade da resposta (metadata + f0..fN)."""
        response = _service_response(PARTNER_METADATA_ENTITIES_XML)

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            result = SimpleCRUDRequestWrapper.try_find(Partner(code=123))

        _assert_typed_partner(result)
        request, token = invoker.call_args[0]
        assert request.service == ServiceName.CRUD_SERVICE_FIND
        assert token == session_token

    def test_try_find_returns_none_for_empty_entities(self, session_token):
        """Sem entidades na resposta, try_find retorna None (.NET)."""
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ):
            assert SimpleCRUDRequestWrapper.try_find(Partner(code=1)) is None

    def test_find_raises_for_empty_entities(self, session_token):
        """Sem entidades na resposta, find lança ServiceRequestUnexpectedResultException."""
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ):
            with pytest.raises(ServiceRequestUnexpectedResultException):
                SimpleCRUDRequestWrapper.find(Partner(code=1))

    def test_find_converts_named_key_entity(self, session_token):
        """find converte a entidade com chaves nomeadas."""
        response = _service_response(_partner_entities_xml(42))

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ):
            result = SimpleCRUDRequestWrapper.find(Partner(code=42))

        assert isinstance(result, Partner)
        assert result.code == 42
        assert result.name == "Parceiro 42"

    def test_find_all_converts_all_parsed_entities(self, session_token):
        """find_all converte todas as entidades da resposta."""
        response = _service_response(_partner_entities_xml(1, 2, 3))

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ):
            results = SimpleCRUDRequestWrapper.find_all(Partner())

        assert [partner.code for partner in results] == [1, 2, 3]
        assert [partner.name for partner in results] == [
            "Parceiro 1",
            "Parceiro 2",
            "Parceiro 3",
        ]

    def test_try_find_with_criteria_converts_parsed_entity(self, session_token):
        """try_find_with_criteria converte a entidade da resposta."""
        response = _service_response(PARTNER_METADATA_ENTITIES_XML)

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            result = SimpleCRUDRequestWrapper.try_find_with_criteria(
                Partner, LiteralCriteria.equals("CODPARC", 123)
            )

        _assert_typed_partner(result)
        assert invoker.call_args[0][0].service == ServiceName.CRUD_SERVICE_FIND

    def test_update_converts_saved_entity(self, session_token):
        """update (saveRecord) converte a entidade devolvida pelo servidor."""
        response = _service_response(
            PARTNER_METADATA_ENTITIES_XML,
            service="CRUDServiceProvider.saveRecord",
        )

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            result = SimpleCRUDRequestWrapper.update(
                Partner(code=123, name="Cliente")
            )

        _assert_typed_partner(result)
        assert invoker.call_args[0][0].service == ServiceName.CRUD_SERVICE_SAVE

    def test_remove_sends_remove_request(self, session_token):
        """remove invoca CRUDServiceProvider.removeRecord na sessão dedicada."""
        response = _service_response("", service="CRUDServiceProvider.removeRecord")

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            assert SimpleCRUDRequestWrapper.remove(Partner(code=123)) is None

        request, token = invoker.call_args[0]
        assert request.service == ServiceName.CRUD_SERVICE_REMOVE
        assert token == session_token

    @pytest.mark.asyncio
    async def test_try_find_async_converts_parsed_entity(self, session_token):
        """try_find_async converte a entidade da resposta."""
        response = _service_response(PARTNER_METADATA_ENTITIES_XML)

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ) as invoker:
            result = await SimpleCRUDRequestWrapper.try_find_async(Partner(code=123))

        _assert_typed_partner(result)
        request, token = invoker.call_args[0]
        assert request.service == ServiceName.CRUD_SERVICE_FIND
        assert token == session_token

    @pytest.mark.asyncio
    async def test_find_async_converts_parsed_entity(self, session_token):
        """find_async converte a entidade da resposta."""
        response = _service_response(_partner_entities_xml(5))

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ):
            result = await SimpleCRUDRequestWrapper.find_async(Partner(code=5))

        assert result.code == 5
        assert result.name == "Parceiro 5"

    @pytest.mark.asyncio
    async def test_find_async_with_criteria_converts_parsed_entity(
        self, session_token
    ):
        """find_async_with_criteria converte a entidade da resposta."""
        response = _service_response(PARTNER_METADATA_ENTITIES_XML)

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ):
            result = await SimpleCRUDRequestWrapper.find_async_with_criteria(
                Partner, LiteralCriteria.equals("CODPARC", 123)
            )

        _assert_typed_partner(result)

    @pytest.mark.asyncio
    async def test_update_async_converts_saved_entity(self, session_token):
        """update_async converte a entidade devolvida pelo servidor."""
        response = _service_response(
            PARTNER_METADATA_ENTITIES_XML,
            service="CRUDServiceProvider.saveRecord",
        )

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ) as invoker:
            result = await SimpleCRUDRequestWrapper.update_async(
                Partner(code=123, name="Cliente")
            )

        _assert_typed_partner(result)
        assert invoker.call_args[0][0].service == ServiceName.CRUD_SERVICE_SAVE


class TestParsedServiceResponseErrors:
    """
    Exceções de resultado inesperado com respostas reais.

    Como no .NET (``ServiceRequestTooManyResultsException(request, response,
    count)`` e ``ServiceRequestUnexpectedResultException(request, response)``),
    as exceções carregam a requisição enviada e a resposta recebida.
    """

    @pytest.fixture(autouse=True)
    def initialized(self, mock_context):
        """Inicializa o wrapper com o contexto simulado."""
        SimpleCRUDRequestWrapper.initialize(mock_context)

    def test_try_find_too_many_results_raises(self):
        """Mais de uma entidade em try_find lança ServiceRequestTooManyResultsException."""
        response = _service_response(_partner_entities_xml(1, 2))

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            with pytest.raises(ServiceRequestTooManyResultsException) as exc_info:
                SimpleCRUDRequestWrapper.try_find(Partner())

        assert exc_info.value.request is invoker.call_args[0][0]
        assert exc_info.value.response is response
        assert "resulted in 2 entities" in str(exc_info.value)

    def test_find_with_criteria_too_many_results_raises(self):
        """Mais de uma entidade em find_with_criteria lança TooManyResults."""
        response = _service_response(_partner_entities_xml(1, 2, 3))

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ):
            with pytest.raises(ServiceRequestTooManyResultsException) as exc_info:
                SimpleCRUDRequestWrapper.find_with_criteria(
                    Partner, LiteralCriteria.equals("ATIVO", "S")
                )

        assert exc_info.value.response is response
        assert "resulted in 3 entities" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_try_find_async_too_many_results_raises(self):
        """Mais de uma entidade em try_find_async lança TooManyResults."""
        response = _service_response(_partner_entities_xml(1, 2))

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ) as invoker:
            with pytest.raises(ServiceRequestTooManyResultsException) as exc_info:
                await SimpleCRUDRequestWrapper.try_find_async(Partner())

        assert exc_info.value.request is invoker.call_args[0][0]
        assert exc_info.value.response is response

    def test_find_not_found_raises_with_request_and_response(self):
        """
        find sem entidade lança UnexpectedResult com a requisição e a resposta.

        Como MustFindInternal (.NET, SimpleCRUDRequestWrapper.cs:135-139):
        ``throw new ServiceRequestUnexpectedResultException(request, response)``.
        """
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                SimpleCRUDRequestWrapper.find(Partner(code=1))

        request = invoker.call_args[0][0]
        assert invoker.call_count == 1
        assert exc_info.value.request is request
        assert exc_info.value.response is response
        assert request.service == ServiceName.CRUD_SERVICE_FIND
        assert "Unknown" not in str(exc_info.value)
        assert "(Parceiro)" in str(exc_info.value)

    def test_find_with_criteria_not_found_raises_with_request_and_response(self):
        """find_with_criteria sem entidade carrega a requisição e a resposta (.NET)."""
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                SimpleCRUDRequestWrapper.find_with_criteria(
                    Partner, LiteralCriteria.equals("CODPARC", 1)
                )

        assert exc_info.value.request is invoker.call_args[0][0]
        assert exc_info.value.response is response
        assert "Unknown" not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_find_async_not_found_raises_with_request_and_response(self):
        """
        find_async sem entidade carrega a requisição e a resposta.

        Como MustFindInternalAsync (.NET, SimpleCRUDRequestWrapper.cs:176-186).
        """
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ) as invoker:
            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                await SimpleCRUDRequestWrapper.find_async(Partner(code=1))

        assert invoker.call_count == 1
        assert exc_info.value.request is invoker.call_args[0][0]
        assert exc_info.value.response is response
        assert "Unknown" not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_find_async_with_criteria_not_found_raises_with_request_and_response(
        self,
    ):
        """find_async_with_criteria sem entidade carrega a requisição e a resposta."""
        response = _service_response('<entities total="0"/>')

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ) as invoker:
            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                await SimpleCRUDRequestWrapper.find_async_with_criteria(
                    Partner, LiteralCriteria.equals("CODPARC", 1)
                )

        assert exc_info.value.request is invoker.call_args[0][0]
        assert exc_info.value.response is response
        assert "Unknown" not in str(exc_info.value)

    def test_update_too_many_results_raises(self):
        """update exige exatamente uma entidade (``Entities.Single()`` no .NET)."""
        response = _service_response(
            _partner_entities_xml(1, 2),
            service="CRUDServiceProvider.saveRecord",
        )

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            with pytest.raises(ServiceRequestTooManyResultsException) as exc_info:
                SimpleCRUDRequestWrapper.update(Partner(code=1))

        assert exc_info.value.request is invoker.call_args[0][0]
        assert exc_info.value.response is response

    def test_update_without_entities_raises_with_request_and_response(self):
        """update sem entidade lança UnexpectedResult com requisição e resposta."""
        response = _service_response(
            "", service="CRUDServiceProvider.saveRecord"
        )

        with patch.object(
            SankhyaContext, "service_invoker_with_token", return_value=response
        ) as invoker:
            with pytest.raises(ServiceRequestUnexpectedResultException) as exc_info:
                SimpleCRUDRequestWrapper.update(Partner(code=1))

        request = invoker.call_args[0][0]
        assert exc_info.value.request is request
        assert exc_info.value.response is response
        assert request.service == ServiceName.CRUD_SERVICE_SAVE

    @pytest.mark.asyncio
    async def test_update_async_too_many_results_raises(self):
        """update_async também exige exatamente uma entidade."""
        response = _service_response(
            _partner_entities_xml(1, 2),
            service="CRUDServiceProvider.saveRecord",
        )

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            return_value=response,
        ):
            with pytest.raises(ServiceRequestTooManyResultsException):
                await SimpleCRUDRequestWrapper.update_async(Partner(code=1))


# =============================================================================
# LiteralCriteria Tests
# =============================================================================


class TestLiteralCriteria:
    """Testes básicos para LiteralCriteria."""

    def test_equals_int(self):
        """equals com inteiro."""
        criteria = LiteralCriteria.equals("CODPARC", 123)
        assert criteria.build_expression() == "CODPARC = 123"

    def test_equals_string(self):
        """equals com string."""
        criteria = LiteralCriteria.equals("NOME", "Test")
        assert criteria.build_expression() == "NOME = 'Test'"

    def test_and_combinator(self):
        """Combinador AND."""
        c1 = LiteralCriteria.equals("A", 1)
        c2 = LiteralCriteria.equals("B", 2)
        result = c1.and_(c2)
        assert "AND" in result.build_expression()

    def test_or_combinator(self):
        """Combinador OR."""
        c1 = LiteralCriteria.equals("A", 1)
        c2 = LiteralCriteria.equals("B", 2)
        result = c1.or_(c2)
        assert "OR" in result.build_expression()

    def test_like(self):
        """Operador LIKE."""
        criteria = LiteralCriteria.like("NOME", "%TEST%")
        assert "LIKE" in criteria.build_expression()

    def test_in(self):
        """Operador IN."""
        criteria = LiteralCriteria.in_("ID", [1, 2, 3])
        assert "IN" in criteria.build_expression()
