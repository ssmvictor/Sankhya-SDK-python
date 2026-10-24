# -*- coding: utf-8 -*-
"""
Testes de integração para concorrência e performance.

Testa operações simultâneas, thread safety e race conditions.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Sequence, Tuple, Union
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
import requests

from sankhya_sdk.core.constants import MAX_RETRY_COUNT
from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    create_login_response,
    create_logout_response,
)


# =============================================================================
# Helpers
# =============================================================================


def _http_response(status_code: int, content: bytes) -> requests.Response:
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


def _entities_response(
    *rows: Dict[str, Any],
    service: ServiceName = ServiceName.CRUD_SERVICE_FIND,
) -> bytes:
    """Gera XML de resposta do CRUDServiceProvider com as entidades informadas."""
    entities = "".join(
        "<entity>" + "".join(f"<{k}>{v}</{k}>" for k, v in row.items()) + "</entity>"
        for row in rows
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<serviceResponse serviceName="{service.internal_value}" status="1">'
        f'<responseBody><entities total="{len(rows)}">{entities}</entities></responseBody>'
        "</serviceResponse>"
    ).encode("utf-8")


class _FakeSankhyaServer:
    """
    Simula o servidor Sankhya como ``side_effect`` de ``requests.Session.request``.

    Login e logout sempre respondem com sucesso (cada login gera um
    JSESSIONID único) e o registro de user agent (DWR) responde vazio.
    As demais chamadas de serviço consomem, em ordem, a fila de respostas;
    itens da fila que são exceções são lançados (falhas de transporte).
    Uma chamada além da fila falha com AssertionError. Thread-safe.
    """

    def __init__(
        self,
        responses: Sequence[Union[requests.Response, BaseException]] = (),
    ) -> None:
        self._lock = threading.Lock()
        self._responses = list(responses)
        self.calls: List[str] = []
        self.logins = 0
        self.logouts = 0

    def calls_to(self, service: ServiceName) -> int:
        """Retorna quantas requisições foram feitas para o serviço."""
        return self.calls.count(service.internal_value)

    def __call__(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        service = parse_qs(urlparse(url).query).get("serviceName", [""])[0]

        with self._lock:
            if service == ServiceName.LOGIN.internal_value:
                self.logins += 1
                session_id = f"SESSION_{uuid4().hex}"
                return _http_response(200, create_login_response(session_id))

            if service == ServiceName.LOGOUT.internal_value:
                self.logouts += 1
                return _http_response(200, create_logout_response())

            if not service:
                assert "DWRController" in url, f"URL inesperada: {url}"
                return _http_response(200, b"")

            self.calls.append(service)
            if not self._responses:
                raise AssertionError(
                    f"Requisição inesperada #{len(self.calls)} para {service}"
                )
            item = self._responses.pop(0)

        if isinstance(item, BaseException):
            raise item
        return item


@contextmanager
def _simple_crud_session() -> Iterator[SankhyaWrapper]:
    """
    Autentica um SankhyaWrapper e inicializa o SimpleCRUDRequestWrapper
    com um SankhyaContext, liberando todos os recursos ao final.
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

        # Múltiplas respostas de busca
        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": i, "NOMEPARC": f"Parceiro {i}"}
            ))
            for i in range(1, 11)
        ])
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

        with _simple_crud_session():
            threads = [
                threading.Thread(target=find_partner, args=(i,))
                for i in range(1, 11)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=5)

            assert not any(t.is_alive() for t in threads)

        # Todas devem ter sucesso, cada resposta entregue a uma única thread
        assert errors == []
        assert len(results) == 10
        assert all(result is not None for _, result in results)
        assert sorted(result.name for _, result in results) == sorted(
            f"Parceiro {i}" for i in range(1, 11)
        )
        assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 10

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_high_volume_concurrent_reads(self, mock_session_class):
        """Testa alto volume de leituras concorrentes."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Uma resposta para cada leitura
        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": i, "NOMEPARC": f"Parceiro {i}"}
            ))
            for i in range(1, 51)
        ])
        mock_session.request.side_effect = server

        errors: List[Exception] = []

        with _simple_crud_session():
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
                        assert future.result() is not None
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

        # Múltiplas respostas de criação
        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": i, "NOMEPARC": f"Novo Parceiro {i}"},
                service=ServiceName.CRUD_SERVICE_SAVE,
            ))
            for i in range(1, 11)
        ])
        mock_session.request.side_effect = server

        results: List[Partner] = []
        errors: List[Exception] = []
        lock = threading.Lock()

        def create_partner(i: int):
            try:
                partner = Partner(name=f"Novo Parceiro {i}")
                result = SimpleCRUDRequestWrapper.update(partner)
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    errors.append(e)

        with _simple_crud_session():
            threads = [
                threading.Thread(target=create_partner, args=(i,))
                for i in range(1, 11)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=10)

            assert not any(t.is_alive() for t in threads)

        # Todas devem ter sucesso
        assert errors == []
        assert len(results) == 10
        assert sorted(result.code for result in results) == list(range(1, 11))
        assert server.calls_to(ServiceName.CRUD_SERVICE_SAVE) == 10

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_concurrent_update_same_entity(self, mock_session_class):
        """Testa atualizações concorrentes da mesma entidade."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Respostas de atualização
        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": 1, "NOMEPARC": f"Parceiro Atualizado {i}"},
                service=ServiceName.CRUD_SERVICE_SAVE,
            ))
            for i in range(5)
        ])
        mock_session.request.side_effect = server

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

        with _simple_crud_session():
            threads = [
                threading.Thread(target=update_partner, args=(i,))
                for i in range(5)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join(timeout=10)

            assert not any(t.is_alive() for t in threads)

        # Todas devem ter sucesso
        assert errors == []
        assert len(results) == 5
        assert all(result.code == 1 for result in results)
        assert sorted(result.name for result in results) == sorted(
            f"Parceiro Atualizado {i}" for i in range(5)
        )
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
        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": i, "NOMEPARC": f"P{i}"}
            ))
            for i in range(50)
        ])
        mock_session.request.side_effect = server

        barrier = threading.Barrier(10)
        results: List[int] = []
        errors: List[Exception] = []
        lock = threading.Lock()

        def worker(thread_id: int):
            barrier.wait()  # Todas as threads começam juntas
            for i in range(5):
                try:
                    result = SimpleCRUDRequestWrapper.try_find(
                        Partner(code=thread_id * 10 + i)
                    )
                    assert result is not None
                    with lock:
                        results.append(thread_id)
                except Exception as e:
                    with lock:
                        errors.append(e)

        with _simple_crud_session():
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

        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": i, "NOMEPARC": f"Parceiro Async {i}"}
            ))
            for i in range(1, 6)
        ])
        mock_session.request.side_effect = server

        with _simple_crud_session():
            # Executar múltiplas buscas assíncronas em paralelo
            tasks = [
                SimpleCRUDRequestWrapper.try_find_async(Partner(code=i))
                for i in range(1, 6)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verificar resultados
        errors = [r for r in results if isinstance(r, BaseException)]
        assert errors == []
        assert sorted(r.name for r in results) == sorted(
            f"Parceiro Async {i}" for i in range(1, 6)
        )
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

        # 100 respostas rápidas
        server = _FakeSankhyaServer([
            _http_response(200, _entities_response(
                {"CODPARC": i, "NOMEPARC": f"P{i}"}
            ))
            for i in range(100)
        ])
        mock_session.request.side_effect = server

        with _simple_crud_session():
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
            return _http_response(200, _entities_response(
                {"CODPARC": 1, "NOMEPARC": "P"}
            ))

        def error_resps():
            # Erro 500 persistente: esgota os retries da requisição
            return [_http_response(500, b"Error") for _ in range(1 + MAX_RETRY_COUNT)]

        # Mistura de sucesso e erros
        server = _FakeSankhyaServer(
            [success_resp()] + error_resps()
            + [success_resp()] + error_resps()
            + [success_resp()]
        )
        mock_session.request.side_effect = server

        successes = 0
        failures: List[Exception] = []

        with _simple_crud_session() as wrapper:
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
            server = _FakeSankhyaServer([
                _http_response(200, _entities_response(
                    {"CODPARC": 1, "NOMEPARC": f"Parceiro Ciclo {cycle}"}
                )),
            ])
            mock_session.request.side_effect = server

            with _simple_crud_session():
                result = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

            # Cada ciclo deve usar o contexto recém-inicializado
            assert result is not None
            assert result.name == f"Parceiro Ciclo {cycle}"
            assert server.calls_to(ServiceName.CRUD_SERVICE_FIND) == 1
