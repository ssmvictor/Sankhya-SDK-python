#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemplo de execução de SQL via DbExplorerSP.executeQuery com OAuth2

Migrado de: Exemplo_dbexplorer.py (autenticação legada)
Para: OAuth2 authentication

Este exemplo demonstra como executar SQL nativo no Sankhya via API Gateway.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from sankhya_sdk.auth.oauth_client import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient

# Carregar variáveis de ambiente
load_dotenv()

# Credenciais OAuth2
SANKHYA_CLIENT_ID = os.getenv("SANKHYA_CLIENT_ID")
SANKHYA_CLIENT_SECRET = os.getenv("SANKHYA_CLIENT_SECRET")
SANKHYA_AUTH_BASE_URL = os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br")
SANKHYA_X_TOKEN = os.getenv("SANKHYA_TOKEN")


def execute_sql(client: GatewayClient, sql: str) -> Dict[str, Any]:
    """
    Executa SQL nativo via DbExplorerSP.executeQuery.

    Args:
        client: Cliente Gateway autenticado
        sql: Query SQL para executar

    Returns:
        Dict com resultado da query:
        {
            "fieldsMetadata": [...],
            "rows": [...]
        }
    """
    response = client.execute_service(
        service_name="DbExplorerSP.executeQuery", request_body={"sql": sql}
    )

    if not GatewayClient.is_success(response):
        error_msg = GatewayClient.get_error_message(response)
        raise Exception(f"Erro ao executar SQL: {error_msg}")

    return response.get("responseBody", {})


def extract_rows(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrai linhas do resultado e converte para lista de dicionários.

    Args:
        response: Resposta do executeQuery

    Returns:
        Lista de dicionários com os dados
    """
    fields_metadata = response.get("fieldsMetadata", [])
    rows = response.get("rows", [])

    # Extrair nomes das colunas
    column_names = [field["name"] for field in fields_metadata]

    # Converter rows (arrays) para dicionários
    result = []
    for row in rows:
        record = dict(zip(column_names, row))
        result.append(record)

    return result


# =============================================================================
# Exemplo 1: Query simples
# =============================================================================


def exemplo_query_simples():
    """Exemplo de query SQL simples"""
    print("=" * 60)
    print("EXEMPLO 1: Query Simples")
    print("=" * 60)

    # Autenticar
    oauth = OAuthClient(base_url=SANKHYA_AUTH_BASE_URL, token=SANKHYA_X_TOKEN)
    if not SANKHYA_CLIENT_ID or not SANKHYA_CLIENT_SECRET:
        raise RuntimeError(
            "SANKHYA_CLIENT_ID e SANKHYA_CLIENT_SECRET devem estar definidos no ambiente"
        )
    oauth.authenticate(SANKHYA_CLIENT_ID, SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    client = GatewayClient(session)

    # Executar SQL
    # Nota: DbExplorerSP.executeQuery usa SQL nativo, então precisa do nome
    # da tabela física (TGFFIN). A entidade lógica "Financeiro" só funciona
    # com client.save_record() - veja atualiza_parceiro.py para exemplo.
    sql = """
        SELECT
            TO_CHAR(FIN.DHBAIXA, 'DD/MM/YYYY HH24:MI:SS') AS DHBAIXA,
            TO_CHAR(FIN.TIMDHBAIXA, 'DD/MM/YYYY HH24:MI:SS') AS TIMDHBAIXA
        FROM TGFFIN FIN
        WHERE FIN.NUFIN = 550273
    """

    print(f"\nExecutando SQL:\n{sql}\n")

    response = execute_sql(client, sql)
    rows = extract_rows(response)

    print(f"Resultado: {len(rows)} registros encontrados\n")

    for i, record in enumerate(rows, 1):
        # Nota: API retorna alias em uppercase
        ad_dt = record.get("AD_DTPAGO")
        tim_dt = record.get("TIMDHBAIXA")
        print(f"{i}. AD_DTPAGO=[{ad_dt}] | TIMDHBAIXA=[{tim_dt}]")


# =============================================================================
# Exemplo 2: Query com JOIN
# =============================================================================


def exemplo_query_join():
    """Exemplo de query SQL com JOIN"""
    print("\n" + "=" * 60)
    print("EXEMPLO 2: Query com JOIN")
    print("=" * 60)

    # Autenticar
    oauth = OAuthClient(base_url=SANKHYA_AUTH_BASE_URL, token=SANKHYA_X_TOKEN)
    if not SANKHYA_CLIENT_ID or not SANKHYA_CLIENT_SECRET:
        raise RuntimeError(
            "SANKHYA_CLIENT_ID e SANKHYA_CLIENT_SECRET devem estar definidos no ambiente"
        )
    oauth.authenticate(SANKHYA_CLIENT_ID, SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    client = GatewayClient(session)

    # Query com JOIN para buscar viagens
    sql = """
        SELECT 
            VIAG.NUVIAG,
            MME.CODPARC,
            PAR.NOMEPARC,
            MDF.DHEMISS
        FROM TGFVIAG VIAG
        JOIN TGFMDFE MDF ON MDF.NUVIAG = VIAG.NUVIAG
        JOIN TGFMME MME ON MME.NUVIAG = VIAG.NUVIAG
        JOIN TGFPAR PAR ON PAR.CODPARC = MME.CODPARC
        WHERE ROWNUM <= 5
        ORDER BY MDF.DHEMISS DESC
    """

    print(f"\nExecutando SQL:\n{sql}\n")

    response = execute_sql(client, sql)
    rows = extract_rows(response)

    print(f"Resultado: {len(rows)} viagens encontradas\n")

    for i, record in enumerate(rows, 1):
        print(
            f"{i}. Viagem {record['NUVIAG']} - Motorista: {record['NOMEPARC']} ({record['CODPARC']})"
        )


# =============================================================================
# Exemplo 3: Query parametrizada (para usar em find_travel_id)
# =============================================================================


def exemplo_buscar_viagem(codparc: int, dhemiss: str, num_ciot: str):
    """
    Exemplo de busca de viagem - equivalente ao sql1 do Java

    Args:
        codparc: Código do parceiro (motorista)
        dhemiss: Data de emissão no formato DD/MM/YYYY
        num_ciot: Número CIOT para verificar duplicidade
    """
    print("\n" + "=" * 60)
    print("EXEMPLO 3: Busca de Viagem Parametrizada")
    print("=" * 60)

    # Autenticar
    oauth = OAuthClient(base_url=SANKHYA_AUTH_BASE_URL, token=SANKHYA_X_TOKEN)
    if not SANKHYA_CLIENT_ID or not SANKHYA_CLIENT_SECRET:
        raise RuntimeError(
            "SANKHYA_CLIENT_ID e SANKHYA_CLIENT_SECRET devem estar definidos no ambiente"
        )
    oauth.authenticate(SANKHYA_CLIENT_ID, SANKHYA_CLIENT_SECRET)

    session = SankhyaSession(oauth_client=oauth, base_url=SANKHYA_AUTH_BASE_URL)
    client = GatewayClient(session)

    # SQL parametrizado (equivalente ao sql1 do Java)
    sql = f"""
        SELECT * FROM (
            SELECT VIAG.NUVIAG, MME.CODPARC
            FROM TGFVIAG VIAG
            JOIN TGFMDFE MDF ON MDF.nuviag=VIAG.nuviag
            JOIN TGFMME MME ON MME.NUVIAG = VIAG.NUVIAG
            WHERE MME.CODPARC = {codparc}
            AND TRUNC(MDF.DHEMISS) BETWEEN TO_DATE('{dhemiss}', 'DD/MM/YYYY') -1 
                AND TO_DATE('{dhemiss}', 'DD/MM/YYYY') +2
            AND NOT EXISTS (
                SELECT 1 FROM TGFCIOT CIOT 
                WHERE CIOT.NUVIAG=VIAG.NUVIAG 
                AND CIOT.SEQMDFE=1 
                AND CIOT.CIOT='{num_ciot}'
            )
            ORDER BY MDF.DHEMISS
        ) WHERE ROWNUM = 1
    """

    print(f"\nBuscando viagem:")
    print(f"  - Motorista (CODPARC): {codparc}")
    print(f"  - Data emissão: {dhemiss}")
    print(f"  - CIOT: {num_ciot}")
    print(f"\nSQL:\n{sql}\n")

    try:
        response = execute_sql(client, sql)
        rows = extract_rows(response)

        if rows:
            record = rows[0]
            print(f"✅ Viagem encontrada!")
            print(f"   NUVIAG: {record['NUVIAG']}")
            print(f"   CODPARC: {record['CODPARC']}")
            return record
        else:
            print("❌ Nenhuma viagem encontrada com os critérios informados")
            return None

    except Exception as e:
        print(f"❌ Erro ao buscar viagem: {e}")
        return None


# =============================================================================
# Main
# =============================================================================


def main():
    """Executa os exemplos"""
    print("DbExplorerSP.executeQuery com OAuth2\n")

    # Exemplo 1: Query simples
    exemplo_query_simples()

    # Exemplo 2: Query com JOIN
    # exemplo_query_join()

    # Exemplo 3: Busca parametrizada
    # Descomente para testar com dados reais:
    # exemplo_buscar_viagem(
    #     codparc=123,  # Código do motorista
    #     dhemiss="10/01/2026",
    #     num_ciot="107194029DIA"
    # )


if __name__ == "__main__":
    main()
