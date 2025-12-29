# -*- coding: utf-8 -*-
"""
Fixtures compartilhadas para testes de integração.

Fornece mocks, fixtures e helpers para simular respostas da API Sankhya
e testar fluxos completos de forma determinística.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, TypeVar
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.value_objects.service_file import ServiceFile
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.models.transport.neighborhood import Neighborhood
from sankhya_sdk.models.transport.invoice_header import InvoiceHeader


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
        entity_strs = []
        for entity in entities:
            fields = "".join(
                f'<field name="{k}">{v}</field>'
                for k, v in entity.items()
            )
            entity_strs.append(f"<entity>{fields}</entity>")
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
    entity_strs = []
    for entity in entities:
        fields = "".join(
            f'<field name="{k}">{v}</field>'
            for k, v in entity.items()
        )
        entity_strs.append(f"<entity>{fields}</entity>")
    
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
        
        # Inicializa com login bem-sucedido por padrão
        login_resp = create_mock_response(200, sample_xml_responses["login_success"])
        responses_queue.append(login_resp)
        
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


# =============================================================================
# Async Fixtures
# =============================================================================


@pytest.fixture
def event_loop():
    """Cria event loop para testes assíncronos."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
