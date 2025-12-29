# Enumerações

Documentação das enumerações (enums) disponíveis no SDK.

## Visão Geral

O SDK define enums para representar valores fixos da API Sankhya:

```python
from sankhya_sdk.enums import (
    EnvironmentType,
    PartnerType,
    ProductStatus,
    InvoiceStatus,
    OperationType,
    # ... e mais
)
```

## Sistema de Metadados

Cada enum possui metadados que facilitam conversões:

```python
from sankhya_sdk.enums import PartnerType

# Valor interno (usado na API)
print(PartnerType.CLIENT.internal_value)  # "C"

# Descrição amigável
print(PartnerType.CLIENT.description)  # "Cliente"

# A partir de valor interno
partner_type = PartnerType.from_internal_value("C")
print(partner_type)  # PartnerType.CLIENT
```

---

## Enums de Ambiente

### EnvironmentType

Tipos de ambiente da API.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `PRODUCTION` | `"producao"` | Produção |
| `HOMOLOGATION` | `"homologacao"` | Homologação |
| `TRAINING` | `"treinamento"` | Treinamento |

```python
from sankhya_sdk.enums import EnvironmentType

env = EnvironmentType.PRODUCTION
print(env.database_name)  # "SANKHYA_PRODUCAO"
```

---

## Enums de Parceiro

### PartnerType

Tipos de parceiro (cliente/fornecedor).

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `CLIENT` | `"C"` | Cliente |
| `SUPPLIER` | `"F"` | Fornecedor |
| `BOTH` | `"A"` | Ambos (cliente e fornecedor) |
| `CARRIER` | `"T"` | Transportadora |
| `EMPLOYEE` | `"E"` | Funcionário |

```python
from sankhya_sdk.enums import PartnerType

# Criar parceiro como cliente
partner.type_partner = PartnerType.CLIENT.internal_value
```

### PartnerSituation

Situação do parceiro.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `ACTIVE` | `"A"` | Ativo |
| `INACTIVE` | `"I"` | Inativo |
| `PENDING` | `"P"` | Pendente |

---

## Enums de Produto

### ProductStatus

Status de produto.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `ACTIVE` | `"A"` | Ativo |
| `INACTIVE` | `"I"` | Inativo |
| `BLOCKED` | `"B"` | Bloqueado |

### ProductType

Tipos de produto.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `FINISHED` | `"P"` | Produto Acabado |
| `RAW_MATERIAL` | `"M"` | Matéria-prima |
| `SERVICE` | `"S"` | Serviço |
| `ASSET` | `"I"` | Ativo Imobilizado |
| `RESALE` | `"R"` | Revenda |

---

## Enums de Nota Fiscal

### InvoiceStatus

Status de nota fiscal.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `PENDING` | `"P"` | Pendente |
| `APPROVED` | `"A"` | Aprovada |
| `CANCELLED` | `"C"` | Cancelada |
| `BILLED` | `"F"` | Faturada |
| `DENIED` | `"N"` | Negada |

### InvoiceType

Tipos de nota fiscal.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `ENTRY` | `"E"` | Entrada |
| `EXIT` | `"S"` | Saída |

### MovementType

Tipos de movimentação.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `SALE` | `"V"` | Venda |
| `PURCHASE` | `"C"` | Compra |
| `TRANSFER` | `"T"` | Transferência |
| `RETURN` | `"D"` | Devolução |

---

## Enums de Operação

### OperationType

Tipos de operação CRUD.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `FIND` | `"loadRecords"` | Busca |
| `INSERT` | `"saveRecord"` | Inserção |
| `UPDATE` | `"saveRecord"` | Atualização |
| `DELETE` | `"removeRecord"` | Exclusão |

### CRUDOperationType

Tipos de operação para wrapper simples.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `READ` | `"R"` | Leitura |
| `CREATE` | `"C"` | Criação |
| `UPDATE` | `"U"` | Atualização |
| `DELETE` | `"D"` | Exclusão |

---

## Enums de Serviço

### ServiceStatus

Status de resposta de serviço.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `SUCCESS` | `"1"` | Sucesso |
| `ERROR` | `"0"` | Erro |
| `WARNING` | `"2"` | Aviso |

### MessageType

Tipos de mensagem de status.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `ERROR` | `"E"` | Erro |
| `WARNING` | `"W"` | Aviso |
| `INFO` | `"I"` | Informação |
| `SUCCESS` | `"S"` | Sucesso |

---

## Enums de Serviços Específicos

### BillingType

Tipos de faturamento.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `INVOICE` | `"NF"` | Nota Fiscal |
| `ORDER` | `"PD"` | Pedido |
| `CONTRACT` | `"CT"` | Contrato |

### NFeEventType

Tipos de evento NFe.

| Membro | Valor Interno | Descrição |
|--------|---------------|-----------|
| `CANCELLATION` | `"110111"` | Cancelamento |
| `CORRECTION` | `"110110"` | Carta de Correção |
| `MANIFESTATION` | `"210200"` | Manifestação |

---

## Criando Enums Customizados

Para criar enums customizados compatíveis com o SDK:

```python
from sankhya_sdk.enums.base import SankhyaEnum, EnumMetadata

class MeuStatus(SankhyaEnum):
    """Status customizado."""
    
    ATIVO = EnumMetadata("A", "Ativo")
    INATIVO = EnumMetadata("I", "Inativo")
    PENDENTE = EnumMetadata("P", "Pendente")
    
    def __init__(self, metadata: EnumMetadata):
        self._internal_value = metadata.internal_value
        self._description = metadata.description
    
    @property
    def internal_value(self) -> str:
        return self._internal_value
    
    @property
    def description(self) -> str:
        return self._description
    
    @classmethod
    def from_internal_value(cls, value: str) -> "MeuStatus":
        for member in cls:
            if member.internal_value == value:
                return member
        raise ValueError(f"Valor não encontrado: {value}")
```

## Uso em Entidades

```python
from sankhya_sdk.transport_entities import Partner
from sankhya_sdk.enums import PartnerType

# Usando enum em entidade
partner = Partner()
partner.type_partner = PartnerType.CLIENT.internal_value

# Convertendo de volta
partner_type = PartnerType.from_internal_value(partner.type_partner)
print(partner_type.description)  # "Cliente"
```

## Próximos Passos

- [Exceções](exceptions.md) - Hierarquia de exceções
- [Modelos](models.md) - Modelos de serviço
- [Core](core.md) - Classes principais
