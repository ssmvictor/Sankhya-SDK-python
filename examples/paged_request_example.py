# -*- coding: utf-8 -*-
"""
Exemplos de uso do PagedRequestWrapper.

Este arquivo demonstra diferentes cenários de uso do PagedRequestWrapper
para carregar grandes conjuntos de dados do Sankhya.
"""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta
from typing import List

# =============================================================================
# Configuração
# =============================================================================

# Carrega variáveis de ambiente (use python-dotenv em produção)
SANKHYA_HOST = os.environ.get("SANKHYA_HOST", "http://localhost")
SANKHYA_PORT = int(os.environ.get("SANKHYA_PORT", "8180"))
SANKHYA_USERNAME = os.environ.get("SANKHYA_USERNAME", "")
SANKHYA_PASSWORD = os.environ.get("SANKHYA_PASSWORD", "")


# =============================================================================
# Exemplo 1: Uso Básico Síncrono
# =============================================================================

def exemplo_basico():
    """
    Exemplo básico de uso do PagedRequestWrapper.
    
    Carrega parceiros de forma paginada e imprime seus nomes.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
    # Cria contexto autenticado
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        # Configura requisição
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        # request.request_body = ... configurar conforme necessário
        
        print("Carregando parceiros...")
        count = 0
        
        # Itera sobre resultados paginados
        for partner in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=object,  # Substituir por sua entidade
            token=ctx.token,
            timeout=timedelta(minutes=5),
            max_results=100,
        ):
            count += 1
            # print(f"Parceiro: {partner}")
        
        print(f"Total carregado: {count} parceiros")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 2: Com Callbacks de Progresso
# =============================================================================

def exemplo_com_callbacks():
    """
    Exemplo com callbacks para monitorar progresso.
    
    Demonstra como usar callbacks para acompanhar o carregamento
    de páginas em tempo real.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.value_objects import PagedRequestEventArgs
    
    def on_page_loaded(args: PagedRequestEventArgs):
        """Callback quando página é carregada com sucesso."""
        progress = args.progress_percentage or 0
        print(
            f"📄 Página {args.current_page}: "
            f"{args.quantity_loaded} itens carregados "
            f"({progress:.1f}%)"
        )
    
    def on_page_error(args: PagedRequestEventArgs):
        """Callback quando ocorre erro no carregamento."""
        print(
            f"❌ Erro na página {args.current_page}: "
            f"{args.exception}"
        )
    
    def on_page_processed(args: PagedRequestEventArgs):
        """Callback quando página é processada."""
        print(
            f"✅ Página {args.current_page} processada. "
            f"Total: {args.total_loaded}"
        )
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        print("Iniciando carregamento com callbacks...\n")
        
        for item in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=object,
            token=ctx.token,
            timeout=timedelta(minutes=10),
            on_page_loaded=on_page_loaded,
            on_page_error=on_page_error,
            on_page_processed=on_page_processed,
        ):
            pass  # Processa item
        
        print("\nCarregamento concluído!")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 3: Processamento On-Demand
# =============================================================================

def exemplo_processamento_on_demand():
    """
    Exemplo com processamento on-demand de lotes.
    
    Demonstra como usar o callback process_data para enriquecer
    dados antes de retorná-los.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
    def enrich_batch(items: List):
        """
        Enriquece lote de itens com informações adicionais.
        
        Este callback é chamado para cada lote de ~50 itens.
        """
        print(f"🔄 Processando lote de {len(items)} itens...")
        
        for item in items:
            # Simula enriquecimento de dados
            # item.extra_info = fetch_external_data(item.code)
            pass
        
        print(f"✅ Lote processado!")
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        print("Carregando com processamento on-demand...\n")
        
        for item in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=object,
            token=ctx.token,
            timeout=timedelta(minutes=5),
            process_data=enrich_batch,
            max_results=200,
        ):
            # Item já foi enriquecido pelo callback
            pass
        
        print("\nProcessamento concluído!")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 4: Versão Assíncrona
# =============================================================================

async def exemplo_async():
    """
    Exemplo de uso assíncrono do PagedRequestWrapper.
    
    Demonstra como usar async for para processar resultados
    de forma assíncrona.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        print("Carregando de forma assíncrona...\n")
        count = 0
        
        async for item in PagedRequestWrapper.get_paged_results_async(
            request=request,
            entity_type=object,
            token=ctx.token,
            timeout=timedelta(minutes=5),
            max_results=100,
        ):
            count += 1
            # Simula processamento assíncrono
            await asyncio.sleep(0.01)
        
        print(f"\nTotal carregado: {count} itens")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 5: Processamento Assíncrono com Callback
# =============================================================================

async def exemplo_async_com_processamento():
    """
    Exemplo de processamento assíncrono com callback.
    
    Demonstra como processar lotes de forma assíncrona usando
    o callback process_data.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
    async def process_batch_async(items: List):
        """Processa lote de forma assíncrona."""
        print(f"🔄 Processando {len(items)} itens de forma assíncrona...")
        
        # Simula múltiplas operações assíncronas
        tasks = [asyncio.sleep(0.01) for _ in items]
        await asyncio.gather(*tasks)
        
        print(f"✅ Lote processado!")
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        print("Carregando com processamento assíncrono...\n")
        
        async for item in PagedRequestWrapper.get_paged_results_async(
            request=request,
            entity_type=object,
            token=ctx.token,
            timeout=timedelta(minutes=5),
            process_data=process_batch_async,
            max_results=200,
        ):
            pass
        
        print("\nProcessamento concluído!")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 6: Tratamento de Erros
# =============================================================================

def exemplo_tratamento_erros():
    """
    Exemplo de tratamento robusto de erros.
    
    Demonstra como tratar erros de forma adequada durante
    o carregamento paginado.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.request_wrappers import (
        PagedRequestWrapper,
        PagedRequestException,
    )
    from sankhya_sdk.value_objects import PagedRequestEventArgs
    
    errors = []
    
    def on_error(args: PagedRequestEventArgs):
        """Registra erros para análise posterior."""
        errors.append({
            "page": args.current_page,
            "error": str(args.exception),
        })
        print(f"⚠️ Erro registrado na página {args.current_page}")
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        
        print("Carregando com tratamento de erros...\n")
        
        try:
            for item in PagedRequestWrapper.get_paged_results(
                request=request,
                entity_type=object,
                token=ctx.token,
                timeout=timedelta(minutes=5),
                on_page_error=on_error,
            ):
                pass
                
        except PagedRequestException as e:
            print(f"\n❌ Erro fatal na página {e.page}: {e}")
            if e.inner_exception:
                print(f"   Causa: {e.inner_exception}")
        
        if errors:
            print(f"\n⚠️ {len(errors)} erros registrados durante o carregamento")
            for err in errors:
                print(f"   - Página {err['page']}: {err['error']}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de PagedRequestWrapper")
    print("=" * 60)
    
    print("\n1. Exemplo Básico")
    print("-" * 40)
    # exemplo_basico()
    
    print("\n2. Exemplo com Callbacks")
    print("-" * 40)
    # exemplo_com_callbacks()
    
    print("\n3. Exemplo Processamento On-Demand")
    print("-" * 40)
    # exemplo_processamento_on_demand()
    
    print("\n4. Exemplo Assíncrono")
    print("-" * 40)
    # asyncio.run(exemplo_async())
    
    print("\n5. Exemplo Assíncrono com Processamento")
    print("-" * 40)
    # asyncio.run(exemplo_async_com_processamento())
    
    print("\n6. Exemplo Tratamento de Erros")
    print("-" * 40)
    # exemplo_tratamento_erros()
    
    print("\n" + "=" * 60)
    print("Descomente os exemplos para executar")
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
