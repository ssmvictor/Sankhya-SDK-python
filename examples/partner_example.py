# -*- coding: utf-8 -*-
"""
Exemplo de uso do SDK Sankhya para a entidade Parceiro (JSON Gateway).

Demonstra operações CRUD usando o GatewayClient:
- Listar parceiros
- Buscar parceiro por código
- Criar/Atualizar parceiro

Tabela Sankhya: TGFPAR
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

# =============================================================================
# Configuração
# =============================================================================

load_dotenv()

SANKHYA_CLIENT_ID = os.getenv("SANKHYA_CLIENT_ID")
SANKHYA_CLIENT_SECRET = os.getenv("SANKHYA_CLIENT_SECRET")
SANKHYA_AUTH_BASE_URL = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")
# X-Token: Token de Integração (obtido em Configurações Gateway > Chave do cliente)
SANKHYA_X_TOKEN = os.getenv("SANKHYA_TOKEN")  # Token de Integração obrigatório


def _create_client():
    """Cria e retorna um GatewayClient autenticado."""
    from sankhya_sdk.auth.oauth_client import OAuthClient
    from sankhya_sdk.http import SankhyaSession, GatewayClient

    oauth = OAuthClient(
        base_url=SANKHYA_AUTH_BASE_URL,
        token=SANKHYA_X_TOKEN,  # None se não configurado
    )
    oauth.authenticate(client_id=SANKHYA_CLIENT_ID, client_secret=SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    return GatewayClient(session)


# =============================================================================
# Exemplo 1: Listar Parceiros
# =============================================================================


def listar_parceiros(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Lista parceiros ativos.

    Usa GatewayClient.load_records para buscar dados via JSON API.

    Args:
        max_results: Limite máximo de resultados

    Returns:
        Lista de dicionários com dados dos parceiros
    """
    from sankhya_sdk.models.dtos import ParceiroListDTO

    client = _create_client()

    # Consulta via JSON Gateway
    response = client.load_records(
        entity="Parceiro",
        fields=["CODPARC", "NOMEPARC", "CGC_CPF", "TIPPESSOA", "ATIVO"],
        criteria="ATIVO = 'S'",
    )

    print("📋 Listando parceiros...")

    # Extrai entidades da resposta
    entities = _extract_entities(response)
    parceiros = []

    for i, record in enumerate(entities[:max_results], 1):
        try:
            parceiro = ParceiroListDTO.model_validate(record)
            parceiros.append(parceiro.model_dump())
            print(f"  {i}. [{parceiro.codigo}] {parceiro.nome}")
        except Exception as e:
            # Fallback para dados brutos se validação falhar
            codigo = record.get("CODPARC", "?")
            nome = record.get("NOMEPARC", "?")
            print(f"  {i}. [{codigo}] {nome}")

    print(f"\n✅ Total: {len(parceiros)} parceiros carregados")
    return parceiros


# =============================================================================
# Exemplo 2: Buscar Parceiro por Código
# =============================================================================


def buscar_parceiro_por_codigo(codigo: int) -> Optional[Dict[str, Any]]:
    """
    Busca um parceiro específico pelo código (CODPARC).

    Args:
        codigo: Código do parceiro

    Returns:
        Dicionário com dados do parceiro ou None se não encontrado
    """
    from sankhya_sdk.models.dtos import ParceiroDTO

    client = _create_client()

    response = client.load_records(
        entity="Parceiro",
        fields=[
            "CODPARC",
            "NOMEPARC",
            "CGC_CPF",
            "TIPPESSOA",
            "EMAIL",
            "TELEFONE",
            "CODCID",
            "NOMEEND",
            "NUMEND",
            "CEP",
            "ATIVO",
            "CLIENTE",
            "FORNECEDOR",
        ],
        criteria=f"CODPARC = {codigo}",
    )

    print(f"🔍 Buscando parceiro código {codigo}...")

    entities = _extract_entities(response)

    if entities:
        record = entities[0]
        try:
            parceiro = ParceiroDTO.model_validate(record)
            print(f"✅ Encontrado: [{parceiro.codigo}] {parceiro.nome}")
            print(f"   CPF/CNPJ: {parceiro.cnpj_cpf or 'N/A'}")
            print(f"   Email: {parceiro.email or 'N/A'}")
            print(f"   Telefone: {parceiro.telefone or 'N/A'}")
            return parceiro.model_dump()
        except Exception:
            print(f"✅ Encontrado: {record}")
            return record
    else:
        print(f"❌ Parceiro {codigo} não encontrado")
        return None


# =============================================================================
# Exemplo 3: Filtrar Parceiros por Nome
# =============================================================================


def filtrar_parceiros_por_nome(nome_parcial: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Filtra parceiros cujo nome contém o texto informado.

    Args:
        nome_parcial: Texto parcial para busca
        max_results: Limite máximo de resultados

    Returns:
        Lista de parceiros encontrados
    """
    from sankhya_sdk.models.dtos import ParceiroListDTO

    client = _create_client()

    response = client.load_records(
        entity="Parceiro",
        fields=["CODPARC", "NOMEPARC", "CGC_CPF", "TIPPESSOA", "ATIVO"],
        criteria=f"UPPER(NOMEPARC) LIKE '%{nome_parcial.upper()}%'",
    )

    print(f"🔍 Buscando parceiros com nome contendo '{nome_parcial}'...")

    entities = _extract_entities(response)
    parceiros = []

    for i, record in enumerate(entities[:max_results], 1):
        try:
            parceiro = ParceiroListDTO.model_validate(record)
            status = "✅" if parceiro.ativo == "S" else "❌"
            print(f"  {status} [{parceiro.codigo}] {parceiro.nome}")
            parceiros.append(parceiro.model_dump())
        except Exception:
            codigo = record.get("CODPARC", "?")
            nome = record.get("NOMEPARC", "?")
            print(f"  ? [{codigo}] {nome}")

    print(f"\n📊 Encontrados: {len(parceiros)} parceiros")
    return parceiros


# =============================================================================
# Exemplo 4: Criar/Atualizar Parceiro
# =============================================================================


def criar_ou_atualizar_parceiro(
    codigo: Optional[int],
    nome: str,
    cgc_cpf: Optional[str] = None,
    email: Optional[str] = None,
    codigo_cidade: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Cria um novo parceiro ou atualiza um existente.

    Args:
        codigo: Código do parceiro (None para criar novo)
        nome: Nome do parceiro
        cgc_cpf: CPF ou CNPJ
        email: E-mail
        codigo_cidade: Código da cidade

    Returns:
        Dados do parceiro salvo ou None em caso de erro
    """
    from sankhya_sdk.models.dtos import ParceiroCreateDTO

    client = _create_client()

    # Monta campos
    fields = {
        "NOMEPARC": nome,
        "CODCID": codigo_cidade,
        "ATIVO": "S",
        "CLIENTE": "S",
        "TIPPESSOA": "J",
    }

    if codigo:
        fields["CODPARC"] = codigo
    if cgc_cpf:
        fields["CGC_CPF"] = cgc_cpf
    if email:
        fields["EMAIL"] = email

    action = "Atualizando" if codigo else "Criando"
    print(f"💾 {action} parceiro '{nome}'...")

    try:
        response = client.save_record(entity="Parceiro", fields=fields)

        # Verifica sucesso
        status = response.get("status", response.get("responseBody", {}).get("status"))
        if status == "1" or status == 1:
            print(f"✅ Parceiro salvo com sucesso!")
            return response
        else:
            error_msg = response.get("statusMessage", "Erro desconhecido")
            print(f"❌ Erro ao salvar: {error_msg}")
            return None

    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return None


# =============================================================================
# Helpers
# =============================================================================


def _extract_entities(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrai lista de entidades da resposta do Gateway.

    Usa GatewayClient.extract_records() para normalizar campos indexados
    (f0, f1, ...) para nomes reais (CODPARC, NOMEPARC, ...).
    """
    from sankhya_sdk.http import GatewayClient

    return GatewayClient.extract_records(response)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de Parceiros (TGFPAR) - JSON Gateway")
    print("=" * 60)

    print("\n1. Listar Parceiros")
    print("-" * 40)
    listar_parceiros(max_results=10)

    print("\n2. Buscar Parceiro por Código")
    print("-" * 40)
    buscar_parceiro_por_codigo(1)

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
    print("Configure as variáveis de ambiente SANKHYA_*")
    print("=" * 60)
