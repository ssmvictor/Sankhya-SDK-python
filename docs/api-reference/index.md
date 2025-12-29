# Referência da API

Documentação completa da API do Sankhya SDK Python.

## Módulos

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } __Core__

    ---

    Classes principais: `SankhyaContext`, `SankhyaWrapper`, configurações.

    [:octicons-arrow-right-24: Core](core.md)

-   :material-format-list-bulleted-type:{ .lg .middle } __Enumerações__

    ---

    Enums para tipos, status e configurações da API.

    [:octicons-arrow-right-24: Enums](enums.md)

-   :material-alert:{ .lg .middle } __Exceções__

    ---

    Hierarquia de exceções do SDK.

    [:octicons-arrow-right-24: Exceções](exceptions.md)

-   :material-database:{ .lg .middle } __Modelos__

    ---

    Modelos de serviço e entidades de transporte.

    [:octicons-arrow-right-24: Modelos](models.md)

-   :material-swap-horizontal:{ .lg .middle } __Request Wrappers__

    ---

    Wrappers de alto nível para operações.

    [:octicons-arrow-right-24: Wrappers](request-wrappers.md)

-   :material-wrench:{ .lg .middle } __Helpers__

    ---

    Utilitários e extensões.

    [:octicons-arrow-right-24: Helpers](helpers.md)

-   :material-check-circle:{ .lg .middle } __Validações__

    ---

    Validadores de entidades.

    [:octicons-arrow-right-24: Validações](validations.md)

</div>

## Sumário Rápido

| Classe | Módulo | Descrição |
|--------|--------|-----------|
| `SankhyaContext` | `sankhya_sdk.core` | Gerenciador de contexto e sessões |
| `SankhyaWrapper` | `sankhya_sdk.core` | Cliente de alto nível para API |
| `SimpleCRUDRequestWrapper` | `sankhya_sdk.request_wrappers` | Operações CRUD |
| `PagedRequestWrapper` | `sankhya_sdk.request_wrappers` | Consultas paginadas |
| `OnDemandRequestWrapper` | `sankhya_sdk.request_wrappers` | Processamento em lote |
| `KnowServicesRequestWrapper` | `sankhya_sdk.request_wrappers` | Serviços específicos |
| `EntityValidator` | `sankhya_sdk.validations` | Validação de entidades |
| `ServiceRequest` | `sankhya_sdk.service_models` | Modelo de requisição |
| `ServiceResponse` | `sankhya_sdk.service_models` | Modelo de resposta |

## Importação Rápida

```python
# Principais
from sankhya_sdk import SankhyaContext, SankhyaSettings

# Request Wrappers
from sankhya_sdk.request_wrappers import (
    SimpleCRUDRequestWrapper,
    PagedRequestWrapper,
    OnDemandRequestWrapper,
    KnowServicesRequestWrapper,
)

# Entidades
from sankhya_sdk.transport_entities import (
    Partner,
    Product,
    InvoiceHeader,
)

# Exceções
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestException,
    ServiceRequestInvalidAuthorizationException,
)

# Validações
from sankhya_sdk.validations import EntityValidator

# Helpers
from sankhya_sdk.helpers import (
    EntityQueryOptions,
    FilterExpression,
)
```
