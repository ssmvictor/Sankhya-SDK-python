# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Nota Fiscal (JSON Gateway).

Demonstra operações de consulta:
- Listar notas fiscais
- Buscar nota por número único (NUNOTA)
- Verificar status de NF-e

Tabelas Sankhya:
- TGFCAB (Cabeçalho da Nota)
- TGFITE (Itens da Nota)
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

# =============================================================================
# Configuração OAuth2
# =============================================================================

load_dotenv()

SANKHYA_CLIENT_ID = os.getenv("SANKHYA_CLIENT_ID")
SANKHYA_CLIENT_SECRET = os.getenv("SANKHYA_CLIENT_SECRET")
SANKHYA_AUTH_BASE_URL = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")
SANKHYA_X_TOKEN = os.getenv("SANKHYA_TOKEN")


def _create_client():
    """Cria e retorna um GatewayClient autenticado via OAuth2."""
    from sankhya_sdk.auth.oauth_client import OAuthClient
    from sankhya_sdk.http import SankhyaSession, GatewayClient

    oauth = OAuthClient(base_url=SANKHYA_AUTH_BASE_URL, token=SANKHYA_X_TOKEN)
    oauth.authenticate(client_id=SANKHYA_CLIENT_ID, client_secret=SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    return GatewayClient(session)


def _extract_entities(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai lista de entidades da resposta do Gateway."""
    from sankhya_sdk.http import GatewayClient

    return GatewayClient.extract_records(response)


# =============================================================================
# Exemplo 1: Listar Notas Fiscais
# =============================================================================


def listar_notas_fiscais(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Lista notas fiscais recentes.

    Args:
        max_results: Limite máximo de resultados

    Returns:
        Lista de notas fiscais
    """
    client = _create_client()

    response = client.load_records(
        entity="CabecalhoNota",
        fields=["NUNOTA", "NUMNOTA", "DTNEG", "CODPARC", "VLRNOTA", "STATUSNFE", "TIPMOV"],
        criteria="DTNEG >= SYSDATE - 30",  # Últimos 30 dias
    )

    print("📋 Listando notas fiscais...")

    entities = _extract_entities(response)
    notas = []

    for i, record in enumerate(entities[:max_results], 1):
        nunota = record.get("NUNOTA", "-")
        numnota = record.get("NUMNOTA", "-")
        valor = float(record.get("VLRNOTA", 0) or 0)
        
        # Garantir que status é string, não dict
        status_raw = record.get("STATUSNFE", "-")
        status = status_raw if isinstance(status_raw, str) else str(status_raw.get("$", "-") if isinstance(status_raw, dict) else "-")

        status_emoji = {
            "A": "✅",  # Aprovada
            "D": "❌",  # Denegada
            "R": "❌",  # Rejeitada
            "C": "⛔",  # Cancelada
            "E": "⏳",  # Em processamento
        }.get(status, "❓")

        print(
            f"  {i}. NUNOTA:{nunota} | Nº:{numnota} | R$ {valor:.2f} | NFe:{status_emoji} {status}"
        )
        notas.append(record)

    print(f"\n✅ Total: {len(notas)} notas")
    return notas


# =============================================================================
# Exemplo 2: Buscar Nota por NUNOTA
# =============================================================================


def buscar_nota_por_nunota(nunota: int) -> Optional[Dict[str, Any]]:
    """
    Busca uma nota fiscal específica pelo número único (NUNOTA).

    Args:
        nunota: Número único da nota

    Returns:
        Dados da nota ou None se não encontrada
    """
    client = _create_client()

    response = client.load_records(
        entity="CabecalhoNota",
        fields=[
            "NUNOTA",
            "NUMNOTA",
            "DTNEG",
            "CODPARC",
            "VLRNOTA",
            "STATUSNFE",
            "TIPMOV",
            "CODTIPOPER",
            "CODTIPVENDA",
            "OBSERVACAO",
            "CODEMP",
        ],
        criteria=f"NUNOTA = {nunota}",
    )

    print(f"🔍 Buscando nota NUNOTA {nunota}...")

    entities = _extract_entities(response)

    if entities:
        nota = entities[0]
        print(f"✅ Encontrada:")
        print(f"   NUNOTA: {nota.get('NUNOTA')}")
        print(f"   Número: {nota.get('NUMNOTA')}")
        print(f"   Valor: R$ {float(nota.get('VLRNOTA', 0) or 0):.2f}")
        print(f"   Status NFe: {nota.get('STATUSNFE', '-')}")
        print(f"   Data: {nota.get('DTNEG', '-')}")
        return nota
    else:
        print(f"❌ Nota {nunota} não encontrada")
        return None


# =============================================================================
# Exemplo 3: Filtrar Notas Aprovadas (STATUSNFE = 'A')
# =============================================================================


def listar_notas_aprovadas(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Lista notas fiscais com NF-e aprovada.

    STATUSNFE = 'A' significa nota aprovada na SEFAZ.

    Valores possíveis de STATUSNFE:
    - 'A' = Aprovada
    - 'D' = Denegada
    - 'R' = Rejeitada
    - 'C' = Cancelada
    - 'E' = Em processamento
    """
    client = _create_client()

    response = client.load_records(
        entity="CabecalhoNota",
        fields=["NUNOTA", "NUMNOTA", "DTNEG", "CODPARC", "VLRNOTA", "STATUSNFE"],
        criteria="STATUSNFE = 'A'",
    )

    print("✅ Listando notas com NF-e APROVADA (STATUSNFE = 'A')...")

    entities = _extract_entities(response)
    notas = []

    for i, record in enumerate(entities[:max_results], 1):
        nunota = record.get("NUNOTA", "-")
        numnota = record.get("NUMNOTA", "-")
        valor = float(record.get("VLRNOTA", 0) or 0)

        print(f"  ✅ NUNOTA:{nunota} | Nº:{numnota} | R$ {valor:.2f}")
        notas.append(record)

    print(f"\n📊 Notas aprovadas: {len(notas)}")
    return notas


# =============================================================================
# Exemplo 4: Listar Itens de uma Nota
# =============================================================================


def listar_itens_nota(nunota: int) -> List[Dict[str, Any]]:
    """
    Lista os itens de uma nota fiscal específica.

    Args:
        nunota: Número único da nota

    Returns:
        Lista de itens da nota
    """
    client = _create_client()

    response = client.load_records(
        entity="ItemNota",
        fields=["NUNOTA", "SEQUENCIA", "CODPROD", "QTDNEG", "VLRUNIT", "VLRTOT"],
        criteria=f"NUNOTA = {nunota}",
    )

    print(f"📦 Listando itens da nota NUNOTA {nunota}...")

    entities = _extract_entities(response)

    total_valor = 0.0
    total_qtd = 0.0

    for i, item in enumerate(entities, 1):
        seq = item.get("SEQUENCIA", "-")
        cod = item.get("CODPROD", "-")
        qtd = float(item.get("QTDNEG", 0) or 0)
        vlr_unit = float(item.get("VLRUNIT", 0) or 0)
        vlr_tot = float(item.get("VLRTOT", 0) or 0)

        total_qtd += qtd
        total_valor += vlr_tot

        print(
            f"  {seq}. Produto:{cod} | Qtd:{qtd:.2f} | Unit:R$ {vlr_unit:.2f} | Total:R$ {vlr_tot:.2f}"
        )

    print(f"\n📊 Resumo:")
    print(f"   Total de itens: {len(entities)}")
    print(f"   Quantidade total: {total_qtd:.2f}")
    print(f"   Valor total: R$ {total_valor:.2f}")

    return entities


# =============================================================================
# Exemplo 5: Filtrar Notas por Parceiro
# =============================================================================


def filtrar_notas_por_parceiro(codigo_parceiro: int, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Filtra notas fiscais de um parceiro específico.

    Útil para verificar histórico de compras/vendas de um cliente.

    Args:
        codigo_parceiro: Código do parceiro
        max_results: Limite máximo de resultados

    Returns:
        Lista de notas do parceiro
    """
    client = _create_client()

    response = client.load_records(
        entity="CabecalhoNota",
        fields=["NUNOTA", "NUMNOTA", "DTNEG", "CODPARC", "VLRNOTA", "STATUSNFE", "TIPMOV"],
        criteria=f"CODPARC = {codigo_parceiro}",
    )

    print(f"📋 Notas do parceiro {codigo_parceiro}...")

    entities = _extract_entities(response)
    notas = []

    for i, record in enumerate(entities[:max_results], 1):
        nunota = record.get("NUNOTA", "-")
        data = record.get("DTNEG", "-")
        valor = float(record.get("VLRNOTA", 0) or 0)
        status = record.get("STATUSNFE", "-")

        print(f"  NUNOTA:{nunota} | {data} | R$ {valor:.2f} | NFe:{status}")
        notas.append(record)

    print(f"\n📊 Notas do parceiro: {len(notas)}")
    return notas


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Notas Fiscais (TGFCAB + TGFITE) - JSON Gateway")
    print("=" * 60)

    print("\n1. Listar Notas Fiscais")
    print("-" * 40)
    listar_notas_fiscais(max_results=10)

    print("\n2. Buscar Nota por NUNOTA")
    print("-" * 40)
    # buscar_nota_por_nunota(12345)

    print("\n3. Listar Notas Aprovadas (STATUSNFE = 'A')")
    print("-" * 40)
    # listar_notas_aprovadas(max_results=10)

    print("\n4. Listar Itens de uma Nota")
    print("-" * 40)
    # listar_itens_nota(12345)

    print("\n5. Filtrar por Parceiro")
    print("-" * 40)
    # filtrar_notas_por_parceiro(1)

    print("\n" + "=" * 60)
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
