import json
import pytest
import requests
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs
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
    # OAuth2 client_credentials token request is form-urlencoded (data=), not JSON
    mock_session.post.assert_called_with(
        "http://api.test/authenticate",
        data={"client_id": "cid", "client_secret": "sec", "grant_type": "client_credentials"},
        headers={},
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
        data={"refresh_token": "refresh_old"},
        headers={},
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


class _CaptureAdapter(requests.adapters.BaseAdapter):
    """Transport adapter that records the prepared request instead of hitting the network."""

    def __init__(self, payload):
        super().__init__()
        self.payload = payload
        self.sent = []

    def send(self, request, **kwargs):
        self.sent.append(request)
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(self.payload).encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        response.url = request.url
        response.request = request
        return response

    def close(self):
        pass


def test_authenticate_sends_x_token_header(mock_session):
    client = OAuthClient("http://api.test", token="xtok")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "token123", "expires_in": 3600}
    mock_session.post.return_value = mock_response

    client.authenticate("cid", "sec")

    mock_session.post.assert_called_with(
        "http://api.test/authenticate",
        data={"client_id": "cid", "client_secret": "sec", "grant_type": "client_credentials"},
        headers={"X-Token": "xtok"},
        timeout=10
    )


def test_authenticate_wire_format_is_form_urlencoded():
    # Real requests.Session (only the transport is stubbed) to pin the on-the-wire contract
    client = OAuthClient("http://api.test", token="xtok")
    adapter = _CaptureAdapter({"access_token": "token123", "expires_in": 3600})
    client._session.mount("http://", adapter)

    assert client.authenticate("cid", "sec") == "token123"

    assert len(adapter.sent) == 1
    sent = adapter.sent[0]
    assert sent.method == "POST"
    assert sent.url == "http://api.test/authenticate"
    assert sent.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert sent.headers["X-Token"] == "xtok"
    assert parse_qs(sent.body, strict_parsing=True) == {
        "client_id": ["cid"],
        "client_secret": ["sec"],
        "grant_type": ["client_credentials"],
    }


def test_refresh_token_wire_format_is_form_urlencoded():
    client = OAuthClient("http://api.test", token="xtok")
    client.token_manager.set_tokens("old_token", 3600, "refresh_old")
    adapter = _CaptureAdapter({"access_token": "new_token", "expires_in": 3600})
    client._session.mount("http://", adapter)

    assert client.refresh_token() == "new_token"

    assert len(adapter.sent) == 1
    sent = adapter.sent[0]
    assert sent.method == "POST"
    assert sent.url == "http://api.test/token/refresh"
    assert sent.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert sent.headers["X-Token"] == "xtok"
    assert parse_qs(sent.body, strict_parsing=True) == {"refresh_token": ["refresh_old"]}
