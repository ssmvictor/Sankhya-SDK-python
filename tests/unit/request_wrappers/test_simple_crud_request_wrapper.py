# -*- coding: utf-8 -*-
"""
Testes unitários para SimpleCRUDRequestWrapper.

Testa operações CRUD, gerenciamento de sessão e processamento de resposta.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sankhya_sdk.core.context import SankhyaContext
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
    SimpleCRUDRequestWrapper._initialized = False
    yield
    SimpleCRUDRequestWrapper._context = None
    SimpleCRUDRequestWrapper._session_token = None
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
        
        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_internal",
            return_value=mock_entity,
        ):
            entity = MockEntity(code=123)
            result = SimpleCRUDRequestWrapper.find(entity)
            
            assert result is not None
    
    def test_find_raises_when_not_found(self, mock_context):
        """find lança exceção quando não encontrada."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        
        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_internal",
            return_value=None,
        ):
            entity = MockEntity(code=999)
            
            with pytest.raises(ServiceRequestUnexpectedResultException):
                SimpleCRUDRequestWrapper.find(entity)
    
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
        
        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_with_criteria_internal",
            return_value=None,
        ):
            criteria = LiteralCriteria.equals("code", 999)
            
            with pytest.raises(ServiceRequestUnexpectedResultException):
                SimpleCRUDRequestWrapper.find_with_criteria(MockEntity, criteria)


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
        
        with patch.object(
            SimpleCRUDRequestWrapper,
            "_can_find_internal_async",
            new_callable=AsyncMock,
            return_value=None,
        ):
            entity = MockEntity(code=999)
            
            with pytest.raises(ServiceRequestUnexpectedResultException):
                await SimpleCRUDRequestWrapper.find_async(entity)
    
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
