# Exemplos do Sankhya SDK Python

Exemplos práticos de uso do SDK para integração com o ERP Sankhya via **JSON Gateway** com autenticação **OAuth2**.

---

## Configuracao

### 1. Variaveis de Ambiente (OAuth2)

Configure as credenciais OAuth2 antes de executar:

```bash
# Windows (PowerShell)
$env:SANKHYA_CLIENT_ID = "seu_client_id"
$env:SANKHYA_CLIENT_SECRET = "seu_client_secret"
$env:SANKHYA_AUTH_BASE_URL = "https://api.sankhya.com.br"
$env:SANKHYA_TOKEN = "seu_x_token"  # Token de Integracao

# Linux/Mac
export SANKHYA_CLIENT_ID="seu_client_id"
export SANKHYA_CLIENT_SECRET="seu_client_secret"
export SANKHYA_AUTH_BASE_URL="https://api.sankhya.com.br"
export SANKHYA_TOKEN="seu_x_token"
```

Ou crie um arquivo `.env` na raiz do projeto:

```env
SANKHYA_CLIENT_ID=seu_client_id
SANKHYA_CLIENT_SECRET=seu_client_secret
SANKHYA_AUTH_BASE_URL=https://api.sankhya.com.br
SANKHYA_TOKEN=seu_x_token
```

### 2. Obtendo Credenciais

| Credencial | Onde Obter |
|------------|------------|
| `CLIENT_ID` | [Portal do Desenvolvedor](https://areadev.sankhya.com.br/) > Minhas Solucoes |
| `CLIENT_SECRET` | [Portal do Desenvolvedor](https://areadev.sankhya.com.br/) > Minhas Solucoes |
| `X-TOKEN` | Sankhya OM > Configuracoes Gateway > Chave do Cliente |

### 3. Instalacao

```bash
pip install -e ".[dev]"
```

---

## Arquivos de Exemplo

| Arquivo | Entidade | Tabela | Descricao |
|---------|----------|--------|-----------|
| `oauth_example.py` | - | - | Autenticacao OAuth2 completa |
| `partner_example.py` | Parceiro | TGFPAR | Clientes, fornecedores, vendedores |
| `product_example.py` | Produto | TGFPRO | Catalogo de produtos |
| `invoice_example.py` | Nota Fiscal | TGFCAB + TGFITE | Notas fiscais e itens |
| `financial_example.py` | Financeiro | TGFFIN | Titulos a receber/pagar |
| `paged_request_example.py` | - | - | Consultas paginadas e filtros |
| `partial_update_example.py` | Varios | TGFFIN, TGFPAR | **Update parcial via DatasetSP.save** |
| `dbexplorer.py` | - | - | Explorador de estrutura do banco de dados |

---

## Padrao de Autenticacao OAuth2

Todos os exemplos usam o mesmo padrao de autenticacao:

```python
import os
from dotenv import load_dotenv
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient

load_dotenv()

# 1. Criar cliente OAuth
oauth = OAuthClient(
    base_url=os.getenv("SANKHYA_AUTH_BASE_URL"),
    token=os.getenv("SANKHYA_TOKEN")  # X-Token
)

# 2. Autenticar
oauth.authenticate(
    client_id=os.getenv("SANKHYA_CLIENT_ID"),
    client_secret=os.getenv("SANKHYA_CLIENT_SECRET")
)

# 3. Criar sessao e cliente
session = SankhyaSession(oauth_client=oauth, base_url=os.getenv("SANKHYA_AUTH_BASE_URL"))
client = GatewayClient(session)

# 4. Fazer consultas
response = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC"],
    criteria="ATIVO = 'S'"
)
```

---

## Entidades

### Parceiro (`Parceiro` -> TGFPAR)

Representa clientes, fornecedores, vendedores e transportadoras.

**Campos Principais:**
| Campo | Descricao |
|-------|-----------|
| `CODPARC` | Codigo do parceiro (PK) |
| `NOMEPARC` | Nome/Razao Social |
| `CGC_CPF` | CNPJ ou CPF |
| `EMAIL` | E-mail |
| `TELEFONE` | Telefone |
| `ATIVO` | Status (S/N) |
| `CLIENTE` | E cliente? (S/N) |
| `FORNECEDOR` | E fornecedor? (S/N) |

---

### Produto (`Produto` -> TGFPRO)

Catalogo de produtos e servicos.

**Campos Principais:**
| Campo | Descricao |
|-------|-----------|
| `CODPROD` | Codigo do produto (PK) |
| `DESCRPROD` | Descricao |
| `REFERENCIA` | Referencia/SKU |
| `NCM` | NCM fiscal |
| `CODGRUPOPROD` | Codigo do grupo |
| `ATIVO` | Status (S/N) |
| `UNIDADE` | Unidade de medida |

---

### Nota Fiscal (`CabecalhoNota` -> TGFCAB)

Cabecalho das notas fiscais.

**Campos Principais:**
| Campo | Descricao |
|-------|-----------|
| `NUNOTA` | Numero unico (PK) |
| `NUMNOTA` | Numero da nota |
| `DTNEG` | Data negociacao |
| `CODPARC` | Codigo parceiro |
| `VLRNOTA` | Valor total |
| `STATUSNFE` | Status NF-e |
| `TIPMOV` | Tipo movimento |

**Status NF-e (`STATUSNFE`):**
| Valor | Significado |
|-------|-------------|
| `'A'` | Aprovada |
| `'D'` | Denegada |
| `'R'` | Rejeitada |
| `'C'` | Cancelada |
| `'E'` | Em processamento |

---

### Financeiro (`Financeiro` -> TGFFIN)

Titulos a receber e a pagar.

**Campos Principais:**
| Campo | Descricao |
|-------|-----------|
| `NUFIN` | Numero unico financeiro (PK) |
| `NUNOTA` | Numero da nota (FK) |
| `DTVENC` | Data vencimento |
| `VLRDESDOB` | Valor desdobramento |
| `CODPARC` | Codigo parceiro |
| `RECDESP` | R=Receita, D=Despesa |
| `DHBAIXA` | Data/hora baixa |
| `PROVISAO` | E provisao? (S/N) |

---

## Como Executar

### Opcao 1: Execucao Direta (Recomendado)

Execute funcoes diretamente via `python -c`:

```bash
# Autenticacao OAuth2
python examples/oauth_example.py

# Parceiros
python -c "from examples.partner_example import listar_parceiros; listar_parceiros(10)"
python -c "from examples.partner_example import buscar_parceiro_por_codigo; buscar_parceiro_por_codigo(1)"

# Produtos
python -c "from examples.product_example import listar_produtos_ativos; listar_produtos_ativos(10)"
python -c "from examples.product_example import buscar_produto_por_codigo; buscar_produto_por_codigo(1)"

# Notas Fiscais
python -c "from examples.invoice_example import listar_notas_fiscais; listar_notas_fiscais(10)"
python -c "from examples.invoice_example import listar_notas_aprovadas; listar_notas_aprovadas(10)"

# Financeiro
python -c "from examples.financial_example import listar_a_receber_em_aberto; listar_a_receber_em_aberto(10)"
python -c "from examples.financial_example import listar_a_pagar_em_aberto; listar_a_pagar_em_aberto(10)"
python -c "from examples.financial_example import listar_titulos_vencidos; listar_titulos_vencidos(10)"

# Update Parcial (DatasetSP.save)
python examples/partial_update_example.py
python -c "from examples.partial_update_example import atualizar_email_parceiro; atualizar_email_parceiro(1, 'novo@email.com')"
python -c "from examples.partial_update_example import atualizar_vencimento_titulo; atualizar_vencimento_titulo(12345, '20/02/2026')"
```

### Opcao 2: Executar Arquivo Completo

```bash
python examples/partner_example.py
python examples/product_example.py
python examples/invoice_example.py
python examples/financial_example.py
python examples/paged_request_example.py
python examples/partial_update_example.py
```

---

## API Utilizada

Os exemplos usam o **JSON Gateway** via `GatewayClient`:

| Metodo | Servico | Descricao |
|--------|---------|-----------|
| `load_records()` | `CRUDServiceProvider.loadRecords` | Consulta entidades |
| `save_record()` | `CRUDServiceProvider.saveRecord` | Criar/Atualizar (completo) |
| `save_record(pk=...)` | `DatasetSP.save` | **Update parcial** (so campos alterados) |
| `execute_service()` | Generico | Executar servico customizado |

### Update Parcial (Novo)

Quando voce precisa alterar apenas alguns campos de um registro existente, use o parametro `pk`:

```python
# UPDATE PARCIAL - altera apenas DTVENC, nao exige outros campos obrigatorios
client.save_record(
    entity="Financeiro",
    fields={"DTVENC": "20/02/2026"},
    pk={"NUFIN": 12345}
)

# UPDATE PARCIAL com PK composta
client.save_record(
    entity="ItemNota",
    fields={"OBSERVACAO": "Desconto especial"},
    pk={"NUNOTA": 100, "SEQUENCIA": 1}
)

# INSERT (sem pk) - comportamento original
client.save_record(
    entity="Parceiro",
    fields={"NOMEPARC": "Novo Parceiro", "TIPPESSOA": "J", ...}
)
```

**Vantagem**: Evita erros de validacao quando o Gateway exige campos obrigatorios que voce nao quer alterar.

### DTOs Disponiveis

| DTO | Entidade | Campos |
|-----|----------|--------|
| `ParceiroDTO` | Parceiro | Completo |
| `ParceiroListDTO` | Parceiro | Listagem |
| `ParceiroCreateDTO` | Parceiro | Criacao |
| `ProdutoDTO` | Produto | Completo |
| `ProdutoListDTO` | Produto | Listagem |
| `NotaDTO` | Nota Fiscal | Completo |
| `MovimentoDTO` | Movimento | Completo |

---

## Renovacao Automatica de Token

O SDK renova automaticamente o token OAuth2 quando necessario:

```python
# O token e renovado automaticamente a cada requisicao se necessario
# Voce nao precisa se preocupar com isso!

for i in range(100):
    # O SDK verifica e renova o token automaticamente
    response = client.load_records("Parceiro", ["CODPARC", "NOMEPARC"])
```

---

## Tratamento de Erros

```python
from sankhya_sdk.auth import AuthError, TokenExpiredError, AuthNetworkError
from sankhya_sdk.exceptions import SankhyaHttpError, SankhyaAuthError

try:
    response = client.load_records("Parceiro", ["CODPARC"])
    
except AuthError as e:
    print(f"Erro de autenticacao: {e.message}")
    
except AuthNetworkError as e:
    print(f"Erro de rede: {e.message}")
    
except SankhyaAuthError:
    print("Token expirado ou invalido")
    
except SankhyaHttpError as e:
    print(f"Erro HTTP {e.status_code}")
```

---

## Mais Informacoes

- [Documentacao Completa](../docs/)
- [API Reference](../docs/api-reference/)
- [Guia de Autenticacao](../docs/getting-started/authentication.md)
- [README Principal](../README.md)
