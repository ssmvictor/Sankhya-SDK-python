# -*- coding: utf-8 -*-
"""
This module contains advanced exceptions related to service requests.
"""

from typing import Any, Optional

from .base import ServiceRequestGeneralException
from .intermediate import ServiceRequestTemporarilyException
from .messages import (
    SERVICE_REQUEST_COMPETITION,
    SERVICE_REQUEST_DUPLICATED_DOCUMENT,
    SERVICE_REQUEST_FULL_TRANSACTION_LOGS,
    SERVICE_REQUEST_INVALID_RELATION,
    SERVICE_REQUEST_PAGINATION,
    SERVICE_REQUEST_REPEATED,
    SERVICE_REQUEST_TOO_MANY_RESULTS,
    SERVICE_REQUEST_UNAVAILABLE,
    SERVICE_REQUEST_UNBALANCED_DELIMITER,
    SERVICE_REQUEST_UNEXPECTED_RESULT,
    SERVICE_REQUEST_UNEXPECTED_RESULT_UNCAUGHT,
)
from ..enums.service_name import ServiceName


class ServiceRequestRepeatedException(ServiceRequestGeneralException):
    """
    Exception thrown when a managed request object that was already consumed is used again.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestRepeatedException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_REPEATED, request)


class ServiceRequestPaginationException(ServiceRequestGeneralException):
    """
    Exception thrown when a paged request fails due to concurrent requests.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestPaginationException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_PAGINATION, request)


class ServiceRequestTooManyResultsException(ServiceRequestGeneralException):
    """
    Exception thrown when a service request returns more results than expected.
    """

    def __init__(
        self, result_length: int, request: Optional[Any] = None, response: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestTooManyResultsException class.

        Args:
            result_length (int): The number of results returned.
            request (Optional[Any]): The service request.
            response (Optional[Any]): The service response.
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
            SERVICE_REQUEST_TOO_MANY_RESULTS.format(service_name, root_entity, result_length),
            request,
            response,
        )


class ServiceRequestUnavailableException(ServiceRequestGeneralException):
    """
    Exception thrown when a service is currently unavailable.
    """

    def __init__(self, service: ServiceName, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestUnavailableException class.

        Args:
            service (ServiceName): The service name.
            request (Optional[Any]): The service request.
        """
        human_readable = service.metadata.human_readable if hasattr(service, "metadata") else str(service)
        super().__init__(SERVICE_REQUEST_UNAVAILABLE.format(human_readable), request)


class ServiceRequestUnbalancedDelimiterException(ServiceRequestGeneralException):
    """
    Exception thrown when there is an unbalanced delimiter in the request.
    """

    def __init__(self, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestUnbalancedDelimiterException class.

        Args:
            request (Optional[Any]): The service request.
        """
        super().__init__(SERVICE_REQUEST_UNBALANCED_DELIMITER, request)


class ServiceRequestUnexpectedResultException(ServiceRequestGeneralException):
    """
    Exception thrown when a service request returns an unexpected result.
    """

    def __init__(
        self,
        request: Optional[Any] = None,
        response: Optional[Any] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestUnexpectedResultException class.

        Args:
            request (Optional[Any]): The service request.
            response (Optional[Any]): The service response.
            message (Optional[str]): An optional error message explaining why the result was unexpected.
        """
        self.error_message = message or ""
        service_name = self._get_service_name(request)

        if message:
            fmt_message = SERVICE_REQUEST_UNEXPECTED_RESULT_UNCAUGHT.format(
                service_name, message
            )
        else:
            fmt_message = SERVICE_REQUEST_UNEXPECTED_RESULT.format(service_name)

        super().__init__(fmt_message, request, response)

    @staticmethod
    def _get_service_name(request: Optional[Any]) -> str:
        if request is None:
            return "Unknown"
        
        service_name = "Unknown"
        if hasattr(request, "service") and isinstance(request.service, ServiceName):
            service_name = request.service.metadata.human_readable
        
        entity = ""
        if hasattr(request, "request_body"):
            body = request.request_body
            if hasattr(body, "data_set") and body.data_set is not None:
                entity = getattr(body.data_set, "root_entity", "")
        
        if entity:
            service_name += f" ({entity})"
        
        return service_name


class ServiceRequestDuplicatedDocumentException(ServiceRequestGeneralException):
    """
    Exception thrown when a partner has a duplicated document.
    """

    def __init__(self, partner_name: str, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestDuplicatedDocumentException class.

        Args:
            partner_name (str): The name of the partner.
            request (Optional[Any]): The service request.
        """
        super().__init__(
            SERVICE_REQUEST_DUPLICATED_DOCUMENT.format(partner_name), request
        )


class ServiceRequestFullTransactionLogsException(ServiceRequestGeneralException):
    """
    Exception thrown when the transaction logs of a database are full.
    """

    def __init__(self, database_name: str, request: Optional[Any] = None) -> None:
        """
        Initializes a new instance of the ServiceRequestFullTransactionLogsException class.

        Args:
            database_name (str): The name of the database.
            request (Optional[Any]): The service request.
        """
        super().__init__(
            SERVICE_REQUEST_FULL_TRANSACTION_LOGS.format(database_name), request
        )


class ServiceRequestInvalidRelationException(ServiceRequestGeneralException):
    """
    Exception thrown when a relation cannot be found.
    """

    def __init__(
        self, relation_name: str, entity_name: str, request: Optional[Any] = None
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestInvalidRelationException class.

        Args:
            relation_name (str): The name of the relation.
            entity_name (str): The name of the entity.
            request (Optional[Any]): The service request.
        """
        super().__init__(
            SERVICE_REQUEST_INVALID_RELATION.format(relation_name, entity_name), request
        )


class ServiceRequestCompetitionException(ServiceRequestTemporarilyException):
    """
    Exception thrown when a competition/concurrency error occurs during the service request.

    This exception indicates that multiple concurrent requests are competing for the same
    resource, which may require retry with appropriate backoff.
    """

    def __init__(
        self,
        request: Optional[Any] = None,
        response: Optional[Any] = None,
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestCompetitionException class.

        Args:
            request (Optional[Any]): The service request that caused the exception.
            response (Optional[Any]): The service response associated with the exception.
        """
        super().__init__(SERVICE_REQUEST_COMPETITION, request, response)


class ServiceRequestDeadlockException(ServiceRequestTemporarilyException):
    """
    Exception thrown when a deadlock occurs during a transaction.

    This exception indicates that a deadlock was detected in the database transaction,
    which typically requires retry with appropriate backoff.
    """

    def __init__(
        self,
        message: str,
        request: Optional[Any] = None,
        response: Optional[Any] = None,
    ) -> None:
        """
        Initializes a new instance of the ServiceRequestDeadlockException class.

        Args:
            message (str): The error message describing the deadlock condition.
            request (Optional[Any]): The service request that caused the exception.
            response (Optional[Any]): The service response associated with the exception.
        """
        super().__init__(message, request, response)
