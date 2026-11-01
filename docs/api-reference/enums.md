# Enumerações

Documentação das enumerações (enums) da API XML legada
(`sankhya_sdk.enums`, também exportadas por `sankhya_sdk`).

## Visão Geral

```python
from sankhya_sdk.enums import (
    BillingType,
    FiscalPersonType,
    InvoiceStatus,
    MovementType,
    ReferenceLevel,
    SankhyaWarningLevel,
    ServiceEnvironment,
    ServiceName,
    ServiceRequestType,
    # ... e mais
)
```

Enums disponíveis: `BillingType`, `FiscalClassification`,
`FiscalInvoiceStatus`, `FiscalPersonType`, `FreightType`, `InventoryType`,
`InvoiceFollowUpReference`, `InvoiceFreightType`, `InvoiceStatus`,
`MovementType`, `OrderHistoryEvent`, `ParameterType`, `ProductSource`,
`ProductSourceType`, `ProductSuggestionType`, `ProductUse`, `ReferenceLevel`,
`SankhyaWarningLevel`, `SankhyaWarningType`, `SellerType`, `ServiceCategory`,
`ServiceEnvironment`, `ServiceModule`, `ServiceName`, `ServiceRequestType`,
`ServiceResponseStatus`, `ServiceType`, `SystemParameterType` e
`TradingSubType`.

## Sistema de Metadados

Quase todos os enums derivam de `MetadataEnum` (`sankhya_sdk.enums._metadata`),
porta dos atributos `InternalValue`/`HumanReadable` do .NET. O `value` de
cada membro é o nome do membro no .NET (ex.: `"Corporation"`); o valor usado
na API fica em `internal_value`:

```python
from sankhya_sdk.enums import FiscalPersonType

# Valor interno (usado na API)
print(FiscalPersonType.CORPORATION.internal_value)  # J

# Descrição legível
print(FiscalPersonType.CORPORATION.human_readable)  # Pessoa jurídica

# A partir do valor interno (ValueError se não existir)
person_type = FiscalPersonType.from_internal_value("F")
print(repr(person_type))  # <FiscalPersonType.INDIVIDUAL: 'Individual'>

# str() retorna o valor interno
print(str(FiscalPersonType.CORPORATION))  # J
```

`metadata` retorna o `EnumMetadata` completo (`internal_value`,
`human_readable` e, em `ServiceName`, `service_module`, `service_category`
e `service_type`). `ServiceResponseStatus` e `ServiceCategory` são enums
inteiros simples, sem metadados.

---

## ServiceName

Nomes dos serviços da API XML: `internal_value` é o `serviceName` enviado na
URL e no `<serviceRequest>`.

```python
from sankhya_sdk.enums import ServiceName

service = ServiceName.CRUD_SERVICE_FIND
print(service.internal_value)    # CRUDServiceProvider.loadRecords
print(service.service_category.name)  # CRUD
```

| Membro | `internal_value` |
|--------|------------------|
| `CRUD_FIND` | `crud.find` |
| `CRUD_REMOVE` | `crud.remove` |
| `CRUD_SAVE` | `crud.save` |
| `CRUD_SERVICE_FIND` | `CRUDServiceProvider.loadRecords` |
| `CRUD_SERVICE_REMOVE` | `CRUDServiceProvider.removeRecord` |
| `CRUD_SERVICE_SAVE` | `CRUDServiceProvider.saveRecord` |
| `LOGIN` | `MobileLoginSP.login` |
| `LOGOUT` | `MobileLoginSP.logout` |
| `NFE_GET_AUTHORIZATION` | `ServicosNfeSP.buscaProcessamentoLote` |
| `NFE_GENERATE_LOT` | `ServicosNfeSP.gerarLote` |
| `INVOICE_INCLUDE` | `CACSP.incluirNota` |
| `INVOICE_HEADER_INCLUDE` | `CACSP.incluirAlterarCabecalhoNota` |
| `INVOICE_ITEM_INCLUDE` | `CACSP.incluirAlterarItemNota` |
| `INVOICE_BILL` | `SelecaoDocumentoSP.faturar` |
| `INVOICE_ACCOMPANIMENTS` | `ServicosNfeSP.getAcompanhamentosNota` |
| `INVOICE_AUTOMATIC_LOW` | `BaixaAutomaticaSP.baixar` |
| `INVOICE_CONFIRM` | `CACSP.confirmarNota` |
| `INVOICE_CANCEL` | `CACSP.cancelarNota` |
| `INVOICE_DUPLICATE` | `CACSP.duplicarNota` |
| `INVOICE_REMOVE` | `CACSP.excluirNotas` |
| `INVOICE_ITEM_REMOVE` | `CACSP.excluirItemNota` |
| `INVOICE_BIND_WITH_ORDER` | `CACSP.ligarPedidoNota` |
| `INVOICE_FLAG_AS_NOT_PENDING` | `CACSP.marcarPedidosComoNaoPendentes` |
| `FINANCIAL_REVERSAL` | `BaixaFinanceiroSP.estornarTitulo` |
| `WARNING_RECEIVE` | `AvisoSistemaSP.getNovosAvisos` |
| `WARNING_SEND` | `AvisoSistemaSP.enviarAviso` |
| `MESSAGE_SEND` | `AvisoSistemaSP.enviarMensagem` |
| `FILE_OPEN` | `RepositorioArquivoSP.abreArquivo` |
| `FILE_DELETE` | `ImportacaoImagemSP.deletaArquivos` |
| `SESSION_GET_ALL` | `SessionManagerSP.getCoreSessions` |
| `SESSION_KILL` | `SessionManagerSP.killSession` |
| `UNLINK_SHIPPING` | `MovimentacaoFinanceiraSP.desvincularRemessa` |
| `DB_EXPLORER_EXECUTE_QUERY` | `DbExplorerSP.executeQuery` |

---

## Enums de Conexão e Requisição

### ServiceEnvironment

Representa os ambientes de serviço.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `NONE` | `0` | Nenhum |
| `PRODUCTION` | `8180` | Produção |
| `SANDBOX` | `8280` | Sandbox |
| `TRAINING` | `8380` | Treinamento |

### ServiceRequestType

Representa o tipo de requisição de serviço.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `DEFAULT` | `Default` | Default |
| `SIMPLE_CRUD` | `SimpleCrud` | Simple CRUD |
| `PAGED_CRUD` | `PagedCrud` | Paged CRUD (retrieve) |
| `QUERYABLE_CRUD` | `QueryableCrud` | Queryable CRUD |
| `ON_DEMAND_CRUD` | `OnDemandCrud` | On demand CRUD (Create, Update, Delete) |
| `KNOW_SERVICES` | `KnowServices` | Know services |

### ReferenceLevel

Representa o nível de referência.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `NONE` | `None` | None |
| `FIRST` | `First` | First |
| `SECOND` | `Second` | Second |
| `THIRD` | `Third` | Third |
| `FOURTH` | `Fourth` | Fourth |
| `FIFTH` | `Fifth` | Fifth |
| `SIXTH` | `Sixth` | Sixth |

### ServiceResponseStatus

Representa o status de uma resposta de serviço.

| Membro | Valor |
|--------|-------|
| `ERROR` | `0` |
| `OK` | `1` |
| `INFO` | `2` |
| `TIMEOUT` | `3` |
| `SERVICE_CANCELED` | `4` |

---

## Enums de Parceiro

### FiscalPersonType

Representa o tipo de uma pessoa fiscal.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `INDIVIDUAL` | `F` | Pessoa física |
| `CORPORATION` | `J` | Pessoa jurídica |

### FiscalClassification

Representa a classificação fiscal de uma entidade.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `FINAL_CUSTOMER` | `C` | Consumidor Final |
| `ICMS_FREE` | `I` | Isento de ICMS |
| `RURAL_PRODUCER` | `P` | Produtor Rural |
| `RETAILER` | `R` | Revendedor |
| `USE_TOP` | `T` | Usar a da TOP |
| `TAXPAYER_CUSTOMER` | `X` | Consumidor Contribuinte |

---

## Enums de Nota Fiscal

### InvoiceStatus

Representa o status de uma fatura.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `SERVICE` | `A` | Atendimento |
| `RELEASED` | `L` | Liberada |
| `PENDING` | `P` | Pendente |

### FiscalInvoiceStatus

Representa o status de uma nota fiscal.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `SENT` | `I` | Enviada |
| `DENIED` | `D` | Denegada |
| `APPROVED` | `A` | Aprovada |
| `WAITING_AUTHORIZATION` | `E` | Aguardando autorização |
| `WAITING_CORRECTION` | `R` | Aguardando correção |
| `VALIDATION_ERROR` | `V` | Com erro de validação |
| `PENDING_RETURN` | `P` | Pendente de retorno |
| `SENT_DPEC` | `S` | Enviada DPEC |
| `NOT_NFE` | `M` | Não é NF-e |
| `NOT_NFSE` | `M` | Não é NFS-e |
| `NFE_THIRD` | `T` | NF-e terceiro |

### MovementType

Representa o tipo de movimento.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `NONE` | `""` | Nenhum |
| `DEPOSIT` | `1` | NF Depósito |
| `WARRANT` | `2` | PD Devol. / Procuração / Warrant |
| `OUTPUT` | `3` | Saídas |
| `BILLING` | `4` | Faturamento |
| `RD8` | `8` | RD8 |
| `BANK_MOVEMENT` | `B` | Movimento bancário |
| `PURCHASE` | `C` | Compra |
| `SALES_RETURN` | `D` | Devolução de venda |
| `PURCHASE_RETURN` | `E` | Devolução de compra |
| `PRODUCTION` | `F` | Produção |
| `PAYMENT` | `G` | Pagamento |
| `FINANCIAL` | `I` | Financeiro |
| `REQUEST_ORDER` | `J` | Pedido de Requisição |
| `TRANSFER_ORDER` | `K` | Pedido de Transferência |
| `REQUEST_RETURN` | `L` | Devolução de Requisição |
| `TRANSFER_RETURN` | `M` | Devolução de Transferência |
| `INPUT` | `N` | Entradas |
| `PURCHASE_ORDER` | `O` | Pedido de compra |
| `SALES_ORDER` | `P` | Pedido de venda |
| `REQUEST` | `Q` | Requisição |
| `RECEIPT` | `R` | Recebimento |
| `TRANSFER` | `T` | Transferência |
| `SALES` | `V` | Venda |
| `MODEL` | `Z` | Modelo |

### BillingType

Representa os diferentes tipos de faturamento.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `NONE` | `""` | Nenhum |
| `NORMAL` | `FaturamentoNormal` | Faturamento normal |
| `DIRECT` | `FaturamentoDireto` | Faturamento direto |

---

## Enums de Avisos

### SankhyaWarningLevel

Representa os níveis de alerta no Sankhya.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `URGENT` | `0` | Urgente |
| `ERROR` | `1` | Erro |
| `WARNING` | `2` | Alerta |
| `INFORMATION` | `3` | Informação |

### SankhyaWarningType

Representa os tipos de alerta no Sankhya.

| Membro | `internal_value` | `human_readable` |
|--------|------------------|------------------|
| `NONE` | `0` | Nenhum |
| `USER` | `usuario` | Usuário |
| `GROUP` | `grupo` | Grupo |

---

## Uso em Entidades

Os campos das entidades de transporte usam os enums diretamente; a
conversão de/para o valor interno é feita na serialização e na conversão
das respostas:

```python
from sankhya_sdk.enums import FiscalPersonType
from sankhya_sdk.helpers import EntityDynamicSerialization
from sankhya_sdk.models.transport import Partner

# Usando enum em entidade (enviado como TIPPESSOA = 'J')
partner = Partner(name="ACME LTDA", fiscal_type=FiscalPersonType.CORPORATION)

# Resposta do servidor (texto) convertida para o enum
partner = EntityDynamicSerialization({"CODPARC": "1", "TIPPESSOA": "F"}).convert_to_type(Partner)
if partner.fiscal_type is not None:
    print(partner.fiscal_type.human_readable)  # Pessoa física
```

## Próximos Passos

- [Exceções](exceptions.md) - Hierarquia de exceções
- [Modelos](models.md) - Modelos de serviço
- [Core](core.md) - Classes principais
