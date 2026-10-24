# -*- coding: utf-8 -*-
"""
Testes de integração para concorrência e performance.

Testa operações simultâneas, thread safety e race conditions.
"""

from __future__ import annotations

import asyncio
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest
import requests

from sankhya_sdk.core.constants import MAX_RETRY_COUNT
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    FakeSankhyaServer,
    ServerReply,
    entities_response,
    find_criteria,
    http_response,
    save_data_row,
    simple_crud_session,
)


# =============================================================================
# Helpers
# =============================================================================


def _requested_partner_code(body: str) -> int:
    """Código do parceiro pedido no critério de CRUDServiceProvider.loadRecords."""
    expression = find_criteria(body)
    match = re.fullmatch(r"CODPARC = (\d+)", expression or "")
    assert match, f"Critério inesperado na busca: {expression!r}"
    return int(match.group(1))


def _find_partner_reply(body: str) -> ServerReply:
    """
    Responde a busca com o parceiro do código pedido na requisição.

    Como a resposta depende do corpo da requisição, uma resposta entregue
    à thread errada (requisições trocadas) é detectada pelo teste.
    """
    code = _requested_partner_code(body)
    return http_response(200, entities_response(
        {"CODPARC": code, "NOMEPARC": f"Parceiro {code}"}
    ))


def _save_partner_reply(body: str) -> ServerReply:
    """
    Responde o saveRecord ecoando o parceiro enviado no dataRow.

    Sem chave na requisição (criação), o código é o número no fim do nome
    (``"Novo Parceiro 7"`` -> 7), simulando a chave gerada pelo servidor.
    """
    keys, local_fields = save_data_row(body)
    name = local_fields["NOMEPARC"]
    code = keys.get("CODPARC") or re.search(r"(\d+)$", name).group(1)
    return http_response(200, entities_response(
        {"CODPARC": code, "NOMEPARC": name},
        service=ServiceName.CRUD_SERVICE_SAVE,
    ))


# =============================================================================
# Testes
# =============================================================================


@pytest.mark.integration
class TestConcurrentReads:
    """Testes de leituras concorrentes."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_find_operations(self, mock_session_class):
        """Testa operações de busca concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Uma resposta por busca, com o parceiro do código pedido
        server = FakeSankhyaServer([_find_partner_reply] * 10)
        mock_session.request.side_effect = server

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

        with simple_crud_session():
            threads = [
                threading.Thread(target=find_partner, args=(i,))
                for i in range(1, 11)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=5)

            assert not any(t.is_alive() for t in threads)

        # Todas devem ter sucesso, cada thread com a resposta da sua busca
        assert errors == []
        assert sorted(code for code, _ in results) == list(range(1, 11))
        for code, result in results:
            assert result is not None
            assert result.code == code
            assert result.name == f"Parceiro {code}"
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 10

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_high_volume_concurrent_reads(self, mock_session_class):
        """Testa alto volume de leituras concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Uma resposta para cada leitura, com o parceiro do código pedido
        server = FakeSankhyaServer([_find_partner_reply] * 50)
        mock_session.request.side_effect = server

        errors: List[Exception] = []

        with simple_crud_session():
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {
                    executor.submit(
                        SimpleCRUDRequestWrapper.try_find, Partner(code=i)
                    ): i
                    for i in range(1, 51)
                }

                completed = 0
                for future in as_completed(futures, timeout=30):
                    try:
                        result = future.result()
                        assert result is not None
                        assert result.code == futures[future]
                        completed += 1
                    except Exception as e:
                        errors.append(e)

        assert errors == []
        assert completed == 50
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 50


@pytest.mark.integration
class TestConcurrentWrites:
    """
    Testes de escritas concorrentes.

    A criação de registros usa ``SimpleCRUDRequestWrapper.update``
    (CRUDServiceProvider.saveRecord), como no SDK .NET: não existe
    operação ``create`` separada.
    """

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_create_operations(self, mock_session_class):
        """Testa operações de criação concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Uma resposta por criação, ecoando o parceiro enviado
        server = FakeSankhyaServer([_save_partner_reply] * 10)
        mock_session.request.side_effect = server

        results: List[Tuple[int, Partner]] = []
        errors: List[Exception] = []
        lock = threading.Lock()

        def create_partner(i: int):
            try:
                partner = Partner(name=f"Novo Parceiro {i}")
                result = SimpleCRUDRequestWrapper.update(partner)
                with lock:
                    results.append((i, result))
            except Exception as e:
                with lock:
                    errors.append(e)

        with simple_crud_session():
            threads = [
                threading.Thread(target=create_partner, args=(i,))
                for i in range(1, 11)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=10)

            assert not any(t.is_alive() for t in threads)

        # Todas devem ter sucesso, cada thread com o registro que criou
        assert errors == []
        assert sorted(i for i, _ in results) == list(range(1, 11))
        for i, result in results:
            assert result.code == i
            assert result.name == f"Novo Parceiro {i}"
        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 10

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_update_same_entity(self, mock_session_class):
        """Testa atualizações concorrentes da mesma entidade."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Uma resposta por atualização, ecoando o parceiro enviado
        server = FakeSankhyaServer([_save_partner_reply] * 5)
        mock_session.request.side_effect = server

        results: List[Tuple[int, Partner]] = []
        errors: List[Exception] = []
        lock = threading.Lock()

        def update_partner(i: int):
            try:
                partner = Partner(code=1, name=f"Parceiro Atualizado {i}")
                result = SimpleCRUDRequestWrapper.update(partner)
                with lock:
                    results.append((i, result))
            except Exception as e:
                with lock:
                    errors.append(e)

        with simple_crud_session():
            threads = [
                threading.Thread(target=update_partner, args=(i,))
                for i in range(5)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=10)

            assert not any(t.is_alive() for t in threads)

        # Todas devem ter sucesso, cada thread com a sua atualização
        assert errors == []
        assert sorted(i for i, _ in results) == list(range(5))
        for i, result in results:
            assert result.code == 1
            assert result.name == f"Parceiro Atualizado {i}"
        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 5


@pytest.mark.integration
class TestThreadSafety:
    """Testes de thread safety."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_wrapper_thread_safety(self, mock_session_class):
        """Testa thread safety do wrapper."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Uma resposta para cada busca (10 threads x 5 buscas)
        server = FakeSankhyaServer([_find_partner_reply] * 50)
        mock_session.request.side_effect = server

        barrier = threading.Barrier(10)
        results: List[int] = []
        errors: List[Exception] = []
        lock = threading.Lock()

        def worker(thread_id: int):
            barrier.wait()  # Todas as threads começam juntas
            for i in range(5):
                try:
                    code = thread_id * 10 + i
                    result = SimpleCRUDRequestWrapper.try_find(Partner(code=code))
                    assert result is not None
                    assert result.code == code
                    with lock:
                        results.append(thread_id)
                except Exception as e:
                    with lock:
                        errors.append(e)

        with simple_crud_session():
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=30)

            assert not any(t.is_alive() for t in threads)

        # Verificar que todas as operações foram realizadas
        assert errors == []
        assert Counter(results) == {thread_id: 5 for thread_id in range(10)}
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 50


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncConcurrency:
    """Testes de concorrência assíncrona."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    async def test_async_concurrent_operations(self, mock_session_class):
        """Testa operações assíncronas concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        server = FakeSankhyaServer([_find_partner_reply] * 5)
        mock_session.request.side_effect = server

        with simple_crud_session():
            # Executar múltiplas buscas assíncronas em paralelo
            tasks = [
                SimpleCRUDRequestWrapper.try_find_async(Partner(code=i))
                for i in range(1, 6)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verificar resultados: gather preserva a ordem das buscas
        errors = [r for r in results if isinstance(r, BaseException)]
        assert errors == []
        assert [r.code for r in results] == [1, 2, 3, 4, 5]
        assert [r.name for r in results] == [f"Parceiro {i}" for i in range(1, 6)]
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 5


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Testes de performance."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_operation_performance(self, mock_session_class):
        """Testa performance de operações em lote."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # 100 respostas rápidas, com o parceiro do código pedido
        server = FakeSankhyaServer([_find_partner_reply] * 100)
        mock_session.request.side_effect = server

        with simple_crud_session():
            start_time = time.time()

            for i in range(100):
                result = SimpleCRUDRequestWrapper.try_find(Partner(code=i))
                assert result is not None
                assert result.code == i

            elapsed = time.time() - start_time

        # Deve completar em tempo razoável (< 5s para 100 operações mockadas)
        assert elapsed < 5.0
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 100


@pytest.mark.integration
class TestResourceCleanup:
    """Testes de limpeza de recursos."""

    @patch("sankhya_sdk.core.wrapper.time.sleep")
    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_cleanup_after_concurrent_errors(self, mock_session_class, mock_sleep):
        """Testa limpeza após erros concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        def success_resp():
            return http_response(200, entities_response(
                {"CODPARC": 1, "NOMEPARC": "P"}
            ))

        def error_resps():
            # Erro 500 persistente: esgota os retries da requisição
            return [http_response(500, b"Error") for _ in range(1 + MAX_RETRY_COUNT)]

        # Mistura de sucesso e erros
        server = FakeSankhyaServer(
            [success_resp()] + error_resps()
            + [success_resp()] + error_resps()
            + [success_resp()]
        )
        mock_session.request.side_effect = server

        successes = 0
        failures: List[Exception] = []

        with simple_crud_session() as wrapper:
            for i in range(5):
                try:
                    SimpleCRUDRequestWrapper.try_find(Partner(code=i))
                    successes += 1
                except (requests.exceptions.HTTPError, SankhyaException) as e:
                    failures.append(e)

            logouts_before_cleanup = server.logouts

        assert successes == 3
        assert len(failures) == 2

        # Cleanup deve funcionar mesmo após erros: sessão encerrada no servidor
        assert server.logouts > logouts_before_cleanup
        assert not wrapper.is_authenticated

        # O wrapper CRUD foi descartado e não aceita novas operações
        with pytest.raises(RuntimeError):
            SimpleCRUDRequestWrapper.try_find(Partner(code=1))

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_multiple_initialize_dispose_cycles(self, mock_session_class):
        """Testa múltiplos ciclos de initialize/dispose."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        for cycle in range(3):
            server = FakeSankhyaServer([
                http_response(200, entities_response(
                    {"CODPARC": 1, "NOMEPARC": f"Parceiro Ciclo {cycle}"}
                )),
            ])
            mock_session.request.side_effect = server

            with simple_crud_session():
                result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

            # Cada ciclo deve usar o contexto recém-inicializado
            assert result is not None
            assert result.name == f"Parceiro Ciclo {cycle}"
            assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 1
