# Uso do Gateway Client

Exemplos práticos de uso do `GatewayClient` e DTOs para a API JSON Gateway.

## Setup Inicial

### Autenticação e Criação do Cliente

```python
import os
from dotenv import load_dotenv
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient

load_dotenv()

# 1. Configurar OAuth
oauth = OAuthClient(
    base_url=os.getenv("SANKHYA_BASE_URL", "https://api.sankhya.com.br"),
    token=os.getenv("SANKHYA_TOKEN")
)

# 2. Autenticar
oauth.authenticate(
    client_id=os.getenv("SANKHYA_CLIENT_ID"),
    client_secret=os.getenv("SANKHYA_CLIENT_SECRET")
)

# 3. Criar sessão e cliente
session = SankhyaSession(oauth_client=oauth)
client = GatewayClient(session)

print("Cliente Gateway configurado!")
```

---

## Consultas (load_records)

### Consulta Simples

```python
# Buscar todos os parceiros ativos
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC", "CGC_CPF"],
    criteria="ATIVO = 'S'"
)

# Processar resultados
entities = result.get("responseBody", {}).get("entities", {})
records = entities.get("entity", [])

# Garantir que é lista (API retorna objeto se for único)
if isinstance(records, dict):
    records = [records]

for record in records:
    codigo = record.get("CODPARC", {}).get("$")
    nome = record.get("NOMEPARC", {}).get("$")
    print(f"{codigo}: {nome}")
```

### Consulta com Múltiplos Filtros

```python
# Clientes pessoa jurídica de uma cidade específica
result = client.load_records(
    entity="Parceiro",
    fields=[
        "CODPARC", "NOMEPARC", "CGC_CPF", 
        "TIPPESSOA", "CODCID", "LIMCRED"
    ],
    criteria="""
        ATIVO = 'S' 
        AND CLIENTE = 'S' 
        AND TIPPESSOA = 'J'
        AND CODCID = 10
        AND LIMCRED > 1000
    """
)
```

### Consulta de Produtos

```python
# Produtos ativos com estoque
result = client.load_records(
    entity="Produto",
    fields=[
        "CODPROD", "DESCRPROD", "REFERENCIA",
        "NCM", "UNIDADE", "ATIVO"
    ],
    criteria="ATIVO = 'S'"
)
```

### Consulta de Notas Fiscais

```python
from sankhya_sdk.http import GatewayModule

# Notas do mês atual (usando MGECOM)
result = client.load_records(
    entity="CabecalhoNota",
    fields=[
        "NUNOTA", "NUMNOTA", "SERIENOTA",
        "CODPARC", "DTNEG", "VLRNOTA"
    ],
    criteria="DTNEG >= '01/01/2025' AND TIPMOV = 'V'",
    module=GatewayModule.MGECOM
)
```

---

## Inserção e Atualização (save_record)

### Inserir Novo Parceiro

```python
# Inserir cliente (sem CODPARC = INSERT)
result = client.save_record(
    entity="Parceiro",
    fields={
        "NOMEPARC": "Nova Empresa LTDA",
        "TIPPESSOA": "J",
        "CGC_CPF": "12345678000199",
        "CODCID": 10,
        "ATIVO": "S",
        "CLIENTE": "S",
        "FORNECEDOR": "N",
        "EMAIL": "contato@novaempresa.com",
        "TELEFONE": "(11) 3000-0000"
    }
)

# Capturar código gerado
response_body = result.get("responseBody", {})
entity = response_body.get("entities", {}).get("entity", {})
new_code = entity.get("CODPARC", {}).get("$")

print(f"Parceiro criado com código: {new_code}")
```

### Atualizar Parceiro Existente

```python
# Atualizar (com CODPARC = UPDATE)
result = client.save_record(
    entity="Parceiro",
    fields={
        "CODPARC": 123,  # PK existente
        "EMAIL": "novo@email.com",
        "TELEFONE": "(11) 99999-9999",
        "LIMCRED": 50000
    }
)

print("Parceiro atualizado com sucesso!")
```

### Inserir Produto

```python
result = client.save_record(
    entity="Produto",
    fields={
        "DESCRPROD": "Notebook Dell Inspiron 15",
        "REFERENCIA": "DELL-INS-15-I7",
        "NCM": "84713012",
        "UNIDADE": "UN",
        "CODGRUPOPROD": 10,
        "ATIVO": "S"
    }
)
```

---

## Usando DTOs

### Com ParceiroDTO

```python
from sankhya_sdk.models.dtos import ParceiroDTO
from sankhya_sdk.models.dtos.parceiro import TipoPessoa

# Criar DTO com validação
parceiro = ParceiroDTO(
    nome="Empresa com Validação LTDA",
    tipo_pessoa=TipoPessoa.JURIDICA,
    cnpj_cpf="98.765.432/0001-10",
    codigo_cidade=10,
    email="valido@empresa.com",
    limite_credito=100000
)

# Serializar para formato Sankhya
payload = parceiro.model_dump(by_alias=True, exclude_none=True)

# Enviar via GatewayClient
result = client.save_record(entity="Parceiro", fields=payload)
```

### Validação de Dados

```python
from pydantic import ValidationError
from sankhya_sdk.models.dtos import ParceiroDTO

try:
    # Validação automática
    parceiro = ParceiroDTO(
        nome="",  # Erro: campo obrigatório vazio
        tipo_pessoa="X",  # Erro: valor inválido
        ativo="TALVEZ"  # Erro: deve ser S ou N
    )
except ValidationError as e:
    print("Erros de validação:")
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

### Parse de Resposta para DTO

```python
from sankhya_sdk.models.dtos import ParceiroListDTO

# Consultar
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC", "TIPPESSOA", "CGC_CPF", "ATIVO"],
    criteria="CLIENTE = 'S' AND ATIVO = 'S'"
)

# Converter para lista de DTOs
entities = result.get("responseBody", {}).get("entities", {}).get("entity", [])
if isinstance(entities, dict):
    entities = [entities]

parceiros = []
for entity in entities:
    try:
        dto = ParceiroListDTO(
            codigo=int(entity["CODPARC"]["$"]),
            nome=entity["NOMEPARC"]["$"],
            tipo_pessoa=entity["TIPPESSOA"]["$"],
            cnpj_cpf=entity.get("CGC_CPF", {}).get("$"),
            ativo=entity["ATIVO"]["$"]
        )
        parceiros.append(dto)
    except Exception as e:
        print(f"Erro ao parsear: {e}")

# Usar DTOs tipados
for p in parceiros:
    print(f"{p.codigo}: {p.nome} ({p.tipo_pessoa.value})")
```

---

## Serviços Customizados

### execute_service Genérico

```python
# Serviço customizado
result = client.execute_service(
    service_name="MeuServicoSP.executarAcao",
    request_body={
        "parametro1": {"$": "valor1"},
        "parametro2": {"$": "valor2"}
    },
    module=GatewayModule.MGE
)
```

### Dataset Personalizado

```python
# Consulta via DatasetSP
result = client.execute_service(
    "DatasetSP.execute",
    {
        "datasetName": "MINHA_CONSULTA",
        "parameters": {
            "PARAM1": {"$": "valor"}
        }
    }
)
```

---

## Tratamento de Erros

### Padrão Recomendado

```python
from sankhya_sdk.exceptions import (
    SankhyaAuthError,
    SankhyaForbiddenError,
    SankhyaNotFoundError,
    SankhyaClientError,
    SankhyaServerError,
)

def buscar_parceiro(client: GatewayClient, codigo: int):
    try:
        result = client.load_records(
            entity="Parceiro",
            fields=["CODPARC", "NOMEPARC"],
            criteria=f"CODPARC = {codigo}"
        )
        return result
        
    except SankhyaAuthError:
        print("Erro: Token expirado. Reautentique.")
        raise
        
    except SankhyaForbiddenError:
        print("Erro: Sem permissão para acessar Parceiro.")
        raise
        
    except SankhyaNotFoundError:
        print(f"Parceiro {codigo} não encontrado.")
        return None
        
    except SankhyaClientError as e:
        print(f"Erro de requisição: {e.status_code}")
        print(f"Detalhes: {e.response_body}")
        raise
        
    except SankhyaServerError as e:
        print(f"Erro no servidor Sankhya: {e.status_code}")
        # Pode tentar retry
        raise
```

### Retry com Backoff

```python
import time
from sankhya_sdk.exceptions import SankhyaServerError

def execute_with_retry(client, service, body, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.execute_service(service, body)
            
        except SankhyaServerError as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential backoff
                print(f"Erro 5xx, tentando novamente em {wait}s...")
                time.sleep(wait)
            else:
                raise
```

---

## Migração de Código Legado

### Antes (SankhyaContext)

```python
# Código antigo
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    partners = crud.find(Partner, "ATIVO = 'S'", max_results=10)
    
    for p in partners:
        print(f"{p.code_partner}: {p.name}")
```

### Depois (GatewayClient)

```python
# Código moderno
from sankhya_sdk.http import GatewayClient
from sankhya_sdk.models.dtos import ParceiroListDTO

client = GatewayClient(session)

result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC"],
    criteria="ATIVO = 'S'"
)

entities = result["responseBody"]["entities"].get("entity", [])
if isinstance(entities, dict):
    entities = [entities]

for entity in entities:
    print(f"{entity['CODPARC']['$']}: {entity['NOMEPARC']['$']}")
```

---

## Exemplo Completo

```python
"""
Exemplo completo de uso do GatewayClient.
"""
import os
from dotenv import load_dotenv
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient
from sankhya_sdk.models.dtos import ParceiroDTO, ParceiroListDTO
from sankhya_sdk.models.dtos.parceiro import TipoPessoa
from sankhya_sdk.exceptions import SankhyaClientError, SankhyaServerError

def main():
    load_dotenv()
    
    # Setup
    oauth = OAuthClient(base_url=os.getenv("SANKHYA_BASE_URL"))
    oauth.authenticate(
        client_id=os.getenv("SANKHYA_CLIENT_ID"),
        client_secret=os.getenv("SANKHYA_CLIENT_SECRET")
    )
    session = SankhyaSession(oauth_client=oauth)
    client = GatewayClient(session)
    
    # 1. Listar parceiros
    print("=== Listando Parceiros ===")
    result = client.load_records(
        entity="Parceiro",
        fields=["CODPARC", "NOMEPARC", "TIPPESSOA", "ATIVO"],
        criteria="CLIENTE = 'S' AND ATIVO = 'S'"
    )
    
    entities = result["responseBody"]["entities"].get("entity", [])
    if isinstance(entities, dict):
        entities = [entities]
    
    for e in entities[:5]:
        print(f"  {e['CODPARC']['$']}: {e['NOMEPARC']['$']}")
    
    # 2. Criar novo parceiro via DTO
    print("\n=== Criando Parceiro ===")
    novo = ParceiroDTO(
        nome="Cliente Gateway Test",
        tipo_pessoa=TipoPessoa.JURIDICA,
        codigo_cidade=10
    )
    
    try:
        result = client.save_record(
            entity="Parceiro",
            fields=novo.model_dump(by_alias=True, exclude_none=True)
        )
        codigo = result["responseBody"]["entities"]["entity"]["CODPARC"]["$"]
        print(f"  Criado com código: {codigo}")
        
    except SankhyaClientError as e:
        print(f"  Erro: {e.response_body}")
    
    print("\nConcluído!")

if __name__ == "__main__":
    main()
```

---

## Próximos Passos

- [API Reference: Gateway Client](../api-reference/gateway-client.md)
- [API Reference: DTOs](../api-reference/dtos.md)
- [Guia de Migração](../migration_guide.md)
