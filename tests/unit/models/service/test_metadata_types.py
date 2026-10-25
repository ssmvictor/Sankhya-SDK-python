"""
Testes unitários para os tipos de metadados de serviço (Pager, Key, Session,
StatusMessage).

O formato XML esperado segue o SDK .NET (Src/Sankhya/Service/Key.cs,
Src/Sankhya/Service/Session.cs, StatusMessage.cs e RequestBody.cs).
"""

import base64

import pytest
from lxml import etree

from sankhya_sdk.models.service.metadata_types import (
    Key,
    Pager,
    Session,
    StatusMessage,
)
from sankhya_sdk.models.service.response_body import ResponseBody


def _b64(text: str, encoding: str = "utf-8") -> str:
    """Codifica o texto em Base64, como o servidor envia o statusMessage."""
    return base64.b64encode(text.encode(encoding)).decode("ascii")


def _status_message(content: str) -> StatusMessage:
    """Deserializa ``<statusMessage><![CDATA[content]]></statusMessage>``."""
    element = etree.fromstring(
        f"<statusMessage><![CDATA[{content}]]></statusMessage>"
    )
    return StatusMessage.from_xml(element)


#: Mensagens reais do servidor (login, deadlock, timeout, sessão).
_SERVER_MESSAGES = [
    "Usuário/Senha inválido.",
    "A transação (ID do processo 64) entrou em deadlock em recursos de bloqueio "
    "com outro processo e foi escolhida como vítima do deadlock. Execute a "
    "transação novamente.",
    "Transaction (Process ID 52) was deadlocked on lock resources with another "
    "process and has been chosen as the deadlock victim. Rerun the transaction.",
    "ORA-00060: deadlock detected while waiting for resource",
    "Erro ao executar a consulta: O tempo limite da consulta expirou.",
    "Não autorizado.",
    "Usuário expirou.",
    "Erro",
    "deadlock",
    "Timeout",
    "Nota fiscal nº 123 já confirmada (§ 1º)",
    "java.lang.NullPointerException\n\tat br.com.sankhya.Foo.bar(Foo.java:12)",
]


class TestStatusMessage:
    """
    StatusMessage.from_xml decodifica o Base64 enviado pelo servidor.

    .NET: StatusMessage.ValueInternal => value.FromBase64() (CrispyWaffle,
    ISO-8859-1) e ServiceResponse.cs:309 sempre usa ValueInternal.
    """

    @pytest.mark.parametrize("encoding", ["utf-8", "iso-8859-1"])
    @pytest.mark.parametrize("message", _SERVER_MESSAGES)
    def test_base64_cdata_is_decoded(self, message, encoding):
        status = _status_message(_b64(message, encoding))

        assert status.value == message
        assert status.decoded_value == message
        assert status.is_encoded is False

    def test_line_wrapped_base64_is_decoded(self):
        """Base64 quebrado em linhas de 76 caracteres (codificador MIME)."""
        message = _SERVER_MESSAGES[1]
        encoded = _b64(message, "iso-8859-1")
        wrapped = "\r\n".join(encoded[i : i + 76] for i in range(0, len(encoded), 76))
        assert "\n" in wrapped

        assert _status_message(wrapped).value == message

    @pytest.mark.parametrize(
        "plain",
        [
            "Usuário/Senha inválido",
            "I/O Error: Connection reset",
            "Erro ao processar requisição",
            "Transaction was deadlocked on lock resources",
            "Sucesso",
        ],
    )
    def test_plain_text_message_is_kept(self, plain):
        """Texto puro (não é Base64) é mantido como está."""
        assert _status_message(plain).value == plain

    @pytest.mark.parametrize(
        "plain",
        [
            # Só usam caracteres do alfabeto Base64 e têm tamanho múltiplo de 4:
            # são Base64 válido, mas decodificam para lixo binário.
            "Erro",
            "test",
            "1234",
            "Ok12",
            "deadlock",
            "Timeout1",
            "Pendente",
            "Recusado",
            "Proibido",
            "Violacao",
            "Invalido",
            "ORA00060",
            "Expirou1",
            "12345678",
            "00000000",
            "Unauthorized",
            "AccessDenied",
            "NaoAutorizado1",
            "123456789012",
        ],
    )
    def test_plain_text_in_base64_alphabet_is_kept(self, plain):
        assert _status_message(plain).value == plain

    @pytest.mark.parametrize(
        "content",
        [
            "VGVzdGU",  # sem padding
            "VGVzdGU==",  # padding a mais
            "=VGVzdGU",  # padding no início
            "VGVzdGV=",  # bits finais não zerados (não canônico)
            "VGVz dGU=",  # espaço no meio
            base64.b64encode(b"\x00\x01\x02\x03\xff\xfe").decode("ascii"),  # binário
            base64.b64encode(b"Erro\x07 de teste").decode("ascii"),  # controle
        ],
    )
    def test_invalid_or_binary_base64_is_kept(self, content):
        assert _status_message(content).value == content

    def test_empty_message(self):
        assert _status_message("").value == ""
        assert StatusMessage.from_xml(etree.fromstring("<statusMessage/>")).value == ""

    def test_encoded_attribute_keeps_encoded_value(self):
        """Formato legado deste SDK: encoded="true" mantém o valor codificado."""
        encoded = _b64("Usuário/Senha inválido.")
        element = etree.fromstring(
            f'<statusMessage encoded="true">{encoded}</statusMessage>'
        )

        status = StatusMessage.from_xml(element)

        assert status.is_encoded is True
        assert status.value == encoded
        assert status.decoded_value == "Usuário/Senha inválido."


class TestPager:
    """Testes para a classe Pager."""

    def test_from_xml_parses_integer_attributes(self):
        """Testa que totalPages/totalRecords são convertidos para int."""
        element = etree.fromstring(
            '<pager totalPages="3" totalRecords="250" pagerId="PG-1"/>'
        )

        pager = Pager.from_xml(element)

        assert pager.total_pages == 3
        assert pager.total_records == 250
        assert pager.pager_id == "PG-1"

    def test_from_xml_without_attributes_returns_none(self):
        """Testa que atributos ausentes resultam em None."""
        pager = Pager.from_xml(etree.fromstring("<pager/>"))

        assert pager.total_pages is None
        assert pager.total_records is None
        assert pager.pager_id is None

    def test_from_xml_invalid_integer_returns_none(self):
        """Testa que valores não numéricos resultam em None."""
        element = etree.fromstring('<pager totalPages="abc" totalRecords=""/>')

        pager = Pager.from_xml(element)

        assert pager.total_pages is None
        assert pager.total_records is None

    def test_round_trip(self):
        """Testa que to_xml/from_xml preservam os valores."""
        original = Pager(total_pages=2, total_records=180, pager_id="PAGER-42")

        restored = Pager.from_xml(original.to_xml())

        assert restored == original

    def test_response_body_parses_pager_element(self):
        """Testa que ResponseBody.from_xml desserializa o elemento <pager>."""
        element = etree.fromstring(
            '<responseBody><pager totalPages="5" totalRecords="42"/></responseBody>'
        )

        body = ResponseBody.from_xml(element)

        assert body.pager.total_pages == 5
        assert body.pager.total_records == 42


class TestKey:
    """Testes para a classe Key (.NET: Service/Key.cs)."""

    def test_from_xml_reads_valor_attribute(self):
        """Testa que o atributo "valor" de <chave> é lido em value."""
        element = etree.fromstring('<chave valor="FILE_KEY_123"/>')

        key = Key.from_xml(element)

        assert key.value == "FILE_KEY_123"

    def test_from_xml_without_valor_returns_none(self):
        """Testa que value é None quando o atributo "valor" não existe."""
        key = Key.from_xml(etree.fromstring("<chave/>"))

        assert key.value is None

    def test_from_xml_still_parses_child_values(self):
        """Testa que os elementos filhos continuam sendo lidos em values (pk)."""
        element = etree.fromstring("<pk><NUNOTA>123</NUNOTA></pk>")

        key = Key.from_xml(element)

        assert key.values == {"NUNOTA": "123"}
        assert key.value is None

    def test_to_xml_writes_valor_attribute(self):
        """Testa que value é serializado no atributo "valor" de <chave>."""
        elem = Key(value="ABC").to_xml()

        assert elem.tag == "chave"
        assert elem.get("valor") == "ABC"

    def test_to_xml_omits_valor_when_not_set(self):
        """Testa que o atributo "valor" é omitido quando value é None."""
        elem = Key().to_xml()

        assert "valor" not in elem.attrib

    def test_round_trip(self):
        """Testa que to_xml/from_xml preservam value, name e values."""
        original = Key(name="k", value="V1", values={"NUNOTA": "1"})

        restored = Key.from_xml(original.to_xml())

        assert restored.value == "V1"
        assert restored.name == "k"
        assert restored.values == {"NUNOTA": "1"}

    def test_response_body_exposes_key_value(self):
        """Testa ResponseBody.Key.Value (.NET KnowServicesRequestWrapper.OpenFile)."""
        element = etree.fromstring(
            '<responseBody><chave valor="FILE_KEY_RETURNED"/></responseBody>'
        )

        body = ResponseBody.from_xml(element)

        assert body.key.value == "FILE_KEY_RETURNED"


class TestSession:
    """Testes para a classe Session (.NET: Service/Session.cs)."""

    def test_to_xml_uses_dotnet_tag_and_id_attribute(self):
        """Testa que a sessão é serializada como <SESSION ID="..."/>."""
        elem = Session(jsession_id="SESSION_TO_KILL").to_xml()

        assert elem.tag == "SESSION"
        assert elem.get("ID") == "SESSION_TO_KILL"
        assert "jsessionid" not in elem.attrib
        assert etree.tostring(elem) == b'<SESSION ID="SESSION_TO_KILL"/>'

    def test_to_xml_uses_dotnet_user_attributes(self):
        """Testa que user_id/user_name usam USERID/USERNAME como no .NET."""
        elem = Session(jsession_id="S1", user_id=7, user_name="admin").to_xml()

        assert elem.get("USERID") == "7"
        assert elem.get("USERNAME") == "admin"
        assert "userId" not in elem.attrib
        assert "userName" not in elem.attrib

    def test_from_xml_reads_dotnet_attributes(self):
        """Testa a desserialização do formato .NET."""
        element = etree.fromstring('<SESSION ID="S1" USERID="7" USERNAME="admin"/>')

        session = Session.from_xml(element)

        assert session.jsession_id == "S1"
        assert session.user_id == 7
        assert session.user_name == "admin"

    def test_from_xml_accepts_legacy_attributes(self):
        """Testa que o formato legado do SDK Python continua sendo lido."""
        element = etree.fromstring(
            '<session jsessionid="S1" userId="7" userName="admin"/>'
        )

        session = Session.from_xml(element)

        assert session.jsession_id == "S1"
        assert session.user_id == 7
        assert session.user_name == "admin"

    def test_round_trip(self):
        """Testa que to_xml/from_xml preservam os valores."""
        original = Session(jsession_id="S1", user_id=7, user_name="admin")

        restored = Session.from_xml(original.to_xml())

        assert restored == original
