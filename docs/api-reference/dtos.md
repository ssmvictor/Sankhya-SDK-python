# DTOs (Data Transfer Objects)

Modelos Pydantic otimizados para a API Gateway JSON do Sankhya.

## Visão Geral

Os DTOs fornecem:

- **Validação automática** de dados via Pydantic
- **Aliases** mapeados para nomes de campos Sankhya
- **Tipagem forte** com suporte a IDEs
- **Serialização** com `model_dump(by_alias=True)`

## Importação

```python
from sankhya_sdk.models.dtos import (
    # Parceiro
    ParceiroDTO, ParceiroCreateDTO, ParceiroListDTO,
    # Nota Fiscal
    NotaDTO, NotaCabecalhoDTO, NotaItemDTO,
    # Financeiro
    MovimentoDTO,
    # Produto
    ProdutoDTO, ProdutoListDTO,
)
```

---

## Enumerações

### TipoPessoa

```python
from sankhya_sdk.models.dtos.parceiro import TipoPessoa

class TipoPessoa(str, Enum):
    FISICA = "F"    # Pessoa Física (CPF)
    JURIDICA = "J"  # Pessoa Jurídica (CNPJ)
```

### TipoOperacao

```python
from sankhya_sdk.models.dtos.nota import TipoOperacao

class TipoOperacao(str, Enum):
    ENTRADA = "E"  # Nota de entrada
    SAIDA = "S"    # Nota de saída
```

### TipoNota

```python
from sankhya_sdk.models.dtos.nota import TipoNota

class TipoNota(str, Enum):
    NFE = "1"     # NF-e
    NFCE = "2"    # NFC-e
    SAT = "3"     # SAT
    MANUAL = "4"  # Manual
```

### TipoTitulo

```python
from sankhya_sdk.models.dtos.movimento import TipoTitulo

class TipoTitulo(str, Enum):
    RECEBER = "R"  # Contas a receber
    PAGAR = "P"    # Contas a pagar
```

### StatusFinanceiro

```python
from sankhya_sdk.models.dtos.movimento import StatusFinanceiro

class StatusFinanceiro(str, Enum):
    ABERTO = "A"     # Em aberto
    BAIXADO = "B"    # Baixado/Pago
    PARCIAL = "P"    # Parcialmente pago
    CANCELADO = "C"  # Cancelado
```

---

## ParceiroDTO

DTO completo para operações com Parceiros (clientes/fornecedores).

### Campos

| Campo Python | Alias Sankhya | Tipo | Descrição |
|--------------|---------------|------|-----------|
| `codigo` | `CODPARC` | `int \| None` | Código (PK) |
| `nome` | `NOMEPARC` | `str` | Nome/Razão Social |
| `nome_fantasia` | `NOMEFANTASIA` | `str \| None` | Nome fantasia |
| `tipo_pessoa` | `TIPPESSOA` | `TipoPessoa` | F=Física, J=Jurídica |
| `cnpj_cpf` | `CGC_CPF` | `str \| None` | CNPJ ou CPF |
| `inscricao_estadual` | `INSCESTADNAUF` | `str \| None` | IE |
| `endereco` | `NOMEEND` | `str \| None` | Logradouro |
| `numero` | `NUMEND` | `str \| None` | Número |
| `complemento` | `COMPLEMENTO` | `str \| None` | Complemento |
| `bairro` | `NOMEBAI` | `str \| None` | Bairro |
| `codigo_cidade` | `CODCID` | `int \| None` | Código da cidade |
| `cep` | `CEP` | `str \| None` | CEP |
| `telefone` | `TELEFONE` | `str \| None` | Telefone |
| `email` | `EMAIL` | `str \| None` | E-mail |
| `ativo` | `ATIVO` | `str` | S=Sim, N=Não |
| `cliente` | `CLIENTE` | `str` | S=Sim, N=Não |
| `fornecedor` | `FORNECEDOR` | `str` | S=Sim, N=Não |
| `limite_credito` | `LIMCRED` | `Decimal \| None` | Limite de crédito |

### Exemplo de Uso

```python
from sankhya_sdk.models.dtos import ParceiroDTO
from sankhya_sdk.models.dtos.parceiro import TipoPessoa

# Criar com validação
parceiro = ParceiroDTO(
    nome="Empresa Exemplo LTDA",
    tipo_pessoa=TipoPessoa.JURIDICA,
    cnpj_cpf="12.345.678/0001-90",
    codigo_cidade=10,
    email="contato@empresa.com"
)

# Serializar para API Sankhya
payload = parceiro.model_dump(by_alias=True, exclude_none=True)
# Resultado:
# {
#     "NOMEPARC": "Empresa Exemplo LTDA",
#     "TIPPESSOA": "J",
#     "CGC_CPF": "12.345.678/0001-90",
#     "CODCID": 10,
#     "EMAIL": "contato@empresa.com",
#     "ATIVO": "S",
#     "CLIENTE": "S",
#     "FORNECEDOR": "N"
# }
```

### ParceiroCreateDTO

Versão simplificada para criação de parceiros.

```python
from sankhya_sdk.models.dtos import ParceiroCreateDTO

novo = ParceiroCreateDTO(
    nome="Novo Cliente",
    tipo_pessoa=TipoPessoa.FISICA,
    cnpj_cpf="123.456.789-00",
    codigo_cidade=10
)
```

### ParceiroListDTO

Versão leve para listagens.

```python
from sankhya_sdk.models.dtos import ParceiroListDTO

# Parse de resposta da API
lista = ParceiroListDTO(
    codigo=123,
    nome="Cliente Teste",
    tipo_pessoa=TipoPessoa.JURIDICA,
    cnpj_cpf="12345678000199",
    ativo="S"
)
```

---

## NotaDTO

DTO para Notas Fiscais completas (cabeçalho + itens).

### NotaCabecalhoDTO

Campos do cabeçalho da nota:

| Campo Python | Alias Sankhya | Tipo | Descrição |
|--------------|---------------|------|-----------|
| `numero_unico` | `NUNOTA` | `int \| None` | Número único (PK) |
| `numero_nota` | `NUMNOTA` | `int \| None` | Número da nota |
| `serie` | `SERIENOTA` | `str \| None` | Série |
| `tipo_operacao` | `TIPMOV` | `TipoOperacao` | E=Entrada, S=Saída |
| `codigo_parceiro` | `CODPARC` | `int` | Código do parceiro |
| `codigo_empresa` | `CODEMP` | `int` | Código da empresa |
| `data_negociacao` | `DTNEG` | `date` | Data de negociação |
| `valor_nota` | `VLRNOTA` | `Decimal \| None` | Valor total |
| `pendente` | `PENDENTE` | `str` | S=Pendente, N=Confirmada |

### NotaItemDTO

Campos dos itens da nota:

| Campo Python | Alias Sankhya | Tipo | Descrição |
|--------------|---------------|------|-----------|
| `numero_unico` | `NUNOTA` | `int` | Número único da nota |
| `sequencia` | `SEQUENCIA` | `int \| None` | Sequência do item |
| `codigo_produto` | `CODPROD` | `int` | Código do produto |
| `quantidade` | `QTDNEG` | `Decimal` | Quantidade |
| `valor_unitario` | `VLRUNIT` | `Decimal` | Valor unitário |
| `valor_total` | `VLRTOT` | `Decimal \| None` | Valor total do item |

### Exemplo

```python
from sankhya_sdk.models.dtos import NotaDTO, NotaCabecalhoDTO, NotaItemDTO
from sankhya_sdk.models.dtos.nota import TipoOperacao
from datetime import date
from decimal import Decimal

# Criar nota com itens
nota = NotaDTO(
    cabecalho=NotaCabecalhoDTO(
        tipo_operacao=TipoOperacao.SAIDA,
        codigo_parceiro=123,
        codigo_empresa=1,
        data_negociacao=date.today()
    ),
    itens=[
        NotaItemDTO(
            numero_unico=0,  # será preenchido
            codigo_produto=100,
            quantidade=Decimal("10"),
            valor_unitario=Decimal("99.90")
        ),
        NotaItemDTO(
            numero_unico=0,
            codigo_produto=200,
            quantidade=Decimal("5"),
            valor_unitario=Decimal("49.90")
        )
    ]
)

# Propriedades calculadas
print(f"Qtd itens: {nota.quantidade_itens}")
print(f"Valor total: {nota.valor_total_itens}")
```

---

## MovimentoDTO

DTO para movimentos financeiros (títulos a pagar/receber).

### Campos Principais

| Campo Python | Alias Sankhya | Tipo | Descrição |
|--------------|---------------|------|-----------|
| `numero_unico` | `NUFIN` | `int \| None` | Número único (PK) |
| `tipo_titulo` | `RECDESP` | `TipoTitulo` | R=Receber, P=Pagar |
| `codigo_parceiro` | `CODPARC` | `int` | Código do parceiro |
| `data_negociacao` | `DTNEG` | `date` | Data de negociação |
| `data_vencimento` | `DTVENC` | `date` | Data de vencimento |
| `valor_desdobramento` | `VLRDESDOB` | `Decimal` | Valor do título |
| `valor_baixado` | `VLRBAIXA` | `Decimal \| None` | Valor já pago |
| `baixado` | `BAIXADO` | `str` | S=Baixado, N=Aberto |

### Propriedades Calculadas

```python
from sankhya_sdk.models.dtos import MovimentoDTO
from sankhya_sdk.models.dtos.movimento import TipoTitulo
from datetime import date
from decimal import Decimal

movimento = MovimentoDTO(
    tipo_titulo=TipoTitulo.RECEBER,
    codigo_parceiro=123,
    codigo_empresa=1,
    data_negociacao=date.today(),
    data_vencimento=date(2025, 12, 31),
    valor_desdobramento=Decimal("1000.00"),
    valor_baixado=Decimal("300.00")
)

# Propriedades
print(f"Status: {movimento.status}")          # StatusFinanceiro.PARCIAL
print(f"Em aberto: {movimento.valor_em_aberto}")  # Decimal("700.00")
print(f"Vencido: {movimento.esta_vencido}")   # True/False
```

---

## ProdutoDTO

DTO para produtos.

### Campos

| Campo Python | Alias Sankhya | Tipo | Descrição |
|--------------|---------------|------|-----------|
| `codigo` | `CODPROD` | `int \| None` | Código (PK) |
| `descricao` | `DESCRPROD` | `str` | Descrição |
| `referencia` | `REFERENCIA` | `str \| None` | SKU/Referência |
| `ncm` | `NCM` | `str \| None` | NCM fiscal |
| `codigo_grupo` | `CODGRUPOPROD` | `int \| None` | Grupo |
| `codigo_marca` | `CODMARCA` | `int \| None` | Marca |
| `unidade` | `UNIDADE` | `str \| None` | Unidade de medida |
| `peso_bruto` | `PESOBRUTO` | `Decimal \| None` | Peso bruto |
| `peso_liquido` | `PESOLIQ` | `Decimal \| None` | Peso líquido |
| `ativo` | `ATIVO` | `str` | S=Sim, N=Não |

### Exemplo

```python
from sankhya_sdk.models.dtos import ProdutoDTO

produto = ProdutoDTO(
    descricao="Notebook Dell Inspiron",
    referencia="DELL-INS-15",
    ncm="84713012",
    unidade="UN"
)

payload = produto.model_dump(by_alias=True, exclude_none=True)
```

---

## Uso com GatewayClient

### Inserir via DTO

```python
from sankhya_sdk.http import GatewayClient
from sankhya_sdk.models.dtos import ParceiroDTO
from sankhya_sdk.models.dtos.parceiro import TipoPessoa

# Criar e validar
parceiro = ParceiroDTO(
    nome="Nova Empresa",
    tipo_pessoa=TipoPessoa.JURIDICA,
    codigo_cidade=10
)

# Enviar para API
client = GatewayClient(session)
result = client.save_record(
    entity="Parceiro",
    fields=parceiro.model_dump(by_alias=True, exclude_none=True)
)
```

### Parse de Resposta

```python
from sankhya_sdk.models.dtos import ParceiroListDTO

# Consultar
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC", "TIPPESSOA", "CGC_CPF", "ATIVO"],
    criteria="ATIVO = 'S'"
)

# Converter para DTOs
entities = result.get("responseBody", {}).get("entities", {}).get("entity", [])

parceiros = []
for entity in entities:
    parceiros.append(ParceiroListDTO(
        codigo=int(entity["CODPARC"]["$"]),
        nome=entity["NOMEPARC"]["$"],
        tipo_pessoa=entity["TIPPESSOA"]["$"],
        cnpj_cpf=entity.get("CGC_CPF", {}).get("$"),
        ativo=entity["ATIVO"]["$"]
    ))
```

---

## Próximos Passos

- [Gateway Client](gateway-client.md) - Cliente para API Gateway
- [Adapters](adapters.md) - Compatibilidade XML
- [Exemplos](../examples/gateway-usage.md) - Casos de uso práticos
