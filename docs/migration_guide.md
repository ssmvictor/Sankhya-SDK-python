# Guia de Migração: XML → JSON Gateway

Este guia descreve como migrar integrações existentes do padrão XML para o novo padrão JSON usando a API Gateway Sankhya.

---

## Por que Migrar?

| Aspecto | XML (Legado) | JSON (Gateway) |
|---------|--------------|----------------|
| Performance | Parsing mais lento | Nativo, mais rápido |
| Debugging | Verboso, difícil de ler | Compacto, fácil de ler |
| Autenticação | Sessão/Token | OAuth2 moderno |
| Suporte | Em deprecação | Padrão recomendado |

---

## Passo 1: Atualizar Autenticação

**Antes (XML):**
```python
from sankhya_sdk.core import SankhyaContext

with SankhyaContext.from_settings() as wrapper:
    # usa username/password
```

**Depois (JSON Gateway):**
```python
from sankhya_sdk.auth import OAuthClient
from sankhya_sdk.http import SankhyaSession, GatewayClient

oauth = OAuthClient(base_url="https://api.sankhya.com.br")
oauth.authenticate(client_id="...", client_secret="...")

session = SankhyaSession(oauth_client=oauth)
client = GatewayClient(session)
```

---

## Passo 2: Migrar Consultas

**Antes:**
```python
request = ServiceRequest(service=ServiceName.CRUD_FIND)
request.root_entity = "Parceiro"
request.fields = ["CODPARC", "NOMEPARC"]
response = wrapper.service_invoker(request)
```

**Depois:**
```python
result = client.load_records(
    entity="Parceiro",
    fields=["CODPARC", "NOMEPARC"],
    criteria="ATIVO = 'S'"
)
```

---

## Passo 3: Migrar Inserções/Atualizações

**Antes:**
```python
request = ServiceRequest(service=ServiceName.CRUD_SAVE)
# ...configurar entidade...
response = wrapper.service_invoker(request)
```

**Depois:**
```python
result = client.save_record(
    entity="Parceiro",
    fields={"NOMEPARC": "Novo", "CODCID": 10, "ATIVO": "S"}
)
```

> **Nota:** A API JSON usa apenas POST. INSERT ou UPDATE é determinado pela existência da PK.

---

## Passo 4: Usar DTOs para Validação

```python
from sankhya_sdk.models.dtos import ParceiroDTO, TipoPessoa

# Input validation
parceiro = ParceiroDTO(
    nome="Empresa Teste",
    tipo_pessoa=TipoPessoa.JURIDICA,
    codigo_cidade=10
)

# Export with Sankhya field names
payload = parceiro.model_dump(by_alias=True, exclude_none=True)
client.save_record("Parceiro", payload)
```

---

## Compatibilidade Temporária

Para integrações que ainda precisam de XML:

```python
from sankhya_sdk.adapters import XmlAdapter

adapter = XmlAdapter()

# Converter payload legado
json_payload = adapter.xml_to_json(xml_string)

# Converter resposta para formato legado
xml_response = adapter.json_to_xml(json_result)
```

---

## Módulos Gateway

| Módulo | Uso | Exemplos |
|--------|-----|----------|
| **MGE** | Cadastros | Parceiro, Produto, Cidade |
| **MGECOM** | Movimentações | Notas, Pedidos, Faturamento |

O `GatewayClient` seleciona o módulo automaticamente baseado no serviço.
