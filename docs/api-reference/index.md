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
| `SankhyaContext` | `sankhya_sdk` / `sankhya_sdk.core` | Gerenciador de contexto e sessões (XML legado) |
| `SankhyaWrapper` | `sankhya_sdk` / `sankhya_sdk.core` | Cliente de uma sessão da API XML |
| `SankhyaSettings` | `sankhya_sdk.config` | Configurações `SANKHYA_*` |
| `SessionInfo` | `sankhya_sdk.core.types` | Informações da sessão |
| `ServiceFile` | `sankhya_sdk.core.types` | Arquivo de download |
| `SimpleCRUDRequestWrapper` | `sankhya_sdk.request_wrappers` | Operações CRUD |
| `PagedRequestWrapper` | `sankhya_sdk.request_wrappers` | Consultas paginadas |
| `OnDemandRequestWrapper` / `OnDemandRequestFactory` | `sankhya_sdk.request_wrappers` | Processamento em lote |
| `KnowServicesRequestWrapper` | `sankhya_sdk.request_wrappers` | Serviços específicos |
| `EntityValidator` | `sankhya_sdk.validations` | Validação da estrutura de classes de entidade |
| `Partner`, `Product`, `InvoiceHeader` | `sankhya_sdk.models.transport` | Entidades de transporte |
| `ServiceRequest` | `sankhya_sdk.models.service` | Modelo de requisição |
| `ServiceResponse` | `sankhya_sdk.models.service` | Modelo de resposta |
| `LiteralCriteria`, `EntityQueryOptions` | `sankhya_sdk.helpers` | Filtros e opções de consulta |

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
from sankhya_sdk import SankhyaContext, SankhyaWrapper
from sankhya_sdk.config import SankhyaSettings

# Request Wrappers
from sankhya_sdk.request_wrappers import (
    SimpleCRUDRequestWrapper,
    PagedRequestWrapper,
    OnDemandRequestFactory,
    OnDemandRequestWrapper,
    KnowServicesRequestWrapper,
)

# Entidades e modelos de serviço
from sankhya_sdk.models.transport import (
    Partner,
    Product,
    InvoiceHeader,
)
from sankhya_sdk.models.service import ServiceRequest, ServiceResponse

# Exceções
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestGeneralException,
    ServiceRequestInvalidAuthorizationException,
)

# Validações
from sankhya_sdk.validations import EntityValidator

# Helpers
from sankhya_sdk.helpers import (
    EntityQueryOptions,
    LiteralCriteria,
    ServiceRequestExtensions,
)
```

## Mudanças de Comportamento (API XML legada)

Comportamentos da API XML legada alinhados ao SDK .NET nesta versão:

| Mudança | Detalhes |
|---------|----------|
| `SimpleCRUDRequestWrapper.initialize(ctx)` adquire uma sessão dedicada (`SIMPLE_CRUD`, um login extra), como `AcquireNewSession(SimpleCrud)` no .NET | [Request Wrappers](request-wrappers.md#ciclo-de-vida) |
| `initialize()` sem contexto (`SimpleCRUDRequestWrapper` e `KnowServicesRequestWrapper`) cria um contexto próprio, e `dispose()` encerra também a sessão principal dele | [Request Wrappers](request-wrappers.md#ciclo-de-vida) |
| `KnowServicesRequestWrapper.initialize(ctx)` continua usando a sessão principal do contexto (divergência conhecida do .NET) | [Request Wrappers](request-wrappers.md#knowservicesrequestwrapper) |
| As entidades das respostas (`EntityDynamic`) trazem os valores como texto bruto; a conversão de tipos é feita por `EntityDynamicSerialization.convert_to_type` | [Helpers](helpers.md#entitydynamicserialization) |
| Campos `entity_ignore` ficam fora de `model_dump()`/`model_dump_json()` | [Modelos](models.md#transportentitybase) |
| `SankhyaContext.__del__` não faz mais `dispose()` (como `~SankhyaContext() => Dispose(false)`): use `with`/`async with` ou `dispose()` | [Core](core.md#ciclo-de-vida) |
| `SankhyaContext.dispose()` finaliza antes os wrappers da `OnDemandRequestFactory`; os assíncronos são aguardados por `async with ctx:` | [Request Wrappers](request-wrappers.md#descarte-pelo-contexto) |
| Os atrasos de retry são lineares (`tentativa × RequestRetryDelay`; ex.: 15, 30 e 45 s em deadlock) | [Tratamento de Erros](../core-concepts/error-handling.md#atrasos-entre-tentativas) |
| A `statusMessage` é decodificada de Base64, e as mensagens do servidor viram as exceções específicas (deadlock, timeout, sessão duplicada...) | [Exceções](exceptions.md#como-o-sdk-escolhe-a-excecao) |
| `OnDemandRequestFailureEvent.is_update` é `True` só para `CRUD_SERVICE_SAVE` (como no .NET) | [Eventos](events.md#ondemandrequestfailureevent) |
| O `flush()` on-demand aguarda as entidades adicionadas antes da chamada, inclusive um lote em envio; na thread worker apenas solicita o envio | [Request Wrappers](request-wrappers.md#flush) |
| `KnowServicesRequestWrapper.get_image(entidade)` / `get_image_async` recebem a entidade e retornam `ServiceFile` | [Request Wrappers](request-wrappers.md#metodos-de-arquivoimagem) |
