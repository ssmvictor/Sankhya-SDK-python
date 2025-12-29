# -*- coding: utf-8 -*-
"""
Request Behavior Options configuration for the Sankhya SDK.

This module provides configuration options for controlling request behavior,
including retry policies and limits.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestBehaviorOptions:
    """
    Configuration options for request behavior and retry policies.

    This immutable dataclass defines the behavior settings for HTTP requests,
    including the maximum number of retry attempts before giving up.

    Attributes:
        max_retry_count: The maximum number of retry attempts for failed requests.
            Defaults to 3 attempts before the request is considered failed.

    Example:
        >>> options = RequestBehaviorOptions()
        >>> print(options.max_retry_count)
        3
        >>> custom_options = RequestBehaviorOptions(max_retry_count=5)
        >>> print(custom_options.max_retry_count)
        5
    """

    max_retry_count: int = 3
