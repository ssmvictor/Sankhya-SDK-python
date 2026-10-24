# -*- coding: utf-8 -*-
"""
Testes de integração para KnowServicesRequestWrapper.

Testa serviços conhecidos: sessões, arquivos, imagens.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.sankhya_warning_level import SankhyaWarningLevel
# SankhyaWrapper.get_file/get_image retornam o ServiceFile de core.types
# (atributo ``filename``), não o de value_objects (atributo ``file_name``).
from sankhya_sdk.core.types import ServiceFile
from sankhya_sdk.models.service.event_types import SystemWarningRecipient
from sankhya_sdk.request_wrappers.know_services_request_wrapper import (
    KnowServicesRequestWrapper,
)

from .conftest import (
    FakeSankhyaServer,
    create_file_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_sessions_response,
    http_response,
    request_xml,
)


SERVICE_OK = b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'


def create_dwr_response() -> Mock:
    """
    Cria mock da resposta do registro de user agent via DWR.

    ``SankhyaWrapper.authenticate()`` faz duas requisições HTTP: o login
    (MobileLoginSP.login) e, em seguida, o POST de registro de user agent
    em /mge/dwr/exec/DWRController.execute.dwr. Toda sequência de respostas
    mockadas precisa, portanto, ter esta resposta logo após a de login;
    caso contrário a chamada DWR consome a resposta da operação testada.

    Returns:
        Mock configurado como resposta HTTP do DWR
    """
    response = create_mock_response(200, b"")
    response.text = ""
    return response


@contextmanager
def _know_services_session(mock_session_class, server: FakeSankhyaServer) -> Iterator[SankhyaContext]:
    """
    Autentica um contexto contra o servidor simulado e inicializa o
    KnowServicesRequestWrapper com ele, liberando tudo ao final.

    O ``FakeSankhyaServer`` responde login/logout/DWR de qualquer sessão
    (no .NET o wrapper adquire uma sessão própria,
    KnowServicesRequestWrapper.cs:19-21) e entrega a fila de respostas
    apenas às chamadas de serviço, registrando o XML enviado.
    """
    mock_session_class.return_value.request.side_effect = server
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    ctx = SankhyaContext(wrapper=wrapper)
    try:
        KnowServicesRequestWrapper.initialize(ctx)
        yield ctx
    finally:
        KnowServicesRequestWrapper.dispose()
        ctx.dispose()


def _request_urls(mock_session: MagicMock) -> List[str]:
    """Retorna as URLs de todas as requisições HTTP feitas na sessão mockada."""
    return [
        str(call.kwargs.get("url", ""))
        for call in mock_session.request.call_args_list
    ]


@pytest.mark.integration
class TestKnowServicesSession:
    """Testes de gerenciamento de sessões."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_get_sessions(self, mock_session_class):
        """Testa obtenção de sessões ativas."""
        # <SESSIONS><SESSION ID USERID USERNAME HOST/></SESSIONS>
        # (Service/SessionsResponse.cs e Service/Session.cs no .NET)
        server = FakeSankhyaServer([
            http_response(200, create_sessions_response([
                {"ID": "SESSION_ADMIN", "USERID": "1", "USERNAME": "admin", "HOST": "192.168.1.1"},
                {"ID": "SESSION_USER1", "USERID": "2", "USERNAME": "user1", "HOST": "192.168.1.2"},
            ])),
        ])
        
        with _know_services_session(mock_session_class, server):
            sessions = KnowServicesRequestWrapper.get_sessions()
        
        # Deve retornar a lista de sessões com os atributos do protocolo
        assert isinstance(sessions, list)
        assert len(sessions) == 2
        assert [
            (s.session_id, s.user_id, s.user_name, s.host) for s in sessions
        ] == [
            ("SESSION_ADMIN", 1, "admin", "192.168.1.1"),
            ("SESSION_USER1", 2, "user1", "192.168.1.2"),
        ]
        assert server.calls == [ServiceName.SESSION_GET_ALL.internal_value]

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_kill_session(self, mock_session_class):
        """Testa encerramento de sessão."""
        server = FakeSankhyaServer([http_response(200, SERVICE_OK)])
        
        with _know_services_session(mock_session_class, server):
            # Encerrar sessão de outro usuário
            KnowServicesRequestWrapper.kill_session("SESSION_TO_KILL")
        
        # Não deve ter lançado exceção e a requisição deve ter sido enviada
        # ao serviço de encerramento com o ID da sessão alvo:
        # <SESSION ID="..."/> (KnowServicesRequestWrapper.cs:41, Session.cs:53)
        (body,) = server.bodies(ServiceName.SESSION_KILL)
        sessions = request_xml(body).findall("requestBody/SESSION")
        assert len(sessions) == 1
        assert sessions[0].attrib == {"ID": "SESSION_TO_KILL"}


@pytest.mark.integration
class TestKnowServicesFiles:
    """Testes de operações com arquivos."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_get_file(self, mock_session_class):
        """Testa download de arquivo."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        file_resp = create_file_response(
            data=b"PDF_CONTENT_HERE",
            content_type="application/pdf",
            filename="document.pdf",
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), file_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            file = wrapper.get_file("FILE_KEY_123")
            
            assert isinstance(file, ServiceFile)
            assert file.data == b"PDF_CONTENT_HERE"
            assert file.content_type == "application/pdf"
            assert file.filename == "document.pdf"
            # Mesmo endpoint do .NET: mge/visualizadorArquivos.mge?chaveArquivo=<key>
            assert any(
                "/mge/visualizadorArquivos.mge?chaveArquivo=FILE_KEY_123" in url
                for url in _request_urls(mock_session)
            )
        finally:
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_get_file_with_invalid_key(self, mock_session_class):
        """Testa erro com chave inválida."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(404, b"File not found")
        error_resp.ok = False
        # Como um requests.Response real, raise_for_status() lança HTTPError em 4xx
        error_resp.raise_for_status.side_effect = requests.HTTPError(
            "404 Client Error: Not Found", response=error_resp
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), error_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            # O erro HTTP 404 deve ser propagado (e não, por exemplo, um
            # StopIteration de mock esgotado)
            with pytest.raises(requests.HTTPError):
                wrapper.get_file("INVALID_KEY")
        finally:
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_large_file_download(self, mock_session_class):
        """Testa download de arquivo grande."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Arquivo grande (1MB de dados simulados)
        large_content = b"X" * (1024 * 1024)
        file_resp = create_file_response(
            data=large_content,
            content_type="application/octet-stream",
            filename="large_file.bin",
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), file_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            file = wrapper.get_file("LARGE_FILE_KEY")
            
            assert len(file.data) == 1024 * 1024
        finally:
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_file_downloads(self, mock_session_class):
        """Testa downloads simultâneos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        file_requests: List[str] = []
        lock = threading.Lock()
        
        def server(method: str, url: str, **kwargs: Any) -> Mock:
            """Responde cada download com o conteúdo da chave pedida na URL."""
            query = parse_qs(urlparse(url).query)
            if "chaveArquivo" in query:
                key = query["chaveArquivo"][0]
                with lock:
                    file_requests.append(key)
                return create_file_response(
                    data=f"{key}_CONTENT".encode(),
                    content_type="text/plain",
                    filename=f"{key}.txt",
                )
            service = query.get("serviceName", [""])[0]
            if service == ServiceName.LOGIN.internal_value:
                return create_mock_response(200, create_login_response())
            if service == ServiceName.LOGOUT.internal_value:
                return create_mock_response(200, create_logout_response())
            assert "DWRController" in url, f"URL inesperada: {url}"
            return create_dwr_response()
        
        mock_session.request.side_effect = server
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            results: Dict[str, ServiceFile] = {}
            errors = []
            
            def download_file(key: str):
                try:
                    file = wrapper.get_file(key)
                    with lock:
                        results[key] = file
                except Exception as e:
                    with lock:
                        errors.append(e)
            
            keys = [f"KEY_{i}" for i in range(3)]
            threads = [
                threading.Thread(target=download_file, args=(key,))
                for key in keys
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=5)
            
            assert not any(t.is_alive() for t in threads)
            
            # Todos os downloads devem ter sucesso, cada thread com o arquivo
            # da chave que pediu
            assert errors == []
            assert sorted(file_requests) == keys
            assert {key: f.data for key, f in results.items()} == {
                key: f"{key}_CONTENT".encode() for key in keys
            }
            assert {key: f.filename for key, f in results.items()} == {
                key: f"{key}.txt" for key in keys
            }
        finally:
            wrapper.dispose()


@pytest.mark.integration
class TestKnowServicesImages:
    """Testes de operações com imagens."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_get_image(self, mock_session_class):
        """Testa download de imagem."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Simular imagem PNG
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image_resp = create_file_response(
            data=png_header,
            content_type="image/png",
            filename="image.png",
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), image_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            image = wrapper.get_image("Produto", {"CODPROD": 1})
            
            # Servidor respondeu 200 com imagem: não pode retornar None
            assert image is not None
            assert image.data.startswith(b"\x89PNG")
            # Mesmo endpoint do .NET: mge/{entity}@IMAGEM@{key}={value}.dbimage
            assert any(
                url.endswith("/mge/Produto@IMAGEM@CODPROD=1.dbimage")
                for url in _request_urls(mock_session)
            )
        finally:
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_get_image_for_entity(self, mock_session_class):
        """Testa obtenção de imagem de entidade."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Simular imagem JPEG
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        image_resp = create_file_response(
            data=jpeg_header,
            content_type="image/jpeg",
            filename="partner.jpg",
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), image_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            image = wrapper.get_image("Parceiro", {"CODPARC": 123})
            
            # Servidor respondeu 200 com imagem: não pode retornar None
            assert image is not None
            assert image.content_type == "image/jpeg"
        finally:
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_get_image_not_found(self, mock_session_class):
        """Testa quando imagem não existe."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Resposta 404 para imagem não encontrada
        not_found_resp = create_mock_response(404, b"")
        not_found_resp.ok = False
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), not_found_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            # HTTP 404 retorna None (mesmo comportamento do GetImage do .NET)
            image = wrapper.get_image("Parceiro", {"CODPARC": 99999})
            assert image is None
        finally:
            wrapper.dispose()


@pytest.mark.integration
class TestKnowServicesMessaging:
    """Testes de operações de mensagens."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_send_warning(self, mock_session_class):
        """Testa envio de aviso."""
        server = FakeSankhyaServer([http_response(200, SERVICE_OK)])
        
        with _know_services_session(mock_session_class, server):
            KnowServicesRequestWrapper.send_warning(
                title="Teste",
                description="Mensagem de teste",
                recipients=[
                    SystemWarningRecipient(user_id=1),
                    SystemWarningRecipient(user_id=2),
                ],
            )
        
        # <aviso importancia="3"><titulo/><descricao/><destinatario id/>
        # (KnowServicesRequestWrapper.cs:46-74, SystemWarning.cs,
        # SystemWarningRecipient.cs); sem dica, <Dica> não é enviado
        (body,) = server.bodies(ServiceName.WARNING_SEND)
        warnings = request_xml(body).findall("requestBody/aviso")
        assert len(warnings) == 1
        warning = warnings[0]
        assert warning.attrib == {
            "importancia": SankhyaWarningLevel.INFORMATION.internal_value
        }
        assert warning.findtext("titulo") == "Teste"
        assert warning.findtext("descricao") == "Mensagem de teste"
        assert warning.find("Dica") is None
        assert [r.attrib for r in warning.findall("destinatario")] == [
            {"id": "1"},
            {"id": "2"},
        ]

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_send_warning_with_tip_and_level(self, mock_session_class):
        """Testa envio de aviso com dica e nível, para todos os usuários."""
        server = FakeSankhyaServer([http_response(200, SERVICE_OK)])
        
        with _know_services_session(mock_session_class, server):
            KnowServicesRequestWrapper.send_warning(
                title="Manutenção",
                description="Sistema indisponível às 22h",
                tip="Salve seu trabalho",
                level=SankhyaWarningLevel.URGENT,
            )
        
        (body,) = server.bodies(ServiceName.WARNING_SEND)
        warning = request_xml(body).find("requestBody/aviso")
        assert warning.get("importancia") == SankhyaWarningLevel.URGENT.internal_value
        assert warning.findtext("Dica") == "Salve seu trabalho"
        # Sem destinatários informados, nenhum <destinatario> é enviado
        assert warning.findall("destinatario") == []


@pytest.mark.integration
class TestKnowServicesFileOperations:
    """Testes de operações de arquivo via KnowServices."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_open_file(self, mock_session_class):
        """Testa abertura de arquivo."""
        server = FakeSankhyaServer([
            http_response(200, b'''<?xml version="1.0"?>
            <serviceResponse status="1">
                <responseBody>
                    <chave valor="FILE_KEY_RETURNED"/>
                </responseBody>
            </serviceResponse>'''),
        ])
        
        with _know_services_session(mock_session_class, server):
            key = KnowServicesRequestWrapper.open_file("/path/to/file.pdf")
        
        # Deve retornar a chave do atributo "valor" de <chave>
        # (.NET: response.ResponseBody.Key.Value)
        assert isinstance(key, str)
        assert key == "FILE_KEY_RETURNED"
        
        # <config path="..."/> (KnowServicesRequestWrapper.cs:635, Config.cs:14)
        (body,) = server.bodies(ServiceName.FILE_OPEN)
        assert request_xml(body).find("requestBody/config").get("path") == "/path/to/file.pdf"

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_delete_files(self, mock_session_class):
        """Testa exclusão de arquivos."""
        server = FakeSankhyaServer([http_response(200, SERVICE_OK)])
        
        with _know_services_session(mock_session_class, server):
            KnowServicesRequestWrapper.delete_files(["/path/to/file1.pdf", "/path/to/file2.pdf"])
        
        # <arquivos><path/></arquivos> e o evento de confirmação em
        # <clientEventList><clientEvent/></clientEventList>
        # (KnowServicesRequestWrapper.cs:641-657, RequestBody.cs)
        (body,) = server.bodies(ServiceName.FILE_DELETE)
        request_body = request_xml(body).find("requestBody")
        assert [p.text for p in request_body.findall("arquivos/path")] == [
            "/path/to/file1.pdf",
            "/path/to/file2.pdf",
        ]
        assert [e.text for e in request_body.findall("clientEventList/clientEvent")] == [
            "br.com.sankhya.actionbutton.clientconfirm"
        ]


@pytest.mark.integration
class TestKnowServicesContextManager:
    """Testes de context manager."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_context_manager_usage(self, mock_session_class):
        """Testa uso como context manager."""
        server = FakeSankhyaServer([http_response(200, create_sessions_response([]))])
        mock_session_class.return_value.request.side_effect = server
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        
        try:
            # __enter__ só cria uma sessão própria (via SankhyaSettings) se o
            # wrapper ainda não foi inicializado; para usar o contexto existente
            # é preciso inicializar antes de entrar no bloco.
            KnowServicesRequestWrapper.initialize(ctx)
            
            with KnowServicesRequestWrapper():
                sessions = KnowServicesRequestWrapper.get_sessions()
                assert sessions == []
            
            # __exit__ deve liberar o wrapper
            assert KnowServicesRequestWrapper._initialized is False
            assert server.calls == [ServiceName.SESSION_GET_ALL.internal_value]
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()
