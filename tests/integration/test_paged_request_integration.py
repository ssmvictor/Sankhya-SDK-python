# -*- coding: utf-8 -*-
"""
Testes de integração para PagedRequestWrapper.

Estes testes requerem uma conexão real com a API Sankhya.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import timedelta
from typing import List, Optional

import pytest

# Marca todos os testes como integração (requerem API real)
pytestmark = pytest.mark.integration


# Skip se não houver credenciais configuradas
has_credentials = all([
    os.environ.get("SANKHYA_HOST"),
    os.environ.get("SANKHYA_PORT"),
    os.environ.get("SANKHYA_USERNAME"),
    os.environ.get("SANKHYA_PASSWORD"),
])

skip_no_credentials = pytest.mark.skipif(
    not has_credentials,
    reason="Credenciais Sankhya não configuradas"
)


@skip_no_credentials
class TestPagedRequestIntegration:
    """Testes de integração para PagedRequestWrapper."""
    
    @pytest.fixture
    def sankhya_context(self):
        """Cria contexto Sankhya autenticado."""
        from sankhya_sdk.core.context import SankhyaContext
        
        ctx = SankhyaContext(
            host=os.environ["SANKHYA_HOST"],
            port=int(os.environ["SANKHYA_PORT"]),
            username=os.environ["SANKHYA_USERNAME"],
            password=os.environ["SANKHYA_PASSWORD"],
        )
        
        yield ctx
        
        ctx.dispose()
    
    def test_paged_request_real_api(self, sankhya_context):
        """Testa requisição paginada com API real."""
        from sankhya_sdk.enums.service_name import ServiceName
        from sankhya_sdk.models.service.service_request import ServiceRequest
        from sankhya_sdk.request_wrappers.paged_request_wrapper import (
            PagedRequestWrapper,
        )
        
        # Cria requisição para buscar parceiros
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        # Configurar request body conforme necessário
        
        pages_loaded = []
        
        def on_page_loaded(args):
            pages_loaded.append(args.current_page)
        
        results = list(PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=object,  # Substituir por entidade real
            token=sankhya_context.token,
            timeout=timedelta(minutes=2),
            max_results=100,
            on_page_loaded=on_page_loaded,
        ))
        
        assert len(results) > 0
        assert len(pages_loaded) > 0
    
    @pytest.mark.asyncio
    async def test_async_paged_request_real_api(self, sankhya_context):
        """Testa requisição paginada assíncrona com API real."""
        from sankhya_sdk.enums.service_name import ServiceName
        from sankhya_sdk.models.service.service_request import ServiceRequest
        from sankhya_sdk.request_wrappers.paged_request_wrapper import (
            PagedRequestWrapper,
        )
        
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        results = []
        async for item in PagedRequestWrapper.get_paged_results_async(
            request=request,
            entity_type=object,
            token=sankhya_context.token,
            timeout=timedelta(minutes=2),
            max_results=50,
        ):
            results.append(item)
        
        assert len(results) > 0
    
    def test_large_dataset_pagination(self, sankhya_context):
        """Testa paginação com dataset grande (>1000 registros)."""
        from sankhya_sdk.enums.service_name import ServiceName
        from sankhya_sdk.models.service.service_request import ServiceRequest
        from sankhya_sdk.request_wrappers.paged_request_wrapper import (
            PagedRequestWrapper,
        )
        
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        pages_loaded = []
        
        def on_page_loaded(args):
            pages_loaded.append({
                "page": args.current_page,
                "quantity": args.quantity_loaded,
                "total": args.total_loaded,
            })
        
        results = list(PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=object,
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
        import threading
        from sankhya_sdk.enums.service_name import ServiceName
        from sankhya_sdk.models.service.service_request import ServiceRequest
        from sankhya_sdk.request_wrappers.paged_request_wrapper import (
            PagedRequestWrapper,
        )
        
        results_1 = []
        results_2 = []
        
        def load_1():
            request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
            results_1.extend(PagedRequestWrapper.get_paged_results(
                request=request,
                entity_type=object,
                token=sankhya_context.token,
                max_results=50,
                timeout=timedelta(minutes=2),
            ))
        
        def load_2():
            request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
            results_2.extend(PagedRequestWrapper.get_paged_results(
                request=request,
                entity_type=object,
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
