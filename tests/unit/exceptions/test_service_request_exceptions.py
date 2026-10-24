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


# =============================================================================
# Paridade de construtores com o .NET (Src/Sankhya/GoodPractices/*.cs)
# =============================================================================

from sankhya_sdk.exceptions import (
    ServiceRequestBusinessRuleRestrictionException,
    ServiceRequestCanceledQueryException,
    ServiceRequestCompetitionException,
    ServiceRequestFileNotFoundException,
    ServiceRequestForeignKeyException,
    ServiceRequestInvalidExpressionException,
)
from sankhya_sdk.models.service.basic_types import LiteralCriteria
from sankhya_sdk.models.service.entity_types import DataSet, Entity
from sankhya_sdk.models.service.metadata_types import Config
from sankhya_sdk.models.service.service_request import ServiceRequest


class MockDataSet:
    def __init__(self, root_entity: str) -> None:
        self.root_entity: str = root_entity


def test_property_value_exception_resolves_entity_from_request() -> None:
    """.NET: ServiceRequestPropertyValueException(propertyName, request) obtém a
    entidade de RequestBody.Entity?.Name ?? Entity?.RootEntity ?? DataSet.RootEntity."""
    mock_request: MockRequest = MockRequest(ServiceName.CRUD_FIND, entity_name="Parceiro")

    exc = ServiceRequestPropertyValueException("CODPARC", request=mock_request)

    assert str(exc) == "The call to the service CRUD - Retrieve couldn't find the field CODPARC on entity Parceiro"
    assert exc.property_name == "CODPARC"
    assert exc.request is mock_request


def test_property_value_exception_falls_back_to_data_set_root_entity() -> None:
    mock_request: MockRequest = MockRequest(
        ServiceName.CRUD_SERVICE_FIND, data_set=MockDataSet("Produto")
    )

    exc = ServiceRequestPropertyValueException("CODPROD", request=mock_request)

    assert str(exc) == (
        "The call to the service CRUD Service Provider - Retrieve couldn't find the field CODPROD on entity Produto"
    )


def test_property_value_exception_keeps_explicit_entity_name() -> None:
    exc = ServiceRequestPropertyValueException("Code", "Partner", MockRequest(ServiceName.CRUD_FIND, entity_name="Other"))

    assert "couldn't find the field Code on entity Partner" in str(exc)
    assert exc.property_name == "Code"


def test_invalid_expression_exception_resolves_expression_from_data_set() -> None:
    """.NET: ServiceRequestInvalidExpressionException(request, response) usa
    RequestBody.DataSet.LiteralCriteria.Expression no CRUDServiceProvider.loadRecords."""
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    request.request_body.data_set = DataSet(
        root_entity="Parceiro", literal_criteria=LiteralCriteria(expression="CODPARC = ")
    )
    response: object = object()

    exc = ServiceRequestInvalidExpressionException(request=request, response=response)

    assert str(exc) == "The filter expression 'CODPARC = ' is invalid, check if it is a valid SQL expression!"
    assert exc.request is request
    assert exc.response is response


def test_invalid_expression_exception_resolves_expression_from_entity() -> None:
    """.NET: nos demais serviços usa RequestBody.Entity.LiteralCriteria.Expression."""
    request = ServiceRequest(service=ServiceName.CRUD_FIND)
    request.request_body.entity = Entity(
        name="Parceiro", literal_criteria=LiteralCriteria(expression="NOMEPARC LIKE")
    )

    exc = ServiceRequestInvalidExpressionException(request=request)

    assert "The filter expression 'NOMEPARC LIKE' is invalid" in str(exc)


def test_invalid_expression_exception_keeps_explicit_expression() -> None:
    exc = ServiceRequestInvalidExpressionException("A = B", None)

    assert "The filter expression 'A = B' is invalid" in str(exc)


def test_canceled_query_exception_uses_message_as_is() -> None:
    """.NET: ServiceRequestCanceledQueryException(message, request) usa a mensagem
    de status recebida, sem formatação."""
    request: object = object()
    response: object = object()

    exc = ServiceRequestCanceledQueryException(
        message="A consulta foi cancelada.", request=request, response=response
    )

    assert str(exc) == "A consulta foi cancelada."
    assert exc.request is request
    assert exc.response is response


def test_canceled_query_exception_keeps_seconds_message() -> None:
    exc = ServiceRequestCanceledQueryException(15)

    assert str(exc) == "Query canceled, probably overloaded on server. Taking 15 seconds to retry."


def test_file_not_found_exception_resolves_path_from_request() -> None:
    """.NET: ServiceRequestFileNotFoundException(request) usa RequestBody.Config.Path."""
    request = ServiceRequest(service=ServiceName.CRUD_FIND)
    request.request_body.config = Config(path="Repo/Contratos/contrato.pdf")

    exc = ServiceRequestFileNotFoundException(request=request)

    assert str(exc) == "Unable to load the file from path Repo/Contratos/contrato.pdf. File or directory not found."
    assert exc.request is request


def test_file_not_found_exception_keeps_explicit_path() -> None:
    exc = ServiceRequestFileNotFoundException("ABC123")

    assert str(exc) == "Unable to load the file from path ABC123. File or directory not found."


def test_file_not_found_exception_without_request() -> None:
    exc = ServiceRequestFileNotFoundException(request=None)

    assert str(exc) == "Unable to load the file from path . File or directory not found."


def test_foreign_key_exception_keeps_response() -> None:
    """.NET: ServiceRequestForeignKeyException(table, column, request, response)."""
    request: object = object()
    response: object = object()

    exc = ServiceRequestForeignKeyException("TGFPAR", "CODCID", request, response)

    assert str(exc) == "The value supplied to TGFPAR.CODCID reference isn't valid."
    assert exc.request is request
    assert exc.response is response


def test_duplicated_document_exception_keeps_response() -> None:
    """.NET: ServiceRequestDuplicatedDocumentException(name, request, response)."""
    response: object = object()

    exc = ServiceRequestDuplicatedDocumentException("João", None, response)

    assert str(exc) == "The partner João has the document duplicated with another partner"
    assert exc.response is response


def test_business_rule_restriction_exception_keeps_response_and_properties() -> None:
    """.NET: ServiceRequestBusinessRuleRestrictionException(businessRuleName, errorMessage,
    request, response) expõe BusinessRuleName e ErrorMessage."""
    response: object = object()

    exc = ServiceRequestBusinessRuleRestrictionException(
        "Validação de Crédito", "Limite excedido.", None, response
    )

    assert str(exc) == (
        "The business rule Validação de Crédito doesn't allow the request to be completed. "
        "Error message: Limite excedido."
    )
    assert exc.business_rule_name == "Validação de Crédito"
    assert exc.error_message == "Limite excedido."
    assert exc.response is response


def test_full_transaction_logs_exception_keeps_response_and_database() -> None:
    """.NET: ServiceRequestFullTransactionLogsException(database, request, response)
    expõe Database."""
    response: object = object()

    exc = ServiceRequestFullTransactionLogsException("SANKHYA", None, response)

    assert exc.database == "SANKHYA"
    assert exc.response is response


def test_competition_exception_message_matches_dotnet() -> None:
    """.NET Resources.resx: ServiceRequestCompetitionException."""
    exc = ServiceRequestCompetitionException()

    assert str(exc) == "The session has been identified as duplicated by Sankhya"
