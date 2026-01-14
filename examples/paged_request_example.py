# -*- coding: utf-8 -*-
"""
Exemplos de uso do GatewayClient com paginação.

Este arquivo demonstra diferentes cenários de consultas paginadas
usando o GatewayClient com autenticação OAuth2.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Callable, Optional

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
# Exemplo 1: Uso Básico - Carregar Todos os Parceiros
# =============================================================================


def exemplo_basico():
    """
    Exemplo básico de carregamento de dados.

    Carrega parceiros e imprime seus nomes.
    """
    client = _create_client()

    print("📋 Carregando parceiros...")

    response = client.load_records(
        entity="Parceiro", fields=["CODPARC", "NOMEPARC", "ATIVO"], criteria="ATIVO = 'S'"
    )

    entities = _extract_entities(response)

    count = 0
    for record in entities[:100]:  # Limita a 100
        count += 1
        codigo = record.get("CODPARC", "-")
        nome = record.get("NOMEPARC", "-")
        print(f"  {count}. [{codigo}] {nome}")

    print(f"\n✅ Total carregado: {count} parceiros")


# =============================================================================
# Exemplo 2: Carregamento com Processamento em Lote
# =============================================================================


def exemplo_processamento_lote():
    """
    Exemplo de processamento de dados em lotes.

    Carrega produtos e processa em lotes de 50.
    """
    client = _create_client()

    print("📦 Carregando produtos em lotes...")

    response = client.load_records(
        entity="Produto",
        fields=["CODPROD", "DESCRPROD", "REFERENCIA", "ATIVO"],
        criteria="ATIVO = 'S'",
    )

    entities = _extract_entities(response)

    # Processa em lotes de 50
    batch_size = 50
    total_processado = 0

    for i in range(0, len(entities), batch_size):
        batch = entities[i : i + batch_size]

        print(f"\n🔄 Processando lote {i // batch_size + 1} ({len(batch)} itens)...")

        for record in batch:
            # Simula processamento
            total_processado += 1

        print(f"✅ Lote processado! Total: {total_processado}")

        if total_processado >= 200:  # Limita para exemplo
            break

    print(f"\n📊 Total processado: {total_processado} produtos")


# =============================================================================
# Exemplo 3: Carregamento com Callback de Progresso
# =============================================================================


def exemplo_com_callback():
    """
    Exemplo com callback para monitorar progresso.

    Demonstra como usar callbacks para acompanhar o carregamento.
    """

    def on_progress(current: int, total: int, item: Dict[str, Any]):
        """Callback de progresso."""
        progress = (current / total * 100) if total > 0 else 0
        nome = item.get("NOMEPARC", "-")[:30]
        print(f"  [{progress:5.1f}%] {current}/{total} - {nome}")

    client = _create_client()

    print("📋 Carregando com monitoramento de progresso...")

    response = client.load_records(
        entity="Parceiro",
        fields=["CODPARC", "NOMEPARC", "CGC_CPF", "ATIVO"],
        criteria="ATIVO = 'S'",
    )

    entities = _extract_entities(response)
    total = min(len(entities), 50)  # Limita a 50 para exemplo

    for i, record in enumerate(entities[:total], 1):
        on_progress(i, total, record)

    print(f"\n✅ Carregamento concluído: {total} itens")


# =============================================================================
# Exemplo 4: Múltiplas Consultas Paralelas
# =============================================================================


def exemplo_multiplas_consultas():
    """
    Exemplo de múltiplas consultas em sequência.

    Demonstra como fazer várias consultas usando o mesmo cliente.
    """
    client = _create_client()

    print("🔄 Executando múltiplas consultas...")

    # Consulta 1: Parceiros
    print("\n📋 Consulta 1: Parceiros ativos")
    response = client.load_records(
        entity="Parceiro", fields=["CODPARC", "NOMEPARC"], criteria="ATIVO = 'S' AND CLIENTE = 'S'"
    )
    parceiros = _extract_entities(response)
    print(f"   Encontrados: {len(parceiros)} parceiros")

    # Consulta 2: Produtos
    print("\n📦 Consulta 2: Produtos ativos")
    response = client.load_records(
        entity="Produto", fields=["CODPROD", "DESCRPROD"], criteria="ATIVO = 'S'"
    )
    produtos = _extract_entities(response)
    print(f"   Encontrados: {len(produtos)} produtos")

    # Consulta 3: Notas recentes
    print("\n📄 Consulta 3: Notas dos últimos 30 dias")
    response = client.load_records(
        entity="CabecalhoNota",
        fields=["NUNOTA", "NUMNOTA", "VLRNOTA"],
        criteria="DTNEG >= SYSDATE - 30",
    )
    notas = _extract_entities(response)
    print(f"   Encontradas: {len(notas)} notas")

    print("\n📊 Resumo:")
    print(f"   Parceiros: {len(parceiros)}")
    print(f"   Produtos:  {len(produtos)}")
    print(f"   Notas:     {len(notas)}")


# =============================================================================
# Exemplo 5: Filtros Avançados
# =============================================================================


def exemplo_filtros_avancados():
    """
    Exemplo com filtros SQL avançados.

    Demonstra uso de LIKE, IN, BETWEEN e funções SQL.
    """
    client = _create_client()

    print("🔍 Exemplos de filtros avançados...")

    # Filtro LIKE
    print("\n1. Filtro LIKE (nome contém 'EMPRESA'):")
    response = client.load_records(
        entity="Parceiro",
        fields=["CODPARC", "NOMEPARC"],
        criteria="UPPER(NOMEPARC) LIKE '%EMPRESA%'",
    )
    entities = _extract_entities(response)
    for r in entities[:5]:
        print(f"   [{r.get('CODPARC')}] {r.get('NOMEPARC')}")

    # Filtro IN
    print("\n2. Filtro IN (tipos específicos):")
    response = client.load_records(
        entity="Parceiro",
        fields=["CODPARC", "NOMEPARC", "TIPPESSOA"],
        criteria="TIPPESSOA IN ('J', 'F') AND ATIVO = 'S'",
    )
    entities = _extract_entities(response)
    for r in entities[:5]:
        tipo = "Jurídica" if r.get("TIPPESSOA") == "J" else "Física"
        print(f"   [{r.get('CODPARC')}] {r.get('NOMEPARC')} ({tipo})")

    # Filtro com função de data
    print("\n3. Filtro com data (últimos 7 dias):")
    response = client.load_records(
        entity="CabecalhoNota",
        fields=["NUNOTA", "NUMNOTA", "DTNEG", "VLRNOTA"],
        criteria="DTNEG >= SYSDATE - 7",
    )
    entities = _extract_entities(response)
    for r in entities[:5]:
        valor = float(r.get("VLRNOTA", 0) or 0)
        print(f"   NUNOTA:{r.get('NUNOTA')} | {r.get('DTNEG')} | R$ {valor:.2f}")

    print("\n✅ Exemplos concluídos!")


# =============================================================================
# Exemplo 6: Tratamento de Erros
# =============================================================================


def exemplo_tratamento_erros():
    """
    Exemplo de tratamento robusto de erros.

    Demonstra como tratar erros de forma adequada.
    """
    from sankhya_sdk.exceptions import (
        SankhyaHttpError,
        SankhyaAuthError,
        SankhyaNotFoundError,
    )
    from sankhya_sdk.auth import AuthError, AuthNetworkError

    print("🔧 Exemplo de tratamento de erros...")

    try:
        client = _create_client()

        # Tenta carregar uma entidade
        response = client.load_records(
            entity="Parceiro", fields=["CODPARC", "NOMEPARC"], criteria="ATIVO = 'S'"
        )

        entities = _extract_entities(response)
        print(f"✅ Carregados: {len(entities)} registros")

    except AuthError as e:
        print(f"❌ Erro de autenticação: {e.message}")
        print("   Verifique CLIENT_ID, CLIENT_SECRET e X-TOKEN")

    except AuthNetworkError as e:
        print(f"❌ Erro de rede na autenticação: {e.message}")
        print("   Verifique sua conexão com a internet")

    except SankhyaAuthError:
        print("❌ Token expirado ou inválido")
        print("   O SDK deveria renovar automaticamente...")

    except SankhyaNotFoundError:
        print("❌ Entidade não encontrada")
        print("   Verifique o nome da entidade")

    except SankhyaHttpError as e:
        print(f"❌ Erro HTTP {e.status_code}: {e.message}")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    print("\n✅ Tratamento de erros demonstrado!")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Consultas Paginadas - JSON Gateway")
    print("=" * 60)

    print("\n1. Exemplo Básico")
    print("-" * 40)
    exemplo_basico()

    print("\n2. Processamento em Lote")
    print("-" * 40)
    # exemplo_processamento_lote()

    print("\n3. Com Callback de Progresso")
    print("-" * 40)
    # exemplo_com_callback()

    print("\n4. Múltiplas Consultas")
    print("-" * 40)
    # exemplo_multiplas_consultas()

    print("\n5. Filtros Avançados")
    print("-" * 40)
    # exemplo_filtros_avancados()

    print("\n6. Tratamento de Erros")
    print("-" * 40)
    # exemplo_tratamento_erros()

    print("\n" + "=" * 60)
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
