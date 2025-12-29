# -*- coding: utf-8 -*-
"""
Unit tests for the SankhyaWrapper and related components.
"""

from unittest.mock import MagicMock, Mock, patch
import threading
import pytest
import requests

from sankhya_sdk.core.constants import (
    DEFAULT_TIMEOUT,
    MAX_RETRY_COUNT,
    MIME_TYPES_TO_EXTENSIONS,
    PORT_TO_ENVIRONMENT,
)
from sankhya_sdk.core.lock_manager import LockManager
from sankhya_sdk.core.low_level_wrapper import LowLevelSankhyaWrapper
from sankhya_sdk.core.types import ServiceAttribute, ServiceFile, SessionInfo
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_environment import ServiceEnvironment
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.exceptions import (
    ServiceRequestDeadlockException,
    ServiceRequestInvalidAuthorizationException,
    ServiceRequestTimeoutException,
    ServiceRequestUnavailableException,
)
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.request_helpers import RequestRetryDelay


class TestConstants:
    """Tests for constants module."""

    def test_default_timeout_value(self):
        """Test DEFAULT_TIMEOUT has expected value."""
        assert DEFAULT_TIMEOUT == 30

    def test_max_retry_count_value(self):
        """Test MAX_RETRY_COUNT has expected value."""
        assert MAX_RETRY_COUNT == 3

    def test_mime_types_mapping(self):
        """Test MIME type to extension mapping."""
        assert MIME_TYPES_TO_EXTENSIONS["image/jpeg"] == "jpg"
        assert MIME_TYPES_TO_EXTENSIONS["image/png"] == "png"
        assert MIME_TYPES_TO_EXTENSIONS["application/pdf"] == "pdf"

    def test_port_to_environment_mapping(self):
        """Test port to environment mapping."""
        assert PORT_TO_ENVIRONMENT[8180] == ServiceEnvironment.PRODUCTION
        assert PORT_TO_ENVIRONMENT[8280] == ServiceEnvironment.SANDBOX
        assert PORT_TO_ENVIRONMENT[8380] == ServiceEnvironment.TRAINING


class TestSessionInfo:
    """Tests for SessionInfo dataclass."""

    def test_session_info_creation(self):
        """Test SessionInfo can be created with all fields."""
        session = SessionInfo(
            session_id="ABC123",
            user_code=42,
            username="admin",
            password="secret",
        )
        assert session.session_id == "ABC123"
        assert session.user_code == 42
        assert session.username == "admin"
        assert session.password == "secret"

    def test_session_info_equality(self):
        """Test SessionInfo equality comparison."""
        session1 = SessionInfo("ABC", 1, "user", "pass")
        session2 = SessionInfo("ABC", 1, "user", "pass")
        assert session1 == session2


class TestServiceFile:
    """Tests for ServiceFile dataclass."""

    def test_service_file_creation(self):
        """Test ServiceFile can be created with required fields."""
        file = ServiceFile(
            data=b"content",
            content_type="image/jpeg",
            file_extension="jpg",
        )
        assert file.data == b"content"
        assert file.content_type == "image/jpeg"
        assert file.file_extension == "jpg"
        assert file.filename is None

    def test_service_file_with_filename(self):
        """Test ServiceFile with optional filename."""
        file = ServiceFile(
            data=b"content",
            content_type="application/pdf",
            file_extension="pdf",
            filename="document.pdf",
        )
        assert file.filename == "document.pdf"


class TestServiceAttribute:
    """Tests for ServiceAttribute dataclass."""

    def test_service_attribute_defaults(self):
        """Test ServiceAttribute default values."""
        attr = ServiceAttribute()
        assert attr.is_transactional is False
        assert attr.is_retriable is True

    def test_service_attribute_custom(self):
        """Test ServiceAttribute with custom values."""
        attr = ServiceAttribute(is_transactional=True, is_retriable=False)
        assert attr.is_transactional is True
        assert attr.is_retriable is False


class TestLockManager:
    """Tests for LockManager class."""

    def setup_method(self):
        """Clear locks before each test."""
        LockManager.clear_all()

    def test_get_lock_creates_new_lock(self):
        """Test that get_lock creates a new lock for unknown key."""
        lock = LockManager.get_lock("test_key")
        assert lock is not None
        assert isinstance(lock, threading.Lock)

    def test_get_lock_returns_same_lock(self):
        """Test that get_lock returns the same lock for same key."""
        lock1 = LockManager.get_lock("test_key")
        lock2 = LockManager.get_lock("test_key")
        assert lock1 is lock2

    def test_different_keys_different_locks(self):
        """Test that different keys get different locks."""
        lock1 = LockManager.get_lock("key1")
        lock2 = LockManager.get_lock("key2")
        assert lock1 is not lock2

    def test_release_lock_removes_lock(self):
        """Test that release_lock removes the lock."""
        LockManager.get_lock("test_key")
        assert LockManager.count() == 1

        LockManager.release_lock("test_key")
        assert LockManager.count() == 0

    def test_release_nonexistent_lock_no_error(self):
        """Test that releasing non-existent lock doesn't raise."""
        LockManager.release_lock("nonexistent")  # Should not raise

    def test_clear_all_removes_all_locks(self):
        """Test that clear_all removes all locks."""
        LockManager.get_lock("key1")
        LockManager.get_lock("key2")
        assert LockManager.count() == 2

        LockManager.clear_all()
        assert LockManager.count() == 0

    def test_thread_safety(self):
        """Test that LockManager is thread-safe."""
        results = []
        errors = []

        def acquire_lock(key, thread_id):
            try:
                lock = LockManager.get_lock(key)
                results.append((thread_id, lock))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=acquire_lock, args=("shared_key", i))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        # All should have gotten the same lock
        locks = {r[1] for r in results}
        assert len(locks) == 1


class TestLowLevelSankhyaWrapper:
    """Tests for LowLevelSankhyaWrapper class."""

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        assert wrapper.host == "http://example.com"
        assert wrapper.port == 8180
        assert wrapper.environment == ServiceEnvironment.PRODUCTION
        assert wrapper.user_code == 0

    def test_initialization_with_sandbox_port(self):
        """Test environment detection from sandbox port."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=8280,
        )
        assert wrapper.environment == ServiceEnvironment.SANDBOX

    def test_initialization_with_training_port(self):
        """Test environment detection from training port."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=8380,
        )
        assert wrapper.environment == ServiceEnvironment.TRAINING

    def test_initialization_with_explicit_environment(self):
        """Test initialization with explicit environment."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=9999,
            environment=ServiceEnvironment.SANDBOX,
        )
        assert wrapper.environment == ServiceEnvironment.SANDBOX

    def test_normalize_host_removes_port(self):
        """Test that host normalization removes port."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com:8180",
            port=8180,
        )
        assert wrapper.host == "http://example.com"

    def test_normalize_host_adds_scheme(self):
        """Test that host normalization adds http scheme."""
        wrapper = LowLevelSankhyaWrapper(
            host="example.com",
            port=8180,
        )
        assert wrapper.host == "http://example.com"

    def test_build_service_url(self):
        """Test URL building for services."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        url = wrapper._build_service_url(ServiceName.LOGIN)
        assert "example.com:8180" in url
        assert "serviceName=MobileLoginSP.login" in url
        assert "outputType=xml" in url

    def test_build_generic_url(self):
        """Test generic URL building."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        url = wrapper._build_generic_url("/mge/test", {"key": "value"})
        assert url == "http://example.com:8180/mge/test?key=value"

    def test_base_url_property(self):
        """Test base_url property."""
        wrapper = LowLevelSankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        assert wrapper.base_url == "http://example.com:8180"


class TestSankhyaWrapper:
    """Tests for SankhyaWrapper class."""

    def setup_method(self):
        """Reset class-level state before each test."""
        SankhyaWrapper._invalid_session_ids = []
        LockManager.clear_all()

    def test_initialization(self):
        """Test wrapper initialization."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        assert wrapper.is_authenticated is False
        assert wrapper.session_id is None
        assert wrapper.request_count == 0

    def test_is_authenticated_false_initially(self):
        """Test that wrapper is not authenticated initially."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        assert wrapper.is_authenticated is False

    @patch.object(SankhyaWrapper, "_make_request")
    @patch.object(SankhyaWrapper, "_register_user_agent")
    def test_authenticate_success(self, mock_user_agent, mock_request):
        """Test successful authentication."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="1">
            <responseBody>
                <jsessionid>SESSION123</jsessionid>
                <idusu>MTI=</idusu>
            </responseBody>
        </serviceResponse>"""
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        wrapper.authenticate("testuser", "testpass")

        assert wrapper.is_authenticated is True
        assert wrapper.session_id == "SESSION123"

    @patch.object(SankhyaWrapper, "_make_request")
    def test_authenticate_failure(self, mock_request):
        """Test authentication failure."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = """<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="0">
            <statusMessage>Usuario/Senha invalido</statusMessage>
        </serviceResponse>""".encode("utf-8")
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        from sankhya_sdk.exceptions import ServiceRequestInvalidCredentialsException
        with pytest.raises(ServiceRequestInvalidCredentialsException):
            wrapper.authenticate("baduser", "badpass")

    def test_dispose_marks_as_disposed(self):
        """Test that dispose marks wrapper as disposed."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        wrapper.dispose()

        with pytest.raises(RuntimeError):
            wrapper.service_invoker(ServiceRequest())

    def test_repr(self):
        """Test string representation."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )
        rep = repr(wrapper)
        assert "SankhyaWrapper" in rep
        assert "example.com" in rep
        assert "PRODUCTION" in rep


class TestSankhyaWrapperRetryLogic:
    """Tests for SankhyaWrapper retry logic."""

    def setup_method(self):
        """Reset class-level state before each test."""
        SankhyaWrapper._invalid_session_ids = []
        LockManager.clear_all()

    def test_handle_exception_max_retries(self):
        """Test that max retries is respected."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
            max_retries=3,
        )

        from sankhya_sdk.request_helpers import RequestRetryData
        retry_data = RequestRetryData(lock_key="test", retry_count=3)

        result = wrapper._handle_exception(
            exception=ServiceRequestUnavailableException(
                service=ServiceName.CRUD_FIND,
                request=None,
                response=None,
            ),
            service_name=ServiceName.CRUD_FIND,
            service_attr=ServiceAttribute(),
            request=ServiceRequest(),
            retry_data=retry_data,
        )

        assert result is False  # Should not retry

    def test_handle_timeout_exception_sets_free_delay(self):
        """Test that timeout exception sets FREE delay."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        from sankhya_sdk.request_helpers import RequestRetryData
        retry_data = RequestRetryData(lock_key="test", retry_count=0)

        result = wrapper._handle_exception_internal(
            exception=ServiceRequestTimeoutException(
                service=ServiceName.CRUD_FIND,
                request=None,
            ),
            service_name=ServiceName.CRUD_FIND,
            category=ServiceName.CRUD_FIND.service_category,
            request=ServiceRequest(),
            retry_data=retry_data,
        )

        assert result is True
        assert retry_data.retry_delay == RequestRetryDelay.FREE

    def test_handle_unavailable_exception_sets_unstable_delay(self):
        """Test that unavailable exception sets UNSTABLE delay."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        from sankhya_sdk.request_helpers import RequestRetryData
        retry_data = RequestRetryData(lock_key="test", retry_count=0)

        result = wrapper._handle_exception_internal(
            exception=ServiceRequestUnavailableException(
                service=ServiceName.CRUD_FIND,
                request=None,
                response=None,
            ),
            service_name=ServiceName.CRUD_FIND,
            category=ServiceName.CRUD_FIND.service_category,
            request=ServiceRequest(),
            retry_data=retry_data,
        )

        assert result is True
        assert retry_data.retry_delay == RequestRetryDelay.UNSTABLE

    def test_handle_deadlock_exception_sets_stable_delay(self):
        """Test that deadlock exception sets STABLE delay."""
        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        from sankhya_sdk.request_helpers import RequestRetryData
        retry_data = RequestRetryData(lock_key="test", retry_count=0)

        result = wrapper._handle_exception_internal(
            exception=ServiceRequestDeadlockException(
                request=None,
            ),
            service_name=ServiceName.CRUD_FIND,
            category=ServiceName.CRUD_FIND.service_category,
            request=ServiceRequest(),
            retry_data=retry_data,
        )

        assert result is True
        assert retry_data.retry_delay == RequestRetryDelay.STABLE


class TestSankhyaWrapperFileOperations:
    """Tests for file and image operations."""

    def setup_method(self):
        """Reset class-level state before each test."""
        SankhyaWrapper._invalid_session_ids = []
        LockManager.clear_all()

    @patch.object(SankhyaWrapper, "_make_request")
    def test_get_file_success(self, mock_request):
        """Test successful file download."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b"file content"
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="test.pdf"',
        }
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        file = wrapper.get_file("ABC123")

        assert file.data == b"file content"
        assert file.content_type == "application/pdf"
        assert file.file_extension == "pdf"
        assert file.filename == "test.pdf"

    @patch.object(SankhyaWrapper, "_make_request")
    def test_get_image_success(self, mock_request):
        """Test successful image download."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b"image content"
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        image = wrapper.get_image("Parceiro", {"CODPARC": 1})

        assert image is not None
        assert image.data == b"image content"
        assert image.content_type == "image/jpeg"
        assert image.file_extension == "jpg"

    @patch.object(SankhyaWrapper, "_make_request")
    def test_get_image_not_found(self, mock_request):
        """Test image not found returns None."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        image = wrapper.get_image("Parceiro", {"CODPARC": 999})

        assert image is None
