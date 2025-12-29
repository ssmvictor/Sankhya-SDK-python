# Modelos

Documentação dos modelos de serviço e entidades de transporte.

## Modelos de Serviço

### ServiceRequest

Modelo para requisições à API.

```python
from sankhya_sdk.service_models import ServiceRequest

request = ServiceRequest(
    service_name="CRUDServiceProvider.loadRecords",
    request_body=RequestBody(
        entity_name="Parceiro",
        criteria="CODPARC > 0"
    )
)
```

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `service_name` | `str` | Nome do serviço |
| `request_body` | `RequestBody` | Corpo da requisição |
| `output_type` | `str \| None` | Tipo de saída esperado |
| `no_auth` | `bool` | Se não requer autenticação |

---

### ServiceResponse

Modelo para respostas da API.

```python
from sankhya_sdk.service_models import ServiceResponse

# Típico: retornado pelo wrapper
response = wrapper.invoke_service("ServiceName", request)

if response.is_success:
    entities = response.entities
else:
    print(f"Erro: {response.status_message}")
```

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `status` | `str` | Status da resposta ("1" = sucesso) |
| `status_message` | `str \| None` | Mensagem de status |
| `response_body` | `ResponseBody` | Corpo da resposta |
| `entities` | `list[EntityBase]` | Entidades retornadas |

#### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `is_success` | `bool` | Se a requisição foi bem-sucedida |
| `has_entities` | `bool` | Se há entidades na resposta |
| `entity_count` | `int` | Quantidade de entidades |

---

### RequestBody

Corpo da requisição.

```python
from sankhya_sdk.service_models import RequestBody

body = RequestBody(
    entity_name="Parceiro",
    criteria="CODPARC > 0 AND ATIVO = 'S'",
    fields=["CODPARC", "NOMEPARC", "CGC_CPF"],
    order_by="NOMEPARC",
    max_results=100
)
```

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `entity_name` | `str` | Nome da entidade |
| `criteria` | `str \| None` | Critério de busca (SQL-like) |
| `fields` | `list[str] \| None` | Campos a retornar |
| `order_by` | `str \| None` | Ordenação |
| `max_results` | `int \| None` | Limite de resultados |
| `include_references` | `bool` | Incluir referências |

---

### ResponseBody

Corpo da resposta.

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `rows` | `list[dict]` | Linhas de dados |
| `total_records` | `int` | Total de registros |
| `page_count` | `int` | Número de páginas |

---

## Entidades de Transporte

### EntityBase

Classe base abstrata para todas as entidades.

```python
from sankhya_sdk.transport_entities import EntityBase

class MinhaEntidade(EntityBase):
    # Implementação customizada
    pass
```

#### Métodos

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `to_xml()` | `Element` | Serializa para XML |
| `from_xml(xml)` | `Self` | Deserializa de XML |
| `validate()` | `list[ValidationError]` | Valida a entidade |
| `get_key_values()` | `dict` | Retorna valores das chaves |

---

### Partner (Parceiro)

Representa clientes, fornecedores e outros parceiros.

```python
from sankhya_sdk.transport_entities import Partner

partner = Partner()
partner.code_partner = 1
partner.name = "Cliente LTDA"
partner.cgc_cpf = "12345678000199"
partner.type_partner = "C"  # Cliente
```

#### Campos

| Campo | Tipo | API | Descrição |
|-------|------|-----|-----------|
| `code_partner` | `int` | `CODPARC` | Código (chave) |
| `name` | `str` | `NOMEPARC` | Nome/Razão Social |
| `cgc_cpf` | `str \| None` | `CGC_CPF` | CNPJ ou CPF |
| `type_partner` | `str` | `TIPPESSOA` | Tipo (C/F/A/T/E) |
| `email` | `str \| None` | `EMAIL` | E-mail |
| `phone` | `str \| None` | `TELEFONE` | Telefone |
| `address` | `str \| None` | `ENDERECO` | Endereço |
| `city` | `str \| None` | `CIDADE` | Cidade |
| `state` | `str \| None` | `UF` | Estado (UF) |
| `zip_code` | `str \| None` | `CEP` | CEP |
| `active` | `bool` | `ATIVO` | Ativo |

---

### Product (Produto)

Representa produtos e serviços.

```python
from sankhya_sdk.transport_entities import Product

product = Product()
product.code_product = 100
product.description = "Produto Exemplo"
product.unit = "UN"
product.active = True
```

#### Campos

| Campo | Tipo | API | Descrição |
|-------|------|-----|-----------|
| `code_product` | `int` | `CODPROD` | Código (chave) |
| `description` | `str` | `DESCRPROD` | Descrição |
| `unit` | `str` | `CODVOL` | Unidade |
| `reference` | `str \| None` | `REFERENCIA` | Referência |
| `ncm` | `str \| None` | `NCM` | Código NCM |
| `sale_price` | `Decimal \| None` | `VLRVENDA` | Preço de venda |
| `cost_price` | `Decimal \| None` | `VLRCUSTO` | Preço de custo |
| `stock_quantity` | `Decimal \| None` | `ESTOQUE` | Quantidade em estoque |
| `active` | `bool` | `ATIVO` | Ativo |

---

### InvoiceHeader (Cabeçalho de Nota Fiscal)

Representa o cabeçalho de notas fiscais.

```python
from sankhya_sdk.transport_entities import InvoiceHeader
from datetime import date

header = InvoiceHeader()
header.single_number = 12345
header.code_partner = 1
header.movement_date = date.today()
header.code_company = 1
header.code_operation_type = 1001
```

#### Campos

| Campo | Tipo | API | Descrição |
|-------|------|-----|-----------|
| `single_number` | `int` | `NUNOTA` | Número único (chave) |
| `code_partner` | `int` | `CODPARC` | Código do parceiro |
| `code_company` | `int` | `CODEMP` | Código da empresa |
| `code_operation_type` | `int` | `CODTIPOPER` | Tipo de operação |
| `movement_date` | `date` | `DTMOV` | Data de movimento |
| `movement_time` | `timedelta \| None` | `HRMOV` | Hora de movimento |
| `invoice_number` | `int \| None` | `NUMNOTA` | Número da NF |
| `series` | `str \| None` | `SERIENOTA` | Série da NF |
| `total_value` | `Decimal \| None` | `VLRNOTA` | Valor total |
| `status` | `str` | `STATUSNOTA` | Status |
| `pending` | `bool` | `PENDENTE` | Pendente |
| `confirmed` | `bool` | `CONFIRMADA` | Confirmada |

---

### InvoiceItem (Item de Nota Fiscal)

Representa itens de notas fiscais.

```python
from sankhya_sdk.transport_entities import InvoiceItem

item = InvoiceItem()
item.single_number = 12345
item.sequence = 1
item.code_product = 100
item.quantity = 10
item.unit_value = Decimal("99.90")
```

#### Campos

| Campo | Tipo | API | Descrição |
|-------|------|-----|-----------|
| `single_number` | `int` | `NUNOTA` | Número único (chave) |
| `sequence` | `int` | `SEQUENCIA` | Sequência (chave) |
| `code_product` | `int` | `CODPROD` | Código do produto |
| `quantity` | `Decimal` | `QTDNEG` | Quantidade |
| `unit_value` | `Decimal` | `VLRUNIT` | Valor unitário |
| `total_value` | `Decimal \| None` | `VLRTOT` | Valor total |
| `discount` | `Decimal \| None` | `VLRDESC` | Desconto |

---

## Value Objects

### FilterExpression

Expressão de filtro para queries.

```python
from sankhya_sdk.helpers import FilterExpression

# Construção fluente
filter_expr = (
    FilterExpression()
    .equals("CODPARC", 1)
    .and_()
    .greater_than("VLRNOTA", 1000)
    .and_()
    .like("NOMEPARC", "%LTDA%")
)

criteria = filter_expr.build()
# "CODPARC = 1 AND VLRNOTA > 1000 AND NOMEPARC LIKE '%LTDA%'"
```

### EntityQueryOptions

Opções para consultas de entidades.

```python
from sankhya_sdk.helpers import EntityQueryOptions

options = EntityQueryOptions(
    include_fields=["CODPARC", "NOMEPARC"],
    order_by="NOMEPARC ASC",
    max_results=100,
    include_references=True
)
```

---

## Criando Entidades Customizadas

```python
from sankhya_sdk.attributes import entity, entity_key, entity_element
from sankhya_sdk.transport_entities import EntityBase

@entity("Contato", "AD_CONTATO")
class Contato(EntityBase):
    """Entidade customizada para contatos."""
    
    @entity_key("IDCONTATO")
    id_contato: int
    
    @entity_element("CODPARC")
    code_partner: int
    
    @entity_element("NOME")
    nome: str
    
    @entity_element("EMAIL", required=False)
    email: str | None = None
    
    @entity_element("TELEFONE", required=False)
    telefone: str | None = None
```

## Próximos Passos

- [Request Wrappers](request-wrappers.md) - Wrappers de operação
- [Sistema de Entidades](../core-concepts/entity-system.md) - Criação de entidades
- [Helpers](helpers.md) - Utilitários
