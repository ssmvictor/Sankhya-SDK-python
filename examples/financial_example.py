# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Financeiro.

Demonstra operaÃ§Ãµes de consulta:
- Listar tÃ­tulos a receber/pagar
- Filtrar por vencimento
- Consultar tÃ­tulos em aberto

Tabela Sankhya: TGFFIN
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from sankhya_sdk.config import settings

# =============================================================================
# ConfiguraÃ§Ã£o
# =============================================================================

SANKHYA_HOST = settings.url
SANKHYA_PORT = settings.port
SANKHYA_USERNAME = settings.username
SANKHYA_PASSWORD = settings.password


# =============================================================================
# Exemplo 1: Listar TÃ­tulos Financeiros
# =============================================================================

def listar_titulos_financeiros(max_results: int = 100):
    """
    Lista tÃ­tulos financeiros de forma paginada.
    
    Retorna tÃ­tulos com informaÃ§Ãµes bÃ¡sicas do financeiro.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        RequestBody, DataSet, Entity, Field
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
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
                root_entity="Financeiro",
                include_presentation=True,
                parallel_loader=False,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="NUFIN"),        # Número único financeiro
                        Field(name="NUNOTA"),       # Número único da nota
                        Field(name="DTVENC"),       # Data de vencimento
                        Field(name="VLRDESDOB"),    # Valor do desdobramento
                        Field(name="CODPARC"),      # Código do parceiro
                        Field(name="RECDESP"),      # R=Receita, D=Despesa
                        Field(name="DHBAIXA"),      # Data/hora baixa
                        Field(name="PROVISAO"),     # É provisão?
                    ]
                )
            )
        )
        
        print("ðŸ’° Listando tÃ­tulos financeiros...")
        count = 0
        
        for titulo in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=dict,  # Usando dict pois nÃ£o hÃ¡ entidade especÃ­fica
            token=ctx.token,
            timeout=timedelta(minutes=5),
            max_results=max_results,
        ):
            count += 1
            nufin = titulo.get("NUFIN", "-")
            valor = float(titulo.get("VLRDESDOB", 0) or 0)
            tipo = "ðŸ“ˆ Receita" if titulo.get("RECDESP") == "R" else "ðŸ“‰ Despesa"
            print(f"  {count}. NUFIN:{nufin} | {tipo} | R$ {valor:.2f}")
        
        print(f"\nâœ… Total: {count} tÃ­tulos")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 2: TÃ­tulos a Receber em Aberto
# =============================================================================

def listar_a_receber_em_aberto(max_results: int = 50):
    """
    Lista tÃ­tulos a RECEBER que estÃ£o em aberto (sem baixa).
    
    Filtra:
    - RECDESP = 'R' (Receita)
    - DHBAIXA IS NULL (Sem data de baixa = em aberto)
    - PROVISAO != 'S' (NÃ£o Ã© provisÃ£o)
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
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
                root_entity="Financeiro",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="NUFIN"), Field(name="NUNOTA"), Field(name="DTVENC"), Field(name="VLRDESDOB"),
                        Field(name="CODPARC"), Field(name="RECDESP"), Field(name="DESDOBESSION")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="""
                        RECDESP = 'R' 
                        AND DHBAIXA IS NULL 
                        AND (PROVISAO IS NULL OR PROVISAO != 'S')
                    """
                )
            )
        )
        
        print("ðŸ“ˆ TÃ­tulos a RECEBER em aberto...")
        count = 0
        total_valor = 0.0
        
        for titulo in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=dict,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            nufin = titulo.get("NUFIN", "-")
            venc = titulo.get("DTVENC", "-")
            valor = float(titulo.get("VLRDESDOB", 0) or 0)
            total_valor += valor
            print(f"  NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f}")
        
        print(f"\nðŸ“Š Total a receber: {count} tÃ­tulos = R$ {total_valor:.2f}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 3: TÃ­tulos a Pagar em Aberto
# =============================================================================

def listar_a_pagar_em_aberto(max_results: int = 50):
    """
    Lista tÃ­tulos a PAGAR que estÃ£o em aberto (sem baixa).
    
    Filtra:
    - RECDESP = 'D' (Despesa)
    - DHBAIXA IS NULL (Sem data de baixa = em aberto)
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
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
                root_entity="Financeiro",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="NUFIN"), Field(name="NUNOTA"), Field(name="DTVENC"), Field(name="VLRDESDOB"),
                        Field(name="CODPARC"), Field(name="RECDESP")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="""
                        RECDESP = 'D' 
                        AND DHBAIXA IS NULL
                    """
                )
            )
        )
        
        print("ðŸ“‰ TÃ­tulos a PAGAR em aberto...")
        count = 0
        total_valor = 0.0
        
        for titulo in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=dict,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            nufin = titulo.get("NUFIN", "-")
            venc = titulo.get("DTVENC", "-")
            valor = float(titulo.get("VLRDESDOB", 0) or 0)
            total_valor += valor
            print(f"  NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f}")
        
        print(f"\nðŸ“Š Total a pagar: {count} tÃ­tulos = R$ {total_valor:.2f}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 4: TÃ­tulos Vencidos
# =============================================================================

def listar_titulos_vencidos(max_results: int = 50):
    """
    Lista tÃ­tulos vencidos e nÃ£o baixados.
    
    Filtra:
    - DTVENC < data atual
    - DHBAIXA IS NULL (em aberto)
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field, Parameter
    )
    from sankhya_sdk.enums.parameter_type import ParameterType
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        # Data atual formatada para SQL
        hoje = datetime.now().strftime("%d/%m/%Y")
        
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="Financeiro",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="NUFIN"), Field(name="NUNOTA"), Field(name="DTVENC"), Field(name="VLRDESDOB"),
                        Field(name="CODPARC"), Field(name="RECDESP")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="DTVENC < ? AND DHBAIXA IS NULL",
                    parameters=[
                        Parameter(type=ParameterType.DATETIME, value=hoje)
                    ]
                )
            )
        )
        
        print(f"âš ï¸ TÃ­tulos VENCIDOS (antes de {hoje})...")
        count = 0
        total_receber = 0.0
        total_pagar = 0.0
        
        for titulo in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=dict,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            nufin = titulo.get("NUFIN", "-")
            venc = titulo.get("DTVENC", "-")
            valor = float(titulo.get("VLRDESDOB", 0) or 0)
            tipo = titulo.get("RECDESP", "-")
            
            if tipo == "R":
                total_receber += valor
                emoji = "ðŸ“ˆ"
            else:
                total_pagar += valor
                emoji = "ðŸ“‰"
            
            print(f"  {emoji} NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f}")
        
        print(f"\nðŸ“Š Vencidos:")
        print(f"   A Receber: R$ {total_receber:.2f}")
        print(f"   A Pagar:   R$ {total_pagar:.2f}")
        print(f"   Total:     {count} tÃ­tulos")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 5: TÃ­tulos por Parceiro
# =============================================================================

def listar_titulos_por_parceiro(codigo_parceiro: int, max_results: int = 50):
    """
    Lista todos os tÃ­tulos financeiros de um parceiro especÃ­fico.
    
    Ãštil para verificar posiÃ§Ã£o financeira de um cliente/fornecedor.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field, Parameter
    )
    from sankhya_sdk.enums.parameter_type import ParameterType
    
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
                root_entity="Financeiro",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="NUFIN"), Field(name="NUMNOTA"), Field(name="DTNEG"), Field(name="DTVENC"),
                        Field(name="CODPARC"), Field(name="VLRDESDOB"), Field(name="VLRBAIXA"), 
                        Field(name="RECDESP"), Field(name="HISTORICO"), Field(name="CODTIPOPER")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="CODPARC = ?",
                    parameters=[
                        Parameter(type=ParameterType.INTEGER, value=str(codigo_parceiro))
                    ]
                )
            )
        )
        
        print(f"ðŸ’¼ TÃ­tulos do parceiro {codigo_parceiro}...")
        count = 0
        
        for titulo in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=dict,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            nufin = titulo.get("NUFIN", "-")
            venc = titulo.get("DTVENC", "-")
            valor = float(titulo.get("VLRDESDOB", 0) or 0)
            tipo = "ðŸ“ˆ" if titulo.get("RECDESP") == "R" else "ðŸ“‰"
            status = "âœ… Baixado" if titulo.get("DHBAIXA") else "â³ Aberto"
            
            print(f"  {tipo} NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f} | {status}")
        
        print(f"\nðŸ“Š Total de tÃ­tulos: {count}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Financeiro (TGFFIN)")
    print("=" * 60)
    
    print("\n1. Listar TÃ­tulos Financeiros")
    print("-" * 40)
    # listar_titulos_financeiros(max_results=10)
    
    print("\n2. TÃ­tulos a Receber em Aberto")
    print("-" * 40)
    # listar_a_receber_em_aberto(max_results=10)
    
    print("\n3. TÃ­tulos a Pagar em Aberto")
    print("-" * 40)
    # listar_a_pagar_em_aberto(max_results=10)
    
    print("\n4. TÃ­tulos Vencidos")
    print("-" * 40)
    # listar_titulos_vencidos(max_results=10)
    
    print("\n5. TÃ­tulos por Parceiro")
    print("-" * 40)
    # listar_titulos_por_parceiro(1)
    
    print("\n" + "=" * 60)
    print("Descomente os exemplos para executar")
    print("Configure as variÃ¡veis de ambiente SANKHYA_*")
    print("=" * 60)
