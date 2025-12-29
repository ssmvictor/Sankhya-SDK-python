# -*- coding: utf-8 -*-
"""
This module contains intermediate exceptions that serve as base classes or implement protocols.
"""

from typing import Any, Optional

from .base import IXmlServiceException, ServiceRequestGeneralException
from .messages import SERVICE_REQUEST_INVALID_OPERATION


class ServiceRequestTemporarilyException(ServiceRequestGeneralException):
    """
    Represents an exception that is thrown when a service request fails temporarily.
    """

    def __init__(
        self,
        message: str,
        request: Optional[Any] = None,
        response: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestTemporarilyException class.

        Args:
            message (str): The error message that explains the reason for the exception.
            request (Optional[Any]): The service request that caused the exception.
            response (Optional[Any]): The service response associated with the exception.
            inner_exception (Optional[Exception]): The exception that is the cause of the current exception.
        """
        super().__init__(message, request, response, inner_exception)


class ServiceRequestInvalidOperationException(Exception, IXmlServiceException):
    """
    Exception thrown when a service request operation is invalid.
    """

    def __init__(
        self, response_xml_obj: Any, inner_exception: Optional[Exception] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestInvalidOperationException class.

        Args:
            response_xml_obj (Any): The XML object containing the response.
            inner_exception (Optional[Exception]): The exception that caused the current exception.
        """
        super().__init__(SERVICE_REQUEST_INVALID_OPERATION)
        self._response_xml_obj = response_xml_obj
        self.__cause__ = inner_exception

    @property
    def request_xml(self) -> Optional[str]:
        """
        Gets the XML representation of the service request.

        Returns:
            Optional[str]: None as this exception typically doesn't have the request XML in the same way.
        """
        return None

    @property
    def response_xml(self) -> Optional[str]:
        """
        Gets the XML representation of the service response.

        Returns:
            Optional[str]: The XML representation of the service response.
        """
        if self._response_xml_obj is not None and hasattr(
            self._response_xml_obj, "to_xml"
        ):
            return self._response_xml_obj.to_xml()
        return str(self._response_xml_obj)
