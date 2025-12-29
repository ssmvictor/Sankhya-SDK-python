# -*- coding: utf-8 -*-
"""
Request Retry Data for the Sankhya SDK.

This module provides a data class for tracking the state of request retries,
including lock keys, retry counts, and delay values.
"""

from dataclasses import dataclass


@dataclass
class RequestRetryData:
    """
    Data class for tracking the state of request retries.

    This mutable dataclass holds the current state of a retry operation,
    including the lock key for identifying the request, the current retry count,
    and the calculated delay before the next retry attempt.

    Attributes:
        lock_key: A unique identifier for the request being retried.
            Used to track and coordinate retry attempts for the same request.
        retry_count: The current number of retry attempts made.
            Incremented after each failed attempt.
        retry_delay: The delay in seconds before the next retry attempt.
            Calculated based on the retry strategy (e.g., exponential backoff).

    Example:
        >>> retry_data = RequestRetryData()
        >>> print(retry_data.retry_count)
        0
        >>> retry_data.retry_count += 1
        >>> print(retry_data.retry_count)
        1
    """

    lock_key: str = ""
    retry_count: int = 0
    retry_delay: int = 0
