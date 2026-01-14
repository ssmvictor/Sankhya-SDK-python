# Adapters

Adaptadores para compatibilidade com integrações legadas.

## Visão Geral

O módulo `adapters` fornece ferramentas para migração gradual de integrações XML para a nova API JSON Gateway, permitindo:

- Conversão bidirecional XML ↔ JSON
- Compatibilidade com payloads legados
- Transformação de formatos de campos

## Importação

```python
from sankhya_sdk.adapters import XmlAdapter
```

---

## XmlAdapter

Adaptador para conversão entre formatos XML e JSON.

### Construtor

```python
adapter = XmlAdapter()
```

Não requer parâmetros de configuração.

---

## Métodos

### xml_to_json

Converte um payload XML para formato JSON.

```python
def xml_to_json(self, xml_payload: str) -> Dict[str, Any]
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `xml_payload` | `str` | String XML a converter |

**Retorno**: `Dict[str, Any]` - Dicionário JSON equivalente.

**Exceções**: `ValueError` se o XML for malformado.

#### Exemplo

```python
from sankhya_sdk.adapters import XmlAdapter

adapter = XmlAdapter()

xml_string = """
<serviceRequest>
    <serviceName>CRUDServiceProvider.loadRecords</serviceName>
    <requestBody>
        <dataSet rootEntity="Parceiro">
            <entity>
                <fieldset list="CODPARC,NOMEPARC"/>
            </entity>
        </dataSet>
    </requestBody>
</serviceRequest>
"""

json_data = adapter.xml_to_json(xml_string)
# Resultado:
# {
#     "serviceName": "CRUDServiceProvider.loadRecords",
#     "requestBody": {
#         "dataSet": {
#             "@attributes": {"rootEntity": "Parceiro"},
#             "entity": {
#                 "fieldset": {
#                     "@attributes": {"list": "CODPARC,NOMEPARC"}
#                 }
#             }
#         }
#     }
# }
```

---

### json_to_xml

Converte um dicionário JSON para formato XML.

```python
def json_to_xml(
    self, 
    json_data: Dict[str, Any], 
    root_name: str = "serviceRequest"
) -> str
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `json_data` | `Dict[str, Any]` | Dicionário a converter |
| `root_name` | `str` | Nome do elemento raiz (padrão: `serviceRequest`) |

**Retorno**: `str` - String XML.

#### Exemplo

```python
json_data = {
    "serviceName": "CRUDServiceProvider.saveRecord",
    "requestBody": {
        "dataSet": {
            "rootEntity": "Parceiro",
            "dataRow": {
                "localFields": {
                    "NOMEPARC": {"$": "Novo Cliente"}
                }
            }
        }
    }
}

xml_string = adapter.json_to_xml(json_data)
```

---

### wrap_legacy_request

Envolve um request legado no formato esperado pela API JSON.

```python
def wrap_legacy_request(
    self,
    service_name: str,
    request_body: Dict[str, Any]
) -> Dict[str, Any]
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `service_name` | `str` | Nome do serviço |
| `request_body` | `Dict[str, Any]` | Corpo da requisição |

**Retorno**: `Dict[str, Any]` - Requisição formatada.

#### Exemplo

```python
# Payload legado
legacy_body = {
    "dataSet": {
        "rootEntity": "Parceiro",
        "entity": {"fieldset": {"list": "CODPARC,NOMEPARC"}}
    }
}

# Envolver para API moderna
wrapped = adapter.wrap_legacy_request(
    "CRUDServiceProvider.loadRecords",
    legacy_body
)
# Resultado:
# {
#     "serviceName": "CRUDServiceProvider.loadRecords",
#     "requestBody": {...}
# }
```

---

### extract_legacy_response

Extrai dados de uma resposta JSON no formato legado.

```python
def extract_legacy_response(
    self, 
    json_response: Dict[str, Any]
) -> Dict[str, Any]
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `json_response` | `Dict[str, Any]` | Resposta da API Gateway |

**Retorno**: `Dict[str, Any]` - Dados extraídos no formato legado.

#### Exemplo

```python
# Resposta da API Gateway
api_response = {
    "serviceName": "CRUDServiceProvider.loadRecords",
    "status": "1",
    "responseBody": {
        "entities": {
            "entity": [
                {"CODPARC": {"$": "1"}, "NOMEPARC": {"$": "Cliente A"}},
                {"CODPARC": {"$": "2"}, "NOMEPARC": {"$": "Cliente B"}}
            ]
        }
    }
}

# Extrair no formato legado
legacy_data = adapter.extract_legacy_response(api_response)
# Resultado:
# {
#     "entities": {
#         "entity": [...]
#     }
# }
```

---

### convert_field_format

Converte formato de campos entre estilo legado e moderno.

```python
def convert_field_format(
    self,
    fields: Dict[str, Any],
    to_sankhya: bool = True
) -> Dict[str, Any]
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `fields` | `Dict[str, Any]` | Dicionário de campos |
| `to_sankhya` | `bool` | Se `True`, converte para formato Sankhya. Se `False`, achata. |

**Formatos**:

- **Sankhya**: `{"CAMPO": {"$": "valor"}}`
- **Legado/Plano**: `{"CAMPO": "valor"}`

#### Exemplo

```python
# Converter de legado para Sankhya
legacy_fields = {
    "NOMEPARC": "Novo Nome",
    "EMAIL": "email@teste.com"
}

sankhya_fields = adapter.convert_field_format(legacy_fields, to_sankhya=True)
# Resultado:
# {
#     "NOMEPARC": {"$": "Novo Nome"},
#     "EMAIL": {"$": "email@teste.com"}
# }

# Converter de Sankhya para legado
flat_fields = adapter.convert_field_format(sankhya_fields, to_sankhya=False)
# Resultado:
# {
#     "NOMEPARC": "Novo Nome",
#     "EMAIL": "email@teste.com"
# }
```

---

## Casos de Uso

### Migração Gradual

Mantenha código legado funcionando enquanto migra para o novo formato:

```python
from sankhya_sdk.adapters import XmlAdapter
from sankhya_sdk.http import GatewayClient

adapter = XmlAdapter()
client = GatewayClient(session)

# Código legado produz XML
xml_request = legacy_system.generate_request()

# Converter para JSON
json_request = adapter.xml_to_json(xml_request)

# Executar via Gateway moderno
result = client.execute_service(
    json_request["serviceName"],
    json_request["requestBody"]
)

# Converter resposta para formato esperado pelo legado
legacy_response = adapter.extract_legacy_response(result)
xml_response = adapter.json_to_xml(legacy_response)

# Processar no sistema legado
legacy_system.process_response(xml_response)
```

### Integração com Sistemas Externos

Receba dados de sistemas que enviam XML:

```python
from flask import Flask, request
from sankhya_sdk.adapters import XmlAdapter

app = Flask(__name__)
adapter = XmlAdapter()

@app.route("/webhook", methods=["POST"])
def webhook():
    # Receber XML de sistema externo
    xml_data = request.data.decode("utf-8")
    
    # Converter para JSON para processamento
    json_data = adapter.xml_to_json(xml_data)
    
    # Processar...
    process_data(json_data)
    
    # Retornar resposta em XML se necessário
    response_data = {"status": "OK"}
    return adapter.json_to_xml(response_data, root_name="response")
```

### Compatibilidade com SDK .NET

O SDK .NET original usa XML. Use o adapter para manter compatibilidade:

```python
# Payload no mesmo formato do SDK .NET
dotnet_style_fields = {
    "NOMEPARC": "Cliente",
    "TIPPESSOA": "J",
    "CODCID": 10
}

# Converter para formato Sankhya Gateway
sankhya_fields = adapter.convert_field_format(dotnet_style_fields)

# Usar com GatewayClient
result = client.save_record("Parceiro", sankhya_fields)
```

---

## Convenções de Formato

### Atributos XML

Atributos são mapeados para `@attributes`:

```python
# XML
# <dataSet rootEntity="Parceiro" includePresentationFields="S">

# JSON
{
    "dataSet": {
        "@attributes": {
            "rootEntity": "Parceiro",
            "includePresentationFields": "S"
        }
    }
}
```

### Conteúdo de Texto

Conteúdo de texto é mapeado para `$`:

```python
# XML
# <NOMEPARC>Cliente Teste</NOMEPARC>

# JSON
{
    "NOMEPARC": {"$": "Cliente Teste"}
}

# Ou se for elemento simples sem filhos:
{
    "NOMEPARC": "Cliente Teste"
}
```

### Elementos Repetidos

Elementos com mesmo nome viram lista:

```python
# XML
# <entity><field>A</field><field>B</field></entity>

# JSON
{
    "entity": {
        "field": ["A", "B"]
    }
}
```

---

## Próximos Passos

- [Gateway Client](gateway-client.md) - Cliente moderno para API
- [DTOs](dtos.md) - Modelos tipados
- [Guia de Migração](../migration_guide.md) - Migração completa XML → JSON
