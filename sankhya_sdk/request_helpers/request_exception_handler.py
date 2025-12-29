# -*- coding: utf-8 -*-
"""
Request Exception Handler for the Sankhya SDK.

This module provides the interface and implementation for handling exceptions
during service requests, with support for retry logic and filtering.
"""

from typing import Protocol, runtime_checkable

from ..enums import ServiceType
from ..exceptions import (
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestTimeoutException,
)
from .request_behavior_options import RequestBehaviorOptions
from .request_exception_details import RequestExceptionDetails
from .request_retry_data import RequestRetryData
from .request_retry_delay import RequestRetryDelay


@runtime_checkable
class IRequestExceptionHandler(Protocol):
    """
    Protocol defining the contract for request exception handlers.

    This protocol specifies the interface that all request exception handlers
    must implement to handle exceptions during service requests.

    The handler is responsible for determining whether a request should be
    retried based on the exception details and current retry state.
    """

    def handle(
        self,
        details: RequestExceptionDetails,
        retry_data: RequestRetryData,
    ) -> bool:
        """
        Handles a request exception and determines if retry should occur.

        Args:
            details: The exception details including the exception, service name,
                and optional request data.
            retry_data: The current retry state including count and delay.

        Returns:
            bool: True if the request should be retried, False otherwise.
        """
        ...


class RequestExceptionHandler(IRequestExceptionHandler):
    """
    Default implementation of the request exception handler.

    This handler implements retry logic for service request exceptions,
    including checks for maximum retry count and specific exception types
    that should not be retried for transactional services.

    Attributes:
        _options: The behavior options controlling retry limits.

    Example:
        >>> from sankhya_sdk.request_helpers import (
        ...     RequestBehaviorOptions,
        ...     RequestExceptionHandler,
        ...     RequestExceptionDetails,
        ...     RequestRetryData,
        ... )
        >>> options = RequestBehaviorOptions(max_retry_count=3)
        >>> handler = RequestExceptionHandler(options)
        >>> retry_data = RequestRetryData(retry_count=0)
        >>> # details = RequestExceptionDetails(...)
        >>> # should_retry = handler.handle(details, retry_data)
    """

    def __init__(self, options: RequestBehaviorOptions) -> None:
        """
        Initializes a new instance of the RequestExceptionHandler.

        Args:
            options: The behavior options that configure retry limits.
        """
        self._options = options

    def handle(
        self,
        details: RequestExceptionDetails,
        retry_data: RequestRetryData,
    ) -> bool:
        """
        Handles a request exception and determines if retry should occur.

        This method checks the following conditions:
        1. If the retry count exceeds the maximum, no retry is performed.
        2. If the service is transactional and the exception is competition,
           deadlock, or timeout related, no retry is performed.
        3. Otherwise, delegates to the internal handler for further processing.

        Args:
            details: The exception details including the exception, service name,
                and optional request data.
            retry_data: The current retry state including count and delay.

        Returns:
            bool: True if the request should be retried, False otherwise.
        """
        # Check if we've reached or exceeded the maximum retry count
        if retry_data.retry_count >= self._options.max_retry_count:
            return False

        # Check if this is a transactional service with a non-retriable exception
        if details.service_type == ServiceType.TRANSACTIONAL:
            exception = details.exception
            if isinstance(
                exception,
                (
                    ServiceRequestCompetitionException,
                    ServiceRequestDeadlockException,
                    ServiceRequestTimeoutException,
                ),
            ):
                return False

        # Delegate to internal handler for further processing
        return self._handle_internal(details, retry_data)

    def _handle_internal(
        self,
        details: RequestExceptionDetails,  # noqa: ARG002
        retry_data: RequestRetryData,
    ) -> bool:
        """
        Internal handler for processing retry logic.

        This method is called after the initial checks pass and is responsible
        for implementing the actual retry logic, including exponential backoff.

        The backoff strategy uses increasing delay levels based on retry count:
        - Retry 0: FREE delay (10 seconds)
        - Retry 1: STABLE delay (15 seconds)
        - Retry 2: UNSTABLE delay (30 seconds)
        - Retry 3+: BREAKDOWN delay (90 seconds)

        Args:
            details: The exception details including the exception, service name,
                and optional request data.
            retry_data: The current retry state including count and delay.

        Returns:
            bool: True to indicate the request should be retried.
        """
        # Calculate exponential backoff delay based on retry count
        retry_count = retry_data.retry_count
        if retry_count == 0:
            retry_data.retry_delay = RequestRetryDelay.FREE
        elif retry_count == 1:
            retry_data.retry_delay = RequestRetryDelay.STABLE
        elif retry_count == 2:
            retry_data.retry_delay = RequestRetryDelay.UNSTABLE
        else:
            retry_data.retry_delay = RequestRetryDelay.BREAKDOWN

        # Increment retry count for the next attempt
        retry_data.retry_count += 1

        return True
