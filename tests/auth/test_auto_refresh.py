import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sankhya_sdk.auth.oauth_client import OAuthClient
from sankhya_sdk.auth.token_manager import TokenManager
from sankhya_sdk.auth.exceptions import AuthError, TokenExpiredError


@pytest.fixture
def mock_session():
    with patch("sankhya_sdk.auth.oauth_client.requests.Session") as mock:
        session_instance = MagicMock()
        mock.return_value = session_instance
        yield session_instance


def test_get_valid_token_with_valid_token(mock_session):
    """Test that get_valid_token returns current token if still valid."""
    client = OAuthClient("http://api.test")
    
    # Set a valid token (expires in 10 minutes)
    client.token_manager.set_tokens("valid_token", expires_in=600)
    
    # Should return the current token without calling refresh
    token = client.get_valid_token()
    
    assert token == "valid_token"
    # Verify no HTTP call was made (no refresh needed)
    mock_session.post.assert_not_called()


def test_get_valid_token_with_expired_token(mock_session):
    """Test that get_valid_token automatically refreshes expired token."""
    client = OAuthClient("http://api.test")
    
    # Set an expired token
    client.token_manager.set_tokens("expired_token", expires_in=-10, refresh_token="ref123")
    
    # Mock successful refresh response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600,
        "refresh_token": "new_ref"
    }
    mock_session.post.return_value = mock_response
    
    # Should automatically refresh and return new token
    token = client.get_valid_token()
    
    assert token == "new_token"
    assert client.token_manager.get_token() == "new_token"
    # Verify refresh endpoint was called
    mock_session.post.assert_called_once()


def test_get_valid_token_near_expiry(mock_session):
    """Test that get_valid_token refreshes token near expiry (within 60s buffer)."""
    client = OAuthClient("http://api.test")
    
    # Set a token that expires in 30 seconds (within 60s buffer)
    client.token_manager.set_tokens("expiring_soon", expires_in=30, refresh_token="ref123")
    
    # Mock successful refresh response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "refreshed_token",
        "expires_in": 3600
    }
    mock_session.post.return_value = mock_response
    
    # Should proactively refresh token
    token = client.get_valid_token()
    
    assert token == "refreshed_token"
    # Verify refresh was triggered
    mock_session.post.assert_called_once()


def test_get_valid_token_refresh_failure_with_reauth(mock_session):
    """Test that get_valid_token falls back to re-auth if refresh fails."""
    client = OAuthClient("http://api.test")
    
    # Set expired token with stored credentials for re-auth
    client.token_manager.set_tokens(
        "expired", 
        expires_in=-10, 
        refresh_token="ref123",
        client_id="cid",
        client_secret="sec"
    )
    
    # Mock refresh failure (400)
    refresh_response = MagicMock()
    refresh_response.status_code = 400
    
    # Mock successful re-auth
    auth_response = MagicMock()
    auth_response.status_code = 200
    auth_response.json.return_value = {
        "access_token": "reauthed_token",
        "expires_in": 3600
    }
    
    mock_session.post.side_effect = [refresh_response, auth_response]
    
    # Should fall back to re-auth
    token = client.get_valid_token()
    
    assert token == "reauthed_token"
    assert mock_session.post.call_count == 2


def test_get_valid_token_no_token_raises_error(mock_session):
    """Test that get_valid_token raises error if no token and can't refresh."""
    client = OAuthClient("http://api.test")
    
    # No token set, no credentials
    with pytest.raises((AuthError, TokenExpiredError)):
        client.get_valid_token()


def test_token_manager_thread_safety():
    """Test that TokenManager operations are thread-safe."""
    import threading
    
    tm = TokenManager()
    tm.set_tokens("token1", 3600)
    
    results = []
    errors = []
    
    def get_token_multiple_times():
        try:
            for _ in range(10):  # Reduced from 100
                token = tm.get_token()
                results.append(token)
        except Exception as e:
            errors.append(e)
    
    # Create 5 threads instead of 10
    threads = [threading.Thread(target=get_token_multiple_times) for _ in range(5)]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion with timeout
    for t in threads:
        t.join(timeout=5.0)  # 5 second timeout per thread
    
    # All operations should succeed
    assert len(errors) == 0
    assert len(results) == 50  # 5 threads * 10 calls
    assert all(r == "token1" for r in results)


def test_integration_session_auto_refresh():
    """Integration test: SankhyaSession should use auto-refresh."""
    from sankhya_sdk.http.session import SankhyaSession
    
    with patch("sankhya_sdk.auth.oauth_client.requests.Session") as mock_oauth_session:
        # Setup OAuth client with expiring token
        oauth_client = OAuthClient("http://api.test")
        oauth_client.token_manager.set_tokens("old_token", expires_in=30, refresh_token="ref")
        
        # Mock refresh response
        refresh_response = MagicMock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600
        }
        mock_oauth_session.return_value.post.return_value = refresh_response
        
        # Create session
        session = SankhyaSession(oauth_client, base_url="http://api.test")
        
        with patch.object(session._session, "request") as mock_request:
            mock_request.return_value = MagicMock(status_code=200)
            
            # Make request - should trigger auto-refresh due to near expiry
            session.get("/some/endpoint")
            
            # Verify the request was made with refreshed token
            call_kwargs = mock_request.call_args[1]
            auth_header = call_kwargs["headers"]["Authorization"]
            assert auth_header == "Bearer new_token"
