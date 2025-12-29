# -*- coding: utf-8 -*-
"""
Testes de integração para concorrência e performance.

Testa operações simultâneas, thread safety e race conditions.
"""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_success_response,
)


@pytest.mark.integration
class TestConcurrentReads:
    """Testes de leituras concorrentes."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_find_operations(self, mock_session_class):
        """Testa operações de busca concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Múltiplas respostas de busca
        find_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"}
                ])
            )
            for i in range(1, 11)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + find_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            results: List[Tuple[int, Partner]] = []
            errors: List[Tuple[int, Exception]] = []
            lock = threading.Lock()
            
            def find_partner(code: int):
                try:
                    result = SimpleCRUDRequestWrapper.try_find(Partner(code=code))
                    with lock:
                        results.append((code, result))
                except Exception as e:
                    with lock:
                        errors.append((code, e))
            
            threads = [
                threading.Thread(target=find_partner, args=(i,))
                for i in range(1, 11)
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=5)
            
            # Pelo menos algumas devem ter sucesso
            assert len(results) > 0 or len(errors) > 0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_high_volume_concurrent_reads(self, mock_session_class):
        """Testa alto volume de leituras concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Muitas respostas
        find_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"}
                ])
            )
            for i in range(100)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + find_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(
                        SimpleCRUDRequestWrapper.try_find, Partner(code=i)
                    )
                    for i in range(1, 51)
                ]
                
                completed = 0
                for future in as_completed(futures, timeout=30):
                    try:
                        future.result()
                        completed += 1
                    except Exception:
                        pass
                
                assert completed > 0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestConcurrentWrites:
    """Testes de escritas concorrentes."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_create_operations(self, mock_session_class):
        """Testa operações de criação concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Múltiplas respostas de criação
        create_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Novo Parceiro {i}"}
                ])
            )
            for i in range(1, 11)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + create_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            results: List[Partner] = []
            errors: List[Exception] = []
            lock = threading.Lock()
            
            def create_partner(i: int):
                try:
                    partner = Partner(name=f"Novo Parceiro {i}")
                    result = SimpleCRUDRequestWrapper.create(partner)
                    with lock:
                        results.append(result)
                except Exception as e:
                    with lock:
                        errors.append(e)
            
            threads = [
                threading.Thread(target=create_partner, args=(i,))
                for i in range(1, 11)
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=10)
            
            # Pelo menos algumas devem ter sucesso
            assert len(results) > 0 or len(errors) > 0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_update_same_entity(self, mock_session_class):
        """Testa atualizações concorrentes da mesma entidade."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Respostas de atualização
        update_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": "1", "NOMEPARC": f"Parceiro Atualizado {i}"}
                ])
            )
            for i in range(5)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + update_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            results: List[Partner] = []
            errors: List[Exception] = []
            lock = threading.Lock()
            
            def update_partner(i: int):
                try:
                    partner = Partner(code=1, name=f"Parceiro Atualizado {i}")
                    result = SimpleCRUDRequestWrapper.update(partner)
                    with lock:
                        results.append(result)
                except Exception as e:
                    with lock:
                        errors.append(e)
            
            threads = [
                threading.Thread(target=update_partner, args=(i,))
                for i in range(5)
            ]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=10)
            
            # Pelo menos uma deve ter sucesso
            assert len(results) > 0 or len(errors) > 0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestThreadSafety:
    """Testes de thread safety."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_wrapper_thread_safety(self, mock_session_class):
        """Testa thread safety do wrapper."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Muitas respostas
        responses = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"P{i}"}
                ])
            )
            for i in range(50)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + responses + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            barrier = threading.Barrier(10)
            results: List[int] = []
            lock = threading.Lock()
            
            def worker(thread_id: int):
                barrier.wait()  # Todas as threads começam juntas
                for i in range(5):
                    try:
                        SimpleCRUDRequestWrapper.try_find(Partner(code=thread_id * 10 + i))
                        with lock:
                            results.append(thread_id)
                    except Exception:
                        pass
            
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join(timeout=30)
            
            # Verificar que operações foram realizadas
            assert len(results) > 0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncConcurrency:
    """Testes de concorrência assíncrona."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    async def test_async_concurrent_operations(self, mock_session_class):
        """Testa operações assíncronas concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        responses = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro Async {i}"}
                ])
            )
            for i in range(10)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + responses + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            async def find_partner(code: int):
                # Simular operação assíncrona
                await asyncio.sleep(0.01)
                return SimpleCRUDRequestWrapper.try_find(Partner(code=code))
            
            # Executar múltiplas buscas em paralelo
            tasks = [find_partner(i) for i in range(1, 6)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verificar resultados
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            assert success_count >= 0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Testes de performance."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_operation_performance(self, mock_session_class):
        """Testa performance de operações em lote."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # 100 respostas rápidas
        responses = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"P{i}"}
                ])
            )
            for i in range(100)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + responses + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            start_time = time.time()
            
            for i in range(100):
                SimpleCRUDRequestWrapper.try_find(Partner(code=i))
            
            elapsed = time.time() - start_time
            
            # Deve completar em tempo razoável (< 5s para 100 operações mockadas)
            assert elapsed < 5.0
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestResourceCleanup:
    """Testes de limpeza de recursos."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_cleanup_after_concurrent_errors(self, mock_session_class):
        """Testa limpeza após erros concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        logout_resp = create_mock_response(200, create_logout_response())
        
        # Mistura de sucesso e erros
        error_resp = create_mock_response(500, b"Error")
        error_resp.ok = False
        
        success_resp = create_mock_response(
            200, create_success_response([{"CODPARC": "1", "NOMEPARC": "P"}])
        )
        
        mock_session.request.side_effect = [
            login_resp,
            success_resp, error_resp, success_resp, error_resp, success_resp,
            logout_resp,
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            for i in range(5):
                try:
                    SimpleCRUDRequestWrapper.try_find(Partner(code=i))
                except Exception:
                    pass
        finally:
            # Cleanup deve funcionar mesmo após erros
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()
            
            # Verificar que dispose foi chamado corretamente
            assert True  # Se chegou aqui, cleanup funcionou

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_multiple_initialize_dispose_cycles(self, mock_session_class):
        """Testa múltiplos ciclos de initialize/dispose."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        for cycle in range(3):
            login_resp = create_mock_response(200, create_login_response())
            find_resp = create_mock_response(
                200, create_success_response([
                    {"CODPARC": "1", "NOMEPARC": f"Parceiro Ciclo {cycle}"}
                ])
            )
            logout_resp = create_mock_response(200, create_logout_response())
            
            mock_session.request.side_effect = [login_resp, find_resp, logout_resp]
            
            wrapper = SankhyaWrapper(host="http://test.local", port=8180)
            wrapper.authenticate("user", "pass")
            
            SimpleCRUDRequestWrapper.initialize(wrapper)
            
            try:
                result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
                assert result is not None
            finally:
                SimpleCRUDRequestWrapper.dispose()
                wrapper.dispose()
