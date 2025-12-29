# -*- coding: utf-8 -*-
"""
Testes unitários para SimpleCRUDRequestWrapper.

Testa operações CRUD, gerenciamento de sessão e processamento de resposta.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sankhya_sdk.exceptions import (
    ServiceRequestTooManyResultsException,
    ServiceRequestUnexpectedResultException,
)
from sankhya_sdk.helpers.filter_expression import LiteralCriteria
from sankhya_sdk.models.base import EntityBase
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
        """Inicializa com contexto existente."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        
        assert SimpleCRUDRequestWrapper._initialized is True
        assert SimpleCRUDRequestWrapper._context is mock_context
        assert SimpleCRUDRequestWrapper._session_token == mock_context.token
    
    @patch("sankhya_sdk.request_wrappers.simple_crud_request_wrapper.SankhyaContext")
    def test_initialize_without_context(self, mock_ctx_class):
        """Inicializa criando novo contexto."""
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        mock_ctx_class.from_settings.return_value = mock_ctx
        
        SimpleCRUDRequestWrapper.initialize()
        
        assert SimpleCRUDRequestWrapper._initialized is True
        mock_ctx_class.from_settings.assert_called_once()
        mock_ctx.acquire_new_session.assert_called_once()
    
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
    
    @patch("sankhya_sdk.request_wrappers.simple_crud_request_wrapper.SankhyaContext")
    def test_context_manager_sync(self, mock_ctx_class):
        """Usa como context manager síncrono."""
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        mock_ctx_class.from_settings.return_value = mock_ctx
        
        with SimpleCRUDRequestWrapper():
            assert SimpleCRUDRequestWrapper._initialized is True
        
        assert SimpleCRUDRequestWrapper._initialized is False
    
    @pytest.mark.asyncio
    @patch("sankhya_sdk.request_wrappers.simple_crud_request_wrapper.SankhyaContext")
    async def test_context_manager_async(self, mock_ctx_class):
        """Usa como context manager assíncrono."""
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        mock_ctx_class.from_settings.return_value = mock_ctx
        
        async with SimpleCRUDRequestWrapper():
            assert SimpleCRUDRequestWrapper._initialized is True
        
        assert SimpleCRUDRequestWrapper._initialized is False


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
        """Extrai entidades do campo entities."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": 1, "name": "Test"}
        ]
        response.response_body.data_set = None
        
        entities = SimpleCRUDRequestWrapper._extract_entities_from_response(response)
        
        assert len(entities) == 1
    
    def test_extract_entities_from_empty_response(self, mock_context):
        """Retorna lista vazia para resposta sem body."""
        SimpleCRUDRequestWrapper.initialize(mock_context)
        
        response = MagicMock()
        response.response_body = None
        
        entities = SimpleCRUDRequestWrapper._extract_entities_from_response(response)
        
        assert entities == []


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
