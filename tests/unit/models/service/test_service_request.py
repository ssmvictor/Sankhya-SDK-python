"""
Testes unitários para ServiceRequest.

Testa serialização XML e criação de requisições.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.request_body import RequestBody
from sankhya_sdk.models.service.entity_types import Entity
from sankhya_sdk.models.service.basic_types import Field
from sankhya_sdk.enums.service_name import ServiceName


class TestServiceRequest:
    """Testes para a classe ServiceRequest."""

    def test_init_default(self):
        """Testa inicialização com valores padrão."""
        req = ServiceRequest()
        
        assert req.service == ServiceName.TEST
        assert req.request_body is not None

    def test_init_with_service(self):
        """Testa inicialização com serviço específico."""
        req = ServiceRequest(service=ServiceName.CRUD_FIND)
        
        assert req.service == ServiceName.CRUD_FIND

    def test_to_xml(self):
        """Testa serialização para XML."""
        req = ServiceRequest(service=ServiceName.CRUD_FIND)
        xml = req.to_xml()
        
        assert xml.tag == "serviceRequest"
        assert xml.get("serviceName") == "crud.find"

    def test_to_xml_with_body(self):
        """Testa serialização com corpo de requisição."""
        req = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        req.request_body.entity = Entity(name="Parceiro")
        
        xml = req.to_xml()
        
        assert xml.tag == "serviceRequest"
        assert xml.get("serviceName") == "CRUDServiceProvider.loadRecords"
        
        body = xml.find("requestBody")
        assert body is not None

    def test_to_xml_string(self):
        """Testa serialização para string XML."""
        req = ServiceRequest(service=ServiceName.LOGIN)
        xml_str = req.to_xml_string()
        
        assert "<serviceRequest" in xml_str
        assert 'serviceName="MobileLoginSP.login"' in xml_str

    def test_to_xml_string_pretty(self):
        """Testa serialização com formatação."""
        req = ServiceRequest(service=ServiceName.LOGIN)
        xml_str = req.to_xml_string(pretty_print=True)
        
        assert "\n" in xml_str

    def test_to_xml_bytes(self):
        """Testa serialização para bytes."""
        req = ServiceRequest(service=ServiceName.LOGIN)
        xml_bytes = req.to_xml_bytes()
        
        assert isinstance(xml_bytes, bytes)
        assert b"<?xml" in xml_bytes
        assert b"UTF-8" in xml_bytes

    def test_from_xml(self):
        """Testa deserialização de XML."""
        xml_str = """
        <serviceRequest serviceName="crud.find">
            <requestBody>
            </requestBody>
        </serviceRequest>
        """
        req = ServiceRequest.from_xml_string(xml_str)
        
        assert req.service == ServiceName.CRUD_FIND

    def test_round_trip(self):
        """Testa serialização e deserialização completa."""
        original = ServiceRequest(service=ServiceName.CRUD_SAVE)
        
        xml_str = original.to_xml_string()
        parsed = ServiceRequest.from_xml_string(xml_str)
        
        assert parsed.service == original.service


class TestServiceRequestIntegration:
    """Testes de integração para ServiceRequest."""

    def test_crud_find_request(self):
        """Testa criação de requisição CRUD Find."""
        req = ServiceRequest(service=ServiceName.CRUD_FIND)
        req.request_body.entity = Entity(
            name="Parceiro",
            fields=[
                Field(name="CODPARC"),
                Field(name="NOMEPARC"),
            ]
        )
        
        xml_str = req.to_xml_string()
        
        assert "CODPARC" in xml_str
        assert "NOMEPARC" in xml_str

    def test_login_request(self):
        """Testa criação de requisição de login."""
        req = ServiceRequest(service=ServiceName.LOGIN)
        req.request_body.username = "usuario"
        req.request_body.password = "senha"
        
        xml = req.to_xml()
        body = xml.find("requestBody")
        
        assert body.find("NOMUSU").text == "usuario"
        assert body.find("INTERNO").text == "senha"
