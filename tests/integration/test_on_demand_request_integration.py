# -*- coding: utf-8 -*-
"""
Testes de integração para OnDemandRequestWrapper.

Testa processamento em lote, throttling, concorrência e retry.

Os testes exercitam a API real (``OnDemandRequestWrapper``,
``AsyncOnDemandRequestWrapper`` e ``OnDemandRequestFactory``) sobre um
``SankhyaContext`` autenticado, com o transporte HTTP simulado por um
servidor que roteia as chamadas pelo ``serviceName``.

O comportamento esperado segue a referência .NET
(``Src/Sankhya/RequestWrappers/OnDemandRequestWrapper.cs``):

- as entidades são acumuladas e enviadas em lote (``CRUDServiceProvider.saveRecord``)
  quando a fila atinge o throughput, ou quando há flush/cancelamento/dispose;
- com ``allow_above_throughput=False`` cada lote tem no máximo ``throughput`` entidades;
- um único worker processa os lotes sequencialmente;
- se o lote falha, as entidades são reenviadas individualmente e cada falha
  individual publica um ``OnDemandRequestFailureEvent``;
- timeouts/deadlocks são tentados novamente uma vez;
- após o cancelamento, ``add`` lança ``CanceledOnDemandRequestWrapperException``.
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from lxml import etree

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
from sankhya_sdk.exceptions import (
    CanceledOnDemandRequestWrapperException,
    SankhyaException,
)
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.async_on_demand_request_wrapper import (
    AsyncOnDemandRequestWrapper,
)
from sankhya_sdk.request_wrappers.on_demand_request_factory import (
    OnDemandRequestFactory,
)
from sankhya_sdk.request_wrappers.on_demand_request_wrapper import (
    OnDemandRequestWrapper,
)

from .conftest import (
    create_error_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_success_response,
)

# =============================================================================
# Infraestrutura de teste (servidor Sankhya simulado)
# =============================================================================

SAVE_RECORD = ServiceName.CRUD_SERVICE_SAVE.internal_value
LOGIN = ServiceName.LOGIN.internal_value
LOGOUT = ServiceName.LOGOUT.internal_value

# Tempo máximo de espera por operações do worker (evita travar a suíte)
WAIT_TIMEOUT = 5.0

ResponseHandler = Callable[[str], bytes]


class _SankhyaServerStub:
    """
    Servidor Sankhya simulado no nível HTTP.

    Roteia cada requisição pelo parâmetro ``serviceName`` da URL e registra
    o corpo XML enviado, permitindo verificar o que foi transmitido.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handlers: Dict[str, ResponseHandler] = {}
        self.calls: List[Tuple[Optional[str], str]] = []

    def on(self, service_name: str, handler: ResponseHandler) -> None:
        """Registra o handler que gera a resposta XML de um serviço."""
        self._handlers[service_name] = handler

    def bodies(self, service_name: str) -> List[str]:
        """Retorna os corpos XML enviados para um serviço, em ordem."""
        with self._lock:
            return [body for name, body in self.calls if name == service_name]

    def __call__(self, method=None, url=None, data=None, headers=None, timeout=None, **_):
        service = parse_qs(urlparse(url).query).get("serviceName", [None])[0]
        body = data.decode("utf-8") if isinstance(data, bytes) else (data or "")
        with self._lock:
            self.calls.append((service, body))

        if service is None:
            # Registro de user agent via DWR (sem conteúdo relevante)
            response = create_mock_response(200, b"")
            response.text = ""
            return response
        if service == LOGIN:
            return create_mock_response(
                200, create_login_response(session_id=f"STUB-{uuid.uuid4().hex}")
            )
        if service == LOGOUT:
            return create_mock_response(200, create_logout_response())

        handler = self._handlers.get(service)
        if handler is None:
            raise AssertionError(f"Serviço inesperado no servidor simulado: {service}")
        return create_mock_response(200, handler(body))


def _save_ok(body: str) -> bytes:
    """Resposta de sucesso para CRUDServiceProvider.saveRecord."""
    return create_success_response()


def _values_in(body: str) -> Set[str]:
    """Retorna os textos e valores de atributos presentes no XML enviado."""
    values: Set[str] = set()
    for element in etree.fromstring(body.encode("utf-8")).iter():
        if element.text and element.text.strip():
            values.add(element.text.strip())
        values.update(value for value in element.attrib.values() if value)
    return values


def _sent_batches(server: _SankhyaServerStub, names: Iterable[str]) -> List[Set[str]]:
    """Para cada saveRecord enviado, retorna quais das entidades informadas ele contém."""
    expected = set(names)
    return [_values_in(body) & expected for body in server.bodies(SAVE_RECORD)]


def _root_entities(body: str) -> Set[str]:
    """Retorna as entidades raiz (atributo rootEntity) de uma requisição."""
    return {
        element.get("rootEntity")
        for element in etree.fromstring(body.encode("utf-8")).iter()
        if element.get("rootEntity")
    }


def _run_with_timeout(func: Callable, *args, timeout: float = WAIT_TIMEOUT):
    """Executa ``func`` em thread daemon e falha se não terminar dentro do timeout."""
    outcome: Dict[str, object] = {}

    def target() -> None:
        try:
            outcome["value"] = func(*args)
        except BaseException as exc:  # repassado ao teste
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    assert not thread.is_alive(), (
        f"{getattr(func, '__qualname__', func)} não terminou em {timeout}s"
    )
    if "error" in outcome:
        raise outcome["error"]  # type: ignore[misc]
    return outcome.get("value")


def _dispose_quietly(wrapper: OnDemandRequestWrapper) -> None:
    """Libera o wrapper na limpeza do teste sem mascarar a falha original."""
    thread = threading.Thread(target=wrapper.dispose, daemon=True)
    thread.start()
    thread.join(WAIT_TIMEOUT)


def _wait_until(predicate: Callable[[], bool], timeout: float = WAIT_TIMEOUT) -> bool:
    """
    Aguarda o predicado ficar verdadeiro (processamento é feito pelo worker).

    Verifica o predicado continuamente e retorna assim que ele vale; o
    ``timeout`` só limita a espera quando o comportamento esperado não ocorre.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.001)
    return predicate()


def _wait_worker_evaluated(wrapper: OnDemandRequestWrapper) -> None:
    """
    Aguarda o worker terminar de avaliar a fila após o último ``add()``.

    Substitui esperas fixas (``time.sleep``) por sincronização com o worker:
    ``add()`` enfileira a entidade e então sinaliza ``_work_available``; só
    o worker limpa esse sinal, no início de cada iteração e antes de avaliar
    a fila (``_process_internal``). Com o sinal limpo, a iteração em curso
    já enxerga a entidade. Um novo sinal (despertar espúrio, inofensivo como
    o que o próprio worker emite após cada lote) só é limpo na iteração
    seguinte, isto é, depois que a avaliação anterior, com qualquer envio
    que ela tenha decidido fazer, terminou.
    """
    for wake_again in (True, False):
        assert _wait_until(lambda: not wrapper._work_available.is_set()), (
            "O worker não consumiu o sinal de trabalho"
        )
        if wake_again:
            wrapper._work_available.set()


def _create_wrapper(
    context: SankhyaContext,
    cancel_token: Optional[threading.Event] = None,
    **kwargs,
) -> OnDemandRequestWrapper:
    """Cria um OnDemandRequestWrapper de salvamento ligado ao contexto."""
    return OnDemandRequestWrapper(
        service=ServiceName.CRUD_SERVICE_SAVE,
        cancel_token=cancel_token or threading.Event(),
        context=context,
        **kwargs,
    )


@pytest.fixture
def sankhya_server():
    """Servidor simulado instalado no transporte HTTP do SDK."""
    server = _SankhyaServerStub()
    with patch("sankhya_sdk.core.low_level_wrapper.requests.Session") as session_cls:
        session_cls.return_value.request.side_effect = server
        yield server


@pytest.fixture
def sankhya_context(sankhya_server):
    """Contexto Sankhya autenticado contra o servidor simulado."""
    wrapper = SankhyaWrapper(host="http://test.local", port=8180)
    wrapper.authenticate("user", "pass")
    context = SankhyaContext(wrapper)
    yield context
    context.dispose()


@pytest.fixture
def failure_events():
    """Captura os OnDemandRequestFailureEvent publicados durante o teste."""
    events: List[OnDemandRequestFailureEvent] = []
    lock = threading.Lock()

    def handler(event: OnDemandRequestFailureEvent) -> None:
        with lock:
            events.append(event)

    EventBus.subscribe(OnDemandRequestFailureEvent, handler)
    try:
        yield events
    finally:
        EventBus.unsubscribe(OnDemandRequestFailureEvent, handler)


# =============================================================================
# Testes
# =============================================================================


@pytest.mark.integration
class TestOnDemandBasic:
    """Testes básicos de on-demand."""

    def test_on_demand_single_request(self, sankhya_server, sankhya_context):
        """Testa requisição única on-demand."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        wrapper = _create_wrapper(sankhya_context)

        try:
            wrapper.add(Partner(name="Parceiro OnDemand"))

            # Flush para processar
            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            # A entidade foi enviada em uma única requisição saveRecord
            assert _sent_batches(sankhya_server, ["Parceiro OnDemand"]) == [
                {"Parceiro OnDemand"}
            ]
            assert wrapper.entities_sent == 1
            assert wrapper.entities_sent_successfully == 1
        finally:
            _dispose_quietly(wrapper)

    def test_on_demand_batch_processing(self, sankhya_server, sankhya_context):
        """Testa processamento de lote de requisições."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        names = [f"Parceiro {i}" for i in range(1, 6)]
        wrapper = _create_wrapper(sankhya_context, throughput=5)

        try:
            # Adicionar múltiplos itens, aguardando o worker avaliar a fila a
            # cada um: abaixo do throughput as entidades continuam acumuladas
            for name in names[:-1]:
                wrapper.add(Partner(name=name))
                _wait_worker_evaluated(wrapper)
                assert sankhya_server.bodies(SAVE_RECORD) == []
            wrapper.add(Partner(name=names[-1]))

            # Flush para processar todos
            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            # Throughput atingido: as 5 entidades vão em um único lote
            assert _sent_batches(sankhya_server, names) == [set(names)]
            assert wrapper.entities_sent == 5
            assert wrapper.entities_sent_successfully == 5
        finally:
            _dispose_quietly(wrapper)


@pytest.mark.integration
class TestOnDemandThrottling:
    """Testes de controle de throughput."""

    def test_on_demand_with_throughput_limit(self, sankhya_server, sankhya_context):
        """Testa controle de throughput."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        names = [f"Parceiro {i}" for i in range(1, 6)]
        partners = [Partner(name=name) for name in names]

        # Throughput de 2 por vez, sem lotes acima do throughput
        wrapper = _create_wrapper(
            sankhya_context, throughput=2, allow_above_throughput=False
        )

        def sent_requests() -> int:
            return len(sankhya_server.bodies(SAVE_RECORD))

        try:
            # Ao atingir o throughput o lote é enviado sem precisar de flush
            wrapper.add(partners[0])
            wrapper.add(partners[1])
            assert _wait_until(lambda: sent_requests() == 1), (
                f"Lote não enviado ao atingir o throughput: {sent_requests()} requisições"
            )

            wrapper.add(partners[2])
            wrapper.add(partners[3])
            assert _wait_until(lambda: sent_requests() == 2), (
                f"Segundo lote não enviado: {sent_requests()} requisições"
            )

            # Abaixo do throughput a entidade aguarda o flush
            wrapper.add(partners[4])
            _wait_worker_evaluated(wrapper)
            assert sent_requests() == 2
            assert wrapper.queue_size == 1

            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            assert _sent_batches(sankhya_server, names) == [
                {names[0], names[1]},
                {names[2], names[3]},
                {names[4]},
            ]
            assert wrapper.entities_sent_successfully == 5
        finally:
            _dispose_quietly(wrapper)

    def test_on_demand_with_concurrency_limit(self, sankhya_server, sankhya_context):
        """Testa limite de concorrência."""
        lock = threading.Lock()
        in_flight = {"current": 0, "max": 0}
        request_threads: List[threading.Thread] = []

        # Medir requisições simultâneas e registrar a thread de cada envio
        # (sem atraso artificial na resposta: a thread identifica o worker)
        def tracked_save(body: str) -> bytes:
            with lock:
                in_flight["current"] += 1
                in_flight["max"] = max(in_flight["max"], in_flight["current"])
                request_threads.append(threading.current_thread())
            try:
                return _save_ok(body)
            finally:
                with lock:
                    in_flight["current"] -= 1

        sankhya_server.on(SAVE_RECORD, tracked_save)
        names = [f"Parceiro {i}" for i in range(1, 6)]
        wrapper = _create_wrapper(sankhya_context, throughput=3)

        try:
            # Primeiro lote ao atingir o throughput; o restante vai no flush,
            # de modo que há mais de um envio para comparar as threads
            for name in names[:3]:
                wrapper.add(Partner(name=name))
            assert _wait_until(lambda: len(sankhya_server.bodies(SAVE_RECORD)) == 1)
            for name in names[3:]:
                wrapper.add(Partner(name=name))

            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            batches = _sent_batches(sankhya_server, names)
            assert batches == [set(names[:3]), set(names[3:])]
            # Todas as entidades enviadas exatamente uma vez
            assert set().union(*batches) == set(names)
            assert sum(len(batch) for batch in batches) == len(names)
            # Um único worker: todos os envios saem da mesma thread (que não é
            # a do teste), então nunca há duas requisições simultâneas
            assert len(set(request_threads)) == 1
            assert request_threads[0] is not threading.current_thread()
            assert in_flight["max"] == 1
            assert wrapper.entities_sent_successfully == 5
        finally:
            _dispose_quietly(wrapper)


@pytest.mark.integration
class TestOnDemandErrorHandling:
    """Testes de tratamento de erros."""

    def test_on_demand_error_handling(
        self, sankhya_server, sankhya_context, failure_events
    ):
        """Testa tratamento de erros individuais."""
        failing_name = "Parceiro Falha"

        # Toda requisição que contém a entidade inválida falha; as demais têm sucesso
        def save_record(body: str) -> bytes:
            if failing_name in _values_in(body):
                return create_error_response("DB.ERROR", "Erro no banco")
            return _save_ok(body)

        sankhya_server.on(SAVE_RECORD, save_record)
        partners = [
            Partner(name="Parceiro 1"),
            Partner(name=failing_name),
            Partner(name="Parceiro 3"),
        ]
        wrapper = _create_wrapper(sankhya_context, throughput=3)

        try:
            for partner in partners:
                wrapper.add(partner)

            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            # Apenas a entidade inválida gera evento de falha
            assert len(failure_events) == 1
            event = failure_events[0]
            assert event.entity is partners[1]
            assert isinstance(event.exception, SankhyaException)
            assert "Erro no banco" in str(event.exception)

            # As demais entidades foram salvas
            saved = set().union(
                *(
                    batch
                    for batch in _sent_batches(
                        sankhya_server, ["Parceiro 1", failing_name, "Parceiro 3"]
                    )
                    if failing_name not in batch
                )
            )
            assert saved == {"Parceiro 1", "Parceiro 3"}
            assert wrapper.entities_sent == 3
            assert wrapper.entities_sent_successfully == 2
        finally:
            _dispose_quietly(wrapper)

    def test_on_demand_retry_failed_requests(
        self, sankhya_server, sankhya_context, failure_events
    ):
        """Testa retry de requisições falhas."""
        attempts = {"count": 0}

        # Primeira tentativa falha (timeout da consulta), segunda sucede
        def save_record(body: str) -> bytes:
            attempts["count"] += 1
            if attempts["count"] == 1:
                return create_error_response(
                    "TIMEOUT", "O tempo limite da consulta foi atingido"
                )
            return _save_ok(body)

        sankhya_server.on(SAVE_RECORD, save_record)
        wrapper = _create_wrapper(sankhya_context)

        try:
            wrapper.add(Partner(name="Parceiro Retry"))

            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            # Falha transitória + nova tentativa bem-sucedida
            assert _sent_batches(sankhya_server, ["Parceiro Retry"]) == [
                {"Parceiro Retry"},
                {"Parceiro Retry"},
            ]
            assert failure_events == []
            assert wrapper.entities_sent_successfully == 1
        finally:
            _dispose_quietly(wrapper)


@pytest.mark.integration
class TestOnDemandCancellation:
    """Testes de cancelamento."""

    def test_on_demand_cancellation(self, sankhya_server, sankhya_context):
        """Testa cancelamento de processamento."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        names = [f"Parceiro {i}" for i in range(10)]
        cancel_token = threading.Event()

        # Throughput alto: nada é enviado antes do cancelamento
        wrapper = _create_wrapper(sankhya_context, cancel_token=cancel_token, throughput=100)

        try:
            # Adicionar itens
            for name in names:
                wrapper.add(Partner(name=name))

            # Cancelar antes de processar tudo
            cancel_token.set()

            # Após o cancelamento, novas entidades são recusadas
            with pytest.raises(CanceledOnDemandRequestWrapperException):
                wrapper.add(Partner(name="Parceiro Apos Cancelamento"))

            # Dispose deve funcionar normalmente
            _run_with_timeout(wrapper.dispose)
            assert wrapper.is_disposed

            # As entidades pendentes não são perdidas: enviadas uma única vez
            batches = _sent_batches(
                sankhya_server, names + ["Parceiro Apos Cancelamento"]
            )
            assert set().union(*batches) == set(names)
            assert sum(len(batch) for batch in batches) == len(names)
        finally:
            _dispose_quietly(wrapper)


@pytest.mark.integration
class TestOnDemandProgress:
    """Testes de rastreamento de progresso."""

    def test_on_demand_progress_tracking(self, sankhya_server, sankhya_context):
        """Testa rastreamento de progresso."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        wrapper = _create_wrapper(
            sankhya_context, throughput=2, allow_above_throughput=False
        )

        try:
            assert wrapper.request_count == 0
            assert wrapper.entities_sent == 0
            assert wrapper.entities_sent_successfully == 0

            # Primeiro lote (throughput atingido)
            for i in range(2):
                wrapper.add(Partner(name=f"Parceiro {i}"))
            assert _wait_until(lambda: wrapper.entities_sent_successfully == 2), (
                "Progresso não refletiu o primeiro lote: "
                f"{wrapper.entities_sent_successfully} entidades"
            )
            assert wrapper.entities_sent == 2
            assert wrapper.request_count == 1

            # Restante via flush
            for i in range(2, 5):
                wrapper.add(Partner(name=f"Parceiro {i}"))
            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            # Progresso deve ter sido atualizado
            assert wrapper.entities_sent == 5
            assert wrapper.entities_sent_successfully == 5
            assert wrapper.request_count == len(sankhya_server.bodies(SAVE_RECORD))
        finally:
            _dispose_quietly(wrapper)


@pytest.mark.integration
class TestOnDemandFactory:
    """Testes do OnDemandRequestFactory."""

    def test_factory_create_wrapper(self, sankhya_server, sankhya_context):
        """Testa criação de wrapper via factory."""
        logins_before = len(sankhya_server.bodies(LOGIN))
        logouts_before = len(sankhya_server.bodies(LOGOUT))
        count_before = OnDemandRequestFactory.get_instance_count()

        # Criar via factory
        key = OnDemandRequestFactory.create_instance(
            Partner,
            ServiceName.CRUD_SERVICE_SAVE,
            threading.Event(),
            context=sankhya_context,
            throughput=5,
        )

        try:
            assert isinstance(key, uuid.UUID)
            on_demand = OnDemandRequestFactory.get_instance_by_key(key)
            assert on_demand is not None
            assert not on_demand.is_disposed
            assert (
                OnDemandRequestFactory.get_instance_for_service(
                    Partner, ServiceName.CRUD_SERVICE_SAVE
                )
                is on_demand
            )
            assert OnDemandRequestFactory.get_instance_count() == count_before + 1

            # O wrapper usa uma sessão dedicada (novo login)
            assert _wait_until(
                lambda: len(sankhya_server.bodies(LOGIN)) == logins_before + 1
            )

            _run_with_timeout(OnDemandRequestFactory.finalize_by_key, key)

            assert on_demand.is_disposed
            assert OnDemandRequestFactory.get_instance_by_key(key) is None
            assert OnDemandRequestFactory.get_instance_count() == count_before

            # A sessão dedicada é encerrada ao finalizar o wrapper (logout)
            assert len(sankhya_server.bodies(LOGOUT)) == logouts_before + 1
        finally:
            OnDemandRequestFactory.finalize_by_key(key)


@pytest.mark.integration
class TestOnDemandAsync:
    """Testes de processamento assíncrono."""

    @pytest.mark.asyncio
    async def test_async_on_demand_processing(self, sankhya_server, sankhya_context):
        """Testa processamento assíncrono on-demand."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        names = [f"Parceiro Async {i}" for i in range(3)]
        wrapper = AsyncOnDemandRequestWrapper(
            service=ServiceName.CRUD_SERVICE_SAVE,
            cancel_event=asyncio.Event(),
            throughput=3,
            context=sankhya_context,
        )

        async def run() -> None:
            # Saída do contexto faz flush e dispose
            async with wrapper:
                for name in names:
                    await wrapper.add(Partner(name=name))
                await wrapper.flush()

        try:
            await asyncio.wait_for(run(), timeout=WAIT_TIMEOUT)

            assert wrapper.is_disposed
            batches = _sent_batches(sankhya_server, names)
            assert set().union(*batches) == set(names)
            assert sum(len(batch) for batch in batches) == len(names)
            assert wrapper.entities_sent_successfully == 3
        finally:
            try:
                await asyncio.wait_for(wrapper.dispose(), timeout=WAIT_TIMEOUT)
            except asyncio.TimeoutError:
                pass


@pytest.mark.integration
class TestOnDemandProducts:
    """Testes de on-demand com Products."""

    def test_on_demand_products(self, sankhya_server, sankhya_context):
        """Testa processamento on-demand de produtos."""
        sankhya_server.on(SAVE_RECORD, _save_ok)
        names = [f"Produto {i}" for i in range(3)]
        wrapper = _create_wrapper(sankhya_context, throughput=3)

        try:
            for name in names:
                wrapper.add(Product(name=name, code_volume="UN"))

            _run_with_timeout(wrapper.flush)
            _run_with_timeout(wrapper.dispose)

            bodies = sankhya_server.bodies(SAVE_RECORD)
            batches = _sent_batches(sankhya_server, names)
            assert set().union(*batches) == set(names)
            assert sum(len(batch) for batch in batches) == len(names)
            # Produtos são salvos na entidade Produto
            assert all(_root_entities(body) == {"Produto"} for body in bodies)
            assert wrapper.entities_sent_successfully == 3
        finally:
            _dispose_quietly(wrapper)
