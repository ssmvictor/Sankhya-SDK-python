# -*- coding: utf-8 -*-
"""
Fixtures compartilhadas para testes de integração.

Fornece mocks, fixtures e helpers para simular respostas da API Sankhya
e testar fluxos completos de forma determinística.
"""

from __future__ import annotations

import base64
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
from xml.sax.saxutils import escape as xml_escape

import pytest
import requests
from lxml import etree

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.models.transport.neighborhood import Neighborhood
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)


T = TypeVar("T", bound=EntityBase)


# =============================================================================
# Helper Functions
# =============================================================================


def create_mock_response(
    status_code: int = 200,
    xml_content: bytes = b"",
    headers: Optional[Dict[str, str]] = None,
) -> Mock:
    """
    Cria objeto Mock de resposta HTTP.
    
    Args:
        status_code: Código de status HTTP
        xml_content: Conteúdo XML da resposta
        headers: Headers HTTP opcionais
        
    Returns:
        Mock configurado como resposta HTTP
    """
    mock_response = Mock()
    mock_response.ok = 200 <= status_code < 400
    mock_response.status_code = status_code
    mock_response.content = xml_content
    mock_response.headers = headers or {"Content-Type": "application/xml"}
    return mock_response


def create_user_agent_response(sankhya_version: str = "4.0.0") -> Mock:
    """
    Cria mock da resposta HTTP do registro de user agent (DWR).

    ``SankhyaWrapper.authenticate`` faz uma segunda requisição HTTP logo
    após o login (``/mge/dwr/exec/DWRController.execute.dwr``) para
    registrar o user agent e obter a versão do Sankhya. Testes que
    enfileiram respostas em ``requests.Session.request`` precisam
    reservar uma resposta para essa chamada.

    Args:
        sankhya_version: Versão do Sankhya informada no HTML

    Returns:
        Mock configurado como resposta HTML do DWR
    """
    html = f'<html><script>var SYSVERSION = "{sankhya_version}";</script></html>'
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = html
    mock_response.content = html.encode("utf-8")
    mock_response.headers = {"Content-Type": "text/html"}
    return mock_response


def create_authentication_responses(
    session_id: str = "MOCK_SESSION_ID_12345",
    user_code: int = 1,
) -> List[Mock]:
    """
    Cria as respostas HTTP consumidas por ``SankhyaWrapper.authenticate``.

    A autenticação faz duas requisições: o login (``MobileLoginSP.login``)
    e o registro de user agent via DWR.

    Args:
        session_id: ID da sessão retornado no login
        user_code: Código do usuário retornado no login

    Returns:
        Lista [resposta do login, resposta do registro de user agent]
    """
    return [
        create_mock_response(200, create_login_response(session_id, user_code)),
        create_user_agent_response(),
    ]


def _create_entity_xml(entity: Dict[str, Any]) -> str:
    """
    Gera o XML de uma entidade no formato do protocolo Sankhya.

    Cada campo é um elemento filho com o nome do campo, por exemplo
    ``<entity><CODPARC>1</CODPARC></entity>`` (formato lido por
    ``ServiceResponse`` e por ``ReadDynamic`` no SDK .NET). Os valores
    são escapados para XML.

    Args:
        entity: Dicionário com campos da entidade

    Returns:
        XML da entidade
    """
    fields = "".join(
        f"<{k}>{xml_escape(str(v))}</{k}>"
        for k, v in entity.items()
    )
    return f"<entity>{fields}</entity>"


def create_success_response(
    entities: Optional[List[Dict[str, Any]]] = None,
    total_records: Optional[int] = None,
) -> bytes:
    """
    Gera XML de resposta bem-sucedida.
    
    Args:
        entities: Lista de dicionários com campos da entidade
        total_records: Total de registros (para paginação)
        
    Returns:
        XML serializado como bytes
    """
    entities_xml = ""
    
    if entities:
        entity_strs = [_create_entity_xml(entity) for entity in entities]
        entities_xml = f"<entities>{' '.join(entity_strs)}</entities>"
    
    total_attr = f' totalRecords="{total_records}"' if total_records else ""
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<serviceResponse status="1"{total_attr}>
    <responseBody>
        {entities_xml}
    </responseBody>
</serviceResponse>'''.encode("utf-8")


def create_error_response(error_code: str, message: str) -> bytes:
    """
    Gera XML de resposta de erro.
    
    Args:
        error_code: Código do erro
        message: Mensagem de erro
        
    Returns:
        XML serializado como bytes
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<serviceResponse status="0">
    <statusMessage>{message}</statusMessage>
    <errorCode>{error_code}</errorCode>
</serviceResponse>'''.encode("utf-8")


def create_login_response(
    session_id: str = "MOCK_SESSION_ID_12345",
    user_code: int = 1,
) -> bytes:
    """
    Gera XML de resposta de login.
    
    Args:
        session_id: ID da sessão
        user_code: Código do usuário
        
    Returns:
        XML serializado como bytes
    """
    # Encode user_code as base64 like the API does
    user_code_b64 = base64.b64encode(str(user_code).encode()).decode()
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<serviceResponse status="1">
    <responseBody>
        <jsessionid>{session_id}</jsessionid>
        <idusu>{user_code_b64}</idusu>
    </responseBody>
</serviceResponse>'''.encode("utf-8")


def create_logout_response() -> bytes:
    """
    Gera XML de resposta de logout.
    
    Returns:
        XML serializado como bytes
    """
    return b'''<?xml version="1.0" encoding="UTF-8"?>
<serviceResponse status="1"></serviceResponse>'''


def create_sessions_response(sessions: Optional[List[Dict[str, Any]]] = None) -> bytes:
    """
    Gera XML de resposta de sessões ativas.
    
    Args:
        sessions: Lista de sessões com campos como user_name, ip_address, etc.
        
    Returns:
        XML serializado como bytes
    """
    if not sessions:
        sessions = []
    
    session_strs = []
    for sess in sessions:
        attrs = " ".join(f'{k}="{v}"' for k, v in sess.items())
        session_strs.append(f"<sessao {attrs}/>")
    
    sessions_xml = "".join(session_strs)
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<serviceResponse status="1">
    <responseBody>
        <sessoes>
            {sessions_xml}
        </sessoes>
    </responseBody>
</serviceResponse>'''.encode("utf-8")


def create_file_response(
    data: bytes = b"FILE_CONTENT",
    content_type: str = "application/pdf",
    filename: str = "document.pdf",
) -> Mock:
    """
    Cria mock de resposta de download de arquivo.
    
    Args:
        data: Conteúdo binário do arquivo
        content_type: MIME type do arquivo
        filename: Nome do arquivo
        
    Returns:
        Mock configurado como resposta de arquivo
    """
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.content = data
    mock_response.headers = {
        "Content-Type": content_type,
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return mock_response


def create_paged_response(
    entities: List[Dict[str, Any]],
    page: int,
    total_records: int,
    page_size: int = 100,
) -> bytes:
    """
    Gera XML de resposta paginada.
    
    Args:
        entities: Entidades da página atual
        page: Número da página (0-indexed)
        total_records: Total de registros
        page_size: Tamanho da página
        
    Returns:
        XML serializado como bytes
    """
    entity_strs = [_create_entity_xml(entity) for entity in entities]
    
    entities_xml = "".join(entity_strs)
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<serviceResponse status="1" totalRecords="{total_records}">
    <responseBody>
        <entities>
            {entities_xml}
        </entities>
    </responseBody>
</serviceResponse>'''.encode("utf-8")


# =============================================================================
# Servidor Sankhya simulado (roteado pelo serviceName)
# =============================================================================


def http_response(status_code: int, content: bytes) -> requests.Response:
    """
    Cria uma resposta HTTP real (requests.Response).

    Usa o objeto real para que ``raise_for_status`` lance HTTPError em
    respostas 4xx/5xx, como no servidor de verdade.
    """
    response = requests.Response()
    response.status_code = status_code
    response._content = content
    response.headers["Content-Type"] = "text/xml;charset=UTF-8"
    response.encoding = "utf-8"
    response.url = "http://test.local:8180/mge/service.sbr"
    return response


def entities_response(
    *rows: Dict[str, Any],
    service: ServiceName = ServiceName.CRUD_SERVICE_FIND,
) -> bytes:
    """Gera XML de resposta do CRUDServiceProvider com as entidades informadas."""
    entities = "".join(_create_entity_xml(row) for row in rows)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<serviceResponse serviceName="{service.internal_value}" status="1">'
        f'<responseBody><entities total="{len(rows)}">{entities}</entities></responseBody>'
        "</serviceResponse>"
    ).encode("utf-8")


def request_xml(body: str) -> etree._Element:
    """Interpreta o corpo XML de uma requisição enviada ao servidor simulado."""
    return etree.fromstring(body.encode("utf-8"))


def find_criteria(body: str) -> Optional[str]:
    """
    Expressão do critério de uma requisição CRUDServiceProvider.loadRecords.

    No .NET (ServiceRequestExtensions.HandleService, CrudServiceFind) o
    critério montado a partir das chaves/campos preenchidos da entidade vai
    em ``dataSet/criteria/expression``.
    """
    return request_xml(body).findtext("requestBody/dataSet/criteria/expression")


def save_data_row(body: str) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    """
    Chaves e campos locais do ``dataRow`` de CRUDServiceProvider.saveRecord.

    No .NET (ServiceRequestExtensions.HandleService, CrudServiceSave) as
    chaves preenchidas vão em ``dataRow/key`` e os demais campos em
    ``dataRow/localFields``.

    Returns:
        Tupla (chaves, campos locais), cada uma como {nome: valor}
    """
    rows = request_xml(body).findall("requestBody/dataSet/dataRow")
    assert len(rows) == 1, f"saveRecord deveria ter um único dataRow: {body}"
    keys = rows[0].find("key")
    local_fields = rows[0].find("localFields")
    return (
        {child.tag: child.text for child in (keys if keys is not None else [])},
        {child.tag: child.text for child in (local_fields if local_fields is not None else [])},
    )


ServerReply = Union[requests.Response, BaseException]
ServerResponder = Callable[[str], ServerReply]


class FakeSankhyaServer:
    """
    Simula o servidor Sankhya como ``side_effect`` de ``requests.Session.request``.

    Roteia cada requisição pelo parâmetro ``serviceName`` da URL. Login e
    logout sempre respondem com sucesso (cada login gera um JSESSIONID
    único) e o registro de user agent (DWR) responde vazio, de modo que as
    sessões adicionais (ex.: a sessão dedicada do SimpleCRUDRequestWrapper,
    ``Context.AcquireNewSession`` no .NET) não consomem as respostas do teste.

    As demais chamadas de serviço consomem, em ordem, a fila de respostas.
    Cada item da fila pode ser:

    - uma resposta HTTP, devolvida como está;
    - uma exceção, lançada (falha de transporte);
    - uma função que recebe o corpo XML da requisição e devolve a resposta
      (ou exceção), para responder de acordo com o que foi pedido.

    Uma chamada além da fila falha com AssertionError. O serviço e o corpo
    XML de cada chamada ficam registrados. Thread-safe.
    """

    def __init__(
        self,
        responses: Sequence[Union[ServerReply, ServerResponder]] = (),
    ) -> None:
        self._lock = threading.Lock()
        self._responses = list(responses)
        self.calls: List[str] = []
        self.requests: List[Tuple[str, str]] = []
        self.logins = 0
        self.logouts = 0

    def calls_to(self, service: ServiceName) -> int:
        """Retorna quantas requisições foram feitas para o serviço."""
        with self._lock:
            return self.calls.count(service.internal_value)

    def bodies(self, service: ServiceName) -> List[str]:
        """Retorna os corpos XML enviados para o serviço, em ordem."""
        with self._lock:
            return [
                body for name, body in self.requests
                if name == service.internal_value
            ]

    def __call__(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        service = parse_qs(urlparse(url).query).get("serviceName", [""])[0]
        data = kwargs.get("data")
        body = data.decode("utf-8") if isinstance(data, bytes) else (data or "")

        with self._lock:
            if service == ServiceName.LOGIN.internal_value:
                self.logins += 1
                session_id = f"SESSION_{uuid4().hex}"
                return http_response(200, create_login_response(session_id))

            if service == ServiceName.LOGOUT.internal_value:
                self.logouts += 1
                return http_response(200, create_logout_response())

            if not service:
                assert "DWRController" in url, f"URL inesperada: {url}"
                return http_response(200, b"")

            self.calls.append(service)
            self.requests.append((service, body))
            if not self._responses:
                raise AssertionError(
                    f"Requisição inesperada #{len(self.calls)} para {service}"
                )
            item = self._responses.pop(0)

        # Mocks também são "callable": só funções respondem pelo corpo
        if not isinstance(item, (requests.Response, Mock, BaseException)):
            item = item(body)
        if isinstance(item, BaseException):
            raise item
        return item


@contextmanager
def simple_crud_session() -> Iterator[SankhyaWrapper]:
    """
    Autentica um SankhyaWrapper e inicializa o SimpleCRUDRequestWrapper
    com um SankhyaContext, liberando todos os recursos ao final.

    ``SimpleCRUDRequestWrapper.initialize(context)`` adquire uma sessão
    dedicada (novo login), como ``Context.AcquireNewSession(SimpleCrud)``
    no .NET (SimpleCRUDRequestWrapper.cs:17-21). O contexto é descartado
    mesmo se a inicialização falhar, para não deixar sessões registradas
    no ``SankhyaContext`` (estado de classe) para os próximos testes.
    """
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    context = SankhyaContext(wrapper=wrapper)
    try:
        SimpleCRUDRequestWrapper.initialize(context)
        yield wrapper
    finally:
        SimpleCRUDRequestWrapper.dispose()
        context.dispose()


# =============================================================================
# Sample Entity Factories
# =============================================================================


@dataclass
class SamplePartner:
    """Factory para criar Partners de teste."""
    
    @staticmethod
    def create(
        code: int = 1,
        name: str = "Parceiro Teste",
        company_name: Optional[str] = None,
        is_active: bool = True,
        email: Optional[str] = None,
    ) -> Partner:
        """Cria um Partner para testes."""
        partner = Partner(
            code=code,
            name=name,
        )
        if company_name:
            partner.company_name = company_name
        if email:
            partner.email_address = email
        return partner
    
    @staticmethod
    def to_xml_dict(partner: Partner) -> Dict[str, Any]:
        """Converte Partner para dicionário XML."""
        result = {"CODPARC": partner.code}
        if partner.name:
            result["NOMEPARC"] = partner.name
        if partner.company_name:
            result["RAZAOSOCIAL"] = partner.company_name
        if partner.email_address:
            result["EMAIL"] = partner.email_address
        return result


@dataclass
class SampleProduct:
    """Factory para criar Products de teste."""
    
    @staticmethod
    def create(
        code: int = 1,
        name: str = "Produto Teste",
        is_active: bool = True,
        code_volume: str = "UN",
    ) -> Product:
        """Cria um Product para testes."""
        product = Product(
            code=code,
            name=name,
            code_volume=code_volume,
        )
        return product
    
    @staticmethod
    def to_xml_dict(product: Product) -> Dict[str, Any]:
        """Converte Product para dicionário XML."""
        result = {"CODPROD": product.code}
        if product.name:
            result["DESCRPROD"] = product.name
        if product.code_volume:
            result["CODVOL"] = product.code_volume
        return result


@dataclass  
class SampleNeighborhood:
    """Factory para criar Neighborhoods de teste."""
    
    @staticmethod
    def create(
        code: int = 1,
        name: str = "Centro",
    ) -> Neighborhood:
        """Cria um Neighborhood para testes."""
        return Neighborhood(code=code, name=name)
    
    @staticmethod
    def to_xml_dict(neighborhood: Neighborhood) -> Dict[str, Any]:
        """Converte Neighborhood para dicionário XML."""
        result = {"CODBAI": neighborhood.code}
        if neighborhood.name:
            result["NOMEBAI"] = neighborhood.name
        return result


# =============================================================================
# Pre-configured XML Responses
# =============================================================================


@pytest.fixture
def sample_xml_responses() -> Dict[str, bytes]:
    """
    Dicionário com XMLs de resposta para diferentes operações.
    
    Returns:
        Dicionário service_name -> xml_response
    """
    return {
        "login_success": create_login_response("SESSION123", 1),
        "login_failure": create_error_response(
            "AUTH.FAILED", "Credenciais inválidas"
        ),
        "logout_success": create_logout_response(),
        "find_partner_success": create_success_response([
            {"CODPARC": "1", "NOMEPARC": "Parceiro Teste"}
        ]),
        "find_partners_multiple": create_success_response([
            {"CODPARC": "1", "NOMEPARC": "Parceiro 1"},
            {"CODPARC": "2", "NOMEPARC": "Parceiro 2"},
            {"CODPARC": "3", "NOMEPARC": "Parceiro 3"},
        ], total_records=3),
        "find_empty": create_success_response([]),
        "create_success": create_success_response([
            {"CODPARC": "100", "NOMEPARC": "Novo Parceiro"}
        ]),
        "update_success": create_success_response([
            {"CODPARC": "1", "NOMEPARC": "Nome Atualizado"}
        ]),
        "delete_success": b'''<?xml version="1.0" encoding="UTF-8"?>
            <serviceResponse status="1"></serviceResponse>''',
        "error_not_found": create_error_response(
            "ENTITY.NOT_FOUND", "Registro não encontrado"
        ),
        "error_duplicate_key": create_error_response(
            "DB.DUPLICATE_KEY", "Chave duplicada"
        ),
        "error_fk_violation": create_error_response(
            "DB.FK_VIOLATION", "Violação de chave estrangeira"
        ),
        "error_timeout": create_error_response(
            "TIMEOUT", "Timeout na operação"
        ),
        "error_deadlock": create_error_response(
            "deadlock", "Deadlock detectado"
        ),
        "sessions_list": create_sessions_response([
            {"CODUSU": "1", "NOMEUSU": "admin", "IP": "192.168.1.1"},
            {"CODUSU": "2", "NOMEUSU": "user1", "IP": "192.168.1.2"},
        ]),
    }


# =============================================================================
# Mock Session Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """
    Mock de requests.Session configurável.
    
    Returns:
        MagicMock para requests.Session
    """
    return MagicMock()


@pytest.fixture
def mock_http_responses():
    """
    Contexto para configurar respostas HTTP sequenciais.
    
    Yields:
        Função para adicionar respostas
    """
    responses = []
    
    def add_response(response: Mock):
        responses.append(response)
    
    def get_responses():
        return responses
    
    yield add_response, get_responses


# =============================================================================
# Wrapper Fixtures
# =============================================================================


@pytest.fixture
def mock_sankhya_server(sample_xml_responses):
    """
    Mock do servidor HTTP com respostas XML pré-configuradas.
    
    Este fixture configura um mock completo do servidor Sankhya que pode
    ser usado para testar fluxos de integração sem depender de um servidor real.
    
    Args:
        sample_xml_responses: Fixture com respostas XML pré-definidas
        
    Yields:
        Tupla (mock_session, add_response_func)
    """
    with patch("sankhya_sdk.core.low_level_wrapper.requests.Session") as mock_cls:
        mock_session = MagicMock()
        mock_cls.return_value = mock_session
        
        responses_queue = []
        
        def add_response(response: Mock):
            """Adiciona uma resposta à fila."""
            responses_queue.append(response)
        
        def configure_side_effect():
            """Configura o side_effect do mock."""
            mock_session.request.side_effect = responses_queue
        
        # Inicializa com autenticação bem-sucedida por padrão: authenticate()
        # consome o login e o registro de user agent (DWR)
        responses_queue.extend(create_authentication_responses("SESSION123", 1))
        
        yield mock_session, add_response, configure_side_effect


@pytest.fixture
def authenticated_wrapper(mock_sankhya_server, sample_xml_responses):
    """
    Wrapper autenticado para testes.
    
    Cria um SankhyaWrapper pré-autenticado usando mocks.
    
    Args:
        mock_sankhya_server: Fixture do servidor mockado
        sample_xml_responses: Fixture com respostas XML
        
    Yields:
        SankhyaWrapper autenticado
    """
    mock_session, add_response, configure = mock_sankhya_server
    
    # Adiciona resposta de logout para cleanup
    logout_resp = create_mock_response(200, sample_xml_responses["logout_success"])
    add_response(logout_resp)
    
    configure()
    
    wrapper = SankhyaWrapper(
        host="http://mock.sankhya.local",
        port=8180,
    )
    
    wrapper.authenticate("testuser", "testpass")
    
    yield wrapper
    
    wrapper.dispose()


@pytest.fixture
def sample_partner() -> Partner:
    """Fixture para Partner de teste."""
    return SamplePartner.create()


@pytest.fixture
def sample_product() -> Product:
    """Fixture para Product de teste."""
    return SampleProduct.create()


@pytest.fixture
def sample_neighborhood() -> Neighborhood:
    """Fixture para Neighborhood de teste."""
    return SampleNeighborhood.create()


# =============================================================================
# Integration Test Markers
# =============================================================================


def pytest_configure(config):
    """Registra markers customizados para testes."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring mocked API"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests requiring real API connection"
    )
    config.addinivalue_line(
        "markers", "asyncio: Asynchronous tests"
    )
