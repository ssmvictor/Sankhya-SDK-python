# Core

Documentação das classes principais da API XML legada: `SankhyaContext`,
`SankhyaWrapper` e `SankhyaSettings`.

```python
from sankhya_sdk import SankhyaContext, SankhyaWrapper
from sankhya_sdk.config import SankhyaSettings
```

## SankhyaContext

Gerenciador central de contexto e sessões, porta do `SankhyaContext` do SDK
.NET. Cada contexto tem uma **sessão principal** (o `SankhyaWrapper`
autenticado) e pode adquirir sessões adicionais, identificadas por tokens
UUID num registro de classe compartilhado.

### Uso Básico

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_entity(request, Partner(code=1))

# Com context manager (recomendado): o with entrega o SankhyaWrapper
# da sessão principal e chama dispose() na saída
with SankhyaContext.from_settings() as wrapper:
    response = wrapper.service_invoker(request)

# Sem context manager
ctx = SankhyaContext.from_settings()
try:
    response = ctx.service_invoker(request)
finally:
    ctx.dispose()
```

!!! warning "O `with` entrega o wrapper, não o contexto"
    `__enter__` e `__aenter__` retornam o `SankhyaWrapper` principal. Quando
    precisar do contexto dentro do bloco (ex.: para
    `SimpleCRUDRequestWrapper.initialize(ctx)`), guarde-o numa variável antes:
    `ctx = SankhyaContext.from_settings()` e depois `with ctx:`.

### Construção

#### `SankhyaContext(wrapper=None, *, host=None, port=None, username=None, password=None)`

Recebe um `SankhyaWrapper` (autenticado ou não) ou os dados de conexão, com
os quais cria e autentica o wrapper. Sem nenhum dos dois, lança
`ValueError`.

#### `from_settings(settings: SankhyaSettings | None = None) -> SankhyaContext`

Cria e autentica o wrapper com `SankhyaWrapper.from_settings(settings)`
(variáveis `SANKHYA_*` / `.env` quando `settings` é `None`). Credenciais
recusadas lançam `ServiceRequestInvalidCredentialsException`.

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.config import SankhyaSettings

# Usa variáveis de ambiente
ctx = SankhyaContext.from_settings()
ctx.dispose()

# Usa configurações personalizadas (campos pelos nomes das variáveis)
settings = SankhyaSettings(
    SANKHYA_URL="http://sankhya.example.com",
    SANKHYA_PORT=8180,
    SANKHYA_USERNAME="usuario",
    SANKHYA_PASSWORD="senha",
)
ctx = SankhyaContext.from_settings(settings)
ctx.dispose()
```

### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `token` | `uuid.UUID` | Token da sessão principal |
| `wrapper` | `SankhyaWrapper` | Wrapper da sessão principal |
| `user_name` | `str` | Usuário autenticado |
| `user_code` | `int` | Código do usuário (`0` se não autenticado) |
| `environment` | `ServiceEnvironment` | Ambiente (pela porta: 8180 produção, 8280 homologação, 8380 treinamento) |
| `database_name` | `str` | Nome do banco do ambiente |

### Sessões

#### `acquire_new_session(request_type=ServiceRequestType.DEFAULT) -> UUID`

Cria um novo `SankhyaWrapper` com as credenciais, o timeout e o número de
tentativas da sessão principal, autentica (um login extra), registra e
retorna o token. Sessões `ON_DEMAND_CRUD` são rastreadas pelo contexto.

#### `finalize_session(token: UUID) -> None`

Faz logout da sessão e a remove do registro.

#### `detach_on_demand_request_wrapper(token: UUID) -> None`

Finaliza uma sessão on-demand e deixa de rastreá-la (usado pelos wrappers
on-demand quando o worker termina).

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName, ServiceRequestType
from sankhya_sdk.models.service import ServiceRequest

ctx = SankhyaContext.from_settings()
try:
    token = ctx.acquire_new_session(ServiceRequestType.DEFAULT)
    try:
        request = ServiceRequest(service=ServiceName.SESSION_GET_ALL)
        response = SankhyaContext.service_invoker_with_token(request, token)
    finally:
        ctx.finalize_session(token)
finally:
    ctx.dispose()
```

### Invocação de Serviços

| Método | Sessão |
|--------|--------|
| `ctx.service_invoker(request)` / `await ctx.service_invoker_async(request)` | Principal |
| `SankhyaContext.service_invoker_with_token(request, token)` | A do token (método estático) |
| `await SankhyaContext.service_invoker_async_with_token(request, token)` | A do token (método estático) |

Todos retornam um `ServiceResponse`; erros do servidor viram exceções (veja
[Exceções](exceptions.md)). Um token desconhecido lança `ValueError`.

### Arquivos e Imagens

| Método | Retorno |
|--------|---------|
| `ctx.get_file(key)` / `get_file_async(key)` | `ServiceFile` (sessão principal) |
| `ctx.get_image(entity, keys)` / `get_image_async(entity, keys)` | `ServiceFile \| None` (sessão principal) |
| `SankhyaContext.get_file_with_token(key, token)` / `get_file_async_with_token` | `ServiceFile` |
| `SankhyaContext.get_image_with_token(entity, keys, token)` / `get_image_async_with_token` | `ServiceFile \| None` |

Veja [Operações com Arquivos](../examples/file-operations.md).

### Ciclo de Vida

#### `dispose() -> None`

Finaliza as sessões e libera os recursos. Idempotente.

- Com sessões on-demand, finaliza antes **todos** os wrappers do
  `OnDemandRequestFactory` (como o .NET), para que enviem o restante da fila.
- Depois encerra **todas** as sessões do registro de classe, inclusive as de
  outros contextos (como o `Dispose` do .NET), e por último a principal.
- `AsyncOnDemandRequestWrapper`s não são aguardados: use `async with ctx:`,
  cuja saída aguarda `AsyncOnDemandRequestFactory.finalize_all()` antes do
  `dispose()`.

!!! warning "O `__del__` não faz logout"
    Como o finalizer do .NET (`~SankhyaContext() => Dispose(false)`), o
    `__del__` apenas marca o contexto como descartado: um contexto não
    descartado continua com as sessões abertas e registradas. Sempre use
    `with`/`async with` ou chame `dispose()` (veja
    [Gerenciamento de Sessões](../core-concepts/session-management.md)).

---

## SankhyaWrapper

Cliente da API XML legada para **uma** sessão: autenticação, invocação de
serviços com retry, arquivos e imagens. Normalmente é criado pelo
`SankhyaContext` (sessão principal e `acquire_new_session`).

### Construção

```python
from sankhya_sdk import SankhyaWrapper

wrapper = SankhyaWrapper(
    host="http://sankhya.example.com",
    port=8180,
    timeout=30,      # segundos
    max_retries=3,   # tentativas extras (padrão 3)
)
wrapper.authenticate("usuario", "senha")
try:
    print(wrapper.session_id, wrapper.user_code, wrapper.environment)
finally:
    wrapper.dispose()  # logout
```

`SankhyaWrapper.from_settings(settings=None)` cria e autentica a partir de
`SankhyaSettings` (`SANKHYA_URL`, `SANKHYA_PORT`, `SANKHYA_TIMEOUT`,
`SANKHYA_MAX_RETRIES`...).

### Métodos

| Método | Descrição |
|--------|-----------|
| `authenticate(username, password)` | Login (`MobileLoginSP.login`); credenciais recusadas lançam `ServiceRequestInvalidCredentialsException` |
| `service_invoker(request) -> ServiceResponse` | Invoca o serviço com a política de retry (veja [Tratamento de Erros](../core-concepts/error-handling.md)) |
| `service_invoker_async(request)` | Versão assíncrona (executa numa thread) |
| `get_file(key) -> ServiceFile` / `get_file_async(key)` | Arquivo pela chave; chave inválida lança `ServiceRequestFileNotFoundException` |
| `get_image(entity, keys) -> ServiceFile \| None` / `get_image_async` | Imagem da entidade (`None` se não houver) |
| `dispose()` / `close()` | Logout e fechamento da sessão HTTP / apenas fechamento da sessão HTTP |

| Propriedade | Descrição |
|-------------|-----------|
| `is_authenticated`, `session_id`, `user_code` | Estado da sessão |
| `host`, `port`, `base_url`, `environment`, `database_name` | Conexão |
| `sankhya_version` | Versão do servidor (lida do DWR no login) |
| `request_count` | Requisições feitas |

Não há métodos CRUD (`find`, `insert`, `update`, `remove`) no wrapper: use o
[`SimpleCRUDRequestWrapper`](request-wrappers.md) ou monte o
`ServiceRequest` e chame `service_invoker`.

---

## SankhyaSettings

Configurações da conexão XML legada (`sankhya_sdk.config`, Pydantic
Settings). Os valores vêm das variáveis de ambiente ou do `.env`; no
construtor, informe os campos pelos nomes das variáveis (aliases).

```python
from sankhya_sdk.config import SankhyaSettings

# A partir de variáveis de ambiente / .env
settings = SankhyaSettings()

# Explícito
settings = SankhyaSettings(
    SANKHYA_URL="http://sankhya.example.com",
    SANKHYA_PORT=8180,
    SANKHYA_USERNAME="usuario",
    SANKHYA_PASSWORD="senha",
    SANKHYA_TIMEOUT=60,
)
print(settings.url, settings.port, settings.timeout)
```

| Campo | Variável | Padrão | Descrição |
|-------|----------|--------|-----------|
| `url` | `SANKHYA_URL` | `http://localhost` | URL do servidor (sem porta) |
| `port` | `SANKHYA_PORT` | `8180` | Porta (define o ambiente) |
| `username` | `SANKHYA_USERNAME` | (obrigatório) | Usuário |
| `password` | `SANKHYA_PASSWORD` | (obrigatório) | Senha |
| `timeout` | `SANKHYA_TIMEOUT` | `30` | Timeout HTTP em segundos |
| `max_retries` | `SANKHYA_MAX_RETRIES` | `3` | Máximo de repetições automáticas |
| `log_level` | `SANKHYA_LOG_LEVEL` | `"INFO"` | Nível de log |
| `key_path`, `appkey`, `token` | `SANKHYA_KEY_PATH`, `SANKHYA_APPKEY`, `SANKHYA_TOKEN` | `None` | Não usados pelo `SankhyaWrapper` |

O módulo também expõe `sankhya_sdk.config.settings`, uma instância criada na
importação e usada por `from_settings()` sem argumentos.

---

## LowLevelSankhyaWrapper

Classe base do `SankhyaWrapper` (`sankhya_sdk.core.LowLevelSankhyaWrapper`):
sessão HTTP (`requests.Session`), montagem de URLs e cookie de sessão. Os
métodos de transporte são internos; a serialização fica nos modelos
(`ServiceRequest.to_xml_string()`, `ServiceResponse.from_xml_string(xml)`).
Expõe as propriedades `host`, `port`, `base_url`, `environment`,
`database_name`, `user_code` e o método `close()`.

---

## Types

Tipos auxiliares utilizados pelo SDK.

```python
from sankhya_sdk.core.types import ServiceAttribute, ServiceFile, SessionInfo
```

### SessionInfo

Dados da sessão autenticada no Sankhya.

```python
from sankhya_sdk.core.types import SessionInfo

session = SessionInfo(
    session_id="ABC123",  # ID da sessão (JSESSIONID)
    user_code=1,          # Código do usuário (IDUSU)
    username="admin",     # Usuário, para reautenticação
    password="secret",    # Senha, para reautenticação
)
print(session.session_id)  # ABC123
```

---

### ServiceFile

Arquivo retornado pelos downloads (`get_file`, `get_image`). Também
exportado como `sankhya_sdk.CoreServiceFile`; não confundir com
`sankhya_sdk.ServiceFile` (`sankhya_sdk.value_objects`), um modelo com
outros campos.

```python
from sankhya_sdk.core.types import ServiceFile

file = ServiceFile(
    data=b"...",               # Conteúdo em bytes
    content_type="image/jpeg", # Tipo MIME
    file_extension="jpg",      # Extensão sem ponto
    filename="foto.jpg",       # Nome original (opcional)
)

# Salvar em disco
with open(file.filename or f"arquivo.{file.file_extension}", "wb") as f:
    f.write(file.data)
```

---

### ServiceAttribute

Metadados de um serviço do Sankhya, usados pela política de retry.

```python
from sankhya_sdk.core.types import ServiceAttribute

attr = ServiceAttribute(is_transactional=True, is_retriable=False)
```

| Atributo | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `is_transactional` | `bool` | `False` | Serviço transacional: sessão duplicada, deadlock e timeout não são repetidos |
| `is_retriable` | `bool` | `True` | Se erros podem ser repetidos |

---

## LockManager

Gerenciador thread-safe de locks por chave (`sankhya_sdk.core.LockManager`).
O `SankhyaWrapper` usa um lock por sessão (chave: `session_id`): as
chamadas de `service_invoker` de uma mesma sessão, com seus retries, são
executadas uma de cada vez entre threads.

```python
from sankhya_sdk.core import LockManager

# Obter lock para uma chave (sempre o mesmo objeto para a mesma chave)
lock = LockManager.get_lock("session_123")

with lock:
    ...  # Operação thread-safe

LockManager.release_lock("session_123")  # Remove o lock do gerenciador
```

Também há `count()` e `clear_all()`.

---

## Ver Também

- [Gerenciamento de Sessões](../core-concepts/session-management.md) - Sessões e dispose
- [Request Wrappers](request-wrappers.md) - CRUD, paginação e lotes
- [Eventos](events.md) - Sistema de eventos
- [Autenticação](auth.md) - OAuthClient e TokenManager (API Gateway)
- [Gateway Client](gateway-client.md) - API JSON moderna
