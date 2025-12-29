# -*- coding: utf-8 -*-
"""
Request Retry Delay constants for the Sankhya SDK.

This module provides delay constants for different system stability levels,
used to determine appropriate wait times between retry attempts.
"""

from typing import Final


class RequestRetryDelay:
    """
    Constants for retry delay values based on system stability levels.

    These delay values (in seconds) are used to determine how long to wait
    before retrying a failed request. The appropriate delay is chosen based
    on the current system stability and error patterns.

    Attributes:
        FREE: Delay for free/idle system conditions (10 seconds).
            Use when the system is generally healthy with occasional transient errors.
        STABLE: Delay for stable system conditions (15 seconds).
            Use when the system is operational but experiencing some load.
        UNSTABLE: Delay for unstable system conditions (30 seconds).
            Use when the system is experiencing intermittent issues or high load.
        BREAKDOWN: Delay for breakdown/critical system conditions (90 seconds).
            Use when the system is experiencing severe issues or is recovering.

    Example:
        >>> import time
        >>> delay = RequestRetryDelay.FREE
        >>> print(f"Waiting {delay} seconds before retry...")
        Waiting 10 seconds before retry...
    """

    FREE: Final[int] = 10
    STABLE: Final[int] = 15
    UNSTABLE: Final[int] = 30
    BREAKDOWN: Final[int] = 90
