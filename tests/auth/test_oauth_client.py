import pytest
import requests
from unittest.mock import MagicMock, patch
from sankhya_sdk.auth.oauth_client import OAuthClient
from sankhya_sdk.auth.exceptions import AuthError, AuthNetworkError

@pytest.fixture
def mock_session():
    with patch("sankhya_sdk.auth.oauth_client.requests.Session") as mock:
        session_instance = MagicMock()
        mock.return_value = session_instance
        yield session_instance

def test_authenticate_success(mock_session):
    client = OAuthClient("http://api.test")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "token123",
        "expires_in": 3600,
        "refresh_token": "refresh123"
    }
    mock_session.post.return_value = mock_response
    
    token = client.authenticate("cid", "sec")
    
    assert token == "token123"
    assert client.token_manager.get_token() == "token123"
    mock_session.post.assert_called_with(
        "http://api.test/authenticate",
        json={"client_id": "cid", "client_secret": "sec", "grant_type": "client_credentials"},
        timeout=10
    )

def test_authenticate_failure(mock_session):
    client = OAuthClient("http://api.test")
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "invalid_client"}
    mock_session.post.return_value = mock_response
    
    with pytest.raises(AuthError) as exc:
        client.authenticate("cid", "sec")
    
    assert "invalid_client" in str(exc.value)

def test_refresh_token_success(mock_session):
    client = OAuthClient("http://api.test")
    client.token_manager.set_tokens("old_token", 3600, "refresh_old")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600
    }
    mock_session.post.return_value = mock_response
    
    new_token = client.refresh_token()
    
    assert new_token == "new_token"
    assert client.token_manager.get_token() == "new_token"
    # Ensure refresh calls correct endpoint
    mock_session.post.assert_called_with(
        "http://api.test/token/refresh",
        json={"refresh_token": "refresh_old"},
        timeout=10
    )

def test_refresh_token_reauth_fallback(mock_session):
    client = OAuthClient("http://api.test")
    # Setup state: expired token, but credentials saved
    client.token_manager.set_tokens("old", 0, "ref", "cid", "sec")
    
    # First call (refresh) fails with 400
    r1 = MagicMock()
    r1.status_code = 400
    
    # Second call (auth) succeeds
    r2 = MagicMock()
    r2.status_code = 200
    r2.json.return_value = {"access_token": "reauthed_token", "expires_in": 3600}
    
    mock_session.post.side_effect = [r1, r2]
    
    token = client.refresh_token()
    
    assert token == "reauthed_token"
    assert mock_session.post.call_count == 2
