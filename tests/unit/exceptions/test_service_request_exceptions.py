# -*- coding: utf-8 -*-
from typing import Any, Optional
import pytest
from sankhya_sdk.exceptions import (
    ServiceRequestTimeoutException,
    ServiceRequestPropertyNameException,
    ServiceRequestPropertyValueException,
    ServiceRequestPropertyWidthException,
    ServiceRequestUnexpectedResultException,
)
from sankhya_sdk.enums.service_name import ServiceName

class MockEntity:
    def __init__(self, name: str) -> None:
        self.name: str = name

class MockRequestBody:
    def __init__(self, entity_name: str = "", data_set: Any = None) -> None:
        self.entity: MockEntity = MockEntity(entity_name)
        self.data_set: Any = data_set

class MockRequest:
    def __init__(self, service: ServiceName, entity_name: str = "", data_set: Any = None) -> None:
        self.service: ServiceName = service
        self.request_body: MockRequestBody = MockRequestBody(entity_name, data_set)

def test_service_request_timeout_exception() -> None:
    service: ServiceName = ServiceName.CRUD_FIND
    exc: ServiceRequestTimeoutException = ServiceRequestTimeoutException(service)
    assert "The call to the CRUD - Retrieve service has timed out" in str(exc)

def test_service_request_property_name_exception() -> None:
    mock_request: MockRequest = MockRequest(ServiceName.CRUD_SAVE, entity_name="Partner")
    
    exc: ServiceRequestPropertyNameException = ServiceRequestPropertyNameException("NomeParc", mock_request)
    assert "The call to the service CRUD - Create/Update couldn't find the field NomeParc on entity  in Partner entity request" in str(exc)
    
    exc_with_entity: ServiceRequestPropertyNameException = ServiceRequestPropertyNameException("NomeParc", mock_request, "AD_TEST")
    assert "The call to the service CRUD - Create/Update couldn't find the field NomeParc on entity AD_TEST in Partner entity request" in str(exc_with_entity)

def test_service_request_property_value_exception() -> None:
    mock_request: MockRequest = MockRequest(ServiceName.CRUD_FIND)
    
    exc: ServiceRequestPropertyValueException = ServiceRequestPropertyValueException("Code", "Partner", mock_request)
    assert "The call to the service CRUD - Retrieve couldn't find the field Code on entity Partner" in str(exc)

def test_service_request_property_width_exception() -> None:
    mock_request: MockRequest = MockRequest(ServiceName.CRUD_SAVE, entity_name="Partner")
    
    exc: ServiceRequestPropertyWidthException = ServiceRequestPropertyWidthException("Name", mock_request, 10, 20)
    assert "The call to the service CRUD - Create/Update couldn't be completed because the width of the value for the Name property on entity Partner is above that allowed. Current width: 20. Width allowed: 10" in str(exc)
    assert exc.property_name == "Name"
    assert exc.allowed_width == 10

def test_service_request_unexpected_result_exception() -> None:
    mock_request: MockRequest = MockRequest(ServiceName.LOGIN)
    
    exc: ServiceRequestUnexpectedResultException = ServiceRequestUnexpectedResultException(mock_request)
    assert "The call to the Login service resulted in an invalid response" in str(exc)
    
    exc_with_msg: ServiceRequestUnexpectedResultException = ServiceRequestUnexpectedResultException(mock_request, message="Error detail")
    assert "The call to the Login service resulted in the following uncaught error message: Error detail" in str(exc_with_msg)
    assert exc_with_msg.error_message == "Error detail"

from sankhya_sdk.exceptions import (
    ServiceRequestRepeatedException,
    ServiceRequestPaginationException,
    ServiceRequestUnavailableException,
    ServiceRequestUnbalancedDelimiterException,
    ServiceRequestDuplicatedDocumentException,
    ServiceRequestFullTransactionLogsException,
    ServiceRequestInvalidRelationException,
)

def test_other_advanced_exceptions() -> None:
    assert "You can not use a managed request object that was already consumed" in str(ServiceRequestRepeatedException())
    assert "Unable to complete the paged request" in str(ServiceRequestPaginationException())
    assert "The call to the Login service is currently unavailable" in str(ServiceRequestUnavailableException(ServiceName.LOGIN))
    assert "There is an unbalanced delimiter in the request" in str(ServiceRequestUnbalancedDelimiterException())
    assert "The partner John Doe has the document duplicated with another partner" in str(ServiceRequestDuplicatedDocumentException("John Doe"))
    assert "The transaction logs of 'SANKHYA' database is full" in str(ServiceRequestFullTransactionLogsException("SANKHYA"))
    assert "The relation Items of entity Invoice cannot be found on Sankhya" in str(ServiceRequestInvalidRelationException("Items", "Invoice"))
