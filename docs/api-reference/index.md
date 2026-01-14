# Referência da API

Documentação completa da API do Sankhya SDK Python.

## Módulos

<div class="grid cards" markdown>

-   :material-key:{ .lg .middle } __Autenticação__

    ---

    OAuth2, TokenManager e exceções de autenticação.

    [:octicons-arrow-right-24: Auth](auth.md)

-   :material-api:{ .lg .middle } __Gateway Client__

    ---

    Cliente moderno para API JSON Gateway.

    [:octicons-arrow-right-24: Gateway Client](gateway-client.md)

-   :material-bell:{ .lg .middle } __Eventos__

    ---

    Sistema de eventos (EventBus, OnDemandRequestFailureEvent).

    [:octicons-arrow-right-24: Eventos](events.md)

-   :material-database-check:{ .lg .middle } __DTOs__

    ---

    Modelos Pydantic para validação e serialização.

    [:octicons-arrow-right-24: DTOs](dtos.md)

-   :material-swap-horizontal-bold:{ .lg .middle } __Adapters__

    ---

    Compatibilidade com integrações XML legadas.

    [:octicons-arrow-right-24: Adapters](adapters.md)

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
| `OAuthClient` | `sankhya_sdk.auth` | Cliente OAuth2 para autenticação |
| `TokenManager` | `sankhya_sdk.auth` | Gerenciador de tokens thread-safe |
| `GatewayClient` | `sankhya_sdk.http` | Cliente para API JSON Gateway |
| `GatewayModule` | `sankhya_sdk.http` | Enum de módulos (MGE, MGECOM) |
| `EventBus` | `sankhya_sdk.events` | Barramento de eventos singleton |
| `ParceiroDTO` | `sankhya_sdk.models.dtos` | DTO para parceiros |
| `NotaDTO` | `sankhya_sdk.models.dtos` | DTO para notas fiscais |
| `MovimentoDTO` | `sankhya_sdk.models.dtos` | DTO para movimentos financeiros |
| `ProdutoDTO` | `sankhya_sdk.models.dtos` | DTO para produtos |
| `XmlAdapter` | `sankhya_sdk.adapters` | Conversor XML ↔ JSON |
| `SankhyaContext` | `sankhya_sdk.core` | Gerenciador de contexto e sessões |
| `SankhyaWrapper` | `sankhya_sdk.core` | Cliente de alto nível para API |
| `SessionInfo` | `sankhya_sdk.core.types` | Informações da sessão |
| `ServiceFile` | `sankhya_sdk.core.types` | Arquivo de download |
| `SimpleCRUDRequestWrapper` | `sankhya_sdk.request_wrappers` | Operações CRUD |
| `PagedRequestWrapper` | `sankhya_sdk.request_wrappers` | Consultas paginadas |
| `OnDemandRequestWrapper` | `sankhya_sdk.request_wrappers` | Processamento em lote |
| `KnowServicesRequestWrapper` | `sankhya_sdk.request_wrappers` | Serviços específicos |
| `EntityValidator` | `sankhya_sdk.validations` | Validação de entidades |
| `ServiceRequest` | `sankhya_sdk.service_models` | Modelo de requisição |
| `ServiceResponse` | `sankhya_sdk.service_models` | Modelo de resposta |

## Importação Rápida

```python
# Autenticação OAuth2 (Recomendado)
from sankhya_sdk.auth import OAuthClient, TokenManager
from sankhya_sdk.auth import AuthError, TokenExpiredError, AuthNetworkError

# Gateway (Recomendado para novos projetos)
from sankhya_sdk.http import GatewayClient, GatewayModule
from sankhya_sdk.models.dtos import (
    ParceiroDTO, ParceiroCreateDTO,
    NotaDTO, NotaCabecalhoDTO, NotaItemDTO,
    MovimentoDTO,
    ProdutoDTO,
)
from sankhya_sdk.adapters import XmlAdapter

# Eventos
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent

# Exceções HTTP
from sankhya_sdk.exceptions import (
    SankhyaHttpError,
    SankhyaAuthError,
    SankhyaForbiddenError,
    SankhyaNotFoundError,
    SankhyaClientError,
    SankhyaServerError,
)

# Core Types
from sankhya_sdk.core.types import SessionInfo, ServiceFile, ServiceAttribute

# Principais (Legado)
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
