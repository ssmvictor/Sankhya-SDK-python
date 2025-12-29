# Enumerações do SDK Sankhya

O SDK Sankhya utiliza um sistema de enums tipados com metadados para replicar a funcionalidade dos atributos do .NET.

## Sistema de Metadados

A classe base `MetadataEnum` permite associar metadados a cada membro do enum, como valores internos da API e descrições legíveis.

### Propriedades Disponíveis

Todos os enums que herdam de `MetadataEnum` possuem as seguintes propriedades:

- `internal_value`: O valor string usado na comunicação com a API Sankhya.
- `human_readable`: Uma descrição amigável do membro do enum.
- `metadata`: Acesso direto ao objeto `EnumMetadata`.

## Exemplo de Uso

```python
from sankhya_sdk.enums import FiscalPersonType, ServiceName

# Acessando valores
print(FiscalPersonType.INDIVIDUAL.internal_value)  # Saída: "F"
print(FiscalPersonType.INDIVIDUAL.human_readable)  # Saída: "Pessoa física"

# Usando em strings (serialização automática para internal_value)
print(f"Tipo: {FiscalPersonType.CORPORATION}")  # Saída: "Tipo: J"

# Enums complexos (ServiceName)
service = ServiceName.CRUD_FIND
print(service.service_module)    # Saída: ServiceModule.MGE
print(service.service_category)  # Saída: ServiceCategory.CRUD
print(service.service_type)      # Saída: ServiceType.RETRIEVE
```

## Lista de Enums Disponíveis

| Enum | Descrição |
|------|-----------|
| `ServiceName` | Nomes dos serviços da API |
| `ServiceModule` | Módulos do sistema (MGE, MGECOM, etc) |
| `ServiceCategory` | Categorias de serviço (CRUD, Invoice, etc) |
| `ServiceType` | Tipos de serviço (Retrieve, Transactional, etc) |
| `FiscalPersonType` | Tipo de pessoa (Física/Jurídica) |
| `InvoiceStatus` | Status de faturas |
| `MovementType` | Tipos de movimento financeiro/estoque |
| ... e outros 22 enums. | |

## Implementação Técnica

Os enums são implementados usando uma tupla no valor do membro, onde o primeiro elemento é o valor real do enum e o segundo é um objeto `EnumMetadata`.

```python
class MyEnum(MetadataEnum):
    MEMBER = ("MemberValue", EnumMetadata(internal_value="m", human_readable="Human Member"))
```
