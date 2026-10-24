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
        # Valores mantidos como texto, como ParseDynamic no .NET
        assert resp.first_entity.get("CODPARC") == "1"

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
        assert resp.first_entity.get("CODPROD") == "123"

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
        
        assert resp.get_entity_field("CODPARC") == "1"
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
        assert codes == ["1", "2"]

    def test_entity_values_are_raw_strings(self):
        """
        Valores não são convertidos para int/float/bool.

        .NET (ServiceResponse.ParseDynamic): ds.SetMember(elementName,
        node.ReadElementContentAsString()). CPF/CNPJ/CEP mantêm os zeros à
        esquerda.
        """
        xml_str = """
        <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
            <responseBody>
                <entities total="1">
                    <entity>
                        <CODPARC>0042</CODPARC>
                        <CGC_CPF>01234567890</CGC_CPF>
                        <CEP>01310100</CEP>
                        <VLRDESC>1.50</VLRDESC>
                        <ATIVO>true</ATIVO>
                        <OBS/>
                    </entity>
                </entities>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)

        assert resp.first_entity.fields == {
            "CODPARC": "0042",
            "CGC_CPF": "01234567890",
            "CEP": "01310100",
            "VLRDESC": "1.50",
            "ATIVO": "true",
            "OBS": None,
        }

    def test_rmd_element_is_ignored(self):
        """O elemento _rmd é ignorado (ParseDynamic, SankhyaConstants.Rmd)."""
        xml_str = """
        <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
            <responseBody>
                <entities total="1">
                    <entity>
                        <CODPARC>1</CODPARC>
                        <_rmd><x>1</x></_rmd>
                    </entity>
                </entities>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)

        assert resp.first_entity.fields == {"CODPARC": "1"}


class TestServiceResponseMetadata:
    """
    Renomeação f0..fN pelo metadata (.NET ProcessCrudServiceProviderEntities,
    entity.ChangeKeys(metadata)).
    """

    XML_WITH_METADATA = """
    <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
        <responseBody>
            <entities total="2" totalPages="1" pagerID="P1">
                <metadata>
                    <fields>
                        <field name="CODPARC"/>
                        <field name="NOMEPARC"/>
                        <field name="CGC_CPF"/>
                    </fields>
                </metadata>
                <entity><f0>1</f0><f1>Cliente A</f1><f2>01234567890</f2></entity>
                <entity><f0>2</f0><f1>Cliente B</f1><f2/></entity>
            </entities>
        </responseBody>
    </serviceResponse>
    """

    def test_entities_receive_field_names(self):
        resp = ServiceResponse.from_xml_string(self.XML_WITH_METADATA)

        assert [e.fields for e in resp.entities] == [
            {"CODPARC": "1", "NOMEPARC": "Cliente A", "CGC_CPF": "01234567890"},
            {"CODPARC": "2", "NOMEPARC": "Cliente B", "CGC_CPF": None},
        ]
        assert resp.get_all_entity_fields("NOMEPARC") == ["Cliente A", "Cliente B"]
        provider = resp.response_body.crud_service_provider_entities
        assert [f.name for f in provider.metadata.fields] == [
            "CODPARC",
            "NOMEPARC",
            "CGC_CPF",
        ]
        assert provider.pager_id == "P1"

    def test_entities_without_metadata_keep_names(self):
        xml_str = """
        <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
            <responseBody>
                <entities total="1">
                    <entity><CODPARC>1</CODPARC><f0>x</f0></entity>
                </entities>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)

        assert resp.first_entity.fields == {"CODPARC": "1", "f0": "x"}
        assert resp.response_body.crud_service_provider_entities.metadata is None

    def test_metadata_key_count_mismatch_raises(self):
        """ChangeKeys (.NET) lança exceção quando as contagens diferem."""
        xml_str = """
        <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
            <responseBody>
                <entities total="1">
                    <metadata><fields><field name="CODPARC"/><field name="NOMEPARC"/></fields></metadata>
                    <entity><f0>1</f0></entity>
                </entities>
            </responseBody>
        </serviceResponse>
        """
        with pytest.raises(ValueError):
            ServiceResponse.from_xml_string(xml_str)

    def test_partner_from_metadata_response(self):
        """Ponta a ponta: entidade posicional convertida em Partner."""
        from sankhya_sdk.helpers.entity_dynamic_serialization import (
            EntityDynamicSerialization,
        )
        from sankhya_sdk.models.transport.partner import Partner

        resp = ServiceResponse.from_xml_string(self.XML_WITH_METADATA)

        partners = [
            EntityDynamicSerialization(e.fields).convert_to_type(Partner)
            for e in resp.entities
        ]

        assert [p.code for p in partners] == [1, 2]
        assert [p.name for p in partners] == ["Cliente A", "Cliente B"]
        assert partners[0].document == "01234567890"
        assert partners[1].document is None


class TestServiceResponseTypedConversion:
    """
    Ponta a ponta: <entity> do XML -> EntityDynamic -> Partner.

    Os valores ficam como texto em EntityDynamic e são convertidos para o
    tipo de cada campo por EntityDynamicSerialization.convert_to_type.
    """

    def test_partner_from_parsed_entity(self):
        from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType
        from sankhya_sdk.helpers.entity_dynamic_serialization import (
            EntityDynamicSerialization,
        )
        from sankhya_sdk.models.transport.partner import Partner

        xml_str = """
        <serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">
            <responseBody>
                <entities total="1">
                    <entity>
                        <CODPARC>42</CODPARC>
                        <NOMEPARC>Cliente</NOMEPARC>
                        <TIPPESSOA>F</TIPPESSOA>
                        <CGC_CPF>01234567890</CGC_CPF>
                        <CEP>01310100</CEP>
                        <ATIVO>S</ATIVO>
                        <CLIENTE>N</CLIENTE>
                        <CODCID>7</CODCID>
                        <DTCAD>25/12/2024 10:11:12</DTCAD>
                    </entity>
                </entities>
            </responseBody>
        </serviceResponse>
        """
        resp = ServiceResponse.from_xml_string(xml_str)

        partner = EntityDynamicSerialization(
            resp.first_entity.fields
        ).convert_to_type(Partner)

        assert partner.code == 42
        assert partner.name == "Cliente"
        assert partner.document == "01234567890"
        assert partner.zip_code == "01310100"
        assert partner.is_active is True
        assert partner.is_client is False
        assert partner.code_city == 7
        assert partner.fiscal_type is FiscalPersonType.INDIVIDUAL
        assert partner.date_created.year == 2024
        assert partner.date_created.day == 25


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
