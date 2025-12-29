# -*- coding: utf-8 -*-
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestGeneralException,
    ServiceRequestTemporarilyException,
    ServiceRequestTimeoutException,
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
