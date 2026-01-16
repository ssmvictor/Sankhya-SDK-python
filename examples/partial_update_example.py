# -*- coding: utf-8 -*-
"""
Exemplo de Update Parcial usando DatasetSP.save (JSON Gateway).

Demonstra o novo recurso de update parcial que permite alterar apenas
campos especificos de um registro sem enviar todos os campos obrigatorios.

Cenario: Quando voce quer alterar apenas a data de vencimento de um titulo
financeiro (TGFFIN), o CRUDServiceProvider.saveRecord exige todos os campos
obrigatorios. Com o DatasetSP.save, voce envia apenas a PK e os campos alterados.

Uso:
    client.save_record(
        entity="Financeiro",
        fields={"DTVENC": "2026-01-20"},
        pk={"NUFIN": 123}
    )

Tabela Sankhya: TGFFIN, TGFPAR, TGFCAB
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# =============================================================================
# Configuracao OAuth2
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
# Exemplo 1: Update Parcial de Titulo Financeiro
# =============================================================================


def atualizar_vencimento_titulo(nufin: int, nova_data: str) -> Dict[str, Any]:
    """
    Atualiza APENAS a data de vencimento de um titulo financeiro.

    Este exemplo demonstra o update parcial: ao inves de enviar todos os
    campos obrigatorios do registro, enviamos apenas a PK e o campo alterado.

    Args:
        nufin: Numero unico financeiro (PK da TGFFIN)
        nova_data: Nova data de vencimento (formato DD/MM/YYYY)

    Returns:
        Resposta da API

    Exemplo:
        >>> atualizar_vencimento_titulo(12345, "20/02/2026")
    """
    client = _create_client()

    print(f"Atualizando vencimento do titulo NUFIN={nufin} para {nova_data}...")

    # UPDATE PARCIAL: envia apenas pk + campos alterados
    # Internamente usa DatasetSP.save ao inves de CRUDServiceProvider.saveRecord
    response = client.save_record(
        entity="Financeiro",
        fields={"DTVENC": nova_data},
        pk={"NUFIN": nufin},
    )

    if client.is_success(response):
        print(f"  Titulo NUFIN={nufin} atualizado com sucesso!")
    else:
        print(f"  Erro: {client.get_error_message(response)}")

    return response


# =============================================================================
# Exemplo 2: Update Parcial de Parceiro
# =============================================================================


def atualizar_email_parceiro(codparc: int, novo_email: str) -> Dict[str, Any]:
    """
    Atualiza APENAS o email de um parceiro.

    Args:
        codparc: Codigo do parceiro (PK da TGFPAR)
        novo_email: Novo email

    Returns:
        Resposta da API

    Exemplo:
        >>> atualizar_email_parceiro(1, "novo@email.com")
    """
    client = _create_client()

    print(f"Atualizando email do parceiro CODPARC={codparc}...")

    response = client.save_record(
        entity="Parceiro",
        fields={"EMAIL": novo_email},
        pk={"CODPARC": codparc},
    )

    if client.is_success(response):
        print(f"  Parceiro CODPARC={codparc} atualizado com sucesso!")
    else:
        print(f"  Erro: {client.get_error_message(response)}")

    return response


# =============================================================================
# Exemplo 3: Update Parcial com Multiplos Campos
# =============================================================================


def atualizar_contato_parceiro(
    codparc: int,
    telefone: Optional[str] = None,
    email: Optional[str] = None,
    contato: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atualiza multiplos campos de contato de um parceiro.

    Demonstra que voce pode enviar varios campos no update parcial,
    desde que nao sejam campos obrigatorios que estejam faltando.

    Args:
        codparc: Codigo do parceiro
        telefone: Novo telefone (opcional)
        email: Novo email (opcional)
        contato: Nome do contato (opcional)

    Returns:
        Resposta da API
    """
    client = _create_client()

    # Monta dict apenas com campos fornecidos
    fields: Dict[str, Any] = {}
    if telefone:
        fields["TELEFONE"] = telefone
    if email:
        fields["EMAIL"] = email
    if contato:
        fields["CONTATO"] = contato

    if not fields:
        print("Nenhum campo para atualizar!")
        return {}

    print(f"Atualizando parceiro CODPARC={codparc} com campos: {list(fields.keys())}...")

    response = client.save_record(
        entity="Parceiro",
        fields=fields,
        pk={"CODPARC": codparc},
    )

    if client.is_success(response):
        print(f"  Parceiro atualizado com sucesso!")
    else:
        print(f"  Erro: {client.get_error_message(response)}")

    return response


# =============================================================================
# Exemplo 4: Update com PK Composta
# =============================================================================


def atualizar_observacao_item_nota(
    nunota: int,
    sequencia: int,
    observacao: str,
) -> Dict[str, Any]:
    """
    Atualiza a observacao de um item de nota fiscal.

    Demonstra update parcial com chave primaria composta (NUNOTA + SEQUENCIA).

    Args:
        nunota: Numero unico da nota
        sequencia: Sequencia do item
        observacao: Nova observacao

    Returns:
        Resposta da API

    Exemplo:
        >>> atualizar_observacao_item_nota(12345, 1, "Item com desconto especial")
    """
    client = _create_client()

    print(f"Atualizando item NUNOTA={nunota}, SEQ={sequencia}...")

    # PK composta: NUNOTA + SEQUENCIA
    response = client.save_record(
        entity="ItemNota",
        fields={"OBSERVACAO": observacao},
        pk={"NUNOTA": nunota, "SEQUENCIA": sequencia},
    )

    if client.is_success(response):
        print(f"  Item atualizado com sucesso!")
    else:
        print(f"  Erro: {client.get_error_message(response)}")

    return response


# =============================================================================
# Exemplo 5: Comparacao entre Insert e Update
# =============================================================================


def demonstrar_diferenca_insert_update():
    """
    Demonstra a diferenca entre INSERT (sem pk) e UPDATE (com pk).

    - Sem pk: usa CRUDServiceProvider.saveRecord (INSERT/UPSERT)
    - Com pk: usa DatasetSP.save (UPDATE parcial)
    """
    print("\n" + "=" * 60)
    print("COMPARACAO: INSERT vs UPDATE PARCIAL")
    print("=" * 60)

    print("\n1. INSERT (sem pk) - CRUDServiceProvider.saveRecord:")
    print("   client.save_record(")
    print('       entity="Parceiro",')
    print('       fields={"NOMEPARC": "Novo Parceiro", "TIPPESSOA": "J", ...}')
    print("   )")
    print("   -> Cria novo registro, exige campos obrigatorios")

    print("\n2. UPDATE PARCIAL (com pk) - DatasetSP.save:")
    print("   client.save_record(")
    print('       entity="Parceiro",')
    print('       fields={"EMAIL": "novo@email.com"},')
    print('       pk={"CODPARC": 123}')
    print("   )")
    print("   -> Atualiza apenas EMAIL, nao exige outros campos")

    print("\n3. FORCAR comportamento antigo mesmo com pk:")
    print("   client.save_record(")
    print('       entity="Parceiro",')
    print('       fields={"EMAIL": "novo@email.com"},')
    print('       pk={"CODPARC": 123},')
    print("       use_dataset_for_update=False  # Forca CRUDServiceProvider")
    print("   )")


# =============================================================================
# Exemplo 6: Prorrogar Vencimentos em Lote
# =============================================================================


def prorrogar_vencimentos_parceiro(
    codparc: int,
    dias: int = 30,
    max_titulos: int = 10,
) -> List[Dict[str, Any]]:
    """
    Prorroga vencimentos de titulos em aberto de um parceiro.

    Demonstra uso pratico do update parcial em lote.

    Args:
        codparc: Codigo do parceiro
        dias: Quantidade de dias para prorrogar
        max_titulos: Limite de titulos a processar

    Returns:
        Lista de respostas das atualizacoes
    """
    client = _create_client()

    # 1. Buscar titulos em aberto do parceiro
    print(f"\nBuscando titulos em aberto do parceiro {codparc}...")

    response = client.load_records(
        entity="Financeiro",
        fields=["NUFIN", "DTVENC", "VLRDESDOB"],
        criteria=f"CODPARC = {codparc} AND DHBAIXA IS NULL",
    )

    titulos = _extract_entities(response)

    if not titulos:
        print("  Nenhum titulo em aberto encontrado.")
        return []

    print(f"  Encontrados {len(titulos)} titulos em aberto.")

    # 2. Atualizar cada titulo
    resultados = []
    for titulo in titulos[:max_titulos]:
        nufin = titulo.get("NUFIN")
        venc_atual = titulo.get("DTVENC", "")
        valor = titulo.get("VLRDESDOB", 0)

        # Calcular nova data (simplificado)
        try:
            dt_venc = datetime.strptime(venc_atual[:10], "%d/%m/%Y")
            nova_dt = dt_venc + timedelta(days=dias)
            nova_data = nova_dt.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            print(f"  Pulando NUFIN={nufin} - data invalida: {venc_atual}")
            continue

        print(f"  NUFIN={nufin} | R${valor} | {venc_atual} -> {nova_data}")

        # Update parcial
        resp = client.save_record(
            entity="Financeiro",
            fields={"DTVENC": nova_data},
            pk={"NUFIN": nufin},
        )
        resultados.append(resp)

    print(f"\n  {len(resultados)} titulos prorrogados em {dias} dias.")
    return resultados


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exemplos de UPDATE PARCIAL - DatasetSP.save")
    print("=" * 60)

    # Demonstrar diferenca conceitual
    demonstrar_diferenca_insert_update()

    print("\n" + "=" * 60)
    print("EXEMPLOS PRATICOS (descomente para executar)")
    print("=" * 60)

    print("\n1. Atualizar vencimento de titulo:")
    print("   atualizar_vencimento_titulo(12345, '20/02/2026')")
    # atualizar_vencimento_titulo(12345, "20/02/2026")

    print("\n2. Atualizar email de parceiro:")
    print("   atualizar_email_parceiro(1, 'novo@email.com')")
    # atualizar_email_parceiro(1, "novo@email.com")

    print("\n3. Atualizar multiplos campos:")
    print("   atualizar_contato_parceiro(1, telefone='11999999999', email='x@y.com')")
    # atualizar_contato_parceiro(1, telefone="11999999999", email="x@y.com")

    print("\n4. Update com PK composta:")
    print("   atualizar_observacao_item_nota(12345, 1, 'Observacao')")
    # atualizar_observacao_item_nota(12345, 1, "Observacao")

    print("\n5. Prorrogar vencimentos em lote:")
    print("   prorrogar_vencimentos_parceiro(codparc=1, dias=30)")
    # prorrogar_vencimentos_parceiro(codparc=1, dias=30)

    print("\n" + "=" * 60)
    print("Configure as variaveis de ambiente SANKHYA_*")
    print("Descomente as chamadas acima para testar")
    print("=" * 60)
