import pytest
from unittest.mock import MagicMock, patch
from sankhya_sdk.http.session import SankhyaSession
from sankhya_sdk.auth.oauth_client import OAuthClient

@pytest.fixture
def mock_oauth_client():
    client = MagicMock(spec=OAuthClient)
    client.token_manager = MagicMock()
    # Setup token manager to return a token primarily
    client.token_manager.get_token.return_value = "valid_token"
    return client

@pytest.fixture
def sankhya_session(mock_oauth_client):
    with patch("sankhya_sdk.http.session.requests.Session") as mock_req_session:
        session = SankhyaSession(mock_oauth_client, "http://api.test")
        session._session = mock_req_session.return_value # Mock inner session
        yield session

def test_session_injects_header(sankhya_session, mock_oauth_client):
    mock_http = sankhya_session._session
    mock_http.request.return_value.status_code = 200
    
    sankhya_session.get("/resource")
    
    mock_http.request.assert_called_once()
    call_kwargs = mock_http.request.call_args[1]
    headers = call_kwargs["headers"]
    
    assert headers["Authorization"] == "Bearer valid_token"
    # Content-Type is set on session.headers, not in request kwargs
    mock_http.headers.update.assert_called()

def test_session_retry_on_401(sankhya_session, mock_oauth_client):
    mock_http = sankhya_session._session
    
    # First response 401, Second response 200
    r1 = MagicMock(status_code=401)
    r2 = MagicMock(status_code=200)
    mock_http.request.side_effect = [r1, r2]
    
    # Mock refresh behavior
    mock_oauth_client.refresh_token.return_value = "refreshed_token"
    
    response = sankhya_session.get("/resource")
    
    assert response.status_code == 200
    assert mock_http.request.call_count == 2
    
    # First call with original token
    # Second call with new token 
    # (Cannot easily inspect kwargs of previous calls in side_effect sequence without call_args_list)
    
    second_call_headers = mock_http.request.call_args_list[1][1]["headers"]
    assert second_call_headers["Authorization"] == "Bearer refreshed_token"
    
    mock_oauth_client.refresh_token.assert_called_once()
