"""
Testes unitários para ServiceResponse.

Testa parsing XML e acesso a entidades.
"""

import pytest
from lxml import etree

from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_response_status import ServiceResponseStatus


class TestServiceResponseParsing:
    """Testes de parsing para ServiceResponse."""

    def test_parse_success_response(self):
        """Testa parsing de resposta de sucesso."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.service == ServiceName.CRUD_FIND
        assert resp.status == ServiceResponseStatus.OK
        assert resp.is_success is True
        assert resp.is_error is False

    def test_parse_error_response(self):
        """Testa parsing de resposta de erro."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="0" errorCode="E001" errorLevel="ERROR">
            <statusMessage>Erro ao processar requisição</statusMessage>
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.status == ServiceResponseStatus.ERROR
        assert resp.is_error is True
        assert resp.error_code == "E001"
        assert resp.error_level == "ERROR"
        assert "Erro" in resp.status_message_text

    def test_parse_with_transaction_id(self):
        """Testa parsing com transaction ID."""
        xml_str = """
        <serviceResponse serviceName="crud.save" status="1" transactionId="TX123">
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.transaction_id == "TX123"

    def test_parse_pending_printing(self):
        """Testa parsing com pendência de impressão."""
        xml_str = """
        <serviceResponse serviceName="CACSP.confirmarNota" status="1" pendingPrinting="true">
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.pending_printing is True


class TestServiceResponseEntities:
    """Testes de acesso a entidades."""

    def test_entities_pt_br(self):
        """Testa acesso a entidades em português."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
                <entidades total="2">
                    <entidade>
                        <CODPARC>1</CODPARC>
                        <NOMEPARC>Cliente A</NOMEPARC>
                    </entidade>
                    <entidade>
                        <CODPARC>2</CODPARC>
                        <NOMEPARC>Cliente B</NOMEPARC>
                    </entidade>
                </entidades>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert len(resp.entities) == 2
        assert resp.first_entity is not None
        assert resp.first_entity.get("CODPARC") == 1

    def test_entities_en(self):
        """Testa acesso a entidades em inglês."""
        xml_str = """
        <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
            <responseBody>
                <entities total="1">
                    <entity>
                        <CODPROD>123</CODPROD>
                        <DESCRPROD>Produto Teste</DESCRPROD>
                    </entity>
                </entities>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert len(resp.entities) == 1
        assert resp.first_entity.get("CODPROD") == 123

    def test_empty_entities(self):
        """Testa resposta sem entidades."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert len(resp.entities) == 0
        assert resp.first_entity is None

    def test_get_entity_field(self):
        """Testa obtenção de campo de entidade."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
                <entidades>
                    <entidade>
                        <CODPARC>1</CODPARC>
                        <NOMEPARC>Cliente</NOMEPARC>
                    </entidade>
                </entidades>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        assert resp.get_entity_field("CODPARC") == 1
        assert resp.get_entity_field("NOMEPARC") == "Cliente"
        assert resp.get_entity_field("INEXISTENTE", "default") == "default"

    def test_get_all_entity_fields(self):
        """Testa obtenção de campo de todas as entidades."""
        xml_str = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
                <entidades>
                    <entidade>
                        <CODPARC>1</CODPARC>
                    </entidade>
                    <entidade>
                        <CODPARC>2</CODPARC>
                    </entidade>
                </entidades>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)
        
        codes = resp.get_all_entity_fields("CODPARC")
        assert codes == [1, 2]


class TestServiceResponseSerialization:
    """Testes de serialização."""

    def test_to_xml(self):
        """Testa serialização para XML."""
        resp = ServiceResponse(
            service=ServiceName.CRUD_FIND,
            status=ServiceResponseStatus.OK,
            transaction_id="TX123",
        )
        xml = resp.to_xml()
        
        assert xml.tag == "serviceResponse"
        assert xml.get("status") == "1"
        assert xml.get("transactionId") == "TX123"

    def test_round_trip(self):
        """Testa serialização e deserialização."""
        original_xml = """
        <serviceResponse serviceName="crud.find" status="1">
            <responseBody>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(original_xml)
        new_xml = resp.to_xml_string()
        
        assert "serviceResponse" in new_xml


class TestServiceResponseRepr:
    """Testes de representação."""

    def test_repr(self):
        """Testa representação string."""
        resp = ServiceResponse(
            service=ServiceName.CRUD_FIND,
            status=ServiceResponseStatus.OK,
        )
        repr_str = repr(resp)
        
        assert "ServiceResponse" in repr_str
        assert "CRUD_FIND" in repr_str
        assert "OK" in repr_str
