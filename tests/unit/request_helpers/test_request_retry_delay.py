# -*- coding: utf-8 -*-
"""Unit tests for RequestRetryDelay."""

import pytest

from sankhya_sdk.request_helpers import RequestRetryDelay


class TestRequestRetryDelay:
    """Tests for the RequestRetryDelay constants."""

    def test_free_constant_value(self) -> None:
        """Test the FREE constant has the correct value."""
        assert RequestRetryDelay.FREE == 10

    def test_stable_constant_value(self) -> None:
        """Test the STABLE constant has the correct value."""
        assert RequestRetryDelay.STABLE == 15

    def test_unstable_constant_value(self) -> None:
        """Test the UNSTABLE constant has the correct value."""
        assert RequestRetryDelay.UNSTABLE == 30

    def test_breakdown_constant_value(self) -> None:
        """Test the BREAKDOWN constant has the correct value."""
        assert RequestRetryDelay.BREAKDOWN == 90

    def test_all_constants_are_integers(self) -> None:
        """Test that all constants are integer type."""
        assert isinstance(RequestRetryDelay.FREE, int)
        assert isinstance(RequestRetryDelay.STABLE, int)
        assert isinstance(RequestRetryDelay.UNSTABLE, int)
        assert isinstance(RequestRetryDelay.BREAKDOWN, int)

    def test_constants_ordering(self) -> None:
        """Test that constants are ordered by severity."""
        assert RequestRetryDelay.FREE < RequestRetryDelay.STABLE
        assert RequestRetryDelay.STABLE < RequestRetryDelay.UNSTABLE
        assert RequestRetryDelay.UNSTABLE < RequestRetryDelay.BREAKDOWN

    def test_constants_are_positive(self) -> None:
        """Test that all delay constants are positive values."""
        assert RequestRetryDelay.FREE > 0
        assert RequestRetryDelay.STABLE > 0
        assert RequestRetryDelay.UNSTABLE > 0
        assert RequestRetryDelay.BREAKDOWN > 0

    def test_constants_usable_in_calculations(self) -> None:
        """Test that constants can be used in arithmetic operations."""
        # Example: calculating exponential backoff multiplier
        base_delay = RequestRetryDelay.FREE
        double_delay = base_delay * 2
        assert double_delay == 20

        # Example: comparing against threshold
        threshold = 25
        assert RequestRetryDelay.FREE < threshold
        assert RequestRetryDelay.STABLE < threshold
        assert RequestRetryDelay.UNSTABLE > threshold
