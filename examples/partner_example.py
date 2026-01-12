# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Partner (Parceiro).

Demonstra operações CRUD básicas:
- Listar parceiros
- Buscar parceiro por código
- Criar/Atualizar parceiro

Tabela Sankhya: TGFPAR
"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Optional

from sankhya_sdk.config import settings

# =============================================================================
# Configuração
# =============================================================================

SANKHYA_HOST = settings.url
SANKHYA_PORT = settings.port
SANKHYA_USERNAME = settings.username
SANKHYA_PASSWORD = settings.password


# =============================================================================
# Exemplo 1: Listar Parceiros (Paginado)
# =============================================================================

def listar_parceiros(max_results: int = 100):
    """
    Lista parceiros de forma paginada.
    
    Usa PagedRequestWrapper para carregar grandes volumes de dados
    sem sobrecarregar a memória.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, Field
    )
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.partner import Partner
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        # Configura requisição para buscar parceiros
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="Parceiro",
                include_presentation=True,
                parallel_loader=False,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPARC"),      # Código do parceiro
                        Field(name="NOMEPARC"),     # Nome
                        Field(name="CGC_CPF"),      # CNPJ/CPF
                        Field(name="EMAIL"),        # E-mail
                        Field(name="TELEFONE"),     # Telefone
                        Field(name="ATIVO"),        # Status ativo
                    ]
                )
            )
        )
        
        print("📋 Listando parceiros...")
        count = 0
        
        for partner in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=Partner,
            token=ctx.token,
            timeout=timedelta(minutes=5),
            max_results=max_results,
        ):
            count += 1
            print(f"  {count}. [{partner.code}] {partner.name}")
        
        print(f"\n✅ Total: {count} parceiros carregados")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 2: Buscar Parceiro por Código
# =============================================================================

def buscar_parceiro_por_codigo(codigo: int) -> Optional[dict]:
    """
    Busca um parceiro específico pelo código (CODPARC).
    
    Retorna os dados do parceiro ou None se não encontrado.
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
                root_entity="Parceiro",
                include_presentation_fields="S",
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPARC"), Field(name="NOMEPARC"), Field(name="CGC_CPF"), Field(name="EMAIL"),
                        Field(name="TELEFONE"), Field(name="CODCID"), Field(name="CODBAI"), Field(name="ENDERECO"),
                        Field(name="NUMEND"), Field(name="CEP"), Field(name="ATIVO"), Field(name="CLIENTE"), Field(name="FORNECEDOR")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="CODPARC = ?",
                    parameters=[
                        Parameter(type=ParameterType.INTEGER, value=str(codigo))
                    ]
                )
            )
        )
        
        print(f"🔍 Buscando parceiro código {codigo}...")
        
        response = ctx.service_invoker(request)
        
        if response.is_success and response.entities:
            partner = response.entities[0]
            print(f"✅ Encontrado: {partner}")
            return partner
        else:
            print(f"❌ Parceiro {codigo} não encontrado")
            return None
            
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 3: Filtrar Parceiros por Nome
# =============================================================================

def filtrar_parceiros_por_nome(nome_parcial: str, max_results: int = 50):
    """
    Filtra parceiros cujo nome contém o texto informado.
    
    Usa LIKE para busca parcial no campo NOMEPARC.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, LiteralCriteria, Field, Parameter
    )
    from sankhya_sdk.enums.parameter_type import ParameterType
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    from sankhya_sdk.models.transport.partner import Partner
    
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
                root_entity="Parceiro",
                include_presentation=True,
                entity=Entity(
                    path="",  # Path vazio indica entidade raiz
                    fields=[
                        Field(name="CODPARC"), 
                        Field(name="NOMEPARC"), 
                        Field(name="CGC_CPF"), 
                        Field(name="ATIVO")
                    ]
                ),
                criteria=LiteralCriteria(
                    expression="UPPER(NOMEPARC) LIKE ?",
                    parameters=[
                        Parameter(type=ParameterType.STRING, value=f"%{nome_parcial.upper()}%")
                    ]
                )
            )
        )
        
        print(f"🔍 Buscando parceiros com nome contendo '{nome_parcial}'...")
        count = 0
        
        for partner in PagedRequestWrapper.get_paged_results(
            request=request,
            entity_type=Partner,
            token=ctx.token,
            timeout=timedelta(minutes=2),
            max_results=max_results,
        ):
            count += 1
            status = "✅" if partner.is_active else "❌"
            print(f"  {status} [{partner.code}] {partner.name}")
        
        print(f"\n📊 Encontrados: {count} parceiros")
        
    finally:
        ctx.dispose()


# =============================================================================
# Exemplo 4: Criar/Atualizar Parceiro
# =============================================================================

def criar_ou_atualizar_parceiro(
    codigo: Optional[int],
    nome: str,
    cgc_cpf: Optional[str] = None,
    email: Optional[str] = None,
):
    """
    Cria um novo parceiro ou atualiza um existente.
    
    Se codigo for None, cria novo parceiro.
    Se codigo for informado, atualiza o parceiro existente.
    """
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service import (
        ServiceRequest, RequestBody, DataSet, Entity, Field
    )
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )
    
    try:
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
        
        # Monta campos do parceiro
        fields_data = {
            "NOMEPARC": nome,
            "ATIVO": "S",
            "CLIENTE": "S",
        }
        
        if codigo:
            fields_data["CODPARC"] = str(codigo)
        if cgc_cpf:
            fields_data["CGC_CPF"] = cgc_cpf
        if email:
            fields_data["EMAIL"] = email
        
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="Parceiro",
                include_presentation_fields="S",
                entities=[
                    Entity(
                        path="",
                        fields=[Field(name=k) for k in fields_data.keys()]
                    )
                ]
            )
        )
        
        # Nota: O corpo exato do SAVE depende da versão do Sankhya
        # Este é um exemplo simplificado
        
        action = "Atualizando" if codigo else "Criando"
        print(f"💾 {action} parceiro '{nome}'...")
        
        response = ctx.service_invoker(request)
        
        if response.is_success:
            print(f"✅ Parceiro salvo com sucesso!")
            return True
        else:
            print(f"❌ Erro ao salvar: {response.status_message}")
            return False
            
    finally:
        ctx.dispose()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Parceiros (TGFPAR)")
    print("=" * 60)
    
    print("\n1. Listar Parceiros (Paginado)")
    print("-" * 40)
    # listar_parceiros(max_results=10)
    
    print("\n2. Buscar Parceiro por Código")
    print("-" * 40)
    # buscar_parceiro_por_codigo(1)
    
    print("\n3. Filtrar por Nome")
    print("-" * 40)
    # filtrar_parceiros_por_nome("EMPRESA")
    
    print("\n4. Criar/Atualizar Parceiro")
    print("-" * 40)
    # criar_ou_atualizar_parceiro(
    #     codigo=None,
    #     nome="NOVO PARCEIRO TESTE",
    #     cgc_cpf="12345678000199",
    #     email="teste@empresa.com"
    # )
    
    print("\n" + "=" * 60)
    print("Descomente os exemplos para executar")
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
