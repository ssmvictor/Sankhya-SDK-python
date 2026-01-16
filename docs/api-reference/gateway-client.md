# Gateway Client

Cliente de alto nível para a API Gateway JSON do Sankhya.

## Visão Geral

O `GatewayClient` fornece uma interface simplificada para executar serviços na API Gateway do Sankhya, com seleção automática de módulo (MGE/MGECOM) e saída JSON.

## Importação

```python
from sankhya_sdk.http import GatewayClient, GatewayModule
```

---

## GatewayModule

Enum que define os módulos disponíveis no Gateway.

```python
class GatewayModule(Enum):
    MGE = "mge"        # Cadastros gerais (Parceiro, Produto, Cidade, etc.)
    MGECOM = "mgecom"  # Movimentações comerciais (Notas, Pedidos, Faturamento)
```

### Mapeamento de Servicos

| Prefixo do Servico | Modulo | Uso |
|--------------------|--------|-----|
| `CRUDServiceProvider` | MGE | Operacoes CRUD em cadastros |
| `DatasetSP` | MGE | Consultas de datasets e **UPDATE PARCIAL** |
| `CACSP` | MGECOM | Servicos comerciais |
| `SelecaoDocumentoSP` | MGECOM | Selecao de documentos |

---

## GatewayClient

Cliente principal para execução de serviços.

### Construtor

```python
def __init__(
    self,
    session: SankhyaSession,
    default_module: GatewayModule = GatewayModule.MGE
)
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `session` | `SankhyaSession` | Sessão autenticada |
| `default_module` | `GatewayModule` | Módulo padrão quando não detectável |

### Exemplo de Inicialização

```python
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient

# Autenticação
oauth = OAuthClient(base_url="https://api.sankhya.com.br")
oauth.authenticate(client_id="...", client_secret="...")

# Criar sessão e cliente
session = SankhyaSession(oauth_client=oauth)
client = GatewayClient(session)
```

---

## Métodos

### execute_service

Executa um serviço genérico no Gateway.

```python
def execute_service(
    self,
    service_name: str,
    request_body: Dict[str, Any],
    module: Optional[GatewayModule] = None
) -> Dict[str, Any]
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `service_name` | `str` | Nome completo do serviço (ex: `CRUDServiceProvider.loadRecords`) |
| `request_body` | `Dict[str, Any]` | Payload da requisição |
| `module` | `GatewayModule \| None` | Módulo (auto-detectado se não informado) |

**Retorno**: `Dict[str, Any]` - Resposta JSON do Gateway.

**Exceções**:

- `SankhyaClientError`: Erros 4xx
- `SankhyaServerError`: Erros 5xx

#### Exemplo

```python
result = client.execute_service(
    "CRUDServiceProvider.loadRecords",
    {
        "dataSet": {
            "rootEntity": "Parceiro",
            "includePresentationFields": "S",
            "entity": {
                "fieldset": {"list": "CODPARC,NOMEPARC"}
            }
        }
    }
)
```

---

### load_records

Consulta registros usando `CRUDServiceProvider.loadRecords`.

```python
def load_records(
    self,
    entity: str,
    fields: List[str],
    criteria: Optional[str] = None,
    module: Optional[GatewayModule] = None
) -> Dict[str, Any]
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `entity` | `str` | Nome da entidade (ex: `Parceiro`, `Produto`) |
| `fields` | `List[str]` | Lista de campos a retornar |
| `criteria` | `str \| None` | Expressão de filtro SQL-like |
| `module` | `GatewayModule \| None` | Módulo (padrão: MGE) |

**Retorno**: `Dict[str, Any]` - Resposta com registros.

#### Exemplo

```python
# Buscar parceiros ativos
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC", "CGC_CPF", "TIPPESSOA"],
    criteria="ATIVO = 'S' AND CLIENTE = 'S'"
)

# Processar resultados
entities = result.get("responseBody", {}).get("entities", {})
records = entities.get("entity", [])

for record in records:
    print(record.get("NOMEPARC", {}).get("$"))
```

---

### save_record

Salva (insere ou atualiza) um registro.

```python
def save_record(
    self,
    entity: str,
    fields: Dict[str, Any],
    field_list: Optional[List[str]] = None,
    module: Optional[GatewayModule] = None,
    *,
    pk: Optional[Dict[str, Any]] = None,
    use_dataset_for_update: bool = True,
    stand_alone: bool = False
) -> Dict[str, Any]
```

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `entity` | `str` | Nome da entidade |
| `fields` | `Dict[str, Any]` | Dicionario de campos e valores |
| `field_list` | `List[str] \| None` | Campos a retornar (CRUDService apenas) |
| `module` | `GatewayModule \| None` | Modulo (padrao: MGE) |
| `pk` | `Dict[str, Any] \| None` | **Chave primaria para UPDATE PARCIAL** |
| `use_dataset_for_update` | `bool` | Usar DatasetSP.save quando pk informada (padrao: True) |
| `stand_alone` | `bool` | Transacao independente (DatasetSP.save apenas) |

**Retorno**: `Dict[str, Any]` - Resposta com registro salvo.

#### Comportamento

| Situacao | Servico Usado | Descricao |
|----------|---------------|-----------|
| `pk=None` | `CRUDServiceProvider.saveRecord` | INSERT/UPSERT (exige campos obrigatorios) |
| `pk={...}` | `DatasetSP.save` | **UPDATE PARCIAL** (so campos alterados) |
| `pk={...}, use_dataset_for_update=False` | `CRUDServiceProvider.saveRecord` | Forca comportamento antigo |

!!! tip "Update Parcial"
    Quando voce fornece o parametro `pk`, o SDK usa internamente o servico `DatasetSP.save`, que permite atualizar apenas os campos especificados sem precisar enviar todos os campos obrigatorios da entidade.

#### Exemplo: Inserir (INSERT)

```python
# Novo parceiro (sem pk = INSERT)
result = client.save_record(
    entity="Parceiro",
    fields={
        "NOMEPARC": "Nova Empresa LTDA",
        "TIPPESSOA": "J",
        "CGC_CPF": "12345678000199",
        "CODCID": 10,
        "ATIVO": "S",
        "CLIENTE": "S"
    }
)

# Capturar codigo gerado
new_code = result["responseBody"]["entities"]["entity"]["CODPARC"]["$"]
print(f"Parceiro criado: {new_code}")
```

#### Exemplo: Update Parcial (com pk)

```python
# Atualiza APENAS o email - nao precisa enviar outros campos
result = client.save_record(
    entity="Parceiro",
    fields={"EMAIL": "novo@email.com"},
    pk={"CODPARC": 123}
)

# Atualiza vencimento de titulo financeiro
result = client.save_record(
    entity="Financeiro",
    fields={"DTVENC": "20/02/2026"},
    pk={"NUFIN": 45678}
)
```

#### Exemplo: PK Composta

```python
# Entidade com chave primaria composta (NUNOTA + SEQUENCIA)
result = client.save_record(
    entity="ItemNota",
    fields={"OBSERVACAO": "Desconto especial"},
    pk={"NUNOTA": 100, "SEQUENCIA": 1}
)
```

#### Exemplo: Forcar Comportamento Antigo

```python
# Mesmo com pk, usa CRUDServiceProvider.saveRecord
result = client.save_record(
    entity="Parceiro",
    fields={"CODPARC": 123, "EMAIL": "novo@email.com"},
    pk={"CODPARC": 123},
    use_dataset_for_update=False  # Forca CRUDServiceProvider
)
```

---

### extract_records (static)

Extrai e normaliza registros de uma resposta do Gateway.

```python
@staticmethod
def extract_records(response: Dict[str, Any]) -> List[Dict[str, Any]]
```

O Gateway retorna dados em formato compacto (f0, f1, f2...). Este metodo mapeia para nomes reais.

#### Exemplo

```python
result = client.load_records("Parceiro", ["CODPARC", "NOMEPARC"])

# Extrair registros normalizados
records = GatewayClient.extract_records(result)

for record in records:
    print(f"{record['CODPARC']}: {record['NOMEPARC']}")
```

---

### is_success (static)

Verifica se a resposta indica sucesso.

```python
@staticmethod
def is_success(response: Dict[str, Any]) -> bool
```

---

### get_error_message (static)

Extrai mensagem de erro da resposta.

```python
@staticmethod
def get_error_message(response: Dict[str, Any]) -> Optional[str]
```

---

## Resolucao Automatica de Modulo

O `GatewayClient` detecta automaticamente o módulo correto baseado no prefixo do serviço:

```python
# Automaticamente usa MGE
client.execute_service("CRUDServiceProvider.loadRecords", {...})

# Automaticamente usa MGECOM
client.execute_service("CACSP.IncluirNota", {...})

# Override manual
client.execute_service(
    "CustomService.doSomething",
    {...},
    module=GatewayModule.MGECOM
)
```

---

## Tratamento de Erros

```python
from sankhya_sdk.exceptions import (
    SankhyaAuthError,
    SankhyaForbiddenError,
    SankhyaNotFoundError,
    SankhyaClientError,
    SankhyaServerError,
)

try:
    result = client.load_records("Parceiro", ["CODPARC", "NOMEPARC"])
    
except SankhyaAuthError:
    print("Token expirado ou inválido")
    
except SankhyaForbiddenError:
    print("Sem permissão para acessar este recurso")
    
except SankhyaNotFoundError:
    print("Entidade ou serviço não encontrado")
    
except SankhyaClientError as e:
    print(f"Erro do cliente: {e.status_code} - {e.response_body}")
    
except SankhyaServerError as e:
    print(f"Erro do servidor: {e.status_code}")
```

---

## Próximos Passos

- [DTOs](dtos.md) - Modelos tipados para validação
- [Adapters](adapters.md) - Compatibilidade com XML legado
- [Exemplos de Gateway](../examples/gateway-usage.md) - Casos de uso práticos
