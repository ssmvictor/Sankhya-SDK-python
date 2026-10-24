"""
Testes unitários para os tipos de eventos e avisos (event_types).

Os formatos esperados vêm do SDK .NET de referência
(Sankhya-SDK-dotnet/Src/Sankhya/Service/SystemWarning.cs,
SystemWarningRecipient.cs e ClientEvent.cs).
"""

from lxml import etree

from sankhya_sdk.enums.sankhya_warning_level import SankhyaWarningLevel
from sankhya_sdk.enums.sankhya_warning_type import SankhyaWarningType
from sankhya_sdk.models.service.event_types import (
    ClientEvent,
    ClientEvents,
    SystemWarning,
    SystemWarningRecipient,
)


def _parse(xml: str) -> etree._Element:
    return etree.fromstring(xml)


class TestSystemWarningRecipient:
    """<destinatario id="..." tipo="..."/>."""

    def test_to_xml_uses_id_attribute(self):
        xml = SystemWarningRecipient(user_id=1).to_xml()

        assert xml.tag == "destinatario"
        # Sem "idusu"/"lido": o .NET só serializa id e tipo quando informados
        assert dict(xml.attrib) == {"id": "1"}

    def test_to_xml_type_uses_internal_value(self):
        user = SystemWarningRecipient(user_id=1, type=SankhyaWarningType.USER).to_xml()
        group = SystemWarningRecipient(user_id=5, type=SankhyaWarningType.GROUP).to_xml()

        assert dict(user.attrib) == {"id": "1", "tipo": "usuario"}
        assert dict(group.attrib) == {"id": "5", "tipo": "grupo"}

    def test_from_xml(self):
        recipient = SystemWarningRecipient.from_xml(
            _parse('<destinatario id="7" tipo="grupo"/>')
        )

        assert recipient.user_id == 7
        assert recipient.type == SankhyaWarningType.GROUP

    def test_from_xml_legacy_idusu(self):
        recipient = SystemWarningRecipient.from_xml(_parse('<destinatario idusu="3"/>'))

        assert recipient.user_id == 3
        assert recipient.type is None


class TestSystemWarning:
    """<aviso importancia=...><titulo/><descricao/><Dica/><destinatario/></aviso>."""

    def test_to_xml_matches_dotnet_shape(self):
        warning = SystemWarning(
            title="Manutenção",
            content="Sistema indisponível",
            tip="Salve seu trabalho",
            priority=SankhyaWarningLevel.WARNING,
            recipients=[
                SystemWarningRecipient(user_id=1, type=SankhyaWarningType.USER),
                SystemWarningRecipient(user_id=2),
            ],
        )

        xml = warning.to_xml()

        assert xml.tag == "aviso"
        assert dict(xml.attrib) == {"importancia": "2"}
        assert [child.tag for child in xml] == [
            "titulo",
            "descricao",
            "Dica",
            "destinatario",
            "destinatario",
        ]
        assert xml.findtext("titulo") == "Manutenção"
        assert xml.findtext("descricao") == "Sistema indisponível"
        assert xml.findtext("Dica") == "Salve seu trabalho"
        assert [dict(d.attrib) for d in xml.findall("destinatario")] == [
            {"id": "1", "tipo": "usuario"},
            {"id": "2"},
        ]

    def test_to_xml_priority_as_internal_value_string(self):
        """O wrapper atual passa level.internal_value (texto)."""
        xml = SystemWarning(title="T", content="D", priority="3").to_xml()

        assert xml.get("importancia") == "3"

    def test_to_xml_omits_unset_fields(self):
        xml = SystemWarning(title="T", content="D").to_xml()

        assert dict(xml.attrib) == {}
        assert [child.tag for child in xml] == ["titulo", "descricao"]

    def test_to_xml_does_not_emit_non_dotnet_markup(self):
        xml = SystemWarning(
            code="X",
            title="T",
            content="D",
            created_at="2024-01-01",
            expire_at="2024-01-02",
            recipients=[SystemWarningRecipient(user_id=1)],
        ).to_xml()

        assert xml.find("conteudo") is None
        assert xml.find("destinatarios") is None
        for attr in ("codigo", "tipo", "prioridade", "criadoEm", "expiraEm"):
            assert xml.get(attr) is None

    def test_from_xml_dotnet_shape(self):
        warning = SystemWarning.from_xml(
            _parse(
                '<aviso importancia="1"><titulo>T</titulo><descricao>D</descricao>'
                '<Dica>Tip</Dica><destinatario id="9" tipo="usuario"/></aviso>'
            )
        )

        assert warning.priority == "1"
        assert warning.title == "T"
        assert warning.content == "D"
        assert warning.tip == "Tip"
        assert len(warning.recipients) == 1
        assert warning.recipients[0].user_id == 9
        assert warning.recipients[0].type == SankhyaWarningType.USER

    def test_round_trip(self):
        original = SystemWarning(
            title="T",
            content="D",
            tip="Tip",
            priority=SankhyaWarningLevel.URGENT,
            recipients=[SystemWarningRecipient(user_id=4, type=SankhyaWarningType.GROUP)],
        )

        parsed = SystemWarning.from_xml(original.to_xml())

        assert etree.tostring(parsed.to_xml()) == etree.tostring(original.to_xml())


class TestClientEvent:
    """<clientEvent id="...">texto</clientEvent>."""

    def test_to_xml_text(self):
        xml = ClientEvent(text="br.com.sankhya.actionbutton.clientconfirm").to_xml()

        assert xml.tag == "clientEvent"
        assert xml.text == "br.com.sankhya.actionbutton.clientconfirm"
        assert dict(xml.attrib) == {}
        assert len(xml) == 0

    def test_to_xml_id(self):
        xml = ClientEvent(id="abc", text="evento").to_xml()

        assert xml.get("id") == "abc"
        assert xml.text == "evento"

    def test_from_xml_text_and_id(self):
        event = ClientEvent.from_xml(
            _parse('<clientEvent id="x1">br.com.sankhya.comercial.evento</clientEvent>')
        )

        assert event.id == "x1"
        assert event.text == "br.com.sankhya.comercial.evento"
        assert event.data == {}

    def test_client_events_response_text(self):
        """Eventos devolvidos na resposta do faturamento (.NET ClientEvents)."""
        events = ClientEvents.from_xml(
            _parse(
                "<clientEvents>"
                "<clientEvent>br.com.sankhya.um</clientEvent>"
                "<clientEvent>br.com.sankhya.dois</clientEvent>"
                "</clientEvents>"
            )
        )

        assert [event.text for event in events.items] == [
            "br.com.sankhya.um",
            "br.com.sankhya.dois",
        ]

    def test_existing_fields_still_serialized(self):
        xml = ClientEvent(type="t", code="c", data={"k": "v"}).to_xml()

        assert xml.get("type") == "t"
        assert xml.get("code") == "c"
        assert xml.findtext("k") == "v"
        assert xml.text is None
