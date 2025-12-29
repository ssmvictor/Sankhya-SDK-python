# -*- coding: utf-8 -*-
"""
Unit tests for SankhyaContext class with multi-session management.
"""

import threading
import uuid
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_environment import ServiceEnvironment
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse


@pytest.fixture(autouse=True)
def clear_wrappers():
    """Clear the global wrappers dictionary before and after each test."""
    with SankhyaContext._wrappers_lock:
        SankhyaContext._wrappers.clear()
    yield
    with SankhyaContext._wrappers_lock:
        SankhyaContext._wrappers.clear()


@pytest.fixture
def mock_wrapper():
    """Create a mock SankhyaWrapper with all necessary attributes."""
    wrapper = MagicMock(spec=SankhyaWrapper)
    wrapper._environment = ServiceEnvironment.PRODUCTION
    wrapper._database_name = "SANKHYA_PRODUCAO"
    wrapper._user_code = 123
    wrapper._host = "http://example.com"
    wrapper._port = 8180
    wrapper._session_info = MagicMock()
    wrapper._session_info.username = "test_user"
    wrapper._session_info.password = "test_pass"
    return wrapper


class TestSankhyaContextInit:
    """Tests for SankhyaContext initialization."""

    def test_init_with_wrapper(self, mock_wrapper):
        """Test context initialization with wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.wrapper is mock_wrapper
        assert isinstance(ctx.token, uuid.UUID)

    def test_init_with_wrapper_registers_in_dict(self, mock_wrapper):
        """Test that init registers wrapper in global dictionary."""
        ctx = SankhyaContext(mock_wrapper)
        
        with SankhyaContext._wrappers_lock:
            assert ctx.token in SankhyaContext._wrappers
            assert SankhyaContext._wrappers[ctx.token] is mock_wrapper

    def test_init_with_params_creates_wrapper(self):
        """Test initialization with host/port/username/password."""
        with patch.object(SankhyaWrapper, '__init__', return_value=None) as mock_init:
            with patch.object(SankhyaWrapper, 'authenticate') as mock_auth:
                # Need to set attributes the context expects
                mock_instance = MagicMock()
                mock_instance._environment = ServiceEnvironment.PRODUCTION
                mock_instance._database_name = "test"
                
                with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=mock_instance):
                    ctx = SankhyaContext(
                        host="http://test.com",
                        port=8180,
                        username="user",
                        password="pass"
                    )
                    assert ctx._host == "http://test.com"
                    assert ctx._port == 8180

    def test_init_without_params_raises_error(self):
        """Test that init without wrapper or params raises ValueError."""
        with pytest.raises(ValueError, match="requer um wrapper ou parâmetros"):
            SankhyaContext()


class TestSankhyaContextProperties:
    """Tests for SankhyaContext properties."""

    def test_token_property_returns_uuid(self, mock_wrapper):
        """Test that token property returns UUID."""
        ctx = SankhyaContext(mock_wrapper)
        assert isinstance(ctx.token, uuid.UUID)

    def test_wrapper_property_returns_wrapper(self, mock_wrapper):
        """Test that wrapper property returns the wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.wrapper is mock_wrapper

    def test_user_name_property(self, mock_wrapper):
        """Test user_name property returns username from session."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.user_name == "test_user"

    def test_user_code_property(self, mock_wrapper):
        """Test user_code property returns user code."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.user_code == 123

    def test_environment_property(self, mock_wrapper):
        """Test environment property returns environment."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.environment == ServiceEnvironment.PRODUCTION

    def test_database_name_property(self, mock_wrapper):
        """Test database_name property returns database name."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.database_name == "SANKHYA_PRODUCAO"


class TestSankhyaContextSessionManagement:
    """Tests for session management methods."""

    def test_acquire_new_session_creates_token(self, mock_wrapper):
        """Test that acquire_new_session creates and returns a token."""
        ctx = SankhyaContext(mock_wrapper)
        
        with patch.object(SankhyaWrapper, '__init__', return_value=None):
            with patch.object(SankhyaWrapper, 'authenticate'):
                new_wrapper = MagicMock()
                with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
                    token = ctx.acquire_new_session()
        
        assert isinstance(token, uuid.UUID)
        assert token != ctx.token

    def test_acquire_new_session_stores_wrapper(self, mock_wrapper):
        """Test that acquire_new_session stores wrapper in dict."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            token = ctx.acquire_new_session()
        
        with SankhyaContext._wrappers_lock:
            assert token in SankhyaContext._wrappers
            assert SankhyaContext._wrappers[token] is new_wrapper

    def test_acquire_new_session_tracks_on_demand(self, mock_wrapper):
        """Test that ON_DEMAND_CRUD is tracked in _on_demand_tokens."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            token = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
        
        assert token in ctx._on_demand_tokens

    def test_acquire_new_session_raises_when_disposed(self, mock_wrapper):
        """Test that acquire_new_session raises when disposed."""
        ctx = SankhyaContext(mock_wrapper)
        ctx.dispose()
        
        with pytest.raises(RuntimeError, match="já foi descartado"):
            ctx.acquire_new_session()

    def test_finalize_session_removes_wrapper(self, mock_wrapper):
        """Test that finalize_session removes wrapper from dict."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            token = ctx.acquire_new_session()
        
        ctx.finalize_session(token)
        
        with SankhyaContext._wrappers_lock:
            assert token not in SankhyaContext._wrappers

    def test_finalize_session_calls_dispose(self, mock_wrapper):
        """Test that finalize_session calls dispose on wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            token = ctx.acquire_new_session()
        
        ctx.finalize_session(token)
        new_wrapper.dispose.assert_called_once()

    def test_finalize_session_ignores_main_token(self, mock_wrapper):
        """Test that finalize_session ignores main session token."""
        ctx = SankhyaContext(mock_wrapper)
        main_token = ctx.token
        
        ctx.finalize_session(main_token)
        
        # Main wrapper should still be in dict
        with SankhyaContext._wrappers_lock:
            assert main_token in SankhyaContext._wrappers
        
        mock_wrapper.dispose.assert_not_called()

    def test_finalize_session_removes_from_on_demand(self, mock_wrapper):
        """Test that finalize_session removes from on_demand_tokens."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            token = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
        
        assert token in ctx._on_demand_tokens
        
        ctx.finalize_session(token)
        
        assert token not in ctx._on_demand_tokens

    def test_detach_on_demand_wrapper(self, mock_wrapper):
        """Test detach_on_demand_request_wrapper calls finalize."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            token = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
        
        ctx.detach_on_demand_request_wrapper(token)
        
        assert token not in ctx._on_demand_tokens
        new_wrapper.dispose.assert_called_once()


class TestSankhyaContextStaticMethods:
    """Tests for static methods with token."""

    def test_get_wrapper_returns_wrapper(self, mock_wrapper):
        """Test _get_wrapper returns registered wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        
        result = SankhyaContext._get_wrapper(ctx.token)
        assert result is mock_wrapper

    def test_get_wrapper_returns_none_for_invalid_token(self):
        """Test _get_wrapper returns None for invalid token."""
        result = SankhyaContext._get_wrapper(uuid.uuid4())
        assert result is None

    def test_service_invoker_with_token(self, mock_wrapper):
        """Test service_invoker_with_token delegates to wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        mock_request = MagicMock(spec=ServiceRequest)
        mock_response = MagicMock(spec=ServiceResponse)
        mock_wrapper.service_invoker.return_value = mock_response
        
        result = SankhyaContext.service_invoker_with_token(mock_request, ctx.token)
        
        assert result is mock_response
        mock_wrapper.service_invoker.assert_called_once_with(mock_request)

    def test_service_invoker_with_invalid_token_raises(self):
        """Test service_invoker_with_token raises for invalid token."""
        mock_request = MagicMock(spec=ServiceRequest)
        
        with pytest.raises(ValueError, match="Wrapper não encontrado"):
            SankhyaContext.service_invoker_with_token(mock_request, uuid.uuid4())

    def test_service_invoker_with_none_request_raises(self, mock_wrapper):
        """Test service_invoker_with_token raises for None request."""
        ctx = SankhyaContext(mock_wrapper)
        
        with pytest.raises(ValueError, match="request não pode ser None"):
            SankhyaContext.service_invoker_with_token(None, ctx.token)

    def test_get_file_with_token(self, mock_wrapper):
        """Test get_file_with_token delegates to wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        mock_file = MagicMock()
        mock_wrapper.get_file.return_value = mock_file
        
        result = SankhyaContext.get_file_with_token("key123", ctx.token)
        
        assert result is mock_file
        mock_wrapper.get_file.assert_called_once_with("key123")

    def test_get_image_with_token(self, mock_wrapper):
        """Test get_image_with_token delegates to wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        mock_file = MagicMock()
        mock_wrapper.get_image.return_value = mock_file
        
        result = SankhyaContext.get_image_with_token("Parceiro", {"CODPARC": 1}, ctx.token)
        
        assert result is mock_file
        mock_wrapper.get_image.assert_called_once_with("Parceiro", {"CODPARC": 1})


class TestSankhyaContextInstanceMethods:
    """Tests for instance service/file methods."""

    def test_service_invoker_delegates_to_wrapper(self, mock_wrapper):
        """Test service_invoker delegates to wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        mock_request = MagicMock(spec=ServiceRequest)
        mock_response = MagicMock(spec=ServiceResponse)
        mock_wrapper.service_invoker.return_value = mock_response
        
        result = ctx.service_invoker(mock_request)
        
        assert result is mock_response
        mock_wrapper.service_invoker.assert_called_once_with(mock_request)

    def test_service_invoker_raises_when_disposed(self, mock_wrapper):
        """Test service_invoker raises when disposed."""
        ctx = SankhyaContext(mock_wrapper)
        ctx.dispose()
        
        with pytest.raises(RuntimeError, match="já foi descartado"):
            ctx.service_invoker(MagicMock())

    def test_service_invoker_raises_for_none_request(self, mock_wrapper):
        """Test service_invoker raises for None request."""
        ctx = SankhyaContext(mock_wrapper)
        
        with pytest.raises(ValueError, match="request não pode ser None"):
            ctx.service_invoker(None)

    def test_get_file_delegates_to_wrapper(self, mock_wrapper):
        """Test get_file delegates to wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        mock_file = MagicMock()
        mock_wrapper.get_file.return_value = mock_file
        
        result = ctx.get_file("key123")
        
        assert result is mock_file
        mock_wrapper.get_file.assert_called_once_with("key123")

    def test_get_image_delegates_to_wrapper(self, mock_wrapper):
        """Test get_image delegates to wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        mock_file = MagicMock()
        mock_wrapper.get_image.return_value = mock_file
        
        result = ctx.get_image("Parceiro", {"CODPARC": 1})
        
        assert result is mock_file
        mock_wrapper.get_image.assert_called_once_with("Parceiro", {"CODPARC": 1})


class TestSankhyaContextLifecycle:
    """Tests for lifecycle management."""

    def test_dispose_finalizes_all_sessions(self, mock_wrapper):
        """Test dispose finalizes all on-demand sessions."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrappers = []
        for _ in range(3):
            new_wrapper = MagicMock()
            new_wrappers.append(new_wrapper)
            with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
                ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
        
        ctx.dispose()
        
        # All on-demand wrappers should be disposed
        for w in new_wrappers:
            w.dispose.assert_called_once()
        
        # Main wrapper should be disposed
        mock_wrapper.dispose.assert_called_once()

    def test_dispose_is_idempotent(self, mock_wrapper):
        """Test that multiple dispose calls don't cause errors."""
        ctx = SankhyaContext(mock_wrapper)
        
        ctx.dispose()
        ctx.dispose()  # Should not raise
        ctx.dispose()  # Should not raise
        
        # Dispose should only be called once
        mock_wrapper.dispose.assert_called_once()

    def test_dispose_clears_on_demand_tokens(self, mock_wrapper):
        """Test dispose clears on_demand_tokens set."""
        ctx = SankhyaContext(mock_wrapper)
        
        new_wrapper = MagicMock()
        with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
            ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
        
        assert len(ctx._on_demand_tokens) == 1
        
        ctx.dispose()
        
        assert len(ctx._on_demand_tokens) == 0

    def test_dispose_removes_from_global_dict(self, mock_wrapper):
        """Test dispose removes main token from global dict."""
        ctx = SankhyaContext(mock_wrapper)
        main_token = ctx.token
        
        ctx.dispose()
        
        with SankhyaContext._wrappers_lock:
            assert main_token not in SankhyaContext._wrappers

    def test_del_calls_dispose(self, mock_wrapper):
        """Test __del__ calls dispose if not already disposed."""
        ctx = SankhyaContext(mock_wrapper)
        ctx.__del__()
        
        mock_wrapper.dispose.assert_called_once()
        assert ctx._disposed is True


class TestSankhyaContextManager:
    """Tests for context manager protocol."""

    def test_enter_returns_wrapper(self, mock_wrapper):
        """Test that __enter__ returns the wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        result = ctx.__enter__()
        assert result is mock_wrapper

    def test_exit_calls_dispose(self, mock_wrapper):
        """Test that __exit__ calls dispose."""
        ctx = SankhyaContext(mock_wrapper)
        ctx.__exit__(None, None, None)
        
        mock_wrapper.dispose.assert_called_once()
        assert ctx._disposed is True

    def test_exit_calls_dispose_on_exception(self, mock_wrapper):
        """Test that __exit__ calls dispose even on exception."""
        ctx = SankhyaContext(mock_wrapper)
        ctx.__exit__(ValueError, ValueError("test"), None)
        
        mock_wrapper.dispose.assert_called_once()

    def test_with_statement_usage(self, mock_wrapper):
        """Test context manager with 'with' statement."""
        ctx = SankhyaContext(mock_wrapper)
        
        with ctx as wrapper:
            assert wrapper is mock_wrapper
        
        mock_wrapper.dispose.assert_called_once()

    def test_with_statement_exception_cleanup(self, mock_wrapper):
        """Test cleanup happens on exception in 'with' block."""
        ctx = SankhyaContext(mock_wrapper)
        
        with pytest.raises(RuntimeError):
            with ctx as wrapper:
                raise RuntimeError("Test exception")
        
        mock_wrapper.dispose.assert_called_once()


class TestSankhyaContextAsync:
    """Tests for async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_enter_returns_wrapper(self, mock_wrapper):
        """Test that __aenter__ returns the wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        result = await ctx.__aenter__()
        assert result is mock_wrapper

    @pytest.mark.asyncio
    async def test_async_exit_calls_dispose(self, mock_wrapper):
        """Test that __aexit__ calls dispose on wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        await ctx.__aexit__(None, None, None)
        
        mock_wrapper.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_with_statement_usage(self, mock_wrapper):
        """Test async context manager with 'async with' statement."""
        ctx = SankhyaContext(mock_wrapper)
        
        async with ctx as wrapper:
            assert wrapper is mock_wrapper
        
        mock_wrapper.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_service_invoker(self, mock_wrapper):
        """Test async service_invoker_async."""
        import asyncio
        ctx = SankhyaContext(mock_wrapper)
        mock_request = MagicMock(spec=ServiceRequest)
        mock_response = MagicMock(spec=ServiceResponse)
        
        # Create async mock
        async def async_invoker(req):
            return mock_response
        
        mock_wrapper.service_invoker_async = async_invoker
        
        result = await ctx.service_invoker_async(mock_request)
        assert result is mock_response


class TestSankhyaContextFromSettings:
    """Tests for from_settings factory method."""

    @patch.object(SankhyaWrapper, "from_settings")
    def test_from_settings_creates_wrapper(self, mock_from_settings, mock_wrapper):
        """Test that from_settings creates a wrapper."""
        mock_from_settings.return_value = mock_wrapper
        
        ctx = SankhyaContext.from_settings()
        
        mock_from_settings.assert_called_once_with(None)
        assert ctx.wrapper is mock_wrapper

    @patch.object(SankhyaWrapper, "from_settings")
    def test_from_settings_with_custom_settings(self, mock_from_settings, mock_wrapper):
        """Test from_settings with custom settings."""
        mock_from_settings.return_value = mock_wrapper
        mock_settings = MagicMock()
        
        ctx = SankhyaContext.from_settings(mock_settings)
        
        mock_from_settings.assert_called_once_with(mock_settings)
        assert ctx.wrapper is mock_wrapper

    @patch.object(SankhyaWrapper, "from_settings")
    def test_from_settings_with_context_manager(self, mock_from_settings, mock_wrapper):
        """Test from_settings used as context manager."""
        mock_from_settings.return_value = mock_wrapper
        
        with SankhyaContext.from_settings() as wrapper:
            assert wrapper is mock_wrapper
        
        mock_wrapper.dispose.assert_called_once()


class TestSankhyaContextThreadSafety:
    """Tests for thread-safety."""

    def test_concurrent_acquire_sessions(self, mock_wrapper):
        """Test multiple threads acquiring sessions simultaneously."""
        ctx = SankhyaContext(mock_wrapper)
        tokens = []
        errors = []
        
        def acquire_session():
            try:
                new_wrapper = MagicMock()
                with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
                    token = ctx.acquire_new_session()
                    tokens.append(token)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=acquire_session) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(tokens) == 10
        assert len(set(tokens)) == 10  # All unique

    def test_concurrent_finalize_sessions(self, mock_wrapper):
        """Test multiple threads finalizing sessions simultaneously."""
        ctx = SankhyaContext(mock_wrapper)
        tokens = []
        errors = []
        
        # Create sessions first
        for _ in range(10):
            new_wrapper = MagicMock()
            with patch('sankhya_sdk.core.context.SankhyaWrapper', return_value=new_wrapper):
                tokens.append(ctx.acquire_new_session())
        
        def finalize_session(token):
            try:
                ctx.finalize_session(token)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=finalize_session, args=(t,)) for t in tokens]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0

    def test_concurrent_service_invocations(self, mock_wrapper):
        """Test multiple threads invoking services simultaneously."""
        ctx = SankhyaContext(mock_wrapper)
        mock_response = MagicMock(spec=ServiceResponse)
        mock_wrapper.service_invoker.return_value = mock_response
        
        results = []
        errors = []
        
        def invoke_service():
            try:
                request = MagicMock(spec=ServiceRequest)
                response = SankhyaContext.service_invoker_with_token(request, ctx.token)
                results.append(response)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=invoke_service) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(results) == 10


class TestSankhyaContextBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_backward_compatibility_with_wrapper(self, mock_wrapper):
        """Test that old usage pattern still works."""
        # Old pattern: pass wrapper directly
        ctx = SankhyaContext(mock_wrapper)
        
        with ctx as wrapper:
            assert wrapper is mock_wrapper
        
        mock_wrapper.dispose.assert_called_once()

    @patch.object(SankhyaWrapper, "from_settings")
    def test_from_settings_still_works(self, mock_from_settings, mock_wrapper):
        """Test from_settings factory method unchanged."""
        mock_from_settings.return_value = mock_wrapper
        
        with SankhyaContext.from_settings() as wrapper:
            assert wrapper is mock_wrapper
        
        mock_wrapper.dispose.assert_called_once()

    def test_wrapper_property_still_exists(self, mock_wrapper):
        """Test wrapper property returns main wrapper."""
        ctx = SankhyaContext(mock_wrapper)
        assert ctx.wrapper is mock_wrapper


class TestSankhyaContextRepr:
    """Tests for __repr__ method."""

    def test_repr_contains_info(self, mock_wrapper):
        """Test that repr contains relevant information."""
        ctx = SankhyaContext(mock_wrapper)
        rep = repr(ctx)
        
        assert "SankhyaContext" in rep
        assert "token=" in rep
        assert "user_code=" in rep
        assert "disposed=" in rep
