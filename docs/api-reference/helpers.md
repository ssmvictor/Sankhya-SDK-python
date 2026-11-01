# Helpers

Documentação dos utilitários e extensões da API XML legada.

## Visão Geral

```python
from sankhya_sdk.helpers import (
    EntityDynamicSerialization,
    EntityQueryOptions,
    GenericServiceEntity,
    LiteralCriteria,
    ServiceRequestExtensions,
    StatusMessageHelper,
    extract_keys,
    get_entity_name,
)
```

---

## EntityQueryOptions

Opções de consulta aceitas por `try_find`, `find`, `find_all` e pelos
métodos `*_with_criteria` do `SimpleCRUDRequestWrapper`, e por
`ServiceRequestExtensions.resolve_with_options`. Modelo Pydantic com
`extra="forbid"`: campos inexistentes lançam `ValidationError`.

### Uso

```python
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

options = EntityQueryOptions(
    max_results=100,
    include_references=False,
    include_presentation_fields=False,
)

partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=True), options)

# Cópias com uma opção alterada
options = options.with_max_results(10).with_references(True, max_depth=2)
```

### Atributos

| Atributo | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `max_results` | `int \| None` (>= 1) | `None` | Limite de linhas (`rowsLimit`) |
| `include_references` | `bool \| None` | `None` | `False` remove as entidades referenciadas da requisição |
| `max_reference_depth` | `int \| None` (0 a 6) | `None` | Profundidade das referências (sem a opção, o `loadRecords` usa o 3º nível) |
| `include_presentation_fields` | `bool \| None` | `None` | Campos de apresentação |
| `use_wildcard_fields` | `bool \| None` | `None` | Usar `*` na lista de campos |
| `timeout` | `timedelta` | 30 minutos | Tempo limite da consulta |

Não há seleção de campos nem ordenação; para isso, monte o `DataSet` à mão
(veja [Queries Avançadas](../examples/advanced-queries.md#requisicao-manual)).

---

## LiteralCriteria

Construtor de expressões de filtro (`sankhya_sdk.helpers.LiteralCriteria`,
porta do `LiteralCriteria` do .NET). Aceito por
`SimpleCRUDRequestWrapper.*_with_criteria` e por
`ServiceRequestExtensions.resolve_with_literal_criteria`. Não confundir com
`sankhya_sdk.models.service.LiteralCriteria`, o modelo do XML
(`expression` e `parameters`).

### Uso Básico

```python
from sankhya_sdk.helpers import LiteralCriteria

# Construção fluente: cada método de fábrica cria um critério, e and_/or_
# combinam dois critérios
criteria = LiteralCriteria.equals("CODPARC", 1).and_(
    LiteralCriteria.greater_than("VLRNOTA", 1000)
)

print(criteria.build_expression())
# CODPARC = 1 AND VLRNOTA > 1000
```

`LiteralCriteria("expressão")` cria um critério com uma expressão livre, e
`str(criteria)` é igual a `build_expression()`.

### Métodos de Comparação

| Método | Exemplo | Expressão |
|--------|---------|-----------|
| `equals(field, value)` | `equals("CODPARC", 1)` | `CODPARC = 1` |
| `not_equals(field, value)` | `not_equals("STATUS", "C")` | `STATUS <> 'C'` |
| `greater_than(field, value)` | `greater_than("VLRNOTA", 1000)` | `VLRNOTA > 1000` |
| `greater_or_equal(field, value)` | `greater_or_equal("ESTOQUE", 10)` | `ESTOQUE >= 10` |
| `less_than(field, value)` | `less_than("ESTOQUE", 10)` | `ESTOQUE < 10` |
| `less_or_equal(field, value)` | `less_or_equal("VLRDESC", 100)` | `VLRDESC <= 100` |
| `like(field, pattern)` | `like("NOMEPARC", "%LTDA%")` | `NOMEPARC LIKE '%LTDA%'` |
| `in_(field, values)` | `in_("CODPARC", [1, 2, 3])` | `CODPARC IN (1, 2, 3)` |
| `between(field, start, end)` | `between("VLRNOTA", 1000, 5000)` | `VLRNOTA BETWEEN 1000 AND 5000` |
| `is_null(field)` | `is_null("EMAIL")` | `EMAIL IS NULL` |
| `is_not_null(field)` | `is_not_null("CGC_CPF")` | `CGC_CPF IS NOT NULL` |

Strings recebem aspas simples (com as aspas internas duplicadas). Os
comparadores numéricos e `between` aceitam apenas números: para datas, use
uma expressão livre com a data no formato do servidor
(`LiteralCriteria(f"DTNEG >= '{data:%d/%m/%Y}'")`).

### Métodos Lógicos

| Método | Resultado |
|--------|-----------|
| `a.and_(b)` | `a AND b` |
| `a.or_(b)` | `(a) OR (b)` |
| `a.not_()` | `NOT (a)` |

```python
from sankhya_sdk.helpers import LiteralCriteria

# Grupo: or_ já coloca parênteses em cada lado
tipo = LiteralCriteria.equals("TIPPESSOA", "F").or_(LiteralCriteria.equals("TIPPESSOA", "J"))

criteria = (
    LiteralCriteria.equals("ATIVO", "S")
    .and_(LiteralCriteria(f"({tipo})"))
    .and_(LiteralCriteria.greater_than("VLRNOTA", 1000))
    .and_(LiteralCriteria.like("NOMEPARC", "%LTDA%"))
)

print(criteria.build_expression())
# ATIVO = 'S' AND ((TIPPESSOA = 'F') OR (TIPPESSOA = 'J')) AND VLRNOTA > 1000 AND NOMEPARC LIKE '%LTDA%'
```

---

## Extensões de Entidade

Funções de `sankhya_sdk.helpers` para inspecionar entidades:

| Função | Retorno | Descrição |
|--------|---------|-----------|
| `get_entity_name(entity_type)` | `str` | Nome da entidade no Sankhya (`@entity`) |
| `extract_keys(entity)` | `EntityResolverResult` | Nome da entidade e chaves preenchidas |
| `get_entity_custom_data(entity_type)` | `dict \| None` | Dados customizados da entidade |
| `get_service_attribute(service)` | `dict \| None` | Atributos do serviço (`ServiceName`) |

```python
from sankhya_sdk.helpers import extract_keys, get_entity_name
from sankhya_sdk.models.transport import Partner

print(get_entity_name(Partner))  # Parceiro

result = extract_keys(Partner(code=1))
print(result.name)  # Parceiro
print(result.keys)  # [{'name': 'CODPARC', 'value': '1'}]
```

!!! warning "Funções de consulta incompletas"
    `query`, `query_with_criteria`, `query_with_options`, `query_light`,
    `update_on_demand` e `remove_on_demand` de `sankhya_sdk.helpers` são
    implementações mínimas: as funções `query*` devolvem a própria entidade
    de exemplo, sem consultar o servidor, e `update_on_demand` /
    `remove_on_demand` apenas guardam a entidade numa fila em memória. Use o
    [`PagedRequestWrapper`](request-wrappers.md#pagedrequestwrapper) e a
    [`OnDemandRequestFactory`](request-wrappers.md#ondemandrequestwrapper).

---

## StatusMessageHelper

Traduz a `statusMessage` de uma resposta com erro na exceção
correspondente (porta do `StatusMessageHelper` do .NET). É chamado pelo
`SankhyaWrapper` para toda resposta com `status="0"`; a mensagem já chega
decodificada de Base64 (`response.status_message_text`).

```python
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.exceptions import ServiceRequestDeadlockException
from sankhya_sdk.helpers import StatusMessageHelper
from sankhya_sdk.models.service import ServiceRequest, ServiceResponse

xml = (
    '<serviceResponse serviceName="CRUDServiceProvider.saveRecord" status="0">'
    "<statusMessage><![CDATA[VHJhbnNhY3Rpb24gd2FzIGRlYWRsb2NrZWQ=]]></statusMessage>"
    "</serviceResponse>"
)
response = ServiceResponse.from_xml_string(xml)
print(response.status_message_text)  # Transaction was deadlocked

request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
try:
    StatusMessageHelper.process_status_message(
        ServiceName.CRUD_SERVICE_SAVE, request, response
    )
except ServiceRequestDeadlockException as e:
    print(f"Deadlock: {e}")
```

`process_status_message(service, request, response)` não retorna nada:
quando a mensagem corresponde a um trecho ou padrão conhecido, lança a
exceção (tabela em [Exceções](exceptions.md#como-o-sdk-escolhe-a-excecao)).
Também exporta os padrões `PROPERTY_VALUE_ERROR_PATTERN`,
`PROPERTY_NAME_ERROR_PATTERN`, `REFERENCE_FIELDS_FIRST_LEVEL_PATTERN` e
`REFERENCE_FIELDS_SECOND_LEVEL_PATTERN`.

---

## ServiceRequestExtensions

Preenche o corpo de um `ServiceRequest` a partir de entidades (porta das
extensões `Resolve` do .NET). Todos os métodos são estáticos, alteram a
requisição e retornam `None`. O formato do corpo depende do serviço
(`CRUD_SERVICE_FIND`/`SAVE`/`REMOVE`, `CRUD_FIND`...).

| Método | Descrição |
|--------|-----------|
| `resolve_generic(request, entity_type)` | Campos e referências do tipo, sem critério |
| `resolve_with_entity(request, entity, max_reference_level=FOURTH)` | Critério (busca) ou chaves e campos (gravação/remoção) a partir dos campos preenchidos |
| `resolve_with_literal_criteria(request, entity_type, criteria)` | Busca com um `LiteralCriteria` |
| `resolve_with_options(request, entity, options)` | Como `resolve_with_entity`, aplicando um `EntityQueryOptions` |
| `resolve_with_collection(request, entities)` / `resolve_with_entities` | Várias entidades numa requisição (lote) |

```python
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import (
    EntityQueryOptions,
    LiteralCriteria,
    ServiceRequestExtensions,
)
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

# Busca com critério literal
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_literal_criteria(
    request, Partner, LiteralCriteria("CODPARC > 0")
)

# Busca a partir de uma entidade de exemplo, com opções
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_options(
    request, Partner(is_active=True), EntityQueryOptions(max_results=100)
)

# Gravação: chave em <key>, campos preenchidos em <localFields>
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
ServiceRequestExtensions.resolve_with_entity(
    request, Partner(code=1, email_address="novo@email.com")
)
print(request.to_xml_string())
```

---

## GenericServiceEntity

Classe base abstrata (Pydantic) para entidades de serviço com serialização
XML a partir dos metadados dos campos (`entity_key`, `entity_element`...).
Herde dela e use `to_xml()`, `to_xml_string()` e `from_xml_string()`:

```python
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.helpers import GenericServiceEntity


@entity("MinhaEntidade")
class MinhaEntidade(GenericServiceEntity):
    code: Optional[int] = entity_key(entity_element("CODIGO", default=None))
    name: Optional[str] = entity_element("NOME", default=None)


item = MinhaEntidade(code=1, name="Teste")
print(item.to_xml_string())
# <MinhaEntidade><CODIGO>1</CODIGO><NOME>Teste</NOME></MinhaEntidade>
```

As entidades de `sankhya_sdk.models.transport` usam outra base
(`TransportEntityBase`); veja [Sistema de Entidades](../core-concepts/entity-system.md).

---

## EntityDynamicSerialization

Converte os dados dinâmicos de uma resposta (nome do campo no Sankhya ->
texto) para entidades tipadas, como o `EntityDynamicSerialization` do .NET.
As entidades das respostas (`ServiceResponse.entities`, `EntityDynamic`)
trazem os valores como **texto bruto**; a conversão para `int`, `bool`,
`datetime`, enums e referências é feita por `convert_to_type`:

```python
from sankhya_sdk.helpers import EntityDynamicSerialization
from sankhya_sdk.models.transport import Partner

data = {"CODPARC": "1", "NOMEPARC": "Parceiro", "ATIVO": "S", "DTCAD": "01/02/2024 10:00:00"}

partner = EntityDynamicSerialization(data).convert_to_type(Partner)
print(partner.code, partner.is_active, partner.date_created)
# 1 True 2024-02-01 10:00:00
```

| Método | Descrição |
|--------|-----------|
| `EntityDynamicSerialization(data=None, key_filter="none")` | Envolve o dicionário (`key_filter`: `"uppercase"`, `"lowercase"` ou `"none"`, aplicado em `to_dict`) |
| `convert_to_type(entity_type)` | Converte para a entidade tipada |
| `get_member(name)` / `set_member(name, value)` | Lê/altera um valor |
| `change_keys(metadata)` | Renomeia as chaves `f0..fN` com os nomes de um `Metadata` |
| `to_dict()` | Dicionário com o filtro de chaves aplicado |

Para uma resposta do `loadRecords`, use
`EntityDynamicSerialization(dict(entity.fields)).convert_to_type(Partner)`
para cada item de `response.entities` (veja
[Queries Avançadas](../examples/advanced-queries.md#requisicao-manual)).

## Próximos Passos

- [Validações](validations.md) - Validação de entidades
- [Request Wrappers](request-wrappers.md) - Wrappers de operação
- [Exemplos](../examples/index.md) - Exemplos práticos
