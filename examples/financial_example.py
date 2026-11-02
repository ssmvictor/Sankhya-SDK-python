# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Financeiro (JSON Gateway).

Demonstra operações de consulta:
- Listar títulos a receber/pagar
- Filtrar por vencimento
- Consultar títulos em aberto

Tabela Sankhya: TGFFIN
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List

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
    from sankhya_sdk.http import GatewayClient, SankhyaSession

    oauth = OAuthClient(base_url=SANKHYA_AUTH_BASE_URL, token=SANKHYA_X_TOKEN)
    oauth.authenticate(client_id=SANKHYA_CLIENT_ID, client_secret=SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    return GatewayClient(session)


def _extract_entities(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai lista de entidades da resposta do Gateway."""
    from sankhya_sdk.http import GatewayClient

    return GatewayClient.extract_records(response)


# =============================================================================
# Exemplo 1: Listar Títulos Financeiros
# =============================================================================


def listar_titulos_financeiros(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Lista títulos financeiros recentes.

    Args:
        max_results: Limite máximo de resultados

    Returns:
        Lista de títulos financeiros
    """
    client = _create_client()

    response = client.load_records(
        entity="Financeiro",
        fields=[
            "NUFIN",
            "NUNOTA",
            "DTVENC",
            "VLRDESDOB",
            "CODPARC",
            "RECDESP",
            "DHBAIXA",
            "PROVISAO",
        ],
        criteria="DTVENC >= SYSDATE - 90",  # Últimos 90 dias
    )

    print("💰 Listando títulos financeiros...")

    entities = _extract_entities(response)
    titulos = []

    for i, record in enumerate(entities[:max_results], 1):
        nufin = record.get("NUFIN", "-")
        valor = float(record.get("VLRDESDOB", 0) or 0)
        tipo = "📈 Receita" if record.get("RECDESP") == "R" else "📉 Despesa"

        print(f"  {i}. NUFIN:{nufin} | {tipo} | R$ {valor:.2f}")
        titulos.append(record)

    print(f"\n✅ Total: {len(titulos)} títulos")
    return titulos


# =============================================================================
# Exemplo 2: Títulos a Receber em Aberto
# =============================================================================


def listar_a_receber_em_aberto(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Lista títulos a RECEBER que estão em aberto (sem baixa).

    Filtra:
    - RECDESP = 'R' (Receita)
    - DHBAIXA IS NULL (Sem data de baixa = em aberto)
    - PROVISAO != 'S' (Não é provisão)
    """
    client = _create_client()

    response = client.load_records(
        entity="Financeiro",
        fields=["NUFIN", "NUNOTA", "DTVENC", "VLRDESDOB", "CODPARC", "RECDESP"],
        criteria="RECDESP = 'R' AND DHBAIXA IS NULL AND (PROVISAO IS NULL OR PROVISAO != 'S')",
    )

    print("📈 Títulos a RECEBER em aberto...")

    entities = _extract_entities(response)
    titulos = []
    total_valor = 0.0

    for record in entities[:max_results]:
        nufin = record.get("NUFIN", "-")
        venc = record.get("DTVENC", "-")
        valor = float(record.get("VLRDESDOB", 0) or 0)
        total_valor += valor

        print(f"  NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f}")
        titulos.append(record)

    print(f"\n📊 Total a receber: {len(titulos)} títulos = R$ {total_valor:.2f}")
    return titulos


# =============================================================================
# Exemplo 3: Títulos a Pagar em Aberto
# =============================================================================


def listar_a_pagar_em_aberto(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Lista títulos a PAGAR que estão em aberto (sem baixa).

    Filtra:
    - RECDESP = 'D' (Despesa)
    - DHBAIXA IS NULL (Sem data de baixa = em aberto)
    """
    client = _create_client()

    response = client.load_records(
        entity="Financeiro",
        fields=["NUFIN", "NUNOTA", "DTVENC", "VLRDESDOB", "CODPARC", "RECDESP"],
        criteria="RECDESP = 'D' AND DHBAIXA IS NULL",
    )

    print("📉 Títulos a PAGAR em aberto...")

    entities = _extract_entities(response)
    titulos = []
    total_valor = 0.0

    for record in entities[:max_results]:
        nufin = record.get("NUFIN", "-")
        venc = record.get("DTVENC", "-")
        valor = float(record.get("VLRDESDOB", 0) or 0)
        total_valor += valor

        print(f"  NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f}")
        titulos.append(record)

    print(f"\n📊 Total a pagar: {len(titulos)} títulos = R$ {total_valor:.2f}")
    return titulos


# =============================================================================
# Exemplo 4: Títulos Vencidos
# =============================================================================


def listar_titulos_vencidos(max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Lista títulos vencidos e não baixados.

    Filtra:
    - DTVENC < data atual
    - DHBAIXA IS NULL (em aberto)
    """
    client = _create_client()

    # Data atual formatada para SQL Oracle
    hoje = datetime.now().strftime("%d/%m/%Y")

    response = client.load_records(
        entity="Financeiro",
        fields=["NUFIN", "NUNOTA", "DTVENC", "VLRDESDOB", "CODPARC", "RECDESP"],
        criteria=f"DTVENC < TO_DATE('{hoje}', 'DD/MM/YYYY') AND DHBAIXA IS NULL",
    )

    print(f"⚠️ Títulos VENCIDOS (antes de {hoje})...")

    entities = _extract_entities(response)
    titulos = []
    total_receber = 0.0
    total_pagar = 0.0

    for record in entities[:max_results]:
        nufin = record.get("NUFIN", "-")
        venc = record.get("DTVENC", "-")
        valor = float(record.get("VLRDESDOB", 0) or 0)
        tipo = record.get("RECDESP", "-")

        if tipo == "R":
            total_receber += valor
            emoji = "📈"
        else:
            total_pagar += valor
            emoji = "📉"

        print(f"  {emoji} NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f}")
        titulos.append(record)

    print("\n📊 Vencidos:")
    print(f"   A Receber: R$ {total_receber:.2f}")
    print(f"   A Pagar:   R$ {total_pagar:.2f}")
    print(f"   Total:     {len(titulos)} títulos")
    return titulos


# =============================================================================
# Exemplo 5: Títulos por Parceiro
# =============================================================================


def listar_titulos_por_parceiro(
    codigo_parceiro: int, max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Lista todos os títulos financeiros de um parceiro específico.

    Útil para verificar posição financeira de um cliente/fornecedor.

    Args:
        codigo_parceiro: Código do parceiro
        max_results: Limite máximo de resultados

    Returns:
        Lista de títulos do parceiro
    """
    client = _create_client()

    response = client.load_records(
        entity="Financeiro",
        fields=[
            "NUFIN",
            "NUMNOTA",
            "DTNEG",
            "DTVENC",
            "CODPARC",
            "VLRDESDOB",
            "VLRBAIXA",
            "RECDESP",
            "DHBAIXA",
        ],
        criteria=f"CODPARC = {codigo_parceiro}",
    )

    print(f"💼 Títulos do parceiro {codigo_parceiro}...")

    entities = _extract_entities(response)
    titulos = []

    for record in entities[:max_results]:
        nufin = record.get("NUFIN", "-")
        venc = record.get("DTVENC", "-")
        valor = float(record.get("VLRDESDOB", 0) or 0)
        tipo = "📈" if record.get("RECDESP") == "R" else "📉"
        status = "✅ Baixado" if record.get("DHBAIXA") else "⏳ Aberto"

        print(f"  {tipo} NUFIN:{nufin} | Venc:{venc} | R$ {valor:.2f} | {status}")
        titulos.append(record)

    print(f"\n📊 Total de títulos: {len(titulos)}")
    return titulos


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Financeiro (TGFFIN) - JSON Gateway")
    print("=" * 60)

    print("\n1. Listar Títulos Financeiros")
    print("-" * 40)
    listar_titulos_financeiros(max_results=10)

    print("\n2. Títulos a Receber em Aberto")
    print("-" * 40)
    # listar_a_receber_em_aberto(max_results=10)

    print("\n3. Títulos a Pagar em Aberto")
    print("-" * 40)
    # listar_a_pagar_em_aberto(max_results=10)

    print("\n4. Títulos Vencidos")
    print("-" * 40)
    # listar_titulos_vencidos(max_results=10)

    print("\n5. Títulos por Parceiro")
    print("-" * 40)
    # listar_titulos_por_parceiro(1)

    print("\n" + "=" * 60)
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
