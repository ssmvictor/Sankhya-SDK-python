# Helpers Module

Este módulo fornece interfaces, dataclasses, extensões e utilitários para manipulação de entidades e requisições de serviço no Sankhya SDK.

## Visão Geral

O módulo helpers foi migrado do SDK .NET e inclui:

| Componente | Tipo | Descrição |
|------------|------|-----------|
| `IFilterExpression` | Protocol | Interface para expressões de filtro |
| `EntityQueryOptions` | Dataclass | Opções de configuração para queries |
| `StatusMessageHelper` | Classe | Processamento de mensagens de erro |
| `EntityExtensions` | Funções | Utilitários para entidades |
| `ServiceRequestExtensions` | Classe | Resolução de requests |
| `GenericServiceEntity` | ABC | Serialização XML de entidades |
| `EntityDynamicSerialization` | Classe | Conversão dinâmica de tipos |

## Uso Básico

### IFilterExpression

```python
from sankhya_sdk.helpers import IFilterExpression

class MyFilter:
    def build_expression(self) -> str:
        return "CODPARC = 123 AND ATIVO = 'S'"

filter = MyFilter()
expression = filter.build_expression()
```

### EntityQueryOptions

```python
from datetime import timedelta
from sankhya_sdk.helpers import EntityQueryOptions

# Valores padrão (30 min timeout)
options = EntityQueryOptions()

# Personalizado
options = EntityQueryOptions(
    max_results=100,
    include_references=True,
    max_reference_depth=3,
    timeout=timedelta(minutes=5),
)

# Fluent API
options = EntityQueryOptions().with_max_results(50).with_references(True)
```

### StatusMessageHelper

```python
from sankhya_sdk.helpers import StatusMessageHelper

# Processa mensagem de status e lança exceção apropriada
StatusMessageHelper.process_status_message(service, request, response)
```

### EntityExtensions

```python
from sankhya_sdk.helpers import extract_keys

# Extrai chaves primárias de uma entidade
result = extract_keys(partner)
print(result.keys)  # [{'name': 'CODPARC', 'value': '123'}]
```

### ServiceRequestExtensions

```python
from sankhya_sdk.helpers import ServiceRequestExtensions, resolve
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.enums import ServiceName

request = ServiceRequest(ServiceName.CRUD_SERVICE_FIND)

# Resolve baseado no tipo da entidade
ServiceRequestExtensions.resolve_generic(request, Partner)

# Ou usando função de conveniência
resolve(request, Partner)
```

### GenericServiceEntity

```python
from sankhya_sdk.helpers import GenericServiceEntity

class MyEntity(GenericServiceEntity):
    code: int
    name: str

entity = MyEntity(code=1, name="Test")
xml = entity.to_xml_string()
```

### EntityDynamicSerialization

```python
from sankhya_sdk.helpers import EntityDynamicSerialization

data = {"CODPARC": "123", "NOMEPARC": "Test"}
serializer = EntityDynamicSerialization(data)
partner = serializer.convert_to_type(Partner)
```

## Comparação .NET vs Python

| .NET | Python |
|------|--------|
| `IFilterExpression` interface | `IFilterExpression` Protocol |
| `EntityQueryOptions` class | `EntityQueryOptions` Pydantic model |
| `TimeSpan` | `timedelta` |
| Extension methods | Funções standalone ou métodos estáticos |
| `ReferenceLevel` enum | `ReferenceLevel` MetadataEnum |
| `XmlSerializer` | `lxml.etree` |
| `IEntity` | `EntityBase` |

## Propriedades de EntityQueryOptions

| Propriedade | Tipo | Padrão | Descrição |
|-------------|------|--------|-----------|
| `max_results` | `Optional[int]` | `None` | Limite de resultados |
| `include_references` | `Optional[bool]` | `None` | Incluir referências |
| `max_reference_depth` | `Optional[int]` | `None` | Profundidade máxima |
| `include_presentation_fields` | `Optional[bool]` | `None` | Campos de apresentação |
| `use_wildcard_fields` | `Optional[bool]` | `None` | Usar wildcard (*) |
| `timeout` | `timedelta` | 30 min | Tempo limite |

## Dependências Futuras

Algumas funções dependem de componentes que serão implementados em fases futuras:

- `query()`, `query_with_criteria()`, `query_light()` → `PagedRequestWrapper`
- `update_on_demand()`, `remove_on_demand()` → `OnDemandRequestFactory`

Essas funções atualmente lançam `NotImplementedError` e serão habilitadas quando as dependências forem implementadas.
