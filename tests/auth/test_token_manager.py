import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sankhya_sdk.auth.token_manager import TokenManager
from sankhya_sdk.auth.exceptions import TokenExpiredError

def test_token_storage():
    tm = TokenManager()
    tm.set_tokens("access123", expires_in=3600, refresh_token="refresh123")
    
    assert tm.get_token() == "access123"
    assert tm.get_refresh_token() == "refresh123"
    assert tm.is_expired() is False

def test_token_expiration_logic():
    tm = TokenManager()
    tm.set_tokens("access123", expires_in=-10) # Expired logically
    
    assert tm.is_expired() is True
    with pytest.raises(TokenExpiredError):
        tm.get_token()

def test_token_buffer_logic():
    tm = TokenManager()
    # Expiring in 50s should be considered expired due to 60s buffer
    tm.set_tokens("access123", expires_in=50) 
    
    assert tm.is_expired() is True
    with pytest.raises(TokenExpiredError):
        tm.get_token()

def test_clear_tokens():
    tm = TokenManager()
    tm.set_tokens("acc", 3600, "ref", "cid", "sec")
    tm.clear()
    
    assert tm._access_token is None
    assert tm._refresh_token is None
    assert tm._client_id is None
