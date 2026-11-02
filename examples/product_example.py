# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Produto (JSON Gateway).

Demonstra operações de consulta usando GatewayClient:
- Listar produtos ativos
- Buscar produto por código
- Filtrar por NCM/grupo

Tabela Sankhya: TGFPRO
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# =============================================================================
# Configuração
# =============================================================================

load_dotenv()

SANKHYA_CLIENT_ID = os.getenv("SANKHYA_CLIENT_ID")
SANKHYA_CLIENT_SECRET = os.getenv("SANKHYA_CLIENT_SECRET")
SANKHYA_AUTH_BASE_URL = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")
SANKHYA_X_TOKEN = os.getenv("SANKHYA_TOKEN")



def _create_client():
    """Cria e retorna um GatewayClient autenticado."""
    from sankhya_sdk.auth.oauth_client import OAuthClient
    from sankhya_sdk.http import GatewayClient, SankhyaSession

    oauth = OAuthClient(
        base_url=SANKHYA_AUTH_BASE_URL,
        token=SANKHYA_X_TOKEN,  # None se não configurado
    )
    oauth.authenticate(client_id=SANKHYA_CLIENT_ID, client_secret=SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    return GatewayClient(session)


def _extract_entities(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai lista de entidades da resposta do Gateway."""
    from sankhya_sdk.http import GatewayClient

    return GatewayClient.extract_records(response)


# =============================================================================
# Exemplo 1: Listar Produtos Ativos
# =============================================================================


def listar_produtos_ativos(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Lista produtos ativos.

    Args:
        max_results: Limite máximo de resultados

    Returns:
        Lista de dicionários com dados dos produtos
    """
    from sankhya_sdk.models.dtos import ProdutoListDTO

    client = _create_client()

    response = client.load_records(
        entity="Produto",
        fields=["CODPROD", "DESCRPROD", "REFERENCIA", "NCM", "ATIVO"],
        criteria="ATIVO = 'S'",
    )

    print("📦 Listando produtos ativos...")

    entities = _extract_entities(response)
    produtos = []

    for i, record in enumerate(entities[:max_results], 1):
        try:
            produto = ProdutoListDTO.model_validate(record)
            ref = produto.referencia or "-"
            print(f"  {i}. [{produto.codigo}] {produto.descricao} (Ref: {ref})")
            produtos.append(produto.model_dump())
        except Exception:
            codigo = record.get("CODPROD", "?")
            desc = record.get("DESCRPROD", "?")
            print(f"  {i}. [{codigo}] {desc}")

    print(f"\n✅ Total: {len(produtos)} produtos ativos")
    return produtos


# =============================================================================
# Exemplo 2: Buscar Produto por Código
# =============================================================================


def buscar_produto_por_codigo(codigo: int) -> Optional[Dict[str, Any]]:
    """
    Busca um produto específico pelo código (CODPROD).

    Args:
        codigo: Código do produto

    Returns:
        Dicionário com dados do produto ou None se não encontrado
    """
    from sankhya_sdk.models.dtos import ProdutoDTO

    client = _create_client()

    response = client.load_records(
        entity="Produto",
        fields=[
            "CODPROD",
            "DESCRPROD",
            "REFERENCIA",
            "NCM",
            "CODGRUPOPROD",
            "CODMARCA",
            "UNIDADE",
            "PESOBRUTO",
            "PESOLIQ",
            "ATIVO",
        ],
        criteria=f"CODPROD = {codigo}",
    )

    print(f"🔍 Buscando produto código {codigo}...")

    entities = _extract_entities(response)

    if entities:
        record = entities[0]
        try:
            produto = ProdutoDTO.model_validate(record)
            print(f"✅ Encontrado: [{produto.codigo}] {produto.descricao}")
            print(f"   Referência: {produto.referencia or 'N/A'}")
            print(f"   NCM: {produto.ncm or 'N/A'}")
            print(f"   Unidade: {produto.unidade or 'N/A'}")
            return produto.model_dump()
        except Exception:
            print(f"✅ Encontrado: {record}")
            return record
    else:
        print(f"❌ Produto {codigo} não encontrado")
        return None


# =============================================================================
# Exemplo 3: Buscar Produtos por NCM
# =============================================================================


def buscar_produtos_por_ncm(ncm: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Busca produtos pelo NCM (Nomenclatura Comum do Mercosul).

    Args:
        ncm: NCM ou início do NCM
        max_results: Limite máximo de resultados

    Returns:
        Lista de produtos encontrados
    """
    from sankhya_sdk.models.dtos import ProdutoListDTO

    client = _create_client()

    response = client.load_records(
        entity="Produto",
        fields=["CODPROD", "DESCRPROD", "REFERENCIA", "NCM", "ATIVO"],
        criteria=f"NCM LIKE '{ncm}%' AND ATIVO = 'S'",
    )

    print(f"🔍 Buscando produtos com NCM iniciando em '{ncm}'...")

    entities = _extract_entities(response)
    produtos = []

    for i, record in enumerate(entities[:max_results], 1):
        try:
            produto = ProdutoListDTO.model_validate(record)
            print(f"  [{produto.codigo}] {produto.descricao} - NCM: {produto.ncm}")
            produtos.append(produto.model_dump())
        except Exception:
            codigo = record.get("CODPROD", "?")
            desc = record.get("DESCRPROD", "?")
            ncm_val = record.get("NCM", "?")
            print(f"  [{codigo}] {desc} - NCM: {ncm_val}")

    print(f"\n📊 Encontrados: {len(produtos)} produtos")
    return produtos


# =============================================================================
# Exemplo 4: Filtrar por Grupo de Produto
# =============================================================================


def filtrar_por_grupo(codigo_grupo: int, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Filtra produtos por código de grupo (CODGRUPOPROD).

    Args:
        codigo_grupo: Código do grupo
        max_results: Limite máximo de resultados

    Returns:
        Lista de produtos do grupo
    """
    from sankhya_sdk.models.dtos import ProdutoListDTO

    client = _create_client()

    response = client.load_records(
        entity="Produto",
        fields=["CODPROD", "DESCRPROD", "REFERENCIA", "CODGRUPOPROD", "ATIVO"],
        criteria=f"CODGRUPOPROD = {codigo_grupo} AND ATIVO = 'S'",
    )

    print(f"📂 Listando produtos do grupo {codigo_grupo}...")

    entities = _extract_entities(response)
    produtos = []

    for i, record in enumerate(entities[:max_results], 1):
        try:
            produto = ProdutoListDTO.model_validate(record)
            status = "✅" if produto.ativo == "S" else "❌"
            print(f"  {status} [{produto.codigo}] {produto.descricao}")
            produtos.append(produto.model_dump())
        except Exception:
            codigo = record.get("CODPROD", "?")
            desc = record.get("DESCRPROD", "?")
            print(f"  ? [{codigo}] {desc}")

    print(f"\n📊 Produtos no grupo: {len(produtos)}")
    return produtos


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Produtos (TGFPRO) - JSON Gateway")
    print("=" * 60)

    print("\n1. Listar Produtos Ativos")
    print("-" * 40)
    listar_produtos_ativos(max_results=10)

    print("\n2. Buscar Produto por Código")
    print("-" * 40)
    buscar_produto_por_codigo(1)

    print("\n3. Buscar por NCM")
    print("-" * 40)
    # buscar_produtos_por_ncm("8471")  # Computadores

    print("\n4. Filtrar por Grupo")
    print("-" * 40)
    # filtrar_por_grupo(1)

    print("\n" + "=" * 60)
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
