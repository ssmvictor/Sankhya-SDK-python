# -*- coding: utf-8 -*-
"""Unit tests for RequestBehaviorOptions."""

import pytest

from sankhya_sdk.request_helpers import RequestBehaviorOptions


class TestRequestBehaviorOptions:
    """Tests for the RequestBehaviorOptions dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are correctly set."""
        options = RequestBehaviorOptions()
        assert options.max_retry_count == 3

    def test_custom_max_retry_count(self) -> None:
        """Test creating with a custom max_retry_count value."""
        options = RequestBehaviorOptions(max_retry_count=5)
        assert options.max_retry_count == 5

    def test_zero_max_retry_count(self) -> None:
        """Test creating with zero max_retry_count (no retries)."""
        options = RequestBehaviorOptions(max_retry_count=0)
        assert options.max_retry_count == 0

    def test_immutability(self) -> None:
        """Test that the dataclass is immutable (frozen)."""
        options = RequestBehaviorOptions()
        with pytest.raises(AttributeError):
            options.max_retry_count = 10  # type: ignore[misc]

    def test_equality(self) -> None:
        """Test equality comparison between instances."""
        options1 = RequestBehaviorOptions(max_retry_count=3)
        options2 = RequestBehaviorOptions(max_retry_count=3)
        options3 = RequestBehaviorOptions(max_retry_count=5)

        assert options1 == options2
        assert options1 != options3

    def test_hash(self) -> None:
        """Test that instances are hashable due to frozen=True."""
        options1 = RequestBehaviorOptions(max_retry_count=3)
        options2 = RequestBehaviorOptions(max_retry_count=3)

        # Should be usable in sets/dicts
        options_set = {options1, options2}
        assert len(options_set) == 1

    def test_repr(self) -> None:
        """Test string representation."""
        options = RequestBehaviorOptions(max_retry_count=5)
        assert "max_retry_count=5" in repr(options)
