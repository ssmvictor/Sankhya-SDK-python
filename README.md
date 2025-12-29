# Sankhya SDK Python

SDK Python para API Sankhya (ERP) - Migração do projeto .NET.

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

## Descrição

Este projeto é uma migração idiomática do [Sankhya-SDK-dotnet](https://github.com/guibranco/Sankhya-SDK-dotnet) para Python. O objetivo é fornecer uma interface robusta, tipada e fácil de usar para integrar com os serviços do ERP Sankhya.

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

A forma mais simples de usar o SDK é através do `SankhyaContext`:

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
  - `core/`: Classes base, wrappers e contexto.
  - `models/`: Entidades de transporte e serviço.
  - `enums/`: Enumerações da API Sankhya.
- `tests/`: Testes unitários e de integração.
- `docs/`: Documentação adicional.

## Diferenças do SDK .NET

- **Nomenclatura**: Uso de `snake_case` seguindo a PEP 8.
- **Tipagem**: Uso extensivo de `Type Hints` e `Pydantic` para validação de dados.
- **Assincronismo**: Suporte planejado para `asyncio` via `httpx`.

## Licença

Este projeto está licenciado sob a mesma licença do projeto original. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
