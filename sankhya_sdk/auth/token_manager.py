import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

from sankhya_sdk.auth.exceptions import TokenExpiredError

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Manages OAuth2 access and refresh tokens.
    Handles storage, expiration checking, and in-memory persistence.
    
    Thread-safe: All operations are protected by a lock for concurrent access.
    
    Expiration Buffer: Tokens are considered expired 60 seconds before actual
    expiration to prevent race conditions and ensure smooth operation.
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None
        self._lock = threading.Lock()  # Thread-safe token operations

    def set_tokens(
        self,
        access_token: str,
        expires_in: int,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Stores tokens and calculates expiration time.
        
        Thread-safe operation.
        
        Args:
            access_token: The OAuth2 access token.
            expires_in: Token validity in seconds.
            refresh_token: Optional refresh token.
            client_id: Optional client_id (for automatic re-auth).
            client_secret: Optional client_secret (for automatic re-auth).
        """
        with self._lock:
            self._access_token = access_token
            self._expires_at = datetime.now() + timedelta(seconds=expires_in)
            if refresh_token:
                self._refresh_token = refresh_token
            
            if client_id:
                self._client_id = client_id
            if client_secret:
                self._client_secret = client_secret

            logger.debug(f"Token update: expires at {self._expires_at}")

    def get_token(self) -> str:
        """
        Returns a valid access token.
        Raises TokenExpiredError if expired (logic to refresh handled by caller/client or explicit refresh call).
        
        Thread-safe operation.
        
        Returns:
            str: Valid access token.
            
        Raises:
            TokenExpiredError: If token is expired or missing.
        """
        with self._lock:
            if not self._access_token:
                raise TokenExpiredError("No access token available. Please authenticate.")

            # Check expiration WITHOUT calling is_expired() to avoid nested lock
            if not self._expires_at:
                raise TokenExpiredError("Access token expired.")
            
            if datetime.now() >= (self._expires_at - timedelta(seconds=60)):
                raise TokenExpiredError("Access token expired.")

            return self._access_token

    def is_expired(self) -> bool:
        """
        Checks if the access token is expired.
        
        Uses a 60-second safety buffer: tokens are considered expired
        60 seconds before their actual expiration time to prevent race
        conditions and ensure smooth token refresh.
        
        Thread-safe operation.
        
        Returns:
            bool: True if token is expired or will expire within 60 seconds.
        """
        with self._lock:
            if not self._expires_at:
                return True
            # Consider expired if within 60 seconds of expiration to be safe
            return datetime.now() >= (self._expires_at - timedelta(seconds=60))

    def get_refresh_token(self) -> Optional[str]:
        """Returns the refresh token. Thread-safe."""
        with self._lock:
            return self._refresh_token

    def get_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Returns stored credentials. Thread-safe."""
        with self._lock:
            return self._client_id, self._client_secret
    
    def clear(self):
        """Clears all stored tokens and credentials. Thread-safe."""
        with self._lock:
            self._access_token = None
            self._refresh_token = None
            self._expires_at = None
            self._client_id = None
            self._client_secret = None
