# Core

Documentação das classes principais do SDK: `SankhyaContext`, `SankhyaWrapper` e `SankhyaSettings`.

## SankhyaContext

Gerenciador central de contexto e sessões.

### Uso Básico

```python
from sankhya_sdk import SankhyaContext

# Com context manager (recomendado)
with SankhyaContext.from_settings() as ctx:
    result = ctx.wrapper.find(Partner, "CODPARC > 0")

# Sem context manager
ctx = SankhyaContext.from_settings()
try:
    result = ctx.wrapper.find(Partner, "CODPARC > 0")
finally:
    ctx.dispose()
```

### Métodos de Classe

#### `from_settings(settings: SankhyaSettings | None = None) -> SankhyaContext`

Cria um contexto a partir de configurações.

```python
# Usa variáveis de ambiente
ctx = SankhyaContext.from_settings()

# Usa configurações personalizadas
settings = SankhyaSettings(
    base_url="https://api.sankhya.com.br",
    username="usuario",
    password="senha"
)
ctx = SankhyaContext.from_settings(settings)
```

### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `wrapper` | `SankhyaWrapper` | Wrapper principal para operações |
| `user_code` | `int` | Código do usuário autenticado |
| `session_token` | `str` | Token da sessão atual |
| `is_authenticated` | `bool` | Se está autenticado |

### Métodos de Instância

#### `acquire_session() -> UUID`

Adquire uma nova sessão paralela.

```python
token = ctx.acquire_session()
# Use invoke_with_token para operações com esta sessão
```

#### `finalize_session(token: UUID) -> None`

Finaliza uma sessão paralela.

```python
ctx.finalize_session(token)
```

#### `detach_session(token: UUID) -> dict`

Detacha uma sessão para uso em outro contexto.

```python
session_data = ctx.detach_session(token)
# Pode ser serializado e enviado para outro processo
```

#### `invoke_with_token(token: UUID, service_name: str, request: ServiceRequest) -> ServiceResponse`

Invoca um serviço usando uma sessão específica.

```python
response = ctx.invoke_with_token(token, "ServiceName", request)
```

#### `dispose() -> None`

Libera todos os recursos e fecha sessões.

```python
ctx.dispose()
```

---

## SankhyaWrapper

Cliente de alto nível para comunicação com a API.

### Uso Básico

```python
from sankhya_sdk import SankhyaContext

with SankhyaContext.from_settings() as ctx:
    wrapper = ctx.wrapper
    partners = wrapper.find(Partner, "CODPARC > 0")
```

### Métodos de Autenticação

#### `login() -> None`

Realiza login na API.

```python
wrapper.login()
```

#### `logout() -> None`

Realiza logout da API.

```python
wrapper.logout()
```

### Métodos CRUD

#### `find(entity_type: Type[T], criteria: str = "", max_results: int = 0) -> list[T]`

Busca entidades.

```python
# Busca simples
partners = wrapper.find(Partner, "CODPARC > 0")

# Com limite
partners = wrapper.find(Partner, "ATIVO = 'S'", max_results=100)
```

#### `update(entity: EntityBase) -> EntityBase`

Atualiza uma entidade.

```python
partner.email = "novo@email.com"
updated = wrapper.update(partner)
```

#### `insert(entity: EntityBase) -> EntityBase`

Insere uma nova entidade.

```python
partner = Partner()
partner.name = "Novo Parceiro"
created = wrapper.insert(partner)
```

#### `remove(entity: EntityBase) -> bool`

Remove uma entidade.

```python
success = wrapper.remove(partner)
```

### Métodos de Serviço

#### `invoke_service(service_name: str, request: ServiceRequest) -> ServiceResponse`

Invoca um serviço da API.

```python
request = ServiceRequest(service_name="ServiceName")
response = wrapper.invoke_service("ServiceName", request)
```

### Métodos de Arquivo

#### `get_file(filename: str) -> bytes`

Baixa um arquivo.

```python
content = wrapper.get_file("relatorio.pdf")
with open("relatorio.pdf", "wb") as f:
    f.write(content)
```

#### `get_image(primary_key: dict, entity_name: str = "Produto") -> bytes`

Baixa uma imagem de entidade.

```python
image = wrapper.get_image({"CODPROD": 100}, "Produto")
```

---

## SankhyaSettings

Configurações do SDK.

### Uso Básico

```python
from sankhya_sdk.core.settings import SankhyaSettings

# A partir de variáveis de ambiente
settings = SankhyaSettings()

# Explícito
settings = SankhyaSettings(
    base_url="https://api.sankhya.com.br",
    username="usuario",
    password="senha",
    environment="producao"
)
```

### Propriedades

| Propriedade | Tipo | Padrão | Descrição |
|-------------|------|--------|-----------|
| `base_url` | `str` | (obrigatório) | URL base da API |
| `username` | `str` | (obrigatório) | Nome de usuário |
| `password` | `str` | (obrigatório) | Senha |
| `environment` | `str` | `"producao"` | Ambiente (producao/homologacao/treinamento) |
| `timeout` | `int` | `30` | Timeout em segundos |
| `max_retries` | `int` | `3` | Máximo de tentativas |
| `log_level` | `str` | `"INFO"` | Nível de logging |

### Variáveis de Ambiente

| Variável | Corresponde a |
|----------|---------------|
| `SANKHYA_BASE_URL` | `base_url` |
| `SANKHYA_USERNAME` | `username` |
| `SANKHYA_PASSWORD` | `password` |
| `SANKHYA_ENVIRONMENT` | `environment` |
| `SANKHYA_TIMEOUT` | `timeout` |
| `SANKHYA_MAX_RETRIES` | `max_retries` |
| `SANKHYA_LOG_LEVEL` | `log_level` |

### Métodos

#### `from_key_file(path: str, passphrase: str) -> SankhyaSettings`

Carrega configurações de arquivo .key.

```python
settings = SankhyaSettings.from_key_file("credenciais.key", "senha_secreta")
```

#### `to_key_file(path: str, passphrase: str) -> None`

Salva configurações em arquivo .key.

```python
settings.to_key_file("credenciais.key", "senha_secreta")
```

---

## LowLevelSankhyaWrapper

Cliente de baixo nível para comunicação HTTP/XML.

!!! note "Uso Avançado"
    Use apenas quando precisar de controle total sobre requisições.

### Métodos

#### `post(url: str, data: str, headers: dict | None = None) -> str`

Envia requisição POST.

```python
xml_response = low_level.post("/mge/service.sbr", xml_request)
```

#### `get(url: str, headers: dict | None = None) -> bytes`

Envia requisição GET.

```python
content = low_level.get("/mge/file.sbr?file=relatorio.pdf")
```

#### `serialize_request(request: ServiceRequest) -> str`

Serializa requisição para XML.

```python
xml = low_level.serialize_request(request)
```

#### `deserialize_response(xml: str) -> ServiceResponse`

Deserializa resposta XML.

```python
response = low_level.deserialize_response(xml_string)
```
