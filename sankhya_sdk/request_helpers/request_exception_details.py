# -*- coding: utf-8 -*-
"""
Request Exception Details for the Sankhya SDK.

This module provides a data class for capturing exception context information,
including the exception, service name, and optional request data.
"""

from dataclasses import dataclass
from typing import Any, Optional

from ..enums import ServiceName, ServiceType


@dataclass
class RequestExceptionDetails:
    """
    Data class containing details about a request exception.

    This dataclass captures the context of an exception that occurred during
    a service request, including the exception itself, the service that was
    called, and optionally the request data that caused the exception.

    Attributes:
        exception: The exception that was raised during the request.
        service_name: The ServiceName enum identifying the service that was called.
        request: Optional request data that caused the exception.
            May be None if the exception occurred before the request was formed.

    Properties:
        service_type: The ServiceType extracted from the service_name metadata.

    Example:
        >>> from sankhya_sdk.enums import ServiceName
        >>> try:
        ...     # some operation that fails
        ...     raise ValueError("Test error")
        ... except Exception as e:
        ...     details = RequestExceptionDetails(
        ...         exception=e,
        ...         service_name=ServiceName.CRUD_FIND,
        ...     )
        ...     print(details.service_type)
    """

    exception: Exception
    service_name: ServiceName
    request: Optional[Any] = None

    @property
    def service_type(self) -> ServiceType:
        """
        Gets the service type from the service name metadata.

        Returns:
            ServiceType: The type of service (e.g., TRANSACTIONAL, QUERY).
        """
        return self.service_name.metadata.service_type
