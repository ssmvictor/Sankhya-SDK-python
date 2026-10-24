# -*- coding: utf-8 -*-
"""
Testes de integração completos para PagedRequestWrapper.

Testa paginação, callbacks, erros, cancelamento e operações assíncronas.

Os testes exercitam a API real do wrapper
(``PagedRequestWrapper.get_paged_results`` / ``get_paged_results_async``)
sobre um ``SankhyaContext`` autenticado, com o transporte HTTP simulado.
As respostas de ``CRUDServiceProvider.loadRecords`` seguem o protocolo do
Sankhya usado pela referência .NET
(``ServiceResponse.ProcessCrudServiceProviderEntities``): elemento
``<entities total=".." totalPages=".." pagerID="..">`` com ``<metadata>`` e
registros ``<entity><f0>..</f0>..</entity>``.

Regras de paginação da referência .NET (``PagedRequestWrapper.cs``): a primeira
página tem 150 registros e as seguintes 300; uma página menor indica o fim.
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from datetime import timedelta
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from lxml import etree

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.service.basic_types import Field
from sankhya_sdk.models.service.entity_types import DataSet, Entity
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.paged_request_wrapper import (
    PagedRequestEventArgs,
    PagedRequestWrapper,
)

from .conftest import (
    create_error_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
)

# =============================================================================
# Infraestrutura de teste (servidor Sankhya simulado)
# =============================================================================

LOAD_RECORDS = ServiceName.CRUD_SERVICE_FIND.internal_value
LOGIN = ServiceName.LOGIN.internal_value
LOGOUT = ServiceName.LOGOUT.internal_value

PARTNER_FIELDS = ("CODPARC", "NOMEPARC")
PRODUCT_FIELDS = ("CODPROD", "DESCRPROD", "CODVOL")

# Timeout das operações paginadas nos testes (evita travar a suíte)
PAGED_TIMEOUT = timedelta(seconds=30)

ResponseHandler = Callable[[str], bytes]


class _SankhyaServerStub:
    """
    Servidor Sankhya simulado no nível HTTP.

    Roteia cada requisição pelo parâmetro ``serviceName`` da URL e registra
    o corpo XML enviado, permitindo verificar o protocolo de paginação.
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


def _load_records_response(
    rows: Sequence[Sequence[object]],
    fields: Sequence[str],
    total_pages: Optional[int] = None,
    pager_id: Optional[str] = None,
) -> bytes:
    """
    Gera a resposta de CRUDServiceProvider.loadRecords no formato do Sankhya.

    Args:
        rows: Valores de cada registro, na ordem de ``fields``
        fields: Nomes dos campos (metadata)
        total_pages: Atributo ``totalPages`` (opcional)
        pager_id: Atributo ``pagerID`` (opcional)
    """
    root = etree.Element("serviceResponse", serviceName=LOAD_RECORDS, status="1")
    body = etree.SubElement(root, "responseBody")
    entities = etree.SubElement(body, "entities", total=str(len(rows)))
    if total_pages is not None:
        entities.set("totalPages", str(total_pages))
    if pager_id is not None:
        entities.set("pagerID", pager_id)

    metadata_fields = etree.SubElement(etree.SubElement(entities, "metadata"), "fields")
    for name in fields:
        etree.SubElement(metadata_fields, "field", name=name)

    for row in rows:
        entity = etree.SubElement(entities, "entity")
        for index, value in enumerate(row):
            etree.SubElement(entity, f"f{index}").text = str(value)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def _partner_rows(first: int, last: int) -> List[Tuple[int, str]]:
    """Gera registros de parceiros com códigos de ``first`` a ``last``."""
    return [(code, f"Parceiro {code}") for code in range(first, last + 1)]


def _build_find_request(root_entity: str, fields: Sequence[str]) -> ServiceRequest:
    """Monta a requisição CRUDServiceProvider.loadRecords consumida pelo wrapper."""
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    request.request_body.data_set = DataSet(
        root_entity=root_entity,
        entity=Entity(path="", fields=[Field(name=name) for name in fields]),
    )
    return request


def _data_set_attributes(body: str) -> Dict[str, str]:
    """Retorna os atributos do elemento dataSet de uma requisição."""
    data_set = etree.fromstring(body.encode("utf-8")).find("requestBody/dataSet")
    assert data_set is not None, f"Requisição sem dataSet: {body}"
    return dict(data_set.attrib)


def _page_number(body: str) -> int:
    """Número da página solicitada (ausente equivale à primeira página)."""
    return int(_data_set_attributes(body).get("pageNumber", "1"))


def _pages_handler(pages: Dict[int, bytes]) -> ResponseHandler:
    """Handler que responde de acordo com o pageNumber solicitado."""

    def handler(body: str) -> bytes:
        page = _page_number(body)
        assert page in pages, f"Página não esperada solicitada: {page}"
        return pages[page]

    return handler


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


def _get_paged_partners(context: SankhyaContext, **kwargs) -> List[Partner]:
    """Executa a consulta paginada de parceiros e materializa o resultado."""
    request = _build_find_request("Parceiro", PARTNER_FIELDS)
    return list(
        PagedRequestWrapper.get_paged_results(
            request,
            Partner,
            context.token,
            timeout=PAGED_TIMEOUT,
            **kwargs,
        )
    )


# =============================================================================
# Testes
# =============================================================================


@pytest.mark.integration
class TestPagedRequestBasic:
    """Testes básicos de paginação."""

    def test_paged_request_single_page(self, sankhya_server, sankhya_context):
        """Testa quando resultado cabe em uma página."""
        sankhya_server.on(
            LOAD_RECORDS,
            _pages_handler({1: _load_records_response(_partner_rows(1, 5), PARTNER_FIELDS)}),
        )

        results = _get_paged_partners(sankhya_context)

        assert len(results) == 5
        assert all(isinstance(partner, Partner) for partner in results)
        assert [partner.code for partner in results] == [1, 2, 3, 4, 5]
        assert results[0].name == "Parceiro 1"
        assert results[4].name == "Parceiro 5"
        # Página menor que 150 encerra a paginação: uma única requisição
        assert len(sankhya_server.bodies(LOAD_RECORDS)) == 1

    def test_paged_request_multiple_pages(self, sankhya_server, sankhya_context):
        """Testa múltiplas páginas (primeira página cheia com 150 registros)."""
        sankhya_server.on(
            LOAD_RECORDS,
            _pages_handler({
                1: _load_records_response(_partner_rows(1, 150), PARTNER_FIELDS),
                2: _load_records_response(_partner_rows(151, 200), PARTNER_FIELDS),
            }),
        )

        results = _get_paged_partners(sankhya_context)

        # Deve ter 200 registros no total, na ordem das páginas
        assert len(results) == 200
        assert [partner.code for partner in results] == list(range(1, 201))
        assert results[149].name == "Parceiro 150"
        assert results[150].name == "Parceiro 151"

        bodies = sankhya_server.bodies(LOAD_RECORDS)
        assert len(bodies) == 2
        assert _page_number(bodies[1]) == 2

    def test_paged_request_with_max_results(self, sankhya_server, sankhya_context):
        """Testa limite de resultados."""
        # Primeira página cheia (haveria mais páginas), mas queremos apenas 25
        sankhya_server.on(
            LOAD_RECORDS,
            _pages_handler({1: _load_records_response(_partner_rows(1, 150), PARTNER_FIELDS)}),
        )

        results = _get_paged_partners(sankhya_context, max_results=25)

        # Deve ter apenas 25 resultados
        assert len(results) == 25
        assert [partner.code for partner in results] == list(range(1, 26))
        # Limite atingido na primeira página: nenhuma página adicional solicitada
        assert len(sankhya_server.bodies(LOAD_RECORDS)) == 1

    def test_paged_request_propagates_pager_metadata(self, sankhya_server, sankhya_context):
        """
        Testa o uso dos metadados de paginação devolvidos pelo servidor.

        Referência .NET (PagedRequestWrapper.LoadPage): o pagerID e o
        totalPages vêm do elemento ``entities`` da resposta; o pagerID é
        reenviado no dataSet da próxima página e o totalPages é informado
        nos argumentos do evento de página carregada.
        """
        sankhya_server.on(
            LOAD_RECORDS,
            _pages_handler({
                1: _load_records_response(
                    _partner_rows(1, 150), PARTNER_FIELDS, total_pages=2, pager_id="PAGER-42"
                ),
                2: _load_records_response(
                    _partner_rows(151, 180), PARTNER_FIELDS, total_pages=2, pager_id="PAGER-42"
                ),
            }),
        )
        pages_loaded: List[PagedRequestEventArgs] = []

        results = _get_paged_partners(sankhya_context, on_page_loaded=pages_loaded.append)

        assert len(results) == 180
        assert [args.total_pages for args in pages_loaded] == [2, 2]

        bodies = sankhya_server.bodies(LOAD_RECORDS)
        assert len(bodies) == 2
        second_page = _data_set_attributes(bodies[1])
        assert second_page.get("pageNumber") == "2"
        assert second_page.get("pagerID") == "PAGER-42"


@pytest.mark.integration
class TestPagedRequestCallbacks:
    """Testes de callbacks de paginação."""

    def test_paged_request_on_page_loaded_callback(self, sankhya_server, sankhya_context):
        """Testa callback on_page_loaded."""
        sankhya_server.on(
            LOAD_RECORDS,
            _pages_handler({1: _load_records_response(_partner_rows(1, 10), PARTNER_FIELDS)}),
        )
        callback_calls: List[PagedRequestEventArgs] = []

        def on_page_loaded(args: PagedRequestEventArgs) -> None:
            callback_calls.append(args)

        results = _get_paged_partners(sankhya_context, on_page_loaded=on_page_loaded)

        assert len(results) == 10
        # Uma única página carregada: callback chamado exatamente uma vez
        assert len(callback_calls) == 1
        args = callback_calls[0]
        assert args.entity_type is Partner
        assert args.current_page == 1
        assert args.quantity_loaded == 10
        assert args.total_loaded == 10
        assert args.exception is None

    def test_paged_request_on_error_callback(self, sankhya_server, sankhya_context):
        """Testa callback de erro."""
        sankhya_server.on(
            LOAD_RECORDS, lambda body: create_error_response("QUERY.ERROR", "Erro na query")
        )
        errors: List[PagedRequestEventArgs] = []

        def on_page_error(args: PagedRequestEventArgs) -> None:
            errors.append(args)

        with pytest.raises(Exception) as exc_info:
            _get_paged_partners(sankhya_context, on_page_error=on_page_error)

        # Callback de erro chamado uma vez, com a página e a exceção do serviço
        assert len(errors) == 1
        assert errors[0].current_page == 1
        assert errors[0].has_error
        assert isinstance(errors[0].exception, SankhyaException)
        assert "Erro na query" in str(errors[0].exception)

        # O erro propagado ao consumidor pertence à hierarquia de exceções do SDK
        assert isinstance(exc_info.value, SankhyaException), (
            f"Erro de paginação propagado como {type(exc_info.value).__module__}."
            f"{type(exc_info.value).__name__}, fora da hierarquia SankhyaException"
        )


@pytest.mark.integration
class TestPagedRequestErrors:
    """Testes de erros durante paginação."""

    def test_paged_request_error_mid_pagination(self, sankhya_server, sankhya_context):
        """Testa erro durante paginação (no meio)."""
        first_page = _load_records_response(_partner_rows(1, 150), PARTNER_FIELDS)

        def load_records(body: str) -> bytes:
            # Primeira página OK, segunda página com erro
            if _page_number(body) == 1:
                return first_page
            return create_error_response("QUERY.ERROR", "Erro ao carregar registros")

        sankhya_server.on(LOAD_RECORDS, load_records)
        errors: List[PagedRequestEventArgs] = []
        results: List[Partner] = []
        request = _build_find_request("Parceiro", PARTNER_FIELDS)

        with pytest.raises(Exception) as exc_info:
            for item in PagedRequestWrapper.get_paged_results(
                request,
                Partner,
                sankhya_context.token,
                timeout=PAGED_TIMEOUT,
                on_page_error=errors.append,
            ):
                results.append(item)

        # Todos os registros da primeira página são entregues antes do erro
        assert [partner.code for partner in results] == list(range(1, 151))
        assert len(sankhya_server.bodies(LOAD_RECORDS)) == 2

        # O erro é sinalizado para a segunda página
        assert len(errors) == 1
        assert errors[0].current_page == 2
        assert errors[0].total_loaded == 150
        assert "Erro ao carregar registros" in str(errors[0].exception)

        # O erro propagado ao consumidor pertence à hierarquia de exceções do SDK
        assert isinstance(exc_info.value, SankhyaException), (
            f"Erro de paginação propagado como {type(exc_info.value).__module__}."
            f"{type(exc_info.value).__name__}, fora da hierarquia SankhyaException"
        )

    def test_paged_request_empty_result(self, sankhya_server, sankhya_context):
        """Testa paginação com resultado vazio."""
        sankhya_server.on(
            LOAD_RECORDS, _pages_handler({1: _load_records_response([], PARTNER_FIELDS)})
        )

        results = _get_paged_partners(sankhya_context)

        assert len(results) == 0
        assert len(sankhya_server.bodies(LOAD_RECORDS)) == 1


@pytest.mark.integration
class TestPagedRequestAsync:
    """Testes de paginação assíncrona."""

    @pytest.mark.asyncio
    async def test_async_paged_request(self, sankhya_server, sankhya_context):
        """Testa paginação assíncrona."""
        sankhya_server.on(
            LOAD_RECORDS,
            _pages_handler({1: _load_records_response(_partner_rows(1, 10), PARTNER_FIELDS)}),
        )
        request = _build_find_request("Parceiro", PARTNER_FIELDS)

        async def consume() -> List[Partner]:
            items: List[Partner] = []
            async for item in PagedRequestWrapper.get_paged_results_async(
                request,
                Partner,
                sankhya_context.token,
                timeout=PAGED_TIMEOUT,
            ):
                items.append(item)
            return items

        results = await asyncio.wait_for(consume(), timeout=PAGED_TIMEOUT.total_seconds())

        assert len(results) == 10
        assert [partner.code for partner in results] == list(range(1, 11))
        assert results[9].name == "Parceiro 10"


@pytest.mark.integration
class TestPagedRequestConcurrency:
    """Testes de concorrência em paginação."""

    def test_concurrent_paged_requests(self, sankhya_server, sankhya_context):
        """Testa múltiplas paginações simultâneas."""
        page = _load_records_response(_partner_rows(1, 5), PARTNER_FIELDS)
        sankhya_server.on(LOAD_RECORDS, lambda body: page)

        results_container: List[Tuple[int, List[int]]] = []
        errors: List[Tuple[int, Exception]] = []

        def fetch_partners(index: int) -> None:
            try:
                results = _get_paged_partners(sankhya_context)
                results_container.append((index, [partner.code for partner in results]))
            except Exception as e:  # pragma: no cover - diagnosticado pelo assert
                errors.append((index, e))

        threads = [
            threading.Thread(target=fetch_partners, args=(i,), daemon=True)
            for i in range(3)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=PAGED_TIMEOUT.total_seconds())

        assert not any(t.is_alive() for t in threads), "Paginação concorrente não terminou"
        # Todas as paginações devem ter sucesso, cada uma com seus 5 registros
        assert errors == []
        assert sorted(index for index, _ in results_container) == [0, 1, 2]
        assert all(codes == [1, 2, 3, 4, 5] for _, codes in results_container)
        assert len(sankhya_server.bodies(LOAD_RECORDS)) == 3


@pytest.mark.integration
class TestPagedRequestProducts:
    """Testes de paginação com Products."""

    def test_paged_products(self, sankhya_server, sankhya_context):
        """Testa paginação de produtos."""
        rows = [(code, f"Produto {code}", "UN") for code in range(1, 21)]
        sankhya_server.on(
            LOAD_RECORDS, _pages_handler({1: _load_records_response(rows, PRODUCT_FIELDS)})
        )
        request = _build_find_request("Produto", PRODUCT_FIELDS)

        results = list(
            PagedRequestWrapper.get_paged_results(
                request, Product, sankhya_context.token, timeout=PAGED_TIMEOUT
            )
        )

        assert len(results) == 20
        assert all(isinstance(product, Product) for product in results)
        assert results[0].code == 1
        assert results[0].name == "Produto 1"
        assert results[0].code_volume == "UN"
        assert results[19].code == 20
        first_request = sankhya_server.bodies(LOAD_RECORDS)[0]
        assert _data_set_attributes(first_request)["rootEntity"] == "Produto"
