"""
Testes unitários para os tipos de sessões ativas (SessionInfo, SessionsResponse).

O formato XML esperado segue o SDK .NET
(Src/Sankhya/Service/SessionsResponse.cs e Src/Sankhya/Service/Session.cs):
<SESSIONS><SESSION ID="..." USERID="..." USERNAME="..." HOST="..." .../></SESSIONS>
"""

from lxml import etree

from sankhya_sdk.models.service.response_body import ResponseBody
from sankhya_sdk.models.service.user_types import SessionInfo, SessionsResponse


DOTNET_SESSIONS_XML = (
    "<SESSIONS>"
    '<SESSION ID="ABC123" CREATIONTIME="01/02/2024 08:00:00"'
    ' LASTACCESSEDTIME="01/02/2024 09:30:00" INACTIVEINTERVAL="15"'
    ' MAXINACTIVEINTERVAL="1800" USERAGENT="Mozilla/5.0" HOST="192.168.1.10"'
    ' LOGINTIME="01/02/2024 08:00:05" AUTHENTICATED="S" USERID="1"'
    ' USERNAME="SUP"/>'
    '<SESSION ID="DEF456" USERID="2" USERNAME="user1" HOST="192.168.1.11"'
    ' AUTHENTICATED="N"/>'
    "</SESSIONS>"
)


class TestSessionInfo:
    """Testes para a classe SessionInfo."""

    def test_from_xml_reads_all_dotnet_attributes(self):
        """Testa a leitura de todos os atributos de Session.cs."""
        element = etree.fromstring(DOTNET_SESSIONS_XML)[0]

        info = SessionInfo.from_xml(element)

        assert info.session_id == "ABC123"
        assert info.creation_time == "01/02/2024 08:00:00"
        assert info.last_accessed_time == "01/02/2024 09:30:00"
        assert info.inactive_interval == 15
        assert info.max_inactive_interval == 1800
        assert info.user_agent == "Mozilla/5.0"
        assert info.host == "192.168.1.10"
        assert info.login_time == "01/02/2024 08:00:05"
        assert info.is_authenticated is True
        assert info.user_id == 1
        assert info.user_name == "SUP"

    def test_from_xml_authenticated_n_is_false(self):
        """Testa que AUTHENTICATED="N" é desserializado como False."""
        element = etree.fromstring(DOTNET_SESSIONS_XML)[1]

        info = SessionInfo.from_xml(element)

        assert info.is_authenticated is False

    def test_from_xml_missing_attributes_are_none(self):
        """Testa que atributos ausentes resultam em None."""
        info = SessionInfo.from_xml(etree.fromstring('<SESSION ID="X"/>'))

        assert info.session_id == "X"
        assert info.user_id is None
        assert info.host is None
        assert info.inactive_interval is None
        assert info.is_authenticated is None

    def test_from_xml_accepts_legacy_attributes(self):
        """Testa que o formato legado do SDK Python continua sendo lido."""
        element = etree.fromstring(
            '<sessao sessionId="S1" idusu="7" nomeUsu="admin" codemp="1"'
            ' ip="10.0.0.1" inicio="t0" ultimaAtividade="t1" aplicacao="app"/>'
        )

        info = SessionInfo.from_xml(element)

        assert info.session_id == "S1"
        assert info.user_id == 7
        assert info.user_name == "admin"
        assert info.company_id == 1
        assert info.ip_address == "10.0.0.1"
        assert info.start_time == "t0"
        assert info.last_activity == "t1"
        assert info.application == "app"

    def test_to_xml_uses_dotnet_format(self):
        """Testa que a serialização usa <SESSION> com atributos do .NET."""
        info = SessionInfo(
            session_id="ABC123",
            user_id=1,
            user_name="SUP",
            host="192.168.1.10",
            inactive_interval=15,
            is_authenticated=True,
        )

        elem = info.to_xml()

        assert elem.tag == "SESSION"
        assert elem.get("ID") == "ABC123"
        assert elem.get("USERID") == "1"
        assert elem.get("USERNAME") == "SUP"
        assert elem.get("HOST") == "192.168.1.10"
        assert elem.get("INACTIVEINTERVAL") == "15"
        assert elem.get("AUTHENTICATED") == "S"

    def test_round_trip(self):
        """Testa que to_xml/from_xml preservam os valores."""
        original = SessionInfo.from_xml(etree.fromstring(DOTNET_SESSIONS_XML)[0])

        restored = SessionInfo.from_xml(original.to_xml())

        assert restored == original


class TestSessionsResponse:
    """Testes para a classe SessionsResponse."""

    def test_from_xml_reads_dotnet_session_elements(self):
        """Testa que os elementos <SESSION> de <SESSIONS> são lidos."""
        response = SessionsResponse.from_xml(etree.fromstring(DOTNET_SESSIONS_XML))

        assert [s.session_id for s in response.sessions] == ["ABC123", "DEF456"]
        assert [s.user_name for s in response.sessions] == ["SUP", "user1"]
        assert [s.host for s in response.sessions] == ["192.168.1.10", "192.168.1.11"]

    def test_from_xml_accepts_legacy_session_elements(self):
        """Testa que elementos legados <sessao> continuam sendo lidos."""
        element = etree.fromstring(
            '<SESSIONS><sessao sessionId="S1" nomeUsu="admin"/></SESSIONS>'
        )

        response = SessionsResponse.from_xml(element)

        assert len(response.sessions) == 1
        assert response.sessions[0].session_id == "S1"
        assert response.sessions[0].user_name == "admin"

    def test_from_xml_empty(self):
        """Testa que <SESSIONS/> vazio resulta em lista vazia."""
        response = SessionsResponse.from_xml(etree.fromstring("<SESSIONS/>"))

        assert response.sessions == []

    def test_to_xml_uses_dotnet_format(self):
        """Testa que a serialização gera <SESSIONS><SESSION .../></SESSIONS>."""
        response = SessionsResponse(
            sessions=[SessionInfo(session_id="A"), SessionInfo(session_id="B")]
        )

        elem = response.to_xml()

        assert elem.tag == "SESSIONS"
        assert [child.tag for child in elem] == ["SESSION", "SESSION"]
        assert [child.get("ID") for child in elem] == ["A", "B"]

    def test_round_trip(self):
        """Testa que to_xml/from_xml preservam as sessões."""
        original = SessionsResponse.from_xml(etree.fromstring(DOTNET_SESSIONS_XML))

        restored = SessionsResponse.from_xml(original.to_xml())

        assert restored == original

    def test_response_body_exposes_sessions(self):
        """Testa ResponseBody.Sessions.Sessions (.NET KnowServicesRequestWrapper.GetSessions)."""
        element = etree.fromstring(
            f"<responseBody>{DOTNET_SESSIONS_XML}</responseBody>"
        )

        body = ResponseBody.from_xml(element)

        assert [s.session_id for s in body.sessions.sessions] == ["ABC123", "DEF456"]
        assert body.sessions.sessions[0].user_id == 1
