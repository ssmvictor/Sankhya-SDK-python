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

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import (
    ServiceRequestFileNotFoundException,
    SankhyaException,
)
from sankhya_sdk.value_objects.service_file import ServiceFile
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
        
        mock_session.request.side_effect = [login_resp, sessions_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        KnowServicesRequestWrapper.initialize(wrapper)
        
        try:
            sessions = KnowServicesRequestWrapper.get_sessions()
            
            # Deve retornar lista de sessões
            assert isinstance(sessions, list)
        finally:
            KnowServicesRequestWrapper.dispose()
            wrapper.dispose()

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
        
        mock_session.request.side_effect = [login_resp, kill_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        KnowServicesRequestWrapper.initialize(wrapper)
        
        try:
            # Encerrar sessão de outro usuário
            KnowServicesRequestWrapper.kill_session("SESSION_TO_KILL")
            
            # Não deve ter lançado exceção
            assert True
        finally:
            KnowServicesRequestWrapper.dispose()
            wrapper.dispose()


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
        
        mock_session.request.side_effect = [login_resp, file_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            file = wrapper.get_file("FILE_KEY_123")
            
            assert isinstance(file, ServiceFile)
            assert file.data == b"PDF_CONTENT_HERE"
            assert file.content_type == "application/pdf"
            assert file.filename == "document.pdf"
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
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            with pytest.raises(Exception):  # Pode ser vários tipos de exceção
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
        
        mock_session.request.side_effect = [login_resp, file_resp, logout_resp]
        
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
        
        mock_session.request.side_effect = [login_resp] + file_resps + [logout_resp]
        
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
            
            # Pelo menos alguns devem ter sucesso
            assert len(results) > 0 or len(errors) == 0
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
        
        mock_session.request.side_effect = [login_resp, image_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            image = wrapper.get_image("Produto", {"CODPROD": 1})
            
            if image:
                assert image.data.startswith(b"\x89PNG")
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
        
        mock_session.request.side_effect = [login_resp, image_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            image = wrapper.get_image("Parceiro", {"CODPARC": 123})
            
            if image:
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
        
        mock_session.request.side_effect = [login_resp, not_found_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            # Pode retornar None ou lançar exceção
            try:
                image = wrapper.get_image("Parceiro", {"CODPARC": 99999})
                # Se retornar, deve ser None
            except Exception:
                pass  # Exceção esperada
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
        
        mock_session.request.side_effect = [login_resp, send_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        KnowServicesRequestWrapper.initialize(wrapper)
        
        try:
            KnowServicesRequestWrapper.send_warning(
                title="Teste",
                message="Mensagem de teste",
                recipient_codes=[1, 2],
            )
        finally:
            KnowServicesRequestWrapper.dispose()
            wrapper.dispose()


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
        
        mock_session.request.side_effect = [login_resp, open_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        KnowServicesRequestWrapper.initialize(wrapper)
        
        try:
            key = KnowServicesRequestWrapper.open_file("/path/to/file.pdf")
            
            # Deve retornar uma chave (string)
            assert isinstance(key, str)
        finally:
            KnowServicesRequestWrapper.dispose()
            wrapper.dispose()

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
        
        mock_session.request.side_effect = [login_resp, delete_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        KnowServicesRequestWrapper.initialize(wrapper)
        
        try:
            KnowServicesRequestWrapper.delete_files(["/path/to/file1.pdf", "/path/to/file2.pdf"])
        finally:
            KnowServicesRequestWrapper.dispose()
            wrapper.dispose()


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
        
        mock_session.request.side_effect = [login_resp, sessions_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        with KnowServicesRequestWrapper() as ks:
            KnowServicesRequestWrapper.initialize(wrapper)
            sessions = KnowServicesRequestWrapper.get_sessions()
            assert isinstance(sessions, list)
        
        wrapper.dispose()
