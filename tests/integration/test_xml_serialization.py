"""
Testes de integração para serialização XML.

Testa serialização/deserialização completa de requests/responses.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.models.service.request_body import RequestBody
from sankhya_sdk.models.service.entity_types import Entity, DataSet
from sankhya_sdk.models.service.basic_types import Field, LiteralCriteria, Parameter
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_response_status import ServiceResponseStatus
from sankhya_sdk.enums.parameter_type import ParameterType


class TestXmlRoundTrip:
    """Testes de round-trip XML."""

    def test_service_request_round_trip(self):
        """Testa round-trip de ServiceRequest."""
        original = ServiceRequest(service=ServiceName.CRUD_FIND)
        original.request_body.entity = Entity(
            name="Parceiro",
            fields=[Field(name="CODPARC"), Field(name="NOMEPARC")]
        )
        
        xml_str = original.to_xml_string()
        parsed = ServiceRequest.from_xml_string(xml_str)
        
        assert parsed.service == original.service

    def test_service_response_round_trip(self):
        """Testa round-trip de ServiceResponse."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1" transactionId="TX123">
            <statusMessage>Sucesso</statusMessage>
            <responseBody codUsuLogado="1" jsessionid="SESS123">
                <entidades total="1">
                    <entidade>
                        <CODPARC>1</CODPARC>
                        <NOMEPARC>Cliente Teste</NOMEPARC>
                    </entidade>
                </entidades>
            </responseBody>
        </serviceResponse>
        """
        
        resp = ServiceResponse.from_xml_string(xml_str)
        new_xml = resp.to_xml_string()
        
        assert resp.service == ServiceName.CRUD_FIND
        assert resp.transaction_id == "TX123"
        assert len(resp.entities) == 1


class TestComplexXmlStructures:
    """Testes com estruturas XML complexas."""

    def test_crud_find_with_literal_criteria(self):
        """Testa requisição com critério literal."""
        req = ServiceRequest(service=ServiceName.CRUD_FIND)
        req.request_body.entity = Entity(
            name="Parceiro",
            fields=[Field(name="CODPARC")],
            literal_criteria=LiteralCriteria(
                expression="CODPARC > ? AND ATIVO = ?",
                parameters=[
                    Parameter(type=ParameterType.NUMERIC, value="0"),
                    Parameter(type=ParameterType.TEXT, value="S"),
                ]
            )
        )
        
        xml = req.to_xml()
        body = xml.find("requestBody")
        entity = body.find("entity")
        
        assert entity is not None
        assert entity.get("name") == "Parceiro"

    def test_dataset_request(self):
        """Testa requisição com DataSet."""
        req = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        req.request_body.data_set = DataSet(
            root_entity="Produto",
            include_presentation=True,
            rows_limit=100,
            entity=Entity(
                name="Produto",
                fields=[Field(name="CODPROD"), Field(name="DESCRPROD")]
            )
        )
        
        xml_str = req.to_xml_string()
        
        assert "dataSet" in xml_str
        assert "rowsLimit" in xml_str

    def test_response_with_multiple_entities(self):
        """Testa resposta com múltiplas entidades."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
                <entidades total="3" totalPages="1">
                    <entidade>
                        <CODPARC>1</CODPARC>
                        <NOMEPARC>Cliente A</NOMEPARC>
                        <ATIVO>S</ATIVO>
                    </entidade>
                    <entidade>
                        <CODPARC>2</CODPARC>
                        <NOMEPARC>Cliente B</NOMEPARC>
                        <ATIVO>S</ATIVO>
                    </entidade>
                    <entidade>
                        <CODPARC>3</CODPARC>
                        <NOMEPARC>Cliente C</NOMEPARC>
                        <ATIVO>N</ATIVO>
                    </entidade>
                </entidades>
            </responseBody>
        </serviceResponse>
        """
        
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert len(resp.entities) == 3
        assert resp.response_body.crud_service_entities.total == 3
        
        codes = resp.get_all_entity_fields("CODPARC")
        assert codes == [1, 2, 3]


class TestRealWorldXml:
    """Testes com XMLs do mundo real."""

    def test_login_response(self):
        """Testa parsing de resposta de login."""
        xml_str = """
        <serviceResponse serviceName="MobileLoginSP.login" status="1">
            <responseBody idusu="123" jsessionid="ABCD1234" callID="0001">
            </responseBody>
        </serviceResponse>
        """
        
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.status == ServiceResponseStatus.OK
        assert resp.response_body.code_user == 123
        assert resp.response_body.jsession_id == "ABCD1234"

    def test_invoice_response(self):
        """Testa parsing de resposta de nota fiscal."""
        xml_str = """
        <serviceResponse serviceName="CACSP.incluirNota" status="1" transactionId="TX999">
            <responseBody>
                <chave>
                    <NUNOTA>12345</NUNOTA>
                </chave>
            </responseBody>
        </serviceResponse>
        """
        
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.transaction_id == "TX999"
        assert resp.response_body.key is not None

    def test_error_response(self):
        """Testa parsing de resposta de erro."""
        xml_str = """
        <serviceResponse serviceName="crud.save" status="0" errorCode="SNK.001" errorLevel="ERROR">
            <statusMessage>Campo obrigatório não informado: CODPROD</statusMessage>
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.is_error
        assert resp.error_code == "SNK.001"
        assert "Campo obrigatório" in resp.status_message_text


class TestXmlCompatibility:
    """Testes de compatibilidade XML."""

    def test_handles_unknown_elements(self):
        """Testa que elementos desconhecidos são ignorados."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <unknownElement>Valor</unknownElement>
            <responseBody>
                <anotherUnknown attr="test"/>
            </responseBody>
        </serviceResponse>
        """
        
        # Não deve lançar exceção
        resp = ServiceResponse.from_xml_string(xml_str)
        assert resp.is_success

    def test_handles_empty_elements(self):
        """Testa elementos vazios."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <statusMessage></statusMessage>
            <responseBody/>
        </serviceResponse>
        """
        
        resp = ServiceResponse.from_xml_string(xml_str)
        assert resp.is_success
        assert resp.status_message_text == ""
