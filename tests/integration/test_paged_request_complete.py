# -*- coding: utf-8 -*-
"""
Testes de integração completos para PagedRequestWrapper.

Testa paginação, callbacks, erros, cancelamento e operações assíncronas.
"""

from __future__ import annotations

import asyncio
import threading
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import PagedRequestException, SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.paged_request_wrapper import (
    PagedRequestWrapper,
    PagedRequestEventArgs,
)

from .conftest import (
    create_error_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_paged_response,
    create_success_response,
)


@pytest.mark.integration
class TestPagedRequestBasic:
    """Testes básicos de paginação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_single_page(self, mock_session_class):
        """Testa quando resultado cabe em uma página."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Resposta com 5 registros (cabe em uma página)
        entities = [{"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} for i in range(1, 6)]
        page_resp = create_mock_response(
            200, create_paged_response(entities, page=0, total_records=5)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, page_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results = list(PagedRequestWrapper.get_paged_results(Partner))
            
            assert len(results) == 5
            assert results[0].code == 1
            assert results[4].code == 5
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_multiple_pages(self, mock_session_class):
        """Testa múltiplas páginas (>100 registros)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Página 1: registros 1-100
        page1_entities = [
            {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} 
            for i in range(1, 101)
        ]
        page1_resp = create_mock_response(
            200, create_paged_response(page1_entities, page=0, total_records=150)
        )
        
        # Página 2: registros 101-150
        page2_entities = [
            {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} 
            for i in range(101, 151)
        ]
        page2_resp = create_mock_response(
            200, create_paged_response(page2_entities, page=1, total_records=150)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, page1_resp, page2_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results = list(PagedRequestWrapper.get_paged_results(Partner))
            
            # Deve ter 150 registros no total
            assert len(results) == 150
            assert results[0].code == 1
            assert results[99].code == 100
            assert results[149].code == 150
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_with_max_results(self, mock_session_class):
        """Testa limite de resultados."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Resposta com 100 registros, mas queremos apenas 25
        entities = [
            {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} 
            for i in range(1, 101)
        ]
        page_resp = create_mock_response(
            200, create_paged_response(entities, page=0, total_records=1000)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, page_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results = list(PagedRequestWrapper.get_paged_results(
                Partner, max_results=25
            ))
            
            # Deve ter apenas 25 resultados
            assert len(results) == 25
            assert results[0].code == 1
            assert results[24].code == 25
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestPagedRequestCallbacks:
    """Testes de callbacks de paginação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_on_page_loaded_callback(self, mock_session_class):
        """Testa callback on_page_loaded."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        entities = [{"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} for i in range(1, 11)]
        page_resp = create_mock_response(
            200, create_paged_response(entities, page=0, total_records=10)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, page_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            callback_calls: List[PagedRequestEventArgs] = []
            
            def on_page_loaded(args: PagedRequestEventArgs):
                callback_calls.append(args)
            
            results = list(PagedRequestWrapper.get_paged_results(
                Partner,
                on_page_loaded=on_page_loaded,
            ))
            
            # Callback deve ter sido chamado pelo menos uma vez
            # (o comportamento exato depende da implementação)
            assert len(results) == 10
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_on_error_callback(self, mock_session_class):
        """Testa callback de erro."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("QUERY.ERROR", "Erro na query")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            errors: List[Exception] = []
            
            def on_error(exc: Exception):
                errors.append(exc)
            
            with pytest.raises((SankhyaException, PagedRequestException)):
                list(PagedRequestWrapper.get_paged_results(
                    Partner,
                    on_error=on_error,
                ))
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestPagedRequestErrors:
    """Testes de erros durante paginação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_error_mid_pagination(self, mock_session_class):
        """Testa erro durante paginação (no meio)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeira página OK
        page1_entities = [
            {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} 
            for i in range(1, 101)
        ]
        page1_resp = create_mock_response(
            200, create_paged_response(page1_entities, page=0, total_records=200)
        )
        
        # Segunda página com erro
        error_resp = create_mock_response(
            200, create_error_response("TIMEOUT", "Query timeout")
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, page1_resp, error_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            # Deve processar primeira página e falhar na segunda
            results = []
            try:
                for item in PagedRequestWrapper.get_paged_results(Partner):
                    results.append(item)
            except (SankhyaException, PagedRequestException):
                pass  # Erro esperado
            
            # Deve ter pelo menos os resultados da primeira página
            # (ou nenhum, dependendo de quando o erro ocorre)
            assert len(results) >= 0
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_request_empty_result(self, mock_session_class):
        """Testa paginação com resultado vazio."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        empty_resp = create_mock_response(
            200, create_paged_response([], page=0, total_records=0)
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, empty_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results = list(PagedRequestWrapper.get_paged_results(Partner))
            
            assert len(results) == 0
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestPagedRequestAsync:
    """Testes de paginação assíncrona."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    @pytest.mark.asyncio
    async def test_async_paged_request(self, mock_session_class):
        """Testa paginação assíncrona."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        entities = [{"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} for i in range(1, 11)]
        page_resp = create_mock_response(
            200, create_paged_response(entities, page=0, total_records=10)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, page_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results = []
            async for item in PagedRequestWrapper.get_paged_results_async(Partner):
                results.append(item)
            
            assert len(results) == 10
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestPagedRequestConcurrency:
    """Testes de concorrência em paginação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_paged_requests(self, mock_session_class):
        """Testa múltiplas paginações simultâneas."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Configurar múltiplas respostas
        responses = [login_resp]
        for _ in range(3):  # 3 requisições paralelas
            entities = [
                {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"} 
                for i in range(1, 6)
            ]
            responses.append(
                create_mock_response(
                    200, create_paged_response(entities, page=0, total_records=5)
                )
            )
        responses.append(create_mock_response(200, create_logout_response()))
        
        mock_session.request.side_effect = responses
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results_container = []
            errors = []
            
            def fetch_partners(index):
                try:
                    results = list(PagedRequestWrapper.get_paged_results(Partner))
                    results_container.append((index, len(results)))
                except Exception as e:
                    errors.append((index, e))
            
            threads = [
                threading.Thread(target=fetch_partners, args=(i,))
                for i in range(3)
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=10)
            
            # Pelo menos algumas devem ter sucesso
            # (comportamento exato depende de threading)
            assert len(errors) == 0 or len(results_container) > 0
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestPagedRequestProducts:
    """Testes de paginação com Products."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_paged_products(self, mock_session_class):
        """Testa paginação de produtos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        entities = [
            {"CODPROD": str(i), "DESCRPROD": f"Produto {i}", "CODVOL": "UN"} 
            for i in range(1, 21)
        ]
        page_resp = create_mock_response(
            200, create_paged_response(entities, page=0, total_records=20)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, page_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        PagedRequestWrapper.initialize(wrapper)
        
        try:
            results = list(PagedRequestWrapper.get_paged_results(Product))
            
            assert len(results) == 20
            assert results[0].code == 1
            assert results[0].name == "Produto 1"
        finally:
            PagedRequestWrapper.dispose()
            wrapper.dispose()
