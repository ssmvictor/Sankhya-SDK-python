# -*- coding: utf-8 -*-
import pytest
from sankhya_sdk.exceptions import (
    InvalidKeyFileException,
    ServiceRequestInvalidAuthorizationException,
    CanceledOnDemandRequestWrapperException,
    ServiceRequestExpiredAuthenticationException,
    ServiceRequestInvalidCredentialsException,
    TooInnerLevelsException,
)

@pytest.mark.parametrize("key,expected_msg", [
    ("abc123", "The supplied key abc123 is not valid"),
    ("xyz789", "The supplied key xyz789 is not valid"),
])
def test_invalid_key_file_exception(key: str, expected_msg: str) -> None:
    exc: InvalidKeyFileException = InvalidKeyFileException(key)
    assert expected_msg in str(exc)
    assert isinstance(exc, Exception)

def test_service_request_invalid_authorization_exception() -> None:
    exc: ServiceRequestInvalidAuthorizationException = ServiceRequestInvalidAuthorizationException()
    assert "Attempt of unauthorized/unauthenticated access" in str(exc)
    
    inner: Exception = Exception("Inner error")
    exc_with_inner: ServiceRequestInvalidAuthorizationException = ServiceRequestInvalidAuthorizationException(inner_exception=inner)
    assert exc_with_inner.__cause__ == inner

def test_canceled_on_demand_request_wrapper_exception() -> None:
    exc: CanceledOnDemandRequestWrapperException = CanceledOnDemandRequestWrapperException()
    assert "Cannot add new items to a cancelled on demand request wrapper instance" in str(exc)

def test_service_request_expired_authentication_exception() -> None:
    exc: ServiceRequestExpiredAuthenticationException = ServiceRequestExpiredAuthenticationException()
    assert "The user's session is expired" in str(exc)

def test_service_request_invalid_credentials_exception() -> None:
    exc: ServiceRequestInvalidCredentialsException = ServiceRequestInvalidCredentialsException()
    assert "Unable to authenticate in Sankhya web service with provided credentials data" in str(exc)

def test_too_inner_levels_exception() -> None:
    exc: TooInnerLevelsException = TooInnerLevelsException("Partner")
    assert "Too many inner levels for entity Partner" in str(exc)
