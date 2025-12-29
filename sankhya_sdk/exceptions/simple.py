# -*- coding: utf-8 -*-
"""
This module contains simple exceptions that inherit directly from Exception.
"""

from typing import Optional

from .messages import (
    CANCELLED_ON_DEMAND_REQUEST_WRAPPER,
    INVALID_KEY_FILE,
    SERVICE_REQUEST_EXPIRED_AUTHENTICATION,
    SERVICE_REQUEST_INVALID_AUTHORIZATION,
    SERVICE_REQUEST_INVALID_CREDENTIALS,
    TOO_INNER_LEVELS,
)


class InvalidKeyFileException(Exception):
    """
    Exception thrown when an invalid key file is encountered.
    """

    def __init__(self, key: str) -> None:
        """
        Initializes a new instance of the InvalidKeyFileException class.

        Args:
            key (str): The key that caused the exception.
        """
        super().__init__(INVALID_KEY_FILE.format(key))


class ServiceRequestInvalidAuthorizationException(Exception):
    """
    Exception thrown when a service request has invalid authorization.
    """

    def __init__(self, inner_exception: Optional[Exception] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestInvalidAuthorizationException class.

        Args:
            inner_exception (Optional[Exception]): The exception that is the cause of the current exception.
        """
        super().__init__(SERVICE_REQUEST_INVALID_AUTHORIZATION)
        self.__cause__ = inner_exception


class CanceledOnDemandRequestWrapperException(Exception):
    """
    Exception thrown when attempting to add items to a cancelled on-demand request wrapper.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the CanceledOnDemandRequestWrapperException class.
        """
        super().__init__(CANCELLED_ON_DEMAND_REQUEST_WRAPPER)


class ServiceRequestExpiredAuthenticationException(Exception):
    """
    Exception thrown when the user's session is expired.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the ServiceRequestExpiredAuthenticationException class.
        """
        super().__init__(SERVICE_REQUEST_EXPIRED_AUTHENTICATION)


class ServiceRequestInvalidCredentialsException(Exception):
    """
    Exception thrown when authentication fails with provided credentials.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the ServiceRequestInvalidCredentialsException class.
        """
        super().__init__(SERVICE_REQUEST_INVALID_CREDENTIALS)


class TooInnerLevelsException(Exception):
    """
    Exception thrown when a service request contains too many inner entity references.
    """

    def __init__(self, entity_name: str) -> None:
        """
        Initializes a new instance of the TooInnerLevelsException class.

        Args:
            entity_name (str): The name of the entity that has too many inner references.
        """
        super().__init__(TOO_INNER_LEVELS.format(entity_name))
