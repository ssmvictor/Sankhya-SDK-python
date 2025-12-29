# -*- coding: utf-8 -*-
"""
This module contains exceptions related to specific business operations.
"""

from typing import Any, Optional

from .base import ServiceRequestGeneralException
from .messages import (
    CONFIRM_INVOICE,
    INVALID_SERVICE_QUERY_OPTIONS,
    INVALID_SERVICE_REQUEST_OPERATION,
    MARK_AS_PAYMENT_PAID,
    MISSING_SERIALIZER_HELPER_ENTITY,
    NO_ITEMS_CONFIRM_INVOICE,
    OPEN_FILE,
    PAGED_REQUEST,
    REMOVE_INVOICE,
    SERVICE_RESPONSE_UNEXPECTED_ELEMENT,
    UNLINK_SHIPPING,
)
from ..enums.service_name import ServiceName


class ConfirmInvoiceException(ServiceRequestGeneralException):
    """
    Exception thrown when an invoice confirmation fails.
    """

    def __init__(
        self,
        single_number: int,
        request: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initializes a new instance of the ConfirmInvoiceException class.

        Args:
            single_number (int): The single number of the invoice that failed to confirm.
            request (Optional[Any]): The service request.
            inner_exception (Optional[Exception]): The cause of the failure.
        """
        super().__init__(
            CONFIRM_INVOICE.format(single_number), request, None, inner_exception
        )


class NoItemsConfirmInvoiceException(ServiceRequestGeneralException):
    """
    Exception thrown when an invoice has no items and cannot be confirmed.
    """

    def __init__(self, single_number: int, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the NoItemsConfirmInvoiceException class.

        Args:
            single_number (int): The single number of the invoice.
            request (Optional[Any]): The service request.
        """
        super().__init__(NO_ITEMS_CONFIRM_INVOICE.format(single_number), request)


class RemoveInvoiceException(ServiceRequestGeneralException):
    """
    Exception thrown when an invoice removal fails.
    """

    def __init__(
        self,
        single_number: int,
        request: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initializes a new instance of the RemoveInvoiceException class.

        Args:
            single_number (int): The single number of the invoice that failed to remove.
            request (Optional[Any]): The service request.
            inner_exception (Optional[Exception]): The cause of the failure.
        """
        super().__init__(
            REMOVE_INVOICE.format(single_number), request, None, inner_exception
        )


class MarkAsPaymentPaidException(ServiceRequestGeneralException):
    """
    Exception thrown when flagging payments as paid fails.
    """

    def __init__(
        self,
        financial_numbers: str,
        request: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initializes a new instance of the MarkAsPaymentPaidException class.

        Args:
            financial_numbers (str): The financial numbers that failed.
            request (Optional[Any]): The service request.
            inner_exception (Optional[Exception]): The cause of the failure.
        """
        super().__init__(
            MARK_AS_PAYMENT_PAID.format(financial_numbers),
            request,
            None,
            inner_exception,
        )


class UnlinkShippingException(ServiceRequestGeneralException):
    """
    Exception thrown when unlinking shipping fails.
    """

    def __init__(
        self,
        financial_numbers: str,
        request: Optional[Any] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initializes a new instance of the UnlinkShippingException class.

        Args:
            financial_numbers (str): The financial numbers that failed.
            request (Optional[Any]): The service request.
            inner_exception (Optional[Exception]): The cause of the failure.
        """
        super().__init__(
            UNLINK_SHIPPING.format(financial_numbers), request, None, inner_exception
        )


class PagedRequestException(ServiceRequestGeneralException):
    """
    Exception thrown when a paged request fails.
    """

    def __init__(
        self, request: Optional[Any] = None, inner_exception: Optional[Exception] = None
    ) -> None:
        """
        Initializes a new instance of the PagedRequestException class.

        Args:
            request (Optional[Any]): The paged request that failed.
            inner_exception (Optional[Exception]): The cause of the failure.
        """
        super().__init__(PAGED_REQUEST, request, None, inner_exception)


class InvalidServiceQueryOptionsException(Exception):
    """
    Exception thrown when invalid query options are provided for a service.
    """

    def __init__(self, service: ServiceName) -> None:
        """
        Initializes a new instance of the InvalidServiceQueryOptionsException class.

        Args:
            service (ServiceName): The service name.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(INVALID_SERVICE_QUERY_OPTIONS.format(human_readable))


class InvalidServiceRequestOperationException(Exception):
    """
    Exception thrown when a service request operation is invalid.
    """

    def __init__(self, service: ServiceName) -> None:
        """
        Initializes a new instance of the InvalidServiceRequestOperationException class.

        Args:
            service (ServiceName): The service name.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(INVALID_SERVICE_REQUEST_OPERATION.format(human_readable))


class MissingSerializerHelperEntityException(Exception):
    """
    Exception thrown when a serializer helper entity is missing.
    """

    def __init__(
        self, property_name: str, entity_name: str, fully_qualified_class_name: str
    ) -> None:
        """
        Initializes a new instance of the MissingSerializerHelperEntityException class.

        Args:
            property_name (str): The name of the property.
            entity_name (str): The name of the entity.
            fully_qualified_class_name (str): The fully qualified class name.
        """
        super().__init__(
            MISSING_SERIALIZER_HELPER_ENTITY.format(
                property_name, entity_name, fully_qualified_class_name
            )
        )


class OpenFileException(Exception):
    """
    Represents an exception that is thrown when a file cannot be opened.
    """

    def __init__(
        self, key: str, inner_exception: Optional[Exception] = None
    ) -> None:
        """
        Initializes a new instance of the OpenFileException class.

        Args:
            key (str): The key associated with the file.
            inner_exception (Optional[Exception]): The cause of the failure.
        """
        super().__init__(OPEN_FILE.format(key))
        self.__cause__ = inner_exception


class ServiceResponseUnexpectedElementException(Exception):
    """
    Exception thrown when a service response contains an unexpected element.
    """

    def __init__(
        self, element_name: str, service: ServiceName, response: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceResponseUnexpectedElementException class.

        Args:
            element_name (str): The name of the unexpected element.
            service (ServiceName): The service name.
            response (Optional[Any]): The service response.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(
            SERVICE_RESPONSE_UNEXPECTED_ELEMENT.format(element_name, human_readable)
        )
        self.response = response
