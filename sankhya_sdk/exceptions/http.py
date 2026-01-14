"""
HTTP-specific exceptions for Sankhya Gateway.

These exceptions map to specific HTTP status codes returned by the API.
"""

from sankhya_sdk.exceptions.base import SankhyaException


class SankhyaHttpError(SankhyaException):
    """Base class for HTTP-related errors."""
    
    def __init__(self, message: str, status_code: int, response_body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        return f"[HTTP {self.status_code}] {super().__str__()}"


class SankhyaAuthError(SankhyaHttpError):
    """
    Authentication error (HTTP 401).
    
    Token expired, invalid, or missing.
    """
    
    def __init__(self, message: str = "Authentication required", response_body: str = ""):
        super().__init__(message, status_code=401, response_body=response_body)


class SankhyaForbiddenError(SankhyaHttpError):
    """
    Authorization error (HTTP 403).
    
    User authenticated but lacks permission.
    """
    
    def __init__(self, message: str = "Access forbidden", response_body: str = ""):
        super().__init__(message, status_code=403, response_body=response_body)


class SankhyaNotFoundError(SankhyaHttpError):
    """
    Resource not found (HTTP 404).
    
    Requested entity or service does not exist.
    """
    
    def __init__(self, message: str = "Resource not found", response_body: str = ""):
        super().__init__(message, status_code=404, response_body=response_body)


class SankhyaClientError(SankhyaHttpError):
    """
    Client error (HTTP 4xx).
    
    Generic client-side error not covered by specific exceptions.
    """
    pass


class SankhyaServerError(SankhyaHttpError):
    """
    Server error (HTTP 5xx).
    
    Error on the Sankhya server side.
    """
    pass


def raise_for_status(status_code: int, response_body: str = "") -> None:
    """
    Raise appropriate exception based on HTTP status code.
    
    Args:
        status_code: HTTP status code from response.
        response_body: Response body for error context.
        
    Raises:
        SankhyaAuthError: On 401.
        SankhyaForbiddenError: On 403.
        SankhyaNotFoundError: On 404.
        SankhyaClientError: On other 4xx.
        SankhyaServerError: On 5xx.
    """
    if 200 <= status_code < 400:
        return
    
    if status_code == 401:
        raise SankhyaAuthError(response_body=response_body)
    elif status_code == 403:
        raise SankhyaForbiddenError(response_body=response_body)
    elif status_code == 404:
        raise SankhyaNotFoundError(response_body=response_body)
    elif 400 <= status_code < 500:
        raise SankhyaClientError(
            f"Client error: {response_body}", 
            status_code=status_code, 
            response_body=response_body
        )
    elif status_code >= 500:
        raise SankhyaServerError(
            f"Server error: {response_body}", 
            status_code=status_code, 
            response_body=response_body
        )
