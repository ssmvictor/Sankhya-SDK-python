# -*- coding: utf-8 -*-
"""
Testes de integração para KnowServicesRequestWrapper.

Testa serviços conhecidos: sessões, arquivos, imagens.
"""

from __future__ import annotations

import threading
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import (
    ServiceRequestFileNotFoundException,
    SankhyaException,
)
# SankhyaWrapper.get_file/get_image retornam o ServiceFile de core.types
# (atributo ``filename``), não o de value_objects (atributo ``file_name``).
from sankhya_sdk.core.types import ServiceFile
from sankhya_sdk.models.service.event_types import SystemWarningRecipient
from sankhya_sdk.request_wrappers.know_services_request_wrapper import (
    KnowServicesRequestWrapper,
)

from .conftest import (
    create_error_response,
    create_file_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_sessions_response,
    create_success_response,
)


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


def _find_service_call(mock_session: MagicMock, service: ServiceName) -> dict:
    """
    Retorna os kwargs da requisição HTTP enviada para o serviço informado.

    Args:
        mock_session: Mock de requests.Session usado pelo wrapper
        service: Serviço esperado

    Returns:
        kwargs da chamada ``request`` ou dicionário vazio se não houve chamada
    """
    marker = f"serviceName={service.internal_value}"
    for call in mock_session.request.call_args_list:
        if marker in str(call.kwargs.get("url", "")):
            return call.kwargs
    return {}


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
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        sessions_resp = create_mock_response(
            200, create_sessions_response([
                {"CODUSU": "1", "NOMEUSU": "admin", "IP": "192.168.1.1"},
                {"CODUSU": "2", "NOMEUSU": "user1", "IP": "192.168.1.2"},
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), sessions_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        KnowServicesRequestWrapper.initialize(ctx)
        
        try:
            sessions = KnowServicesRequestWrapper.get_sessions()
            
            # Deve retornar lista de sessões
            assert isinstance(sessions, list)
            assert _find_service_call(mock_session, ServiceName.SESSION_GET_ALL)
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_kill_session(self, mock_session_class):
        """Testa encerramento de sessão."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        kill_resp = create_mock_response(
            200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), kill_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        KnowServicesRequestWrapper.initialize(ctx)
        
        try:
            # Encerrar sessão de outro usuário
            KnowServicesRequestWrapper.kill_session("SESSION_TO_KILL")
            
            # Não deve ter lançado exceção e a requisição deve ter sido
            # enviada ao serviço de encerramento com o ID da sessão alvo
            kill_call = _find_service_call(mock_session, ServiceName.SESSION_KILL)
            assert kill_call
            assert b"SESSION_TO_KILL" in kill_call["data"]
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()


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
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Configurar múltiplas respostas de arquivo
        file_resps = [
            create_file_response(
                data=f"FILE_{i}_CONTENT".encode(),
                content_type="text/plain",
                filename=f"file_{i}.txt",
            )
            for i in range(3)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = (
            [login_resp, create_dwr_response()] + file_resps + [logout_resp]
        )
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            results = []
            errors = []
            
            def download_file(key: str):
                try:
                    file = wrapper.get_file(key)
                    results.append(file)
                except Exception as e:
                    errors.append(e)
            
            threads = [
                threading.Thread(target=download_file, args=(f"KEY_{i}",))
                for i in range(3)
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=5)
            
            # Todos os downloads devem ter sucesso, cada um com um arquivo
            assert errors == []
            assert sorted(f.data for f in results) == [
                f"FILE_{i}_CONTENT".encode() for i in range(3)
            ]
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
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        send_resp = create_mock_response(
            200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), send_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        KnowServicesRequestWrapper.initialize(ctx)
        
        try:
            KnowServicesRequestWrapper.send_warning(
                title="Teste",
                description="Mensagem de teste",
                recipients=[
                    SystemWarningRecipient(user_id=1),
                    SystemWarningRecipient(user_id=2),
                ],
            )
            
            send_call = _find_service_call(mock_session, ServiceName.WARNING_SEND)
            assert send_call
            assert b"Mensagem de teste" in send_call["data"]
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()


@pytest.mark.integration
class TestKnowServicesFileOperations:
    """Testes de operações de arquivo via KnowServices."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_open_file(self, mock_session_class):
        """Testa abertura de arquivo."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        open_resp = create_mock_response(
            200, b'''<?xml version="1.0"?>
            <serviceResponse status="1">
                <responseBody>
                    <chave valor="FILE_KEY_RETURNED"/>
                </responseBody>
            </serviceResponse>'''
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), open_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        KnowServicesRequestWrapper.initialize(ctx)
        
        try:
            key = KnowServicesRequestWrapper.open_file("/path/to/file.pdf")
            
            # Deve retornar a chave do atributo "valor" de <chave>
            # (.NET: response.ResponseBody.Key.Value)
            assert isinstance(key, str)
            assert key == "FILE_KEY_RETURNED"
            assert _find_service_call(mock_session, ServiceName.FILE_OPEN)
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_delete_files(self, mock_session_class):
        """Testa exclusão de arquivos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        delete_resp = create_mock_response(
            200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), delete_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        KnowServicesRequestWrapper.initialize(ctx)
        
        try:
            KnowServicesRequestWrapper.delete_files(["/path/to/file1.pdf", "/path/to/file2.pdf"])
            
            delete_call = _find_service_call(mock_session, ServiceName.FILE_DELETE)
            assert delete_call
            assert b"/path/to/file1.pdf" in delete_call["data"]
            assert b"/path/to/file2.pdf" in delete_call["data"]
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()


@pytest.mark.integration
class TestKnowServicesContextManager:
    """Testes de context manager."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_context_manager_usage(self, mock_session_class):
        """Testa uso como context manager."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        sessions_resp = create_mock_response(200, create_sessions_response([]))
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_dwr_response(), sessions_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        ctx = SankhyaContext(wrapper=wrapper)
        
        try:
            # __enter__ só cria uma sessão própria (via SankhyaSettings) se o
            # wrapper ainda não foi inicializado; para usar o contexto existente
            # é preciso inicializar antes de entrar no bloco.
            KnowServicesRequestWrapper.initialize(ctx)
            
            with KnowServicesRequestWrapper() as ks:
                sessions = KnowServicesRequestWrapper.get_sessions()
                assert isinstance(sessions, list)
            
            # __exit__ deve liberar o wrapper
            assert KnowServicesRequestWrapper._initialized is False
            assert _find_service_call(mock_session, ServiceName.SESSION_GET_ALL)
        finally:
            KnowServicesRequestWrapper.dispose()
            ctx.dispose()
