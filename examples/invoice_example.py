# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade InvoiceHeader (Nota Fiscal).

Demonstra operaÃ§Ãµes de consulta:
- Listar notas fiscais
- Buscar nota por nÃºmero Ãºnico (NUNOTA)
- Verificar status de NF-e
- JOIN com TGFITE para soma de QTDNEG

Tabelas Sankhya: 
- TGFCAB (CabeÃ§alho da Nota)
- TGFITE (Itens da Nota)
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================================================
# ConfiguraÃ§Ã£o
# =============================================================================

SANKHYA_HOST = os.environ.get("SANKHYA_HOST", "http://localhost")
SANKHYA_PORT = int(os.environ.get("SANKHYA_PORT", "8180"))
SANKHYA_USERNAME = os.environ.get("SANKHYA_USERNAME", "")
SANKHYA_PASSWORD = os.environ.get("SANKHYA_PASSWORD", "")


# =============================================================================
# Exemplo 1: Listar Notas Fiscais
# =============================================================================

def listar_notas_fiscais(max_results: int = 100):
    """
    Lista notas fiscais de forma paginada.
    
    Retorna notas com informaÃ§Ãµes bÃ¡sicas do cabeÃ§alho.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        RequestBody, DataSet, Entity
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.invoice_header import InvoiceHeader
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="CabecalhoNota",
                include_presentation_fields="S",
                parallel_loader="false",
                entities=[
                    Entity(
                        path="",
                        fields=[
                            "NUNOTA",       # NÃºmero Ãºnico
                            "NUMNOTA",      # NÃºmero da nota
                            "DTNEG",        # Data de negociaÃ§Ã£o
                            "CODPARC",      # CÃ³digo do parceiro
                            "VLRNOTA",      # Valor da nota
                            "STATUSNFE",    # Status NF-e
                            "TIPMOV",       # Tipo de movimento
                        ]
                    )
                ]
            )
        )
        
        print("ðŸ“‹ Listando notas fiscais...")
        count = 0
        
        for invoice in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=InvoiceHeader,
            token=ctx.token,
            timeout=timedelta(minutes=5),
            max_results=max_results,
        ):
            count += 1
            status = invoice.fiscal_invoice_status or "-"
            valor = invoice.invoice_value or 0
            print(f"  {count}. NUNOTA:{invoice.single_number} | NÂº:{invoice.invoice_number} | R$ {valor:.2f} | NFe:{status}")
        
        print(f"\nâœ… Total: {count} notas")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 2: Buscar Nota por NUNOTA
# =============================================================================

def buscar_nota_por_nunota(nunota: int) -> Optional[dict]:
    """
    Busca uma nota fiscal especÃ­fica pelo nÃºmero Ãºnico (NUNOTA).
    
    Retorna os dados completos da nota ou None se nÃ£o encontrada.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria
    )
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="CabecalhoNota",
                include_presentation_fields="S",
                entities=[
                    Entity(
                        path="",
                        fields=[
                            "NUNOTA", "NUMNOTA", "DTNEG", "CODPARC",
                            "VLRNOTA", "STATUSNFE", "TIPMOV", "CODTIPOPER",
                            "CODTIPVENDA", "OBSERVACAO", "CODEMP"
                        ]
                    )
                ],
                criteria=LiteralCriteria(
                    expression="NUNOTA = :NUNOTA",
                    parameters=[{"name": "NUNOTA", "value": str(nunota)}]
                )
            )
        )
        
        print(f"ðŸ” Buscando nota NUNOTA {nunota}...")
        
        response = ctx.service_invoker(request)
        
        if response.is_success and response.entities:
            invoice = response.entities[0]
            print(f"âœ… Encontrada: {invoice}")
            return invoice
        else:
            print(f"âŒ Nota {nunota} nÃ£o encontrada")
            return None
            
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 3: Filtrar Notas Aprovadas (STATUSNFE = 'A')
# =============================================================================

def listar_notas_aprovadas(max_results: int = 50):
    """
    Lista notas fiscais com NF-e aprovada.
    
    STATUSNFE = 'A' significa nota aprovada na SEFAZ.
    
    Valores possÃ­veis de STATUSNFE:
    - 'A' = Aprovada
    - 'D' = Denegada
    - 'R' = Rejeitada
    - 'C' = Cancelada
    - 'E' = Em processamento
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.invoice_header import InvoiceHeader
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="CabecalhoNota",
                include_presentation_fields="S",
                entities=[
                    Entity(
                        path="",
                        fields=[
                            "NUNOTA", "NUMNOTA", "DTNEG", "CODPARC",
                            "VLRNOTA", "STATUSNFE"
                        ]
                    )
                ],
                criteria=LiteralCriteria(
                    expression="STATUSNFE = 'A'"  # 'A' = Aprovada
                )
            )
        )
        
        print("âœ… Listando notas com NF-e APROVADA (STATUSNFE = 'A')...")
        count = 0
        
        for invoice in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=InvoiceHeader,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            valor = invoice.invoice_value or 0
            print(f"  âœ… NUNOTA:{invoice.single_number} | NÂº:{invoice.invoice_number} | R$ {valor:.2f}")
        
        print(f"\nðŸ“Š Notas aprovadas: {count}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 4: Consulta com JOIN TGFITE - Soma de QTDNEG
# =============================================================================

def consultar_notas_com_quantidade_itens(max_results: int = 50):
    """
    Consulta notas com a soma das quantidades negociadas (QTDNEG).
    
    Faz JOIN entre TGFCAB e TGFITE para calcular SUM(QTDNEG).
    
    Esta consulta usa SQL nativo via CRUD_FIND para permitir
    agregaÃ§Ãµes que nÃ£o sÃ£o possÃ­veis com o CRUD padrÃ£o.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import ServiceRequest, RequestBody
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        # Para consultas com JOIN e agregaÃ§Ãµes, usamos CRUD_FIND com SQL
        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        
        # Query SQL com JOIN TGFCAB + TGFITE e SUM(QTDNEG)
        sql_query = """
            SELECT 
                CAB.NUNOTA,
                CAB.NUMNOTA,
                CAB.DTNEG,
                CAB.CODPARC,
                CAB.VLRNOTA,
                CAB.STATUSNFE,
                SUM(ITE.QTDNEG) AS TOTAL_QTDNEG
            FROM TGFCAB CAB
            INNER JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
            WHERE CAB.STATUSNFE = 'A'
            GROUP BY 
                CAB.NUNOTA, 
                CAB.NUMNOTA, 
                CAB.DTNEG, 
                CAB.CODPARC, 
                CAB.VLRNOTA, 
                CAB.STATUSNFE
            ORDER BY CAB.DTNEG DESC
        """
        
        # Configura o request body para consulta nativa
        request.request_body = RequestBody()
        request.request_body.custom_query = sql_query.strip()
        
        print("ðŸ“Š Consultando notas com soma de quantidades (JOIN TGFITE)...")
        print("-" * 60)
        
        response = ctx.service_invoker(request)
        
        if response.is_success:
            count = 0
            for row in response.entities or []:
                count += 1
                if count > max_results:
                    break
                    
                nunota = row.get("NUNOTA", "-")
                numnota = row.get("NUMNOTA", "-")
                vlrnota = float(row.get("VLRNOTA", 0) or 0)
                total_qtd = float(row.get("TOTAL_QTDNEG", 0) or 0)
                
                print(f"  NUNOTA:{nunota} | NÂº:{numnota} | R$ {vlrnota:.2f} | Qtd Total: {total_qtd:.2f}")
            
            print("-" * 60)
            print(f"ðŸ“‹ Exibidas: {min(count, max_results)} notas")
        else:
            print(f"âŒ Erro na consulta: {response.status_message}")
            
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 5: Filtrar Notas por Parceiro
# =============================================================================

def filtrar_notas_por_parceiro(codigo_parceiro: int, max_results: int = 50):
    """
    Filtra notas fiscais de um parceiro especÃ­fico.
    
    Ãštil para verificar histÃ³rico de compras/vendas de um cliente.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.invoice_header import InvoiceHeader
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="CabecalhoNota",
                include_presentation_fields="S",
                entities=[
                    Entity(
                        path="",
                        fields=[
                            "NUNOTA", "NUMNOTA", "DTNEG", "CODPARC",
                            "VLRNOTA", "STATUSNFE", "TIPMOV"
                        ]
                    )
                ],
                criteria=LiteralCriteria(
                    expression="CODPARC = :CODPARC",
                    parameters=[{"name": "CODPARC", "value": str(codigo_parceiro)}]
                )
            )
        )
        
        print(f"ðŸ“‹ Notas do parceiro {codigo_parceiro}...")
        count = 0
        
        for invoice in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=InvoiceHeader,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            status_nfe = invoice.fiscal_invoice_status or "-"
            valor = invoice.invoice_value or 0
            print(f"  NUNOTA:{invoice.single_number} | {invoice.movement_date} | R$ {valor:.2f} | NFe:{status_nfe}")
        
        print(f"\nðŸ“Š Notas do parceiro: {count}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Notas Fiscais (TGFCAB + TGFITE)")
    print("=" * 60)
    
    print("\n1. Listar Notas Fiscais")
    print("-" * 40)
    # listar_notas_fiscais(max_results=10)
    
    print("\n2. Buscar Nota por NUNOTA")
    print("-" * 40)
    # buscar_nota_por_nunota(12345)
    
    print("\n3. Listar Notas Aprovadas (STATUSNFE = 'A')")
    print("-" * 40)
    # listar_notas_aprovadas(max_results=10)
    
    print("\n4. Consulta com JOIN TGFITE (SUM QTDNEG)")
    print("-" * 40)
    # consultar_notas_com_quantidade_itens(max_results=10)
    
    print("\n5. Filtrar por Parceiro")
    print("-" * 40)
    # filtrar_notas_por_parceiro(1)
    
    print("\n" + "=" * 60)
    print("Descomente os exemplos para executar")
    print("Configure as variÃ¡veis de ambiente SANKHYA_*")
    print("=" * 60)
