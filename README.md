# Sankhya SDK Python

SDK Python para API Sankhya (ERP) - Migração do projeto .NET.

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

## Descrição

Este projeto é uma migração idiomática do [Sankhya-SDK-dotnet](https://github.com/guibranco/Sankhya-SDK-dotnet) para Python. O objetivo é fornecer uma interface robusta, tipada e fácil de usar para integrar com os serviços do ERP Sankhya.

## 📚 Documentação

A documentação completa do projeto está disponível em: **[https://datavi.ia.br/docs-site-sdk/](https://datavi.ia.br/docs-site-sdk/)**

## Instalação

Para instalar em modo de desenvolvimento:

```bash
pip install -e ".[dev]"
```

## Configuração

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Preencha as credenciais no arquivo `.env`.
   - `SANKHYA_URL`: URL do servidor.
   - `SANKHYA_USERNAME` / `SANKHYA_PASSWORD`: Credenciais.
   - `SANKHYA_KEY_PATH`: Caminho para o arquivo de chave (.key) se necessário.

## Quick Start

## Autenticação
 
### Novo: OAuth2 (Recomendado)

O SDK suporta agora o fluxo de autenticação OAuth2 (Client Credentials) usando `SankhyaSession`.

**Configuração (.env):**
```bash
SANKHYA_CLIENT_ID=seu_client_id
SANKHYA_CLIENT_SECRET=seu_client_secret
SANKHYA_AUTH_BASE_URL=https://api.sankhya.com.br # Opcional
SANKHYA_TOKEN=seu_x_token # Opcional (X-Token)
```

**Uso:**
```python
import os
from dotenv import load_dotenv
from sankhya_sdk.auth.oauth_client import OAuthClient
from sankhya_sdk.http.session import SankhyaSession

load_dotenv()

# 1. Autenticar
oauth = OAuthClient(
    base_url=os.getenv("SANKHYA_AUTH_BASE_URL", "https://api.sankhya.com.br"),
    token=os.getenv("SANKHYA_TOKEN")
)
token = oauth.authenticate(
    client_id=os.getenv("SANKHYA_CLIENT_ID"),
    client_secret=os.getenv("SANKHYA_CLIENT_SECRET")
)

# 2. Criar sessão
session = SankhyaSession(oauth_client=oauth)

# 3. Fazer requisições
response = session.get("/gateway/v1/mge/teste")
```

## 🔄 Auto-Refresh de Tokens OAuth2

O SDK gerencia automaticamente a renovação de tokens OAuth2, garantindo que suas aplicações funcionem continuamente sem interrupções por tokens expirados.

### Características

✅ **Renovação Automática**: Tokens são renovados automaticamente antes de expirar (margem de segurança de 60 segundos)  
✅ **Thread-Safe**: Operações protegidas por locks para uso em aplicações multi-thread  
✅ **Transparente**: Não precisa gerenciar refresh manualmente - funciona "out of the box"  
✅ **Logging Inteligente**: Logs informativos quando renovação ocorre

### Como Funciona

1. **Verificação Automática**: Toda vez que você faz uma requisição, o SDK verifica se o token ainda é válido
2. **Renovação Proativa**: Se o token está expirado ou próximo de expirar (dentro de 60s), é renovado automaticamente
3. **Fallback Inteligente**: Se o refresh falhar, o SDK tenta re-autenticar usando credenciais armazenadas

### Exemplo de Uso

```python
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http.session import SankhyaSession

# Configure uma vez
oauth = OAuthClient(base_url="...", token="...")
oauth.authenticate(client_id, client_secret)

session = SankhyaSession(oauth)

# Faça quantas requisições quiser - o SDK cuida do resto!
for i in range(100):
    response = session.get("/api/endpoint")
    # Token é renovado automaticamente quando necessário
    # Você não precisa se preocupar com nada! 🎉
```

### Detalhamento Técnico

**Margem de Segurança**: Tokens são considerados inválidos 60 segundos antes de expirarem. Isso previne race conditions e garante que o token nunca expire durante uma requisição.

**Thread-Safety**: Todas as operações de token no `TokenManager` são protegidas por `threading.Lock()`, permitindo uso seguro em aplicações com múltiplas threads.

**Método Recomendado**: Use `oauth_client.get_valid_token()` ao invés de `token_manager.get_token()` - ele implementa toda a lógica de auto-refresh.


### JSON Gateway Client (Novo)

O `GatewayClient` oferece uma interface de alto nível para a API Gateway JSON:

```python
from sankhya_sdk.http import GatewayClient, GatewayModule

# Criar cliente
client = GatewayClient(session)

# Consultar parceiros
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC", "TIPPESSOA"],
    criteria="ATIVO = 'S'"
)

# Inserir/Atualizar parceiro (POST)
result = client.save_record(
    entity="Parceiro",
    fields={"NOMEPARC": "Novo Parceiro", "CODCID": 10, "ATIVO": "S"}
)

# Usar módulo específico (MGE para cadastros, MGECOM para notas)
result = client.execute_service(
    "CACSP.IncluirNota",
    payload,
    module=GatewayModule.MGECOM
)
```

### DTOs Tipados

Use os DTOs para validação automática de dados:

```python
from sankhya_sdk.models.dtos import ParceiroDTO, NotaDTO, MovimentoDTO

# Parceiro com validação Pydantic
parceiro = ParceiroDTO(
    nome="Empresa Teste",
    tipo_pessoa=TipoPessoa.JURIDICA,
    cnpj_cpf="12.345.678/0001-90",
    codigo_cidade=10
)

# Exportar com aliases Sankhya
payload = parceiro.model_dump(by_alias=True, exclude_none=True)
# {"NOMEPARC": "Empresa Teste", "TIPPESSOA": "J", ...}
```

### XML Adapter (Compatibilidade Legada)

Para integrações existentes que usam XML:

```python
from sankhya_sdk.adapters import XmlAdapter

adapter = XmlAdapter()

# Converter XML → JSON
json_data = adapter.xml_to_json(xml_string)

# Converter JSON → XML
xml_string = adapter.json_to_xml(json_data)
```


### Legado: SankhyaContext (SankhyaWrapper)
 
A forma clássica de usar o SDK é através do `SankhyaContext`:

```python
from sankhya_sdk.core import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.models.service import ServiceRequest

# Usando context manager (recomendado)
with SankhyaContext.from_settings() as wrapper:
    request = ServiceRequest(service=ServiceName.CRUD_FIND)
    # Configurar request...
    response = wrapper.service_invoker(request)
    
    if response.is_success:
        for entity in response.entities:
            print(entity)
```

### Uso Assíncrono

```python
async with SankhyaContext.from_settings() as wrapper:
    response = await wrapper.service_invoker_async(request)
```

### Download de Arquivos

```python
with SankhyaContext.from_settings() as wrapper:
    # Baixar arquivo
    file = wrapper.get_file("CHAVE_ARQUIVO")
    with open(file.filename or "arquivo.pdf", "wb") as f:
        f.write(file.data)
    
    # Baixar imagem de entidade
    image = wrapper.get_image("Parceiro", {"CODPARC": 1})
    if image:
        with open(f"parceiro.{image.file_extension}", "wb") as f:
            f.write(image.data)
```

Para mais detalhes, consulte a [documentação do wrapper](docs/wrapper.md).

### Múltiplas Sessões

O SDK suporta gerenciamento de múltiplas sessões simultâneas com tokens UUID:

```python
from sankhya_sdk.enums import ServiceRequestType

ctx = SankhyaContext.from_settings()

with ctx:
    # Token da sessão principal
    main_token = ctx.token
    
    # Criar sessão secundária
    token2 = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
    
    # Invocar serviço com sessão específica
    response = SankhyaContext.service_invoker_with_token(request, token2)
    
    # Finalizar sessão quando não mais necessária
    ctx.finalize_session(token2)
```

### Validações de Entidades

O SDK inclui um módulo de validação para garantir que classes de entidade seguem os requisitos:

```python
from sankhya_sdk.validations import EntityValidator, EntityValidation

# Validar uma classe de entidade
EntityValidator.validate_entity(MyEntity)

# Analisar mensagens de erro da API
error_msg = "Campo não existe: PARCEIRO->NOMEPARC"
if match := EntityValidation.match_property_not_found(error_msg):
    entity = match.group("entity")
    field = match.group("propertyName")
    print(f"Campo '{field}' não encontrado em '{entity}'")
```

Para mais detalhes, consulte a [documentação de validações](docs/validations.md).

## Estrutura do Projeto

- `sankhya_sdk/`: Código fonte do SDK.
  - `auth/`: Autenticação OAuth2 (`OAuthClient`, `TokenManager`).
  - `http/`: Cliente HTTP (`SankhyaSession`, `GatewayClient`).
  - `adapters/`: Compatibilidade legada (`XmlAdapter`).
  - `models/`: Entidades de transporte e DTOs.
    - `dtos/`: DTOs JSON (`ParceiroDTO`, `NotaDTO`, `MovimentoDTO`).
    - `transport/`: Entidades completas (`Partner`, `Product`, etc.).
  - `exceptions/`: Exceções customizadas (HTTP, Auth, etc.).
  - `core/`: Classes base, wrappers e contexto.
  - `enums/`: Enumerações da API Sankhya.
- `tests/`: Testes unitários e de integração.
- `docs/`: Documentação adicional.


## Diferenças do SDK .NET

- **Nomenclatura**: Uso de `snake_case` seguindo a PEP 8.
- **Tipagem**: Uso extensivo de `Type Hints` e `Pydantic` para validação de dados.
- **Assincronismo**: Suporte planejado para `asyncio` via `httpx`.

## Licença

Este projeto está licenciado sob a mesma licença do projeto original. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
