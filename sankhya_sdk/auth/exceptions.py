class AuthError(Exception):
    """Base exception for authentication errors."""
    def __init__(self, message: str, code: str = None, status_code: int = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class TokenExpiredError(AuthError):
    """Raised when the access token has expired and cannot be refreshed."""
    pass


class AuthNetworkError(AuthError):
    """Raised when there are network issues during authentication."""
    pass
