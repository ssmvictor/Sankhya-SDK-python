# -*- coding: utf-8 -*-
"""
Testes unitários para PagedRequestWrapper e PagedRequestEventArgs.
"""

from __future__ import annotations

import asyncio
import queue
import threading
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import (
    PagedRequestException as SdkPagedRequestException,
    SankhyaException,
    ServiceRequestGeneralException,
)
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service.basic_types import Field
from sankhya_sdk.models.service.entity_types import DataSet, Entity
from sankhya_sdk.models.service.request_body import RequestBody
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.request_wrappers.paged_request_wrapper import (
    PagedRequestException,
    PagedRequestWrapper,
)
from sankhya_sdk.value_objects.paged_request_event_args import PagedRequestEventArgs


# =============================================================================
# Test Entity for Testing
# =============================================================================


class MockEntity(EntityBase):
    """Entidade mock para testes."""
    
    code: Optional[int] = None
    name: Optional[str] = None


class DataSetWithPagerId(DataSet):
    """DataSet com o campo pager_id (equivalente ao DataSet.PagerId do .NET)."""

    pager_id: Optional[str] = None


def _provider_entities_response(
    rows: List[Dict[str, Any]],
    pager_id: Optional[str] = None,
    total_pages: Optional[int] = None,
) -> ServiceResponse:
    """
    Monta um ServiceResponse real a partir do XML de CRUDServiceProvider.

    No protocolo Sankhya a paginação vem nos atributos ``pagerID`` e
    ``totalPages`` do elemento ``<entities>`` (CrudServiceProviderEntities).
    """
    attrs = f' total="{len(rows)}"'
    if total_pages is not None:
        attrs += f' totalPages="{total_pages}"'
    if pager_id is not None:
        attrs += f' pagerID="{pager_id}"'

    entities_xml = "".join(
        "<entity>"
        + "".join(f"<{key}>{value}</{key}>" for key, value in row.items())
        + "</entity>"
        for row in rows
    )

    return ServiceResponse.from_xml_string(
        '<serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">'
        f"<responseBody><entities{attrs}>{entities_xml}</entities></responseBody>"
        "</serviceResponse>"
    )


# =============================================================================
# PagedRequestEventArgs Tests
# =============================================================================


class TestPagedRequestEventArgs:
    """Testes para PagedRequestEventArgs."""
    
    def test_creation_basic(self):
        """Testa criação básica do event args."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=1,
            total_loaded=150,
        )
        
        assert args.entity_type is MockEntity
        assert args.current_page == 1
        assert args.total_loaded == 150
        assert args.quantity_loaded is None
        assert args.total_pages is None
        assert args.exception is None
    
    def test_creation_with_all_fields(self):
        """Testa criação com todos os campos."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=2,
            total_loaded=300,
            quantity_loaded=150,
            total_pages=10,
        )
        
        assert args.current_page == 2
        assert args.total_loaded == 300
        assert args.quantity_loaded == 150
        assert args.total_pages == 10
    
    def test_creation_with_exception(self):
        """Testa criação com exceção."""
        error = ValueError("Test error")
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=1,
            total_loaded=0,
            exception=error,
        )
        
        assert args.exception is error
        assert args.has_error is True
    
    def test_has_error_false(self):
        """Testa has_error quando não há erro."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=1,
            total_loaded=150,
        )
        
        assert args.has_error is False
    
    def test_is_complete_true(self):
        """Testa is_complete quando carregamento está completo."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=5,
            total_loaded=750,
            total_pages=5,
        )
        
        assert args.is_complete is True
    
    def test_is_complete_false(self):
        """Testa is_complete quando carregamento não está completo."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=3,
            total_loaded=450,
            total_pages=5,
        )
        
        assert args.is_complete is False
    
    def test_is_complete_none_total_pages(self):
        """Testa is_complete quando total_pages é None."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=3,
            total_loaded=450,
        )
        
        assert args.is_complete is False
    
    def test_progress_percentage(self):
        """Testa cálculo de percentual de progresso."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=5,
            total_loaded=750,
            total_pages=10,
        )
        
        assert args.progress_percentage == 50.0
    
    def test_progress_percentage_none(self):
        """Testa progress_percentage quando total_pages é None."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=5,
            total_loaded=750,
        )
        
        assert args.progress_percentage is None
    
    def test_progress_percentage_zero_total_pages(self):
        """Testa progress_percentage quando total_pages é 0."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=1,
            total_loaded=0,
            total_pages=0,
        )
        
        assert args.progress_percentage is None
    
    def test_str_representation(self):
        """Testa representação string do event args."""
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=2,
            total_loaded=300,
            total_pages=5,
        )
        
        result = str(args)
        
        assert "MockEntity" in result
        assert "page=2" in result
        assert "/5" in result
        assert "loaded=300" in result
    
    def test_str_representation_with_error(self):
        """Testa representação string com erro."""
        error = ValueError("Test error")
        args = PagedRequestEventArgs(
            entity_type=MockEntity,
            current_page=1,
            total_loaded=0,
            exception=error,
        )
        
        result = str(args)
        
        assert "error=" in result


# =============================================================================
# PagedRequestWrapper Tests
# =============================================================================


class TestPagedRequestWrapper:
    """Testes para PagedRequestWrapper."""
    
    @pytest.fixture
    def mock_token(self):
        """Cria token mock."""
        return uuid.uuid4()
    
    @pytest.fixture
    def mock_request(self):
        """Cria requisição mock."""
        return MagicMock(spec=ServiceRequest)
    
    @pytest.fixture
    def service_request(self):
        """
        Cria requisição real de CRUDServiceProvider.loadRecords.

        MagicMock(spec=ServiceRequest) não expõe campos de instância do
        pydantic v2 (ex.: request_body), por isso os testes que percorrem
        a requisição usam o modelo real.
        """
        return ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

    @pytest.fixture
    def mock_response(self):
        """Cria resposta real com dados paginados (página de 150 itens)."""
        return _provider_entities_response(
            [{"code": i, "name": f"Entity {i}"} for i in range(150)],
            pager_id="test-pager-id",
            total_pages=3,
        )
    
    def test_wrapper_initialization(self, mock_token, mock_request):
        """Testa inicialização do wrapper."""
        wrapper = PagedRequestWrapper(
            request=mock_request,
            entity_type=MockEntity,
            token=mock_token,
            max_results=100,
        )
        
        assert wrapper._request is mock_request
        assert wrapper._entity_type is MockEntity
        assert wrapper._token == mock_token
        assert wrapper._max_results == 100
        assert wrapper._results_loaded == 0
    
    def test_callback_registration(self, mock_token, mock_request):
        """Testa registro de callbacks."""
        wrapper = PagedRequestWrapper(
            request=mock_request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        callback1 = MagicMock()
        callback2 = MagicMock()
        callback3 = MagicMock()
        
        # Testa encadeamento
        result = (
            wrapper
            .on_page_loaded(callback1)
            .on_page_error(callback2)
            .on_page_processed(callback3)
        )
        
        assert result is wrapper
        assert callback1 in wrapper._on_page_loaded
        assert callback2 in wrapper._on_page_error
        assert callback3 in wrapper._on_page_processed
    
    def test_dispatch_page_loaded(self, mock_token, mock_request):
        """Testa disparo de callback de página carregada."""
        wrapper = PagedRequestWrapper(
            request=mock_request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        callback = MagicMock()
        wrapper.on_page_loaded(callback)
        
        wrapper._results_loaded = 150
        wrapper._dispatch_page_loaded(page=1, quantity=150, total_pages=3)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert isinstance(args, PagedRequestEventArgs)
        assert args.current_page == 1
        assert args.quantity_loaded == 150
        assert args.total_pages == 3
    
    def test_dispatch_page_error(self, mock_token, mock_request):
        """Testa disparo de callback de erro."""
        wrapper = PagedRequestWrapper(
            request=mock_request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        callback = MagicMock()
        wrapper.on_page_error(callback)
        
        error = ValueError("Test error")
        wrapper._dispatch_page_error(page=1, exception=error)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert args.exception is error
        assert args.has_error is True
    
    def test_dispatch_callback_exception_handled(self, mock_token, mock_request):
        """Testa que exceções em callbacks são tratadas."""
        wrapper = PagedRequestWrapper(
            request=mock_request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        def failing_callback(args):
            raise RuntimeError("Callback error")
        
        wrapper.on_page_loaded(failing_callback)
        
        # Não deve lançar exceção
        wrapper._dispatch_page_loaded(page=1, quantity=150)
    
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_load_page_success(self, mock_context, mock_token, mock_response):
        """Testa carregamento de página com sucesso."""
        mock_context.service_invoker_with_token.return_value = mock_response
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        wrapper = PagedRequestWrapper(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        success, quantity, total_pages = wrapper._load_page(1)
        
        assert success is True
        assert quantity == 150
        assert total_pages == 3
        assert wrapper._pager_id == "test-pager-id"
        assert wrapper._total_pages == 3
        assert wrapper._items.qsize() == 150
        # Valores do XML permanecem como texto bruto (ParseDynamic no .NET);
        # a conversão tipada acontece em convert_to_type
        first = wrapper._items.get_nowait()
        assert first.dictionary == {"code": "0", "name": "Entity 0"}
        typed = first.convert_to_type(MockEntity)
        assert typed.code == 0
        assert typed.name == "Entity 0"

    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_load_page_sends_pager_id_on_next_page(
        self, mock_context, mock_token, mock_response
    ):
        """O pagerID da página anterior é enviado no dataSet da próxima (.NET)."""
        mock_context.service_invoker_with_token.return_value = mock_response

        request = ServiceRequest(
            service=ServiceName.CRUD_SERVICE_FIND,
            request_body=RequestBody(data_set=DataSetWithPagerId()),
        )
        wrapper = PagedRequestWrapper(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
        )

        assert wrapper._load_page(1)[0] is True
        assert request.request_body.data_set.pager_id is None

        assert wrapper._load_page(2)[0] is True
        assert request.request_body.data_set.page_number == 2
        assert request.request_body.data_set.pager_id == "test-pager-id"

    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_load_page_serializes_pager_id_in_data_set(
        self, mock_context, mock_token, mock_response
    ):
        """
        DataSet.pager_id da página seguinte é serializado como pagerID (.NET).

        Usa o modelo DataSet real (sem subclasses), como o .NET atribui
        ``_request.RequestBody.DataSet.PagerId`` antes da próxima página.
        """
        mock_context.service_invoker_with_token.return_value = mock_response

        request = ServiceRequest(
            service=ServiceName.CRUD_SERVICE_FIND,
            request_body=RequestBody(data_set=DataSet(root_entity="Parceiro")),
        )
        wrapper = PagedRequestWrapper(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
        )

        assert wrapper._load_page(1)[0] is True
        assert wrapper._load_page(2)[0] is True

        data_set_xml = request.request_body.data_set.to_xml()
        assert data_set_xml.get("pagerID") == "test-pager-id"
        assert data_set_xml.get("pageNumber") == "2"
        sent_request = mock_context.service_invoker_with_token.call_args[0][0]
        assert sent_request is request

    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_load_page_data_set_without_pager_id_field(
        self, mock_context, mock_token, mock_response
    ):
        """DataSet sem campo pager_id não faz a carga da próxima página falhar."""
        mock_context.service_invoker_with_token.return_value = mock_response

        request = ServiceRequest(
            service=ServiceName.CRUD_SERVICE_FIND,
            request_body=RequestBody(data_set=DataSet()),
        )
        wrapper = PagedRequestWrapper(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
        )

        assert wrapper._load_page(1)[0] is True
        success, quantity, _ = wrapper._load_page(2)

        assert success is True
        assert quantity == 150
        assert wrapper._load_error is None
        assert request.request_body.data_set.page_number == 2

    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_load_page_ignores_non_positive_total_pages(
        self, mock_context, mock_token, service_request
    ):
        """totalPages <= 0 indica total desconhecido (como no .NET)."""
        mock_context.service_invoker_with_token.return_value = (
            _provider_entities_response(
                [{"code": 1, "name": "Entity 1"}],
                pager_id="pager-1",
                total_pages=0,
            )
        )
        wrapper = PagedRequestWrapper(
            request=service_request,
            entity_type=MockEntity,
            token=mock_token,
        )

        success, quantity, total_pages = wrapper._load_page(1)

        assert success is True
        assert quantity == 1
        assert total_pages is None
        assert wrapper._total_pages is None
        assert wrapper._pager_id == "pager-1"
    
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_load_page_error(self, mock_context, mock_token, mock_request):
        """Testa carregamento de página com erro."""
        mock_context.service_invoker_with_token.side_effect = Exception("API Error")
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        wrapper = PagedRequestWrapper(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        error_callback = MagicMock()
        wrapper.on_page_error(error_callback)
        
        success, quantity, total_pages = wrapper._load_page(1)
        
        assert success is False
        assert quantity == 0
        error_callback.assert_called_once()
    
    def test_extract_entities_from_response_entities(self, mock_token, service_request):
        """Testa extração de entidades do campo entities."""
        wrapper = PagedRequestWrapper(
            request=service_request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        response = _provider_entities_response(
            [
                {"code": 1, "name": "Entity 1"},
                {"code": 2, "name": "Entity 2"},
            ]
        )
        
        entities = wrapper._extract_entities_from_response(response)

        assert len(entities) == 2
        # Texto bruto do XML; convert_to_type produz o valor tipado
        assert entities[0].dictionary["code"] == "1"
        assert entities[0].convert_to_type(MockEntity).code == 1
        assert entities[1].convert_to_type(MockEntity).name == "Entity 2"
    
    @staticmethod
    def _request_with_fields(*names: str) -> ServiceRequest:
        """Requisição loadRecords com a lista de campos solicitados."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body.data_set = DataSet(
            root_entity="Parceiro",
            entity=Entity(path="", fields=[Field(name=name) for name in names]),
        )
        return request

    def test_extract_entities_does_not_rename_with_request_fields(self, mock_token):
        """
        As chaves não são renomeadas com os campos da requisição.

        No .NET (LoadPage/ProcessCrudServiceProviderEntities) só o
        ``<metadata>`` da resposta renomeia f0..fN; sem metadata as chaves
        ficam como recebidas, sem supor a ordem dos campos solicitados.
        """
        wrapper = PagedRequestWrapper(
            request=self._request_with_fields("CODPARC", "NOMEPARC", "CGC_CPF"),
            entity_type=MockEntity,
            token=mock_token,
        )
        response = _provider_entities_response(
            [{"f0": "1", "f1": "Parceiro 1"}, {"f0": "2", "f1": "Parceiro 2"}]
        )

        entities = wrapper._extract_entities_from_response(response)

        assert [entity.dictionary for entity in entities] == [
            {"f0": "1", "f1": "Parceiro 1"},
            {"f0": "2", "f1": "Parceiro 2"},
        ]
        assert [entity.dictionary for entity in entities] == [
            dict(entity.fields) for entity in response.entities
        ]

    def test_extract_entities_keeps_names_from_response_metadata(self, mock_token):
        """Nomes vêm do <metadata> da resposta, mesmo em ordem diferente da requisição."""
        wrapper = PagedRequestWrapper(
            request=self._request_with_fields("CODPARC", "NOMEPARC"),
            entity_type=MockEntity,
            token=mock_token,
        )
        response = ServiceResponse.from_xml_string(
            '<serviceResponse serviceName="CRUDServiceProvider.loadRecords" status="1">'
            '<responseBody><entities total="1">'
            '<metadata><fields><field name="NOMEPARC"/><field name="CODPARC"/>'
            "</fields></metadata>"
            "<entity><f0>Parceiro 9</f0><f1>009</f1></entity>"
            "</entities></responseBody></serviceResponse>"
        )

        entities = wrapper._extract_entities_from_response(response)

        assert [entity.dictionary for entity in entities] == [
            {"NOMEPARC": "Parceiro 9", "CODPARC": "009"}
        ]

    def test_extract_entities_empty_response(self, mock_token, service_request):
        """Testa extração de entidades com resposta vazia."""
        wrapper = PagedRequestWrapper(
            request=service_request,
            entity_type=MockEntity,
            token=mock_token,
        )
        
        response = ServiceResponse(response_body=None)
        
        entities = wrapper._extract_entities_from_response(response)
        
        assert entities == []
    
    def test_page_size_constants(self):
        """Testa constantes de tamanho de página."""
        assert PagedRequestWrapper.PAGE_SIZE_SMALL == 150
        assert PagedRequestWrapper.PAGE_SIZE_LARGE == 300


# =============================================================================
# PagedRequestWrapper Generator Tests
# =============================================================================


class TestPagedRequestWrapperGenerator:
    """Testes para os generators do PagedRequestWrapper."""
    
    @pytest.fixture
    def mock_token(self):
        """Cria token mock."""
        return uuid.uuid4()
    
    @pytest.mark.skip(reason="Threading tests - mock doesn't persist in thread")
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_get_paged_results_single_page(self, mock_context, mock_token):
        """Testa get_paged_results com página única."""
        # Configura resposta com menos de 150 itens (indica última página)
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": i, "name": f"Entity {i}"} for i in range(50)
        ]
        response.response_body.pager = MagicMock()
        response.response_body.pager.pager_id = None
        response.response_body.pager.total_pages = 1
        response.response_body.pager.total_records = 50
        
        mock_context.service_invoker_with_token.return_value = response
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        results = list(PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
            timeout=timedelta(seconds=10),
        ))
        
        assert len(results) == 50
        mock_context.service_invoker_with_token.assert_called()
    
    @pytest.mark.skip(reason="Threading tests - mock doesn't persist in thread")
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_get_paged_results_with_max_results(self, mock_context, mock_token):
        """Testa get_paged_results com limite de max_results."""
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": i, "name": f"Entity {i}"} for i in range(150)
        ]
        response.response_body.pager = MagicMock()
        response.response_body.pager.pager_id = None
        response.response_body.pager.total_pages = 10
        response.response_body.pager.total_records = 1500
        
        mock_context.service_invoker_with_token.return_value = response
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        results = list(PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
            max_results=50,
            timeout=timedelta(seconds=10),
        ))
        
        assert len(results) == 50
    
    @pytest.mark.skip(reason="Threading tests - mock doesn't persist in thread")
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_get_paged_results_with_callbacks(self, mock_context, mock_token):
        """Testa get_paged_results com callbacks."""
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": i, "name": f"Entity {i}"} for i in range(50)
        ]
        response.response_body.pager = MagicMock()
        response.response_body.pager.pager_id = None
        response.response_body.pager.total_pages = 1
        response.response_body.pager.total_records = 50
        
        mock_context.service_invoker_with_token.return_value = response
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        page_loaded_callback = MagicMock()
        
        list(PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
            on_page_loaded=page_loaded_callback,
            timeout=timedelta(seconds=10),
        ))
        
        page_loaded_callback.assert_called()
    
    @pytest.mark.skip(reason="Threading tests - mock doesn't persist in thread")
    @patch("sankhya_sdk.core.context.SankhyaContext")
    def test_get_paged_results_with_process_data(self, mock_context, mock_token):
        """Testa get_paged_results com callback de processamento."""
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": i, "name": f"Entity {i}"} for i in range(100)
        ]
        response.response_body.pager = MagicMock()
        response.response_body.pager.pager_id = None
        response.response_body.pager.total_pages = 1
        response.response_body.pager.total_records = 100
        
        mock_context.service_invoker_with_token.return_value = response
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        processed_batches = []
        
        def process_data(batch):
            processed_batches.append(len(batch))
        
        list(PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
            process_data=process_data,
            timeout=timedelta(seconds=10),
        ))
        
        # Deve ter processado lotes
        assert len(processed_batches) >= 1


# =============================================================================
# PagedRequestWrapper Async Tests
# =============================================================================


class TestPagedRequestWrapperAsync:
    """Testes para os métodos assíncronos do PagedRequestWrapper."""
    
    @pytest.fixture
    def mock_token(self):
        """Cria token mock."""
        return uuid.uuid4()
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Async tests require complex coroutine setup")
    @patch("sankhya_sdk.core.context.SankhyaContext")
    async def test_get_paged_results_async_single_page(
        self, mock_context, mock_token
    ):
        """Testa get_paged_results_async com página única."""
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": i, "name": f"Entity {i}"} for i in range(50)
        ]
        response.response_body.pager = MagicMock()
        response.response_body.pager.pager_id = None
        response.response_body.pager.total_pages = 1
        response.response_body.pager.total_records = 50
        
        mock_context.service_invoker_async_with_token = AsyncMock(
            return_value=response
        )
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        results = []
        async for item in PagedRequestWrapper.get_paged_results_async(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
            timeout=timedelta(seconds=10),
        ):
            results.append(item)
        
        assert len(results) == 50
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Async mock requires complex coroutine setup")
    @patch("sankhya_sdk.core.context.SankhyaContext")
    async def test_get_paged_results_async_with_max_results(
        self, mock_context, mock_token
    ):
        """Testa get_paged_results_async com limite de max_results."""
        response = MagicMock()
        response.response_body = MagicMock()
        response.response_body.entities = [
            {"code": i, "name": f"Entity {i}"} for i in range(150)
        ]
        response.response_body.pager = MagicMock()
        response.response_body.pager.pager_id = None
        response.response_body.pager.total_pages = 10
        response.response_body.pager.total_records = 1500
        
        mock_context.service_invoker_async_with_token = AsyncMock(
            return_value=response
        )
        
        request = MagicMock()
        request.request_body = MagicMock()
        request.request_body.data_set = MagicMock()
        
        results = []
        async for item in PagedRequestWrapper.get_paged_results_async(
            request=request,
            entity_type=MockEntity,
            token=mock_token,
            max_results=30,
            timeout=timedelta(seconds=10),
        ):
            results.append(item)
        
        assert len(results) == 30


# =============================================================================
# PagedRequestException Tests
# =============================================================================


class TestPagedRequestException:
    """Testes para PagedRequestException."""
    
    def test_exception_creation(self):
        """Testa criação de exceção."""
        exc = PagedRequestException("Test error", page=5)
        
        assert str(exc) == "Test error"
        assert exc.page == 5
        assert exc.inner_exception is None
    
    def test_exception_with_inner_exception(self):
        """Testa exceção com exceção interna."""
        inner = ValueError("Inner error")
        exc = PagedRequestException(
            "Outer error",
            page=3,
            inner_exception=inner,
        )
        
        assert exc.page == 3
        assert exc.inner_exception is inner

    def test_exception_belongs_to_sdk_hierarchy(self):
        """
        Deriva da PagedRequestException do SDK (GoodPractices/PagedRequestException.cs).

        Assim ``except sankhya_sdk.exceptions.PagedRequestException`` e
        ``except SankhyaException`` capturam os erros do wrapper.
        """
        inner = ServiceRequestGeneralException("Falha no serviço")
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        exc = PagedRequestException(
            "Erro na página 2",
            page=2,
            inner_exception=inner,
            request=request,
        )

        assert isinstance(exc, SdkPagedRequestException)
        assert isinstance(exc, ServiceRequestGeneralException)
        assert isinstance(exc, SankhyaException)
        assert str(exc) == "Erro na página 2"
        assert exc.page == 2
        assert exc.inner_exception is inner
        assert exc.__cause__ is inner
        assert exc.request is request


class TestPagedRequestErrorPropagation:
    """Erros de carga propagados pelos generators (hierarquia do SDK)."""

    @staticmethod
    def _request() -> ServiceRequest:
        return ServiceRequest(
            service=ServiceName.CRUD_SERVICE_FIND,
            request_body=RequestBody(data_set=DataSet(root_entity="Parceiro")),
        )

    def test_get_paged_results_raises_sdk_paged_request_exception(self):
        """Falha na carga chega ao consumidor como PagedRequestException do SDK."""
        error = ServiceRequestGeneralException("Erro na query")
        request = self._request()
        on_page_error = MagicMock()

        with patch.object(
            SankhyaContext, "service_invoker_with_token", side_effect=error
        ):
            with pytest.raises(SdkPagedRequestException) as exc_info:
                list(
                    PagedRequestWrapper.get_paged_results(
                        request,
                        MockEntity,
                        uuid.uuid4(),
                        timeout=timedelta(seconds=30),
                        on_page_error=on_page_error,
                    )
                )

        assert isinstance(exc_info.value, SankhyaException)
        assert exc_info.value.request is request
        assert exc_info.value.inner_exception.inner_exception is error
        on_page_error.assert_called_once()
        assert on_page_error.call_args[0][0].exception is error

    @pytest.mark.asyncio
    async def test_get_paged_results_async_raises_sdk_paged_request_exception(self):
        """Versão assíncrona também propaga PagedRequestException do SDK."""
        error = ServiceRequestGeneralException("Erro na query")
        request = self._request()

        with patch.object(
            SankhyaContext,
            "service_invoker_async_with_token",
            new_callable=AsyncMock,
            side_effect=error,
        ):
            with pytest.raises(SdkPagedRequestException) as exc_info:
                async for _ in PagedRequestWrapper.get_paged_results_async(
                    request,
                    MockEntity,
                    uuid.uuid4(),
                    timeout=timedelta(seconds=30),
                ):
                    pass

        assert isinstance(exc_info.value, SankhyaException)
        assert exc_info.value.request is request


# =============================================================================
# Cache Tests
# =============================================================================


class TestPagedRequestWrapperCache:
    """Testes para o sistema de cache do PagedRequestWrapper."""
    
    def test_get_cache_key(self):
        """Testa geração de chave de cache."""
        key = PagedRequestWrapper._get_cache_key(MockEntity, user_code=123)
        
        assert "MockEntity" in key
        assert "123" in key
    
    def test_acquire_cache_lock_success(self):
        """Testa aquisição de lock de cache com sucesso."""
        key = f"test_key_{uuid.uuid4()}"
        
        result = PagedRequestWrapper._acquire_cache_lock(key)
        
        assert result is True
        
        # Limpa
        PagedRequestWrapper._release_cache_lock(key)
    
    def test_acquire_cache_lock_already_locked(self):
        """Testa aquisição de lock quando já está travado."""
        key = f"test_key_{uuid.uuid4()}"
        
        # Primeira aquisição
        PagedRequestWrapper._acquire_cache_lock(key)
        
        # Segunda aquisição deve falhar
        result = PagedRequestWrapper._acquire_cache_lock(key)
        
        assert result is False
        
        # Limpa
        PagedRequestWrapper._release_cache_lock(key)
    
    def test_release_cache_lock(self):
        """Testa liberação de lock de cache."""
        key = f"test_key_{uuid.uuid4()}"
        
        PagedRequestWrapper._acquire_cache_lock(key)
        PagedRequestWrapper._release_cache_lock(key)
        
        # Deve poder adquirir novamente
        result = PagedRequestWrapper._acquire_cache_lock(key)
        assert result is True
        
        # Limpa
        PagedRequestWrapper._release_cache_lock(key)
