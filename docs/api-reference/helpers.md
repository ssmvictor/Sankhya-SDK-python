# Helpers

Documentação dos utilitários e extensões do SDK.

## Visão Geral

```python
from sankhya_sdk.helpers import (
    EntityExtensions,
    EntityQueryOptions,
    FilterExpression,
    StatusMessageHelper,
    ServiceRequestExtensions,
)
```

---

## EntityQueryOptions

Opções para consultas de entidades.

### Uso

```python
from sankhya_sdk.helpers import EntityQueryOptions

options = EntityQueryOptions(
    include_fields=["CODPARC", "NOMEPARC", "CGC_CPF"],
    exclude_fields=["SENHA"],
    order_by="NOMEPARC ASC",
    max_results=100,
    include_references=True
)

partners = crud.find_with_options(Partner, "ATIVO = 'S'", options)
```

### Atributos

| Atributo | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `include_fields` | `list[str] \| None` | `None` | Campos a incluir |
| `exclude_fields` | `list[str] \| None` | `None` | Campos a excluir |
| `order_by` | `str \| None` | `None` | Ordenação |
| `max_results` | `int` | `0` | Limite de resultados |
| `include_references` | `bool` | `False` | Incluir referências |
| `distinct` | `bool` | `False` | Resultados distintos |

---

## FilterExpression

Construtor fluente de filtros.

### Uso Básico

```python
from sankhya_sdk.helpers import FilterExpression

# Construção fluente
filter_expr = (
    FilterExpression()
    .equals("CODPARC", 1)
    .and_()
    .greater_than("VLRNOTA", 1000)
)

criteria = filter_expr.build()
# "CODPARC = 1 AND VLRNOTA > 1000"
```

### Métodos de Comparação

#### `equals(field, value) -> FilterExpression`

Igualdade.

```python
filter_expr.equals("CODPARC", 1)
# CODPARC = 1
```

#### `not_equals(field, value) -> FilterExpression`

Diferença.

```python
filter_expr.not_equals("STATUS", "C")
# STATUS <> 'C'
```

#### `greater_than(field, value) -> FilterExpression`

Maior que.

```python
filter_expr.greater_than("VLRNOTA", 1000)
# VLRNOTA > 1000
```

#### `greater_or_equal(field, value) -> FilterExpression`

Maior ou igual.

```python
filter_expr.greater_or_equal("DTMOV", date(2024, 1, 1))
# DTMOV >= '01/01/2024'
```

#### `less_than(field, value) -> FilterExpression`

Menor que.

```python
filter_expr.less_than("ESTOQUE", 10)
# ESTOQUE < 10
```

#### `less_or_equal(field, value) -> FilterExpression`

Menor ou igual.

```python
filter_expr.less_or_equal("VLRDESC", 100)
# VLRDESC <= 100
```

#### `like(field, pattern) -> FilterExpression`

Padrão LIKE.

```python
filter_expr.like("NOMEPARC", "%LTDA%")
# NOMEPARC LIKE '%LTDA%'
```

#### `in_(field, values) -> FilterExpression`

Lista de valores.

```python
filter_expr.in_("CODPARC", [1, 2, 3])
# CODPARC IN (1, 2, 3)
```

#### `between(field, start, end) -> FilterExpression`

Intervalo.

```python
filter_expr.between("DTMOV", date(2024, 1, 1), date(2024, 12, 31))
# DTMOV BETWEEN '01/01/2024' AND '31/12/2024'
```

#### `is_null(field) -> FilterExpression`

Valor nulo.

```python
filter_expr.is_null("EMAIL")
# EMAIL IS NULL
```

#### `is_not_null(field) -> FilterExpression`

Valor não nulo.

```python
filter_expr.is_not_null("CGC_CPF")
# CGC_CPF IS NOT NULL
```

### Métodos Lógicos

#### `and_() -> FilterExpression`

Operador AND.

```python
filter_expr.equals("A", 1).and_().equals("B", 2)
# A = 1 AND B = 2
```

#### `or_() -> FilterExpression`

Operador OR.

```python
filter_expr.equals("A", 1).or_().equals("B", 2)
# A = 1 OR B = 2
```

#### `group_start() -> FilterExpression`

Inicia grupo.

```python
filter_expr.group_start().equals("A", 1).or_().equals("B", 2).group_end()
# (A = 1 OR B = 2)
```

#### `group_end() -> FilterExpression`

Finaliza grupo.

### Exemplo Complexo

```python
filter_expr = (
    FilterExpression()
    .equals("ATIVO", "S")
    .and_()
    .group_start()
        .equals("TIPPESSOA", "C")
        .or_()
        .equals("TIPPESSOA", "A")
    .group_end()
    .and_()
    .greater_than("VLRNOTA", 1000)
    .and_()
    .like("NOMEPARC", "%LTDA%")
)

# ATIVO = 'S' AND (TIPPESSOA = 'C' OR TIPPESSOA = 'A') AND VLRNOTA > 1000 AND NOMEPARC LIKE '%LTDA%'
```

---

## EntityExtensions

Utilitários para manipulação de entidades.

### Métodos

#### `extract_keys(entity) -> dict`

Extrai valores das chaves.

```python
from sankhya_sdk.helpers import EntityExtensions

partner = Partner()
partner.code_partner = 1

keys = EntityExtensions.extract_keys(partner)
# {"CODPARC": 1}
```

#### `is_update_operation(entity) -> bool`

Verifica se é atualização.

```python
is_update = EntityExtensions.is_update_operation(partner)
# True se entidade tem chaves preenchidas
```

#### `clone(entity) -> EntityBase`

Clona uma entidade.

```python
cloned = EntityExtensions.clone(partner)
```

#### `get_changed_fields(original, modified) -> list[str]`

Lista campos alterados.

```python
changes = EntityExtensions.get_changed_fields(original, modified)
# ["email", "phone"]
```

---

## StatusMessageHelper

Utilitário para interpretar mensagens de status.

### Uso

```python
from sankhya_sdk.helpers import StatusMessageHelper

message = "E|100|Registro não encontrado|Detalhes adicionais"
parsed = StatusMessageHelper.parse(message)

print(parsed.type)      # "ERROR"
print(parsed.code)      # "100"
print(parsed.message)   # "Registro não encontrado"
print(parsed.details)   # "Detalhes adicionais"
```

### Estrutura Parsed

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `type` | `str` | Tipo (ERROR/WARNING/INFO) |
| `code` | `str` | Código interno |
| `message` | `str` | Mensagem principal |
| `details` | `str \| None` | Detalhes adicionais |

### Métodos

#### `is_error(message) -> bool`

Verifica se é erro.

```python
if StatusMessageHelper.is_error(status_message):
    handle_error()
```

#### `is_warning(message) -> bool`

Verifica se é aviso.

```python
if StatusMessageHelper.is_warning(status_message):
    log_warning()
```

---

## ServiceRequestExtensions

Utilitários para requisições.

### Métodos

#### `apply_options_to_request(request, options) -> ServiceRequest`

Aplica opções a uma requisição.

```python
from sankhya_sdk.helpers import ServiceRequestExtensions, EntityQueryOptions

options = EntityQueryOptions(max_results=100)
request = ServiceRequestExtensions.apply_options_to_request(request, options)
```

#### `build_criteria_request(entity_type, criteria) -> ServiceRequest`

Constrói requisição de busca.

```python
request = ServiceRequestExtensions.build_criteria_request(
    Partner,
    "CODPARC > 0"
)
```

---

## GenericServiceEntity

Entidade genérica para serviços.

### Uso

```python
from sankhya_sdk.helpers import GenericServiceEntity

# Para chamadas de serviço genéricas
entity = GenericServiceEntity("MeuServico")
entity.set_field("CAMPO1", "valor1")
entity.set_field("CAMPO2", 123)

xml = entity.to_xml()
```

---

## EntityDynamicSerialization

Serialização dinâmica de entidades.

### Métodos

#### `serialize(entity) -> Element`

Serializa entidade para XML.

```python
from sankhya_sdk.helpers import EntityDynamicSerialization

xml = EntityDynamicSerialization.serialize(partner)
```

#### `deserialize(xml, entity_type) -> EntityBase`

Deserializa XML para entidade.

```python
partner = EntityDynamicSerialization.deserialize(xml, Partner)
```

#### `serialize_list(entities) -> Element`

Serializa lista de entidades.

```python
xml = EntityDynamicSerialization.serialize_list(partners)
```

#### `deserialize_list(xml, entity_type) -> list[EntityBase]`

Deserializa lista de entidades.

```python
partners = EntityDynamicSerialization.deserialize_list(xml, Partner)
```

## Próximos Passos

- [Validações](validations.md) - Validação de entidades
- [Request Wrappers](request-wrappers.md) - Wrappers de operação
- [Exemplos](../examples/index.md) - Exemplos práticos
