# 📚 Exemplos do Sankhya SDK Python

Exemplos práticos de uso do SDK para integração com o ERP Sankhya.

---

## 🚀 Configuração

### 1. Variáveis de Ambiente

Configure as credenciais antes de executar:

```bash
# Windows (PowerShell)
$env:SANKHYA_HOST = "http://seu-servidor-sankhya"
$env:SANKHYA_PORT = "8180"
$env:SANKHYA_USERNAME = "seu_usuario"
$env:SANKHYA_PASSWORD = "sua_senha"
```

Ou crie um arquivo `.env` na raiz do projeto:

```env
SANKHYA_HOST=http://seu-servidor-sankhya
SANKHYA_PORT=8180
SANKHYA_USERNAME=seu_usuario
SANKHYA_PASSWORD=sua_senha
```

### 2. Instalação

```bash
pip install -e ".[dev]"
```

---

## 📂 Arquivos de Exemplo

| Arquivo | Entidade | Tabela | Descrição |
|---------|----------|--------|-----------|
| `partner_example.py` | Parceiro | TGFPAR | Clientes, fornecedores, vendedores |
| `product_example.py` | Produto | TGFPRO | Catálogo de produtos |
| `invoice_example.py` | Nota Fiscal | TGFCAB + TGFITE | Notas fiscais e itens |
| `financial_example.py` | Financeiro | TGFFIN | Títulos a receber/pagar |
| `paged_request_example.py` | - | - | Carregamento paginado |

---

## 📋 Entidades

### Parceiro (`Partner` → TGFPAR)

Representa clientes, fornecedores, vendedores e transportadoras.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| `CODPARC` | Código do parceiro (PK) |
| `NOMEPARC` | Nome/Razão Social |
| `CGC_CPF` | CNPJ ou CPF |
| `EMAIL` | E-mail |
| `TELEFONE` | Telefone |
| `ATIVO` | Status (S/N) |
| `CLIENTE` | É cliente? (S/N) |
| `FORNECEDOR` | É fornecedor? (S/N) |

**Exemplos Disponíveis:**
- Listar parceiros (paginado)
- Buscar por código
- Filtrar por nome (LIKE)
- Criar/Atualizar parceiro

---

### Produto (`Product` → TGFPRO)

Catálogo de produtos e serviços.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| `CODPROD` | Código do produto (PK) |
| `DESCRPROD` | Descrição |
| `REFERENCIA` | Referência/SKU |
| `NCM` | NCM fiscal |
| `CODGRUPOPROD` | Código do grupo |
| `ATIVO` | Status (S/N) |
| `UNIDADE` | Unidade de medida |

**Exemplos Disponíveis:**
- Listar produtos ativos
- Buscar por código
- Filtrar por NCM
- Filtrar por grupo

---

### Nota Fiscal (`InvoiceHeader` → TGFCAB)

Cabeçalho das notas fiscais com relacionamento aos itens.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| `NUNOTA` | Número único (PK) |
| `NUMNOTA` | Número da nota |
| `DTNEG` | Data negociação |
| `CODPARC` | Código parceiro |
| `VLRNOTA` | Valor total |
| `STATUSNFE` | Status NF-e |
| `TIPMOV` | Tipo movimento |

**Status NF-e (`STATUSNFE`):**
| Valor | Significado |
|-------|-------------|
| `'A'` | ✅ Aprovada |
| `'D'` | ❌ Denegada |
| `'R'` | ❌ Rejeitada |
| `'C'` | ⛔ Cancelada |
| `'E'` | ⏳ Em processamento |

**Itens da Nota (TGFITE):**
| Campo | Descrição |
|-------|-----------|
| `NUNOTA` | Número único (FK) |
| `SEQUENCIA` | Sequência do item |
| `CODPROD` | Código produto |
| `QTDNEG` | Quantidade negociada |
| `VLRUNIT` | Valor unitário |
| `VLRTOT` | Valor total |

**Exemplos Disponíveis:**
- Listar notas fiscais
- Buscar por NUNOTA
- Filtrar notas aprovadas (`STATUSNFE = 'A'`)
- **JOIN com TGFITE** - Soma de `QTDNEG` por nota
- Filtrar por parceiro

---

### Financeiro (TGFFIN)

Títulos a receber e a pagar.

**Campos Principais:**
| Campo | Descrição |
|-------|-----------|
| `NUFIN` | Número único financeiro (PK) |
| `NUNOTA` | Número da nota (FK) |
| `DTVENC` | Data vencimento |
| `VLRDESDOB` | Valor desdobramento |
| `CODPARC` | Código parceiro |
| `RECDESP` | R=Receita, D=Despesa |
| `DHBAIXA` | Data/hora baixa |
| `PROVISAO` | É provisão? (S/N) |

**Exemplos Disponíveis:**
- Listar títulos financeiros
- Títulos a receber em aberto
- Títulos a pagar em aberto
- Títulos vencidos
- Títulos por parceiro

---

## ▶️ Como Executar

### Opção 1: Execução Direta (Recomendado)

Execute funções diretamente via `python -c`:

```bash
# Parceiros
python -c "from examples.partner_example import listar_parceiros; listar_parceiros(10)"
python -c "from examples.partner_example import buscar_parceiro_por_codigo; buscar_parceiro_por_codigo(1)"
python -c "from examples.partner_example import filtrar_parceiros_por_nome; filtrar_parceiros_por_nome('EMPRESA')"

# Produtos
python -c "from examples.product_example import listar_produtos_ativos; listar_produtos_ativos(10)"
python -c "from examples.product_example import buscar_produto_por_codigo; buscar_produto_por_codigo(1)"
python -c "from examples.product_example import buscar_produtos_por_ncm; buscar_produtos_por_ncm('8471')"

# Notas Fiscais
python -c "from examples.invoice_example import listar_notas_fiscais; listar_notas_fiscais(10)"
python -c "from examples.invoice_example import listar_notas_aprovadas; listar_notas_aprovadas(10)"
python -c "from examples.invoice_example import consultar_notas_com_quantidade_itens; consultar_notas_com_quantidade_itens(10)"

# Financeiro
python -c "from examples.financial_example import listar_a_receber_em_aberto; listar_a_receber_em_aberto(10)"
python -c "from examples.financial_example import listar_a_pagar_em_aberto; listar_a_pagar_em_aberto(10)"
python -c "from examples.financial_example import listar_titulos_vencidos; listar_titulos_vencidos(10)"
```

### Opção 2: Descomentar no arquivo

1. Abra o arquivo de exemplo
2. Descomente a função desejada (remova o `#`)
3. Execute:

```bash
python examples/partner_example.py
python examples/product_example.py
python examples/invoice_example.py
python examples/financial_example.py
```

---

## 🔧 Serviços Utilizados

| ServiceName | Descrição | Uso |
|-------------|-----------|-----|
| `CRUD_SERVICE_FIND` | Consulta com entidades | Listar, buscar |
| `CRUD_SERVICE_SAVE` | Criar/Atualizar | Salvar dados |
| `CRUD_FIND` | Consulta SQL nativa | JOINs, agregações |

---

## 📖 Mais Informações

- [Documentação Completa](https://datavi.ia.br/docs-site-sdk/)
- [README Principal](../README.md)
