# -*- coding: utf-8 -*-
"""
Testes de integração para PagedRequestWrapper.

Estes testes requerem uma conexão real com a API Sankhya e usam as mesmas
variáveis de ambiente do SDK (``SankhyaSettings``, ver ``.env.example``):
``SANKHYA_URL``, ``SANKHYA_PORT`` (padrão 8180), ``SANKHYA_USERNAME`` e
``SANKHYA_PASSWORD``. Sem elas, os testes são ignorados.
"""

from __future__ import annotations

import os
import threading
from datetime import timedelta
from typing import List

import pytest

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.service.basic_types import Field
from sankhya_sdk.models.service.entity_types import DataSet, Entity
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.request_wrappers.paged_request_wrapper import PagedRequestWrapper

# Marca todos os testes como integração (requerem API real)
pytestmark = pytest.mark.integration


# Variáveis de ambiente lidas pelo SDK (sankhya_sdk/config.py)
REQUIRED_ENV_VARS = ("SANKHYA_URL", "SANKHYA_USERNAME", "SANKHYA_PASSWORD")
DEFAULT_PORT = "8180"

# Skip se não houver credenciais configuradas
has_credentials = all(os.environ.get(name) for name in REQUIRED_ENV_VARS)

skip_no_credentials = pytest.mark.skipif(
    not has_credentials,
    reason=(
        "Credenciais Sankhya não configuradas "
        f"({', '.join(REQUIRED_ENV_VARS)})"
    ),
)


def _build_partner_request() -> ServiceRequest:
    """Monta a consulta CRUDServiceProvider.loadRecords de parceiros."""
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    request.request_body.data_set = DataSet(
        root_entity="Parceiro",
        entity=Entity(
            path="",
            fields=[Field(name="CODPARC"), Field(name="NOMEPARC")],
        ),
    )
    return request


@skip_no_credentials
class TestPagedRequestIntegration:
    """Testes de integração para PagedRequestWrapper."""

    @pytest.fixture
    def sankhya_context(self):
        """Cria contexto Sankhya autenticado."""
        from sankhya_sdk.core.context import SankhyaContext
        
        ctx = SankhyaContext(
            host=os.environ["SANKHYA_URL"],
            port=int(os.environ.get("SANKHYA_PORT") or DEFAULT_PORT),
            username=os.environ["SANKHYA_USERNAME"],
            password=os.environ["SANKHYA_PASSWORD"],
        )
        
        yield ctx
        
        ctx.dispose()

    def test_paged_request_real_api(self, sankhya_context):
        """Testa requisição paginada com API real."""
        pages_loaded = []
        
        def on_page_loaded(args):
            pages_loaded.append(args.current_page)
        
        results = list(PagedRequestWrapper.get_paged_results(
            request=_build_partner_request(),
            entity_type=Partner,
            token=sankhya_context.token,
            timeout=timedelta(minutes=2),
            max_results=100,
            on_page_loaded=on_page_loaded,
        ))
        
        assert len(results) > 0
        assert all(isinstance(partner, Partner) for partner in results)
        assert len(pages_loaded) > 0

    @pytest.mark.asyncio
    async def test_async_paged_request_real_api(self, sankhya_context):
        """Testa requisição paginada assíncrona com API real."""
        results = []
        async for item in PagedRequestWrapper.get_paged_results_async(
            request=_build_partner_request(),
            entity_type=Partner,
            token=sankhya_context.token,
            timeout=timedelta(minutes=2),
            max_results=50,
        ):
            results.append(item)
        
        assert len(results) > 0
        assert all(isinstance(partner, Partner) for partner in results)

    def test_large_dataset_pagination(self, sankhya_context):
        """Testa paginação com dataset grande (>1000 registros)."""
        pages_loaded = []
        
        def on_page_loaded(args):
            pages_loaded.append({
                "page": args.current_page,
                "quantity": args.quantity_loaded,
                "total": args.total_loaded,
            })
        
        results = list(PagedRequestWrapper.get_paged_results(
            request=_build_partner_request(),
            entity_type=Partner,
            token=sankhya_context.token,
            timeout=timedelta(minutes=5),
            max_results=1500,
            on_page_loaded=on_page_loaded,
        ))
        
        # Verifica que múltiplas páginas foram carregadas
        if len(results) > 300:
            assert len(pages_loaded) > 1

    def test_concurrent_paged_requests(self, sankhya_context):
        """Testa múltiplas requisições paginadas simultâneas."""
        results_1: List[Partner] = []
        results_2: List[Partner] = []
        
        def load_1():
            results_1.extend(PagedRequestWrapper.get_paged_results(
                request=_build_partner_request(),
                entity_type=Partner,
                token=sankhya_context.token,
                max_results=50,
                timeout=timedelta(minutes=2),
            ))
        
        def load_2():
            results_2.extend(PagedRequestWrapper.get_paged_results(
                request=_build_partner_request(),
                entity_type=Partner,
                token=sankhya_context.token,
                max_results=50,
                timeout=timedelta(minutes=2),
            ))
        
        t1 = threading.Thread(target=load_1)
        t2 = threading.Thread(target=load_2)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        assert len(results_1) > 0
        assert len(results_2) > 0
