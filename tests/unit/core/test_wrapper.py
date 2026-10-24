# -*- coding: utf-8 -*-
"""
Unit tests for the SankhyaWrapper and related components.
"""

from unittest.mock import MagicMock, Mock, call, patch
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
    ServiceRequestCanceledQueryException,
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestFileNotFoundException,
    ServiceRequestInaccessibleException,
    ServiceRequestInvalidAuthorizationException,
    ServiceRequestPropertyValueException,
    ServiceRequestTimeoutException,
    ServiceRequestUnavailableException,
)
from sankhya_sdk.models.service.basic_types import Field
from sankhya_sdk.models.service.entity_types import Entity
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.request_helpers import RequestRetryData, RequestRetryDelay


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
            <statusMessage>Usuário/Senha inválido</statusMessage>
        </serviceResponse>""".encode("utf-8")
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        from sankhya_sdk.exceptions import ServiceRequestInvalidCredentialsException
        with pytest.raises(ServiceRequestInvalidCredentialsException):
            wrapper.authenticate("baduser", "badpass")

    @patch.object(SankhyaWrapper, "_make_request")
    def test_service_invoker_internal_unavailable_status_message(self, mock_request):
        """Status de indisponibilidade deve gerar ServiceRequestUnavailableException com a resposta."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="0">
            <statusMessage>I/O Error: Connection reset</statusMessage>
        </serviceResponse>"""
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(
            host="http://example.com",
            port=8180,
        )

        request = ServiceRequest(service=ServiceName.LOGIN)
        with pytest.raises(ServiceRequestUnavailableException) as exc_info:
            wrapper._service_invoker_internal(
                request=request,
                service_name=ServiceName.LOGIN,
                request_count=1,
            )

        assert exc_info.value.request is request
        assert isinstance(exc_info.value.response, ServiceResponse)

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
                message="Transaction was deadlocked on lock resources",
                request=None,
            ),
            service_name=ServiceName.CRUD_FIND,
            category=ServiceName.CRUD_FIND.service_category,
            request=ServiceRequest(),
            retry_data=retry_data,
        )

        assert result is True
        assert retry_data.retry_delay == RequestRetryDelay.STABLE


def _status_xml(status: int, message: str = "") -> bytes:
    """Gera o XML de uma resposta de serviço com status e mensagem."""
    status_message = f"<statusMessage>{message}</statusMessage>" if message else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<serviceResponse status="{status}">{status_message}'
        "<responseBody></responseBody></serviceResponse>"
    ).encode("utf-8")


def _http_ok(content: bytes) -> Mock:
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.content = content
    return response


class TestSankhyaWrapperRetryParity:
    """
    Paridade do retry com o .NET (SankhyaWrapper.cs, ServiceInvokerInternal,
    HandleException e HandleExceptionInternal): o atraso é zerado a cada
    tentativa, cresce linearmente (RetryCount * RequestRetryDelay.X) e uma
    requisição é tentada no máximo 1 + 3 vezes.
    """

    def setup_method(self):
        SankhyaWrapper._invalid_session_ids = []
        LockManager.clear_all()

    @staticmethod
    def _wrapper(with_session: bool = True) -> SankhyaWrapper:
        wrapper = SankhyaWrapper(host="http://example.com", port=8180)
        if with_session:
            wrapper._session_info = SessionInfo("SESSION", 1, "user", "pass")
        return wrapper

    @staticmethod
    def _release(wrapper: SankhyaWrapper) -> None:
        # Evita logout real (rede) ao descartar o wrapper no fim do teste
        wrapper._session_info = None
        wrapper.dispose()

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch.object(SankhyaWrapper, "_service_invoker_internal")
    def test_retry_delay_is_reset_between_attempts(self, mock_internal, mock_sleep):
        """Um retry sem atraso (competição) não repete o atraso do deadlock anterior."""
        expected = Mock(spec=ServiceResponse)
        mock_internal.side_effect = [
            ServiceRequestDeadlockException("deadlock", None, None),
            ServiceRequestCompetitionException(None, None),
            expected,
        ]
        wrapper = self._wrapper(with_session=False)
        try:
            response = wrapper.service_invoker(ServiceRequest(service=ServiceName.CRUD_FIND))
        finally:
            self._release(wrapper)

        assert response is expected
        assert mock_internal.call_count == 3
        assert mock_sleep.call_args_list == [call(RequestRetryDelay.STABLE)]

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch.object(SankhyaWrapper, "_make_request")
    def test_retry_delay_grows_linearly(self, mock_request, mock_sleep):
        """Atrasos de 1x, 2x e 3x o valor base, como RetryCount * RequestRetryDelay.Unstable."""
        mock_request.side_effect = [
            _http_ok(_status_xml(0, "I/O Error: Connection reset")),
            _http_ok(_status_xml(0, "I/O Error: Connection reset")),
            _http_ok(_status_xml(0, "I/O Error: Connection reset")),
            _http_ok(_status_xml(1)),
        ]
        wrapper = self._wrapper()
        try:
            response = wrapper.service_invoker(ServiceRequest(service=ServiceName.CRUD_FIND))
        finally:
            self._release(wrapper)

        assert isinstance(response, ServiceResponse)
        assert mock_request.call_count == 4
        assert mock_sleep.call_args_list == [
            call(1 * RequestRetryDelay.UNSTABLE),
            call(2 * RequestRetryDelay.UNSTABLE),
            call(3 * RequestRetryDelay.UNSTABLE),
        ]

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch.object(SankhyaWrapper, "_make_request")
    def test_max_attempts_matches_dotnet(self, mock_request, mock_sleep):
        """.NET: RetryCount > 3 interrompe na 4ª tentativa (1 tentativa + 3 retries)."""
        mock_request.side_effect = [
            _http_ok(_status_xml(0, "I/O Error: Connection reset")) for _ in range(5)
        ]
        wrapper = self._wrapper()
        try:
            with pytest.raises(ServiceRequestUnavailableException):
                wrapper.service_invoker(ServiceRequest(service=ServiceName.CRUD_FIND))
        finally:
            self._release(wrapper)

        assert mock_request.call_count == 1 + MAX_RETRY_COUNT
        assert len(mock_sleep.call_args_list) == MAX_RETRY_COUNT

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch.object(SankhyaWrapper, "_make_request")
    def test_transactional_deadlock_is_not_retried(self, mock_request, mock_sleep):
        """
        "deadlock" gera ServiceRequestDeadlockException e, em serviço transacional
        (saveRecord), não é retentado, para não duplicar a gravação
        (SankhyaWrapper.cs, HandleException).
        """
        mock_request.side_effect = [
            _http_ok(_status_xml(0, "Transaction was deadlocked on lock resources")),
            _http_ok(_status_xml(1)),
        ]
        wrapper = self._wrapper()
        try:
            with pytest.raises(ServiceRequestDeadlockException):
                wrapper.service_invoker(
                    ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
                )
        finally:
            self._release(wrapper)

        assert mock_request.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.parametrize(
        "message",
        [
            "Não foi possível gravar o registro: situação de concorrência",
            "Não foi possível gravar no log de acessos",
            "Violação da restrição PRIMARY KEY 'PK_TSIRLG'",
        ],
    )
    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch.object(SankhyaWrapper, "_make_request")
    def test_transactional_competition_is_not_retried(self, mock_request, mock_sleep, message):
        """
        Mensagens de concorrência geram ServiceRequestCompetitionException e, em
        serviço transacional, não são retentadas nem reautenticam
        (SankhyaWrapper.cs, HandleException).
        """
        mock_request.side_effect = [
            _http_ok(_status_xml(0, message)),
            _http_ok(_status_xml(1)),
        ]
        wrapper = self._wrapper()
        try:
            with patch.object(SankhyaWrapper, "authenticate") as mock_authenticate:
                with pytest.raises(ServiceRequestCompetitionException):
                    wrapper.service_invoker(
                        ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
                    )
        finally:
            self._release(wrapper)

        assert mock_request.call_count == 1
        mock_authenticate.assert_not_called()
        mock_sleep.assert_not_called()

    @pytest.mark.parametrize(
        "exception,base_delay",
        [
            (ServiceRequestDeadlockException("deadlock", None, None), RequestRetryDelay.STABLE),
            (ServiceRequestTimeoutException(ServiceName.CRUD_FIND), RequestRetryDelay.FREE),
            (ServiceRequestUnavailableException(ServiceName.CRUD_FIND), RequestRetryDelay.UNSTABLE),
            (ServiceRequestCanceledQueryException(message="A consulta foi cancelada"), RequestRetryDelay.STABLE),
        ],
    )
    def test_handler_delay_is_attempt_times_base(self, exception, base_delay):
        """Na 3ª tentativa (2 retries feitos) o atraso é 3x o valor base."""
        wrapper = self._wrapper(with_session=False)
        retry_data = RequestRetryData(lock_key="test", retry_count=2)
        try:
            result = wrapper._handle_exception_internal(
                exception=exception,
                service_name=ServiceName.CRUD_FIND,
                category=ServiceName.CRUD_FIND.service_category,
                request=ServiceRequest(),
                retry_data=retry_data,
            )
        finally:
            self._release(wrapper)

        assert result is True
        assert retry_data.retry_delay == 3 * base_delay

    def test_property_value_retry_uses_linear_delay(self):
        """Campo ausente do XML da requisição: retry com RetryCount * Stable."""
        wrapper = self._wrapper(with_session=False)
        retry_data = RequestRetryData(lock_key="test", retry_count=1)
        try:
            result = wrapper._handle_exception_internal(
                exception=ServiceRequestPropertyValueException("CODPARC", "Parceiro"),
                service_name=ServiceName.CRUD_FIND,
                category=ServiceName.CRUD_FIND.service_category,
                request=ServiceRequest(service=ServiceName.CRUD_FIND),
                retry_data=retry_data,
            )
        finally:
            self._release(wrapper)

        assert result is True
        assert retry_data.retry_delay == 2 * RequestRetryDelay.STABLE

    def test_property_value_present_in_request_is_not_retried(self):
        """.NET compara o nome do campo com o XML sem diferenciar maiúsculas."""
        wrapper = self._wrapper(with_session=False)
        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        request.request_body.entity = Entity(name="Parceiro", fields=[Field(name="codparc")])
        retry_data = RequestRetryData(lock_key="test", retry_count=0)
        try:
            result = wrapper._handle_exception_internal(
                exception=ServiceRequestPropertyValueException("CODPARC", "Parceiro"),
                service_name=ServiceName.CRUD_FIND,
                category=ServiceName.CRUD_FIND.service_category,
                request=request,
                retry_data=retry_data,
            )
        finally:
            self._release(wrapper)

        assert result is False
        assert retry_data.retry_delay == 0

    def test_inaccessible_outside_authorization_reauthenticates_without_delay(self):
        """.NET: fora da categoria Authorization apenas reautentica, sem atraso."""
        wrapper = self._wrapper()
        retry_data = RequestRetryData(lock_key="test", retry_count=0)
        try:
            with patch.object(SankhyaWrapper, "_invalidate") as mock_invalidate, \
                    patch.object(SankhyaWrapper, "authenticate") as mock_authenticate:
                result = wrapper._handle_exception_internal(
                    exception=ServiceRequestInaccessibleException("example.com", 8180),
                    service_name=ServiceName.CRUD_FIND,
                    category=ServiceName.CRUD_FIND.service_category,
                    request=ServiceRequest(),
                    retry_data=retry_data,
                )
        finally:
            self._release(wrapper)

        assert result is True
        assert retry_data.retry_delay == 0
        mock_invalidate.assert_called_once()
        mock_authenticate.assert_called_once_with("user", "pass")

    def test_inaccessible_on_authorization_uses_linear_breakdown_delay(self):
        """.NET: na categoria Authorization o atraso é RetryCount * Breakdown."""
        wrapper = self._wrapper(with_session=False)
        retry_data = RequestRetryData(lock_key="test", retry_count=1)
        try:
            result = wrapper._handle_exception_internal(
                exception=ServiceRequestInaccessibleException("example.com", 8180),
                service_name=ServiceName.LOGIN,
                category=ServiceName.LOGIN.service_category,
                request=ServiceRequest(service=ServiceName.LOGIN),
                retry_data=retry_data,
            )
        finally:
            self._release(wrapper)

        assert result is True
        assert retry_data.retry_delay == 2 * RequestRetryDelay.BREAKDOWN


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
    def test_get_file_not_found_on_server_raises_file_not_found(self, mock_request):
        """
        Página HTML com SankhyaConstants.FileNotFoundOnServer (lida como
        ISO-8859-1, como no .NET ProcessFileResponse) gera
        ServiceRequestFileNotFoundException para a chave, e não TypeError.
        """
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = (
            "<html><body>O arquivo solicitado não existe no servidor</body></html>"
        ).encode("iso-8859-1")
        mock_response.headers = {"Content-Type": "text/html;charset=ISO-8859-1"}
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(host="http://example.com", port=8180)

        with pytest.raises(ServiceRequestFileNotFoundException) as exc_info:
            wrapper.get_file("CHAVE_INVALIDA")

        assert str(exc_info.value) == (
            "Unable to load the file from path CHAVE_INVALIDA. File or directory not found."
        )

    @patch.object(SankhyaWrapper, "_make_request")
    def test_get_file_html_error_page_raises_file_not_found(self, mock_request):
        """Página HTML de erro gera ServiceRequestFileNotFoundException, e não TypeError."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Erro ao abrir o arquivo</body></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(host="http://example.com", port=8180)

        with pytest.raises(ServiceRequestFileNotFoundException) as exc_info:
            wrapper.get_file("ABC123")

        assert "ABC123" in str(exc_info.value)

    @patch.object(SankhyaWrapper, "_make_request")
    def test_get_file_html_without_error_is_returned(self, mock_request):
        """Um arquivo HTML válido é devolvido normalmente."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Relatorio</body></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_request.return_value = mock_response

        wrapper = SankhyaWrapper(host="http://example.com", port=8180)

        file = wrapper.get_file("ABC123")

        assert file.data == b"<html><body>Relatorio</body></html>"
        assert file.content_type == "text/html"

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
