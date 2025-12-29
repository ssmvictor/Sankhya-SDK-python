# -*- coding: utf-8 -*-
"""Unit tests for RequestRetryData."""

import pytest

from sankhya_sdk.request_helpers import RequestRetryData


class TestRequestRetryData:
    """Tests for the RequestRetryData dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are correctly set."""
        retry_data = RequestRetryData()
        assert retry_data.lock_key == ""
        assert retry_data.retry_count == 0
        assert retry_data.retry_delay == 0

    def test_custom_lock_key(self) -> None:
        """Test creating with a custom lock_key value."""
        retry_data = RequestRetryData(lock_key="my-request-123")
        assert retry_data.lock_key == "my-request-123"

    def test_custom_retry_count(self) -> None:
        """Test creating with a custom retry_count value."""
        retry_data = RequestRetryData(retry_count=5)
        assert retry_data.retry_count == 5

    def test_custom_retry_delay(self) -> None:
        """Test creating with a custom retry_delay value."""
        retry_data = RequestRetryData(retry_delay=30)
        assert retry_data.retry_delay == 30

    def test_all_custom_values(self) -> None:
        """Test creating with all custom values."""
        retry_data = RequestRetryData(
            lock_key="request-456",
            retry_count=3,
            retry_delay=15,
        )
        assert retry_data.lock_key == "request-456"
        assert retry_data.retry_count == 3
        assert retry_data.retry_delay == 15

    def test_mutability(self) -> None:
        """Test that the dataclass is mutable (not frozen)."""
        retry_data = RequestRetryData()

        # Should be able to modify values
        retry_data.lock_key = "updated-key"
        retry_data.retry_count = 2
        retry_data.retry_delay = 10

        assert retry_data.lock_key == "updated-key"
        assert retry_data.retry_count == 2
        assert retry_data.retry_delay == 10

    def test_increment_retry_count(self) -> None:
        """Test incrementing retry count."""
        retry_data = RequestRetryData()
        retry_data.retry_count += 1
        assert retry_data.retry_count == 1
        retry_data.retry_count += 1
        assert retry_data.retry_count == 2

    def test_equality(self) -> None:
        """Test equality comparison between instances."""
        data1 = RequestRetryData(lock_key="key", retry_count=1, retry_delay=10)
        data2 = RequestRetryData(lock_key="key", retry_count=1, retry_delay=10)
        data3 = RequestRetryData(lock_key="key", retry_count=2, retry_delay=10)

        assert data1 == data2
        assert data1 != data3

    def test_repr(self) -> None:
        """Test string representation."""
        retry_data = RequestRetryData(
            lock_key="test-key",
            retry_count=1,
            retry_delay=15,
        )
        repr_str = repr(retry_data)
        assert "lock_key='test-key'" in repr_str
        assert "retry_count=1" in repr_str
        assert "retry_delay=15" in repr_str
