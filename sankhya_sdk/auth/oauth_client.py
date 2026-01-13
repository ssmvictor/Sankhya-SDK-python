import logging
import requests
from typing import Optional, Dict

from sankhya_sdk.auth.exceptions import AuthError, AuthNetworkError
from sankhya_sdk.auth.token_manager import TokenManager

logger = logging.getLogger(__name__)

class OAuthClient:
    """
    Client for interacting with Sankhya OAuth2 endpoints.
    Allows refreshing tokens.
    """

    def __init__(self, base_url: str, token_manager: Optional[TokenManager] = None, token: Optional[str] = None):
        """
        Args:
            base_url: Base URL for authentication.
            token_manager: Optional TokenManager.
            token: Optional proprietary Sankhya token (X-Token) required for some environments.
        """
        self.base_url = base_url.rstrip("/")
        self.token_manager = token_manager or TokenManager()
        self.sankhya_token = token
        self._session = requests.Session()
        
    def authenticate(self, client_id: str, client_secret: str) -> str:
        """
        Performs authentication using client_id and client_secret.
        Returns the access token and updates the TokenManager.
        """
        url = f"{self.base_url}/authenticate"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        
        headers = {}
        if self.sankhya_token:
            headers["X-Token"] = self.sankhya_token

        try:
            logger.debug(f"Authenticating against {url} with headers {headers.keys()}")
            response = self._session.post(url, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                refresh_token = data.get("refresh_token")
                
                if not access_token:
                    raise AuthError("Response did not contain access_token", status_code=response.status_code)
                
                self.token_manager.set_tokens(
                    access_token=access_token,
                    expires_in=expires_in,
                    refresh_token=refresh_token,
                    client_id=client_id,
                    client_secret=client_secret
                )
                return access_token
            else:
                self._handle_error(response)

        except requests.RequestException as e:
            raise AuthNetworkError(f"Network error during authentication: {str(e)}")

    def refresh_token(self) -> str:
        refresh_token = self.token_manager.get_refresh_token()
        
        if not refresh_token:
            return self._attempt_reauth()

        url = f"{self.base_url}/token/refresh"
        payload = {"refresh_token": refresh_token}
        
        headers = {}
        if self.sankhya_token:
            headers["X-Token"] = self.sankhya_token

        try:
            logger.debug(f"Refreshing token at {url}")
            response = self._session.post(url, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                new_refresh_token = data.get("refresh_token")
                
                self.token_manager.set_tokens(
                    access_token=access_token,
                    expires_in=expires_in,
                    refresh_token=new_refresh_token or refresh_token
                )
                return access_token
            else:
                return self._attempt_reauth()

        except requests.RequestException as e:
            raise AuthNetworkError(f"Network error during token refresh: {str(e)}")

    def _attempt_reauth(self) -> str:
        cid, secret = self.token_manager.get_credentials()
        if cid and secret:
            return self.authenticate(cid, secret)
        raise AuthError("Cannot refresh token: no refresh token and no stored credentials.")

    def _handle_error(self, response: requests.Response):
        status = response.status_code
        try:
            error_data = response.json()
            message = error_data.get("error_description") or error_data.get("error") or response.text
        except ValueError:
            message = response.text
            
        raise AuthError(f"Authentication failed: {message}", status_code=status)
