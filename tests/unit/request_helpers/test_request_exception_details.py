# -*- coding: utf-8 -*-
"""Unit tests for RequestExceptionDetails."""

import pytest

from sankhya_sdk.enums import ServiceName, ServiceType
from sankhya_sdk.request_helpers import RequestExceptionDetails


class TestRequestExceptionDetails:
    """Tests for the RequestExceptionDetails dataclass."""

    def test_creation_with_required_params(self) -> None:
        """Test creating with only required parameters."""
        exception = ValueError("Test error")
        details = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_FIND,
        )
        assert details.exception is exception
        assert details.service_name == ServiceName.CRUD_FIND
        assert details.request is None

    def test_creation_with_request(self) -> None:
        """Test creating with all parameters including request."""
        exception = RuntimeError("Test error")
        mock_request = {"entity": "TestEntity"}
        details = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_SAVE,
            request=mock_request,
        )
        assert details.exception is exception
        assert details.service_name == ServiceName.CRUD_SAVE
        assert details.request == mock_request

    def test_service_type_property_transactional(self) -> None:
        """Test service_type property returns correct type for transactional service."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_SAVE,  # TRANSACTIONAL
        )
        assert details.service_type == ServiceType.TRANSACTIONAL

    def test_service_type_property_retrieve(self) -> None:
        """Test service_type property returns correct type for retrieve service."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,  # RETRIEVE
        )
        assert details.service_type == ServiceType.RETRIEVE

    def test_service_type_property_non_transactional(self) -> None:
        """Test service_type property returns correct type for non-transactional service."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_REMOVE,  # NON_TRANSACTIONAL
        )
        assert details.service_type == ServiceType.NON_TRANSACTIONAL

    def test_different_service_names(self) -> None:
        """Test creating with different ServiceName values."""
        test_cases = [
            (ServiceName.LOGIN, ServiceType.RETRIEVE),
            (ServiceName.INVOICE_CONFIRM, ServiceType.NON_TRANSACTIONAL),
            (ServiceName.INVOICE_INCLUDE, ServiceType.TRANSACTIONAL),
        ]

        for service_name, expected_type in test_cases:
            details = RequestExceptionDetails(
                exception=Exception("Test"),
                service_name=service_name,
            )
            assert details.service_type == expected_type

    def test_exception_types(self) -> None:
        """Test with different exception types."""
        exceptions = [
            ValueError("Invalid value"),
            TypeError("Wrong type"),
            RuntimeError("Runtime error"),
            Exception("Generic error"),
        ]

        for exc in exceptions:
            details = RequestExceptionDetails(
                exception=exc,
                service_name=ServiceName.CRUD_FIND,
            )
            assert details.exception is exc
            assert str(details.exception) == str(exc)

    def test_equality(self) -> None:
        """Test equality comparison between instances."""
        exception = ValueError("Test")
        details1 = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_FIND,
        )
        details2 = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_FIND,
        )
        # Same exception reference and same service name
        assert details1 == details2

    def test_inequality_different_service(self) -> None:
        """Test inequality when service names differ."""
        exception = ValueError("Test")
        details1 = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_FIND,
        )
        details2 = RequestExceptionDetails(
            exception=exception,
            service_name=ServiceName.CRUD_SAVE,
        )
        assert details1 != details2

    def test_repr(self) -> None:
        """Test string representation."""
        details = RequestExceptionDetails(
            exception=ValueError("Test"),
            service_name=ServiceName.CRUD_FIND,
        )
        repr_str = repr(details)
        assert "RequestExceptionDetails" in repr_str
        assert "service_name" in repr_str
