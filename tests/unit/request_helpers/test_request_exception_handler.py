# -*- coding: utf-8 -*-
"""Unit tests for RequestExceptionHandler."""

import pytest

from sankhya_sdk.enums import ServiceName, ServiceType
from sankhya_sdk.exceptions import (
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestTimeoutException,
)
from sankhya_sdk.request_helpers import (
    IRequestExceptionHandler,
    RequestBehaviorOptions,
    RequestExceptionDetails,
    RequestExceptionHandler,
    RequestRetryData,
)


class TestIRequestExceptionHandler:
    """Tests for the IRequestExceptionHandler protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that RequestExceptionHandler implements IRequestExceptionHandler."""
        options = RequestBehaviorOptions()
        handler = RequestExceptionHandler(options)
        assert isinstance(handler, IRequestExceptionHandler)


class TestRequestExceptionHandler:
    """Tests for the RequestExceptionHandler class."""

    @pytest.fixture
    def handler(self) -> RequestExceptionHandler:
        """Create a handler with default options."""
        options = RequestBehaviorOptions(max_retry_count=3)
        return RequestExceptionHandler(options)

    @pytest.fixture
    def retry_data(self) -> RequestRetryData:
        """Create default retry data."""
        return RequestRetryData()

    def test_initialization(self) -> None:
        """Test handler initialization with options."""
        options = RequestBehaviorOptions(max_retry_count=5)
        handler = RequestExceptionHandler(options)
        assert handler._options.max_retry_count == 5

    def test_retry_count_exceeds_max_returns_false(
        self, handler: RequestExceptionHandler
    ) -> None:
        """Test that exceeding max retry count returns False."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )
        retry_data = RequestRetryData(retry_count=4)  # Exceeds max of 3

        result = handler.handle(details, retry_data)
        assert result is False

    def test_retry_count_at_max_returns_false(
        self, handler: RequestExceptionHandler
    ) -> None:
        """Test that retry count at max returns False (>= check)."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )
        retry_data = RequestRetryData(retry_count=3)  # == 3 (max)

        result = handler.handle(details, retry_data)
        assert result is False

    def test_transactional_competition_exception_returns_false(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that competition exception on transactional service returns False."""
        exception = ServiceRequestCompetitionException()
        details = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_SAVE,  # TRANSACTIONAL
        )

        result = handler.handle(details, retry_data)
        assert result is False

    def test_transactional_deadlock_exception_returns_false(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that deadlock exception on transactional service returns False."""
        exception = ServiceRequestDeadlockException("Deadlock detected")
        details = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_SAVE,  # TRANSACTIONAL
        )

        result = handler.handle(details, retry_data)
        assert result is False

    def test_transactional_timeout_exception_returns_false(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that timeout exception on transactional service returns False."""
        exception = ServiceRequestTimeoutException(ServiceName.CRUD_SAVE)
        details = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_SAVE,  # TRANSACTIONAL
        )

        result = handler.handle(details, retry_data)
        assert result is False

    def test_non_transactional_competition_exception_calls_internal(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that competition exception on non-transactional service goes to internal handler."""
        exception = ServiceRequestCompetitionException()
        details = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_FIND,  # RETRIEVE (not TRANSACTIONAL)
        )

        # Should call _handle_internal which returns True
        result = handler.handle(details, retry_data)
        assert result is True

    def test_regular_exception_calls_internal_handler(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that regular exceptions pass to internal handler."""
        details = RequestExceptionDetails(
            exception=ValueError("Regular error"),
            service_name=ServiceName.CRUD_FIND,
        )

        # Should call _handle_internal which returns True
        result = handler.handle(details, retry_data)
        assert result is True

    def test_transactional_with_regular_exception_calls_internal(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that regular exceptions on transactional service go to internal handler."""
        details = RequestExceptionDetails(
            exception=ValueError("Not a special exception"),
            service_name=ServiceName.CRUD_SAVE,  # TRANSACTIONAL
        )

        # Regular exception should pass through to internal handler
        result = handler.handle(details, retry_data)
        assert result is True

    def test_handle_internal_returns_true(
        self, handler: RequestExceptionHandler, retry_data: RequestRetryData
    ) -> None:
        """Test that _handle_internal returns True for retry."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        result = handler._handle_internal(details, retry_data)
        assert result is True

    def test_custom_max_retry_count(self) -> None:
        """Test with custom max retry count."""
        options = RequestBehaviorOptions(max_retry_count=1)
        handler = RequestExceptionHandler(options)

        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        # retry_count = 2 exceeds max of 1
        retry_data = RequestRetryData(retry_count=2)
        result = handler.handle(details, retry_data)
        assert result is False

        # retry_count = 1 equals max, should return False (>= check)
        retry_data = RequestRetryData(retry_count=1)
        result = handler.handle(details, retry_data)
        assert result is False

        # retry_count = 0 is less than max, should return True
        retry_data = RequestRetryData(retry_count=0)
        result = handler.handle(details, retry_data)
        assert result is True

    def test_zero_max_retry_means_no_retries(self) -> None:
        """Test that zero max retry count disables retries."""
        options = RequestBehaviorOptions(max_retry_count=0)
        handler = RequestExceptionHandler(options)

        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        # retry_count = 1 exceeds max of 0
        retry_data = RequestRetryData(retry_count=1)
        result = handler.handle(details, retry_data)
        assert result is False

        # retry_count = 0 equals max of 0, should return False (>= check)
        retry_data = RequestRetryData(retry_count=0)
        result = handler.handle(details, retry_data)
        assert result is False


class TestRequestExceptionHandlerEdgeCases:
    """Edge case tests for RequestExceptionHandler."""

    def test_first_retry_attempt(self) -> None:
        """Test handling first retry attempt (retry_count = 0)."""
        options = RequestBehaviorOptions(max_retry_count=3)
        handler = RequestExceptionHandler(options)
        retry_data = RequestRetryData(retry_count=0)

        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        # Should pass to _handle_internal and return True
        result = handler.handle(details, retry_data)
        assert result is True

    def test_different_service_types(self) -> None:
        """Test that only TRANSACTIONAL blocks special exceptions."""
        options = RequestBehaviorOptions()
        handler = RequestExceptionHandler(options)
        retry_data = RequestRetryData()
        exception = ServiceRequestCompetitionException()

        # Test all service types that should allow retry for competition exception
        non_transactional_services = [
            ServiceName.CRUD_FIND,  # RETRIEVE
            ServiceName.CRUD_REMOVE,  # NON_TRANSACTIONAL
            ServiceName.LOGIN,  # RETRIEVE
        ]

        for service_name in non_transactional_services:
            details = RequestExceptionDetails(
                exception=exception,
                service_name=service_name,
            )
            # Should pass to _handle_internal and return True
            result = handler.handle(details, retry_data)
            assert result is True


class TestExponentialBackoff:
    """Tests for the exponential backoff implementation."""

    @pytest.fixture
    def handler(self) -> RequestExceptionHandler:
        """Create a handler with default options."""
        options = RequestBehaviorOptions(max_retry_count=10)
        return RequestExceptionHandler(options)

    def test_backoff_delay_retry_0(self, handler: RequestExceptionHandler) -> None:
        """Test that retry 0 uses FREE delay (10 seconds)."""
        retry_data = RequestRetryData(retry_count=0)
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        handler._handle_internal(details, retry_data)

        assert retry_data.retry_delay == 10  # FREE
        assert retry_data.retry_count == 1  # Incremented

    def test_backoff_delay_retry_1(self, handler: RequestExceptionHandler) -> None:
        """Test that retry 1 uses STABLE delay (15 seconds)."""
        retry_data = RequestRetryData(retry_count=1)
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        handler._handle_internal(details, retry_data)

        assert retry_data.retry_delay == 15  # STABLE
        assert retry_data.retry_count == 2  # Incremented

    def test_backoff_delay_retry_2(self, handler: RequestExceptionHandler) -> None:
        """Test that retry 2 uses UNSTABLE delay (30 seconds)."""
        retry_data = RequestRetryData(retry_count=2)
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        handler._handle_internal(details, retry_data)

        assert retry_data.retry_delay == 30  # UNSTABLE
        assert retry_data.retry_count == 3  # Incremented

    def test_backoff_delay_retry_3_and_beyond(
        self, handler: RequestExceptionHandler
    ) -> None:
        """Test that retry 3+ uses BREAKDOWN delay (90 seconds)."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        for retry_count in [3, 4, 5, 10]:
            retry_data = RequestRetryData(retry_count=retry_count)
            handler._handle_internal(details, retry_data)

            assert retry_data.retry_delay == 90  # BREAKDOWN
            assert retry_data.retry_count == retry_count + 1  # Incremented

    def test_retry_count_increment(self, handler: RequestExceptionHandler) -> None:
        """Test that retry_count is properly incremented."""
        retry_data = RequestRetryData(retry_count=0)
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        # Simulate multiple retries
        for expected_count in range(1, 5):
            handler._handle_internal(details, retry_data)
            assert retry_data.retry_count == expected_count


class TestMaxRetryBoundary:
    """Tests for the max_retry_count boundary enforcement."""

    def test_retry_count_equals_max_returns_false(self) -> None:
        """Test that retry_count == max_retry_count returns False."""
        options = RequestBehaviorOptions(max_retry_count=3)
        handler = RequestExceptionHandler(options)

        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        # retry_count = 3 equals max, should return False
        retry_data = RequestRetryData(retry_count=3)
        result = handler.handle(details, retry_data)
        assert result is False

    def test_zero_max_retry_count_blocks_first_attempt(self) -> None:
        """Test that max_retry_count=0 blocks even the first retry attempt."""
        options = RequestBehaviorOptions(max_retry_count=0)
        handler = RequestExceptionHandler(options)

        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        # retry_count = 0 equals max of 0, should return False
        retry_data = RequestRetryData(retry_count=0)
        result = handler.handle(details, retry_data)
        assert result is False

    def test_retry_count_less_than_max_returns_true(self) -> None:
        """Test that retry_count < max_retry_count returns True."""
        options = RequestBehaviorOptions(max_retry_count=3)
        handler = RequestExceptionHandler(options)

        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )

        for count in [0, 1, 2]:
            retry_data = RequestRetryData(retry_count=count)
            result = handler.handle(details, retry_data)
            assert result is True, f"Expected True for retry_count={count}"
