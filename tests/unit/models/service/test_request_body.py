"""
Testes unitários para RequestBody.

Os nomes de elementos esperados vêm do SDK .NET de referência
(Sankhya-SDK-dotnet/Src/Sankhya/Service/RequestBody.cs).
"""

from lxml import etree

from sankhya_sdk.enums.billing_type import BillingType
from sankhya_sdk.enums.sankhya_warning_level import SankhyaWarningLevel
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.service.basic_types import Path, Paths
from sankhya_sdk.models.service.event_types import (
    ClientEvent,
    ClientEvents,
    SystemWarning,
    SystemWarningRecipient,
)
from sankhya_sdk.models.service.invoice_types import (
    Invoice,
    Invoices,
    InvoicesWithCurrency,
)
from sankhya_sdk.models.service.metadata_types import Session
from sankhya_sdk.models.service.request_body import RequestBody
from sankhya_sdk.models.service.service_request import ServiceRequest


CLIENT_CONFIRM = "br.com.sankhya.actionbutton.clientconfirm"


class _ElementStub:
    """Colaborador mínimo com to_xml() para verificar a delegação do RequestBody."""

    def __init__(self, tag: str, **attributes: str) -> None:
        self._tag = tag
        self._attributes = attributes

    def to_xml(self) -> etree._Element:
        return etree.Element(self._tag, **self._attributes)


class TestRequestBodySession:
    """.NET: [XmlElement("SESSION")] public Session Session."""

    def test_session_element_is_upper_case(self):
        xml = RequestBody(session=Session(jsession_id="ABC123")).to_xml()

        assert [child.tag for child in xml] == ["SESSION"]
        assert xml.find("session") is None
        assert "ABC123" in etree.tostring(xml, encoding="unicode")

    def test_session_element_is_appended_as_is(self):
        """Contrato: Session.to_xml() devolve <SESSION ID=.../>, anexado sem alterações."""
        session = _ElementStub("SESSION", ID="SESSION_TO_KILL")

        xml = RequestBody(session=session).to_xml()

        assert len(xml) == 1
        assert xml[0].tag == "SESSION"
        assert dict(xml[0].attrib) == {"ID": "SESSION_TO_KILL"}
        assert len(xml[0]) == 0

    def test_kill_session_request_xml(self):
        request = ServiceRequest(
            service=ServiceName.SESSION_KILL,
            request_body=RequestBody(session=Session(jsession_id="S1")),
        )

        body = request.to_xml().find("requestBody")

        assert body.find("SESSION") is not None


class TestRequestBodySystemWarning:
    """.NET: [XmlElement("aviso")] public SystemWarning SystemWarning."""

    def test_system_warning_element_is_aviso(self):
        warning = SystemWarning(
            title="Teste",
            content="Mensagem de teste",
            priority=SankhyaWarningLevel.INFORMATION,
            recipients=[SystemWarningRecipient(user_id=1)],
        )

        xml = RequestBody(system_warning=warning).to_xml()

        assert [child.tag for child in xml] == ["aviso"]
        aviso = xml.find("aviso")
        assert aviso.get("importancia") == "3"
        assert aviso.findtext("titulo") == "Teste"
        assert aviso.findtext("descricao") == "Mensagem de teste"
        assert [dict(d.attrib) for d in aviso.findall("destinatario")] == [{"id": "1"}]


class TestRequestBodyDeleteFiles:
    """.NET DeleteFiles: <clientEventList><clientEvent>...</clientEvent></clientEventList>
    e <arquivos><path>...</path></arquivos>."""

    def test_client_events_and_paths_use_dotnet_containers(self):
        body = RequestBody(
            paths=Paths(items=[Path(value="/a.pdf"), Path(value="/b.pdf")]),
            client_events=ClientEvents(items=[ClientEvent(text=CLIENT_CONFIRM)]),
        )

        xml = body.to_xml()

        assert xml.find("clientEvents") is None
        assert xml.find("paths") is None
        assert [e.text for e in xml.findall("clientEventList/clientEvent")] == [
            CLIENT_CONFIRM
        ]
        assert [p.text for p in xml.findall("arquivos/path")] == ["/a.pdf", "/b.pdf"]

    def test_client_events_as_list(self):
        """.NET RequestBody.ClientEvents é ClientEvent[] (XmlArray)."""
        xml = RequestBody(client_events=[ClientEvent(text=CLIENT_CONFIRM)]).to_xml()

        assert [e.text for e in xml.findall("clientEventList/clientEvent")] == [
            CLIENT_CONFIRM
        ]

    def test_paths_as_list(self):
        xml = RequestBody(paths=[Path(value="/a.pdf")]).to_xml()

        assert [p.text for p in xml.findall("arquivos/path")] == ["/a.pdf"]


class TestRequestBodyInvoices:
    """Atributos de <notas> preservados ao serem anexados no corpo."""

    def test_bill_invoices_attributes_preserved(self):
        invoices = Invoices(
            billing_type=BillingType.NORMAL,
            code_operation_type=1100,
            date_billing=None,
            date_exit=None,
            time_exit=None,
            is_date_validated=True,
            invoices_with_currency=InvoicesWithCurrency(currency_value="undefined"),
            items=[Invoice(value="12345")],
            one_invoice_for_each=True,
        )

        xml = RequestBody(invoices=invoices).to_xml()

        notas = xml.find("notas")
        assert notas.get("codTipOper") == "1100"
        assert notas.get("tipoFaturamento") == "FaturamentoNormal"
        assert notas.get("dtFaturamento") == ""
        assert notas.findtext("nota") == "12345"
        assert notas.find("notasComMoeda").get("valorMoeda") == "undefined"


class TestRequestBodyDelegation:
    """entity/data_set continuam delegando para o to_xml() do próprio objeto."""

    def test_data_set_and_entity_delegate_to_xml(self):
        body = RequestBody(
            data_set=_ElementStub("dataSet", rootEntity="Parceiro"),
            entity=_ElementStub("entity", path=""),
        )

        xml = body.to_xml()

        assert xml.find("dataSet").get("rootEntity") == "Parceiro"
        assert xml.find("entity").get("path") == ""


class TestRequestBodyFromXml:
    """from_xml aceita os nomes do .NET (e os legados)."""

    def test_from_xml_dotnet_tags(self):
        element = etree.fromstring(
            "<requestBody>"
            '<SESSION ID="S1"/>'
            '<aviso importancia="2"><titulo>T</titulo><descricao>D</descricao></aviso>'
            f"<clientEventList><clientEvent>{CLIENT_CONFIRM}</clientEvent></clientEventList>"
            "<arquivos><path>/a.pdf</path></arquivos>"
            "</requestBody>"
        )

        body = RequestBody.from_xml(element)

        assert body.session is not None
        assert body.system_warning.title == "T"
        assert body.system_warning.content == "D"
        assert body.system_warning.priority == "2"
        assert [e.text for e in body.client_events.items] == [CLIENT_CONFIRM]
        assert [p.value for p in body.paths.items] == ["/a.pdf"]

    def test_round_trip_keeps_dotnet_tags(self):
        original = RequestBody(
            system_warning=SystemWarning(title="T", content="D"),
            client_events=ClientEvents(items=[ClientEvent(text=CLIENT_CONFIRM)]),
            paths=Paths(items=[Path(value="/a.pdf")]),
        )

        parsed = RequestBody.from_xml(original.to_xml())

        assert [child.tag for child in parsed.to_xml()] == [
            "aviso",
            "clientEventList",
            "arquivos",
        ]
        assert etree.tostring(parsed.to_xml()) == etree.tostring(original.to_xml())
