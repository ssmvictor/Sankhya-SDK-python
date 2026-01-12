# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Product (Produto).

Demonstra operaÃ§Ãµes de consulta:
- Listar produtos ativos
- Buscar produto por cÃ³digo
- Filtrar por grupo/marca

Tabela Sankhya: TGFPRO
"""

from __future__ import annotations

import os
from datetime import timedelta
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
# Exemplo 1: Listar Produtos Ativos
# =============================================================================

def listar_produtos_ativos(max_results: int = 100):
    """
    Lista produtos ativos de forma paginada.
    
    Filtra apenas produtos com ATIVO = 'S'.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.product import Product
    
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
                root_entity="Produto",
                include_presentation=True,
                parallel_loader=False,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPROD"),       # Código do produto
                        Field(name="DESCRPROD"),     # Descrição
                        Field(name="REFERENCIA"),    # Referência/SKU
                        Field(name="NCM"),           # NCM fiscal
                        Field(name="CODGRUPOPROD"),  # Código do grupo
                        Field(name="CODMARCA"),      # Código da marca
                        Field(name="ATIVO"),         # Status ativo
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="ATIVO = 'S'"
                )
            )
        )
        
        print("ðŸ“¦ Listando produtos ativos...")
        count = 0
        
        for product in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=Product,
            token=ctx.token,
            timeout=timedelta(minutes=5),
            max_results=max_results,
        ):
            count += 1
            ref = product.reference or "-"
            print(f"  {count}. [{product.code}] {product.description} (Ref: {ref})")
        
        print(f"\nâœ… Total: {count} produtos ativos")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 2: Buscar Produto por CÃ³digo
# =============================================================================

def buscar_produto_por_codigo(codigo: int) -> Optional[dict]:
    """
    Busca um produto especÃ­fico pelo cÃ³digo (CODPROD).
    
    Retorna os dados do produto ou None se nÃ£o encontrado.
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
                root_entity="Produto",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPROD"), Field(name="DESCRPROD"), Field(name="REFERENCIA"), Field(name="NCM"),
                        Field(name="CODGRUPOPROD"), Field(name="CODMARCA"), Field(name="ATIVO"),
                        Field(name="PESOBRUTO"), Field(name="PESOLIQ"), Field(name="UNIDADE")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="CODPROD = ?",
                    parameters=[
                        Parameter(type=ParameterType.INTEGER, value=str(codigo))
                    ]
                )
            )
        )
        
        print(f"ðŸ” Buscando produto cÃ³digo {codigo}...")
        
        response = ctx.service_invoker(request)
        
        if response.is_success and response.entities:
            product = response.entities[0]
            print(f"âœ… Encontrado: {product}")
            return product
        else:
            print(f"âŒ Produto {codigo} nÃ£o encontrado")
            return None
            
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 3: Buscar Produto por NCM
# =============================================================================

def buscar_produtos_por_ncm(ncm: str, max_results: int = 50):
    """
    Busca produtos pelo NCM (Nomenclatura Comum do Mercosul).
    
    Ãštil para consultas fiscais.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field, Parameter
    )
    from sankhya_sdk.enums.parameter_type import ParameterType
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.product import Product
    
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
                root_entity="Produto",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPROD"), Field(name="DESCRPROD"), Field(name="NCM"), Field(name="REFERENCIA"), Field(name="ATIVO")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="NCM LIKE ? AND ATIVO = 'S'",
                    parameters=[
                        Parameter(type=ParameterType.STRING, value=f"{ncm}%")
                    ]
                )
            )
        )
        
        print(f"ðŸ” Buscando produtos com NCM iniciando em '{ncm}'...")
        count = 0
        
        for product in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=Product,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            print(f"  [{product.code}] {product.description} - NCM: {product.ncm}")
        
        print(f"\nðŸ“Š Encontrados: {count} produtos")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 4: Filtrar por Grupo de Produto
# =============================================================================

def filtrar_por_grupo(codigo_grupo: int, max_results: int = 50):
    """
    Filtra produtos por cÃ³digo de grupo (CODGRUPOPROD).
    
    Grupos organizam produtos por categoria no Sankhya.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field, Parameter
    )
    from sankhya_sdk.enums.parameter_type import ParameterType
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.product import Product
    
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
                root_entity="Produto",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPROD"), Field(name="DESCRPROD"), Field(name="REFERENCIA"),
                        Field(name="CODGRUPOPROD"), Field(name="ATIVO")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="CODGRUPOPROD = ? AND ATIVO = 'S'",
                    parameters=[
                        Parameter(type=ParameterType.INTEGER, value=str(codigo_grupo))
                    ]
                )
            )
        )
        
        print(f"ðŸ“‚ Listando produtos do grupo {codigo_grupo}...")
        count = 0
        
        for product in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=Product,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            status = "âœ…" if product.is_active else "âŒ"
            print(f"  {status} [{product.code}] {product.description}")
        
        print(f"\nðŸ“Š Produtos no grupo: {count}")
        
    finally:
        ctx.dispose()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Produtos (TGFPRO)")
    print("=" * 60)
    
    print("\n1. Listar Produtos Ativos")
    print("-" * 40)
    # listar_produtos_ativos(max_results=10)
    
    print("\n2. Buscar Produto por CÃ³digo")
    print("-" * 40)
    # buscar_produto_por_codigo(1)
    
    print("\n3. Buscar por NCM")
    print("-" * 40)
    # buscar_produtos_por_ncm("8471")  # Computadores
    
    print("\n4. Filtrar por Grupo")
    print("-" * 40)
    # filtrar_por_grupo(1)
    
    print("\n" + "=" * 60)
    print("Descomente os exemplos para executar")
    print("Configure as variÃ¡veis de ambiente SANKHYA_*")
    print("=" * 60)
