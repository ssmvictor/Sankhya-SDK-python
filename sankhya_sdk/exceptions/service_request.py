# -*- coding: utf-8 -*-
"""
This module contains exceptions related to service requests.
"""

from typing import Any, Optional

from .base import ServiceRequestGeneralException
from .intermediate import ServiceRequestTemporarilyException
from .messages import (
    SERVICE_REQUEST_ATTRIBUTE,
    SERVICE_REQUEST_BUSINESS_RULE_RESTRICTION,
    SERVICE_REQUEST_CANCELED_QUERY,
    SERVICE_REQUEST_EXTERNAL,
    SERVICE_REQUEST_FILE_NOT_FOUND,
    SERVICE_REQUEST_FOREIGN_KEY,
    SERVICE_REQUEST_INACCESSIBLE,
    SERVICE_REQUEST_INVALID_EXPRESSION,
    SERVICE_REQUEST_INVALID_SUBQUERY,
    SERVICE_REQUEST_PARTNER_FISCAL_CLASSIFICATION,
    SERVICE_REQUEST_PARTNER_INVALID_DOCUMENT_LENGTH,
    SERVICE_REQUEST_PARTNER_STATE_INSCRIPTION,
    SERVICE_REQUEST_PROPERTY_NAME,
    SERVICE_REQUEST_PROPERTY_VALUE,
    SERVICE_REQUEST_PROPERTY_WIDTH,
    SERVICE_REQUEST_TIMEOUT,
)
from ..enums.service_name import ServiceName


class ServiceRequestTimeoutException(ServiceRequestTemporarilyException):
    """
    Exception thrown when a service request times out.
    """

    def __init__(self, service: ServiceName, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestTimeoutException class.

        Args:
            service (ServiceName): The service that timed out.
            request (Optional[Any]): The service request that caused the timeout.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(SERVICE_REQUEST_TIMEOUT.format(human_readable), request)


class ServiceRequestPropertyNameException(ServiceRequestGeneralException):
    """
    Represents an exception that is thrown when there is an issue with a property name in a service request.
    """

    def __init__(
        self,
        property_name: str,
        request: Optional[Any] = None,
        entity_name: str = "",
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestPropertyNameException class.

        Args:
            property_name (str): The name of the property that caused the exception.
            request (Optional[Any]): The service request that caused the exception.
            entity_name (str): The name of the entity that caused the exception.
        """
        service_name = "Unknown"
        root_entity = "Unknown"
        if request is not None:
            if hasattr(request, "service") and isinstance(request.service, ServiceName):
                service_name = request.service.metadata.human_readable
            
            # Attempt to extract entity name from request body if available
            if hasattr(request, "request_body"):
                body = request.request_body
                if hasattr(body, "entity") and body.entity is not None:
                    root_entity = getattr(body.entity, "name", getattr(body.entity, "root_entity", "Unknown"))
                elif hasattr(body, "data_set") and body.data_set is not None:
                    root_entity = getattr(body.data_set, "root_entity", "Unknown")

        message = SERVICE_REQUEST_PROPERTY_NAME.format(
            service_name, property_name, entity_name, root_entity
        )
        super().__init__(message, request)


class ServiceRequestPropertyValueException(ServiceRequestGeneralException):
    """
    Exception thrown when there is an issue with a property value in a service request.
    """

    def __init__(
        self, property_name: str, entity_name: str, request: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestPropertyValueException class.

        Args:
            property_name (str): The name of the property.
            entity_name (str): The name of the entity.
            request (Optional[Any]): The service request.
        """
        service_name = "Unknown"
        if request is not None and hasattr(request, "service") and isinstance(request.service, ServiceName):
            service_name = request.service.metadata.human_readable
            
        super().__init__(
            SERVICE_REQUEST_PROPERTY_VALUE.format(service_name, property_name, entity_name),
            request,
        )


class ServiceRequestPropertyWidthException(ServiceRequestGeneralException):
    """
    Exception thrown when a property width exceeds the allowed limit in a service request.
    """

    def __init__(
        self,
        property_name: str,
        request: Optional[Any],
        width_allowed: int,
        current_width: int,
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestPropertyWidthException class.

        Args:
            property_name (str): The name of the property that exceeded the width limit.
            request (Optional[Any]): The service request that contains the property.
            width_allowed (int): The maximum allowed width for the property.
            current_width (int): The current width of the property.
        """
        service_name = "Unknown"
        root_entity = "Unknown"
        if request is not None:
            if hasattr(request, "service") and isinstance(request.service, ServiceName):
                service_name = request.service.metadata.human_readable
            
            if hasattr(request, "request_body"):
                body = request.request_body
                if hasattr(body, "entity") and body.entity is not None:
                    root_entity = getattr(body.entity, "name", getattr(body.entity, "root_entity", "Unknown"))
                elif hasattr(body, "data_set") and body.data_set is not None:
                    root_entity = getattr(body.data_set, "root_entity", "Unknown")

        super().__init__(
            SERVICE_REQUEST_PROPERTY_WIDTH.format(
                service_name, property_name, root_entity, current_width, width_allowed
            ),
            request,
        )
        self.property_name = property_name
        self.allowed_width = width_allowed


class ServiceRequestAttributeException(ServiceRequestGeneralException):
    """
    Exception thrown when a service request is missing a required attribute.
    """

    def __init__(
        self, service: ServiceName, attribute_name: str, request: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestAttributeException class.

        Args:
            service (ServiceName): The service name.
            attribute_name (str): The missing attribute name.
            request (Optional[Any]): The service request.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(
            SERVICE_REQUEST_ATTRIBUTE.format(human_readable, attribute_name), request
        )


class ServiceRequestBusinessRuleRestrictionException(ServiceRequestGeneralException):
    """
    Exception thrown when a business rule restricts a service request.
    """

    def __init__(
        self, rule_name: str, message: str, request: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestBusinessRuleRestrictionException class.

        Args:
            rule_name (str): The name of the business rule.
            message (str): The error message from the business rule.
            request (Optional[Any]): The service request.
        """
        super().__init__(
            SERVICE_REQUEST_BUSINESS_RULE_RESTRICTION.format(rule_name, message), request
        )


class ServiceRequestCanceledQueryException(ServiceRequestGeneralException):
    """
    Exception thrown when a query is canceled due to server overload.
    """

    def __init__(self, seconds: int, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestCanceledQueryException class.

        Args:
            seconds (int): The number of seconds to wait before retrying.
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_CANCELED_QUERY.format(seconds), request)


class ServiceRequestExternalException(ServiceRequestGeneralException):
    """
    Exception thrown when an internal Sankhya error occurs.
    """

    def __init__(self, service: ServiceName, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestExternalException class.

        Args:
            service (ServiceName): The service name.
            request (Optional[Any]): The service request.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(SERVICE_REQUEST_EXTERNAL.format(human_readable), request)


class ServiceRequestForeignKeyException(ServiceRequestGeneralException):
    """
    Exception thrown when a foreign key reference is invalid.
    """

    def __init__(
        self, entity_name: str, property_name: str, request: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestForeignKeyException class.

        Args:
            entity_name (str): The name of the entity.
            property_name (str): The name of the property.
            request (Optional[Any]): The service request.
        """
        super().__init__(
            SERVICE_REQUEST_FOREIGN_KEY.format(entity_name, property_name), request
        )


class ServiceRequestFileNotFoundException(ServiceRequestGeneralException):
    """
    Exception thrown when a file is not found.
    """

    def __init__(self, file_path: str, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestFileNotFoundException class.

        Args:
            file_path (str): The path to the file.
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_FILE_NOT_FOUND.format(file_path), request)


class ServiceRequestInaccessibleException(ServiceRequestGeneralException):
    """
    Exception thrown when the Sankhya server is inaccessible.
    """

    def __init__(self, host: str, port: int, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestInaccessibleException class.

        Args:
            host (str): The server host.
            port (int): The server port.
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_INACCESSIBLE.format(host, port), request)


class ServiceRequestInvalidExpressionException(ServiceRequestGeneralException):
    """
    Exception thrown when a filter expression is invalid.
    """

    def __init__(self, expression: str, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestInvalidExpressionException class.

        Args:
            expression (str): The invalid expression.
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_INVALID_EXPRESSION.format(expression), request)


class ServiceRequestInvalidSubqueryException(ServiceRequestGeneralException):
    """
    Exception thrown when a subquery returns more than one value.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestInvalidSubqueryException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_INVALID_SUBQUERY, request)


class ServiceRequestPartnerInvalidDocumentLengthException(
    ServiceRequestGeneralException
):
    """
    Exception thrown when a partner document has an invalid length.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestPartnerInvalidDocumentLengthException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_PARTNER_INVALID_DOCUMENT_LENGTH, request)


class ServiceRequestPartnerStateInscriptionException(ServiceRequestGeneralException):
    """
    Exception thrown when a partner state inscription is invalid.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestPartnerStateInscriptionException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_PARTNER_STATE_INSCRIPTION, request)


class ServiceRequestPartnerFiscalClassificationException(
    ServiceRequestGeneralException
):
    """
    Exception thrown when a partner fiscal classification is invalid.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestPartnerFiscalClassificationException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_PARTNER_FISCAL_CLASSIFICATION, request)
