# -*- coding: utf-8 -*-
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestGeneralException,
    ServiceRequestTemporarilyException,
    ServiceRequestTimeoutException,
    ServiceRequestExternalException,
    ServiceRequestUnavailableException,
    IXmlServiceException,
)
from sankhya_sdk.enums.service_name import ServiceName

def test_exception_hierarchy() -> None:
    exc: ServiceRequestTimeoutException = ServiceRequestTimeoutException(ServiceName.CRUD_FIND)
    
    assert isinstance(exc, ServiceRequestTimeoutException)
    assert isinstance(exc, ServiceRequestTemporarilyException)
    assert isinstance(exc, ServiceRequestGeneralException)
    assert isinstance(exc, SankhyaException)
    assert isinstance(exc, Exception)

def test_ixml_service_exception_protocol() -> None:
    exc: ServiceRequestGeneralException = ServiceRequestGeneralException("Error", None, None)
    assert isinstance(exc, IXmlServiceException)
    assert exc.request_xml is None
    assert exc.response_xml is None

def test_unavailable_exception_is_temporarily_and_keeps_response() -> None:
    """Paridade com .NET: ServiceRequestUnavailableException(service, request, response)
    deriva de ServiceRequestTemporarilyException."""
    request: object = object()
    response: object = object()
    exc = ServiceRequestUnavailableException(ServiceName.CRUD_FIND, request, response)

    assert isinstance(exc, ServiceRequestTemporarilyException)
    assert isinstance(exc, ServiceRequestGeneralException)
    assert exc.request is request
    assert exc.response is response
    assert "The call to the CRUD - Retrieve service is currently unavailable" in str(exc)

    exc_kw = ServiceRequestUnavailableException(
        service=ServiceName.CRUD_FIND, request=None, response=response
    )
    assert exc_kw.response is response

def test_external_exception_is_temporarily_and_keeps_response() -> None:
    """Paridade com .NET: ServiceRequestExternalException(service, request, response)
    deriva de ServiceRequestTemporarilyException."""
    request: object = object()
    response: object = object()
    exc = ServiceRequestExternalException(
        service=ServiceName.CRUD_FIND, request=request, response=response
    )

    assert isinstance(exc, ServiceRequestTemporarilyException)
    assert exc.request is request
    assert exc.response is response
    assert "Internal Sankhya error (NPE) on call to the CRUD - Retrieve service" in str(exc)
