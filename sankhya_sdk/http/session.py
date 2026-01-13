import logging
import requests
from typing import Optional, Any, Dict

from sankhya_sdk.auth.oauth_client import OAuthClient
from sankhya_sdk.auth.exceptions import TokenExpiredError, AuthError, AuthNetworkError

logger = logging.getLogger(__name__)

class SankhyaSession:
    """
    HTTP Session wrapper that handles OAuth2 authentication header injection
    and token refresh on 401 errors.
    """

    def __init__(self, oauth_client: OAuthClient, base_url: Optional[str] = None):
        """
        Args:
            oauth_client: The OAuthClient instance (which holds the TokenManager).
            base_url: Optional base URL to prepend to paths.
        """
        self.oauth_client = oauth_client
        self.token_manager = oauth_client.token_manager
        self.base_url = base_url.rstrip("/") if base_url else ""
        self._session = requests.Session()
        self._set_default_headers()

    def _set_default_headers(self):
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Wraps requests.request to inject authorization header.
        Performs one retry if a 401 occurs, forcing a token refresh.
        """
        full_url = self._build_url(url)
        
        # Inject token
        self._ensure_auth_header(kwargs)

        try:
            response = self._session.request(method, full_url, **kwargs)
            
            if response.status_code == 401:
                logger.info("Received 401 Unauthorized. Attempting to refresh token.")
                try:
                    # Attempt to refresh the token using the client
                    new_token = self.oauth_client.refresh_token()
                    
                    # Update header with new token
                    headers = kwargs.get("headers", {})
                    headers["Authorization"] = f"Bearer {new_token}"
                    kwargs["headers"] = headers
                    
                    # Retry the request
                    logger.info("Retrying request with new token.")
                    response = self._session.request(method, full_url, **kwargs)
                    
                except (AuthError, AuthNetworkError) as e:
                    logger.error(f"Failed to refresh token during retry: {e}")
                    # Allow the original 401 or the new error to bubble up? 
                    # Usually better to let the user know auth failed.
                    raise e
            
            return response

        except requests.RequestException as e:
            raise e

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self.request("DELETE", url, **kwargs)

    def _ensure_auth_header(self, request_kwargs: Dict[str, Any]):
        """Injects access token into headers."""
        headers = request_kwargs.get("headers", {})
        if "Authorization" not in headers:
            try:
                token = self.token_manager.get_token()
                headers["Authorization"] = f"Bearer {token}"
            except TokenExpiredError:
                # Proceeding without token might act as anonymous or fail later
                pass
        
        request_kwargs["headers"] = headers

    def _build_url(self, url: str) -> str:
        if self.base_url and not url.startswith("http"):
            return f"{self.base_url}/{url.lstrip('/')}"
        return url
