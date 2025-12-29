# -*- coding: utf-8 -*-
"""
This module contains the base exceptions and interfaces for the Sankhya SDK.
"""

from typing import Any, Optional, Protocol, runtime_checkable

from .messages import SERVICE_REQUEST_GENERAL


@runtime_checkable
class IXmlServiceException(Protocol):
    """
    Protocol for exceptions that provide XML representations of service requests and responses.
    """

    @property
    def request_xml(self) -> Optional[str]:
        """
        Gets the XML representation of the service request.

        Returns:
            Optional[str]: The XML representation of the service request, or None.
        """
        ...

    @property
    def response_xml(self) -> Optional[str]:
        """
        Gets the XML representation of the service response.

        Returns:
            Optional[str]: The XML representation of the service response, or None.
        """
        ...


class SankhyaException(Exception):
    """
    Base exception class for all Sankhya SDK exceptions.
    """

    pass


class ServiceRequestGeneralException(SankhyaException):
    """
    Represents a general exception that occurs during a service request.

    Attributes:
        request (Optional[Any]): The service request associated with the exception.
        response (Optional[Any]): The service response associated with the exception.
    """

    def __init__(
        self,
        message: str = SERVICE_REQUEST_GENERAL,
        request: Optional[Any] = None,
        response: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestGeneralException class.

        Args:
            message (str): The error message that explains the reason for the exception.
            request (Optional[Any]): The service request associated with the exception.
            response (Optional[Any]): The service response associated with the exception.
            inner_exception (Optional[Exception]): The exception that is the cause of the current exception.
        """
        super().__init__(message)
        self._request = request
        self._response = response
        self.__cause__ = inner_exception

    @property
    def request(self) -> Optional[Any]:
        """
        Gets the service request associated with the exception.

        Returns:
            Optional[Any]: The service request.
        """
        return self._request

    @property
    def response(self) -> Optional[Any]:
        """
        Gets the service response associated with the exception.

        Returns:
            Optional[Any]: The service response.
        """
        return self._response

    @property
    def request_xml(self) -> Optional[str]:
        """
        Gets the XML representation of the service request.

        Returns:
            Optional[str]: The XML representation of the service request, or None.
        """
        if self._request is not None and hasattr(self._request, "get_serializer"):
            # This will be properly implemented when ServiceRequest is available
            serializer = self._request.get_serializer()
            if hasattr(serializer, "to_xml"):
                return serializer.to_xml()
        return None

    @property
    def response_xml(self) -> Optional[str]:
        """
        Gets the XML representation of the service response.

        Returns:
            Optional[str]: The XML representation of the service response, or None.
        """
        if self._response is not None and hasattr(self._response, "get_serializer"):
            # This will be properly implemented when ServiceResponse is available
            serializer = self._response.get_serializer()
            if hasattr(serializer, "to_xml"):
                return serializer.to_xml()
        return None
