# Modelos

Documentação dos modelos de serviço (`sankhya_sdk.models.service`) e das
entidades de transporte (`sankhya_sdk.models.transport`) da API XML legada.

## Modelos de Serviço

### ServiceRequest

Requisição à API (`<serviceRequest>`): o serviço (`ServiceName`) e o corpo.
Normalmente o corpo é preenchido por `ServiceRequestExtensions` (veja
[Helpers](helpers.md#servicerequestextensions)) ou pelos wrappers.

```python
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_literal_criteria(
    request, Partner, LiteralCriteria("CODPARC > 0")
)

print(request.to_xml_string())
```

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `service` | `ServiceName` | Serviço (o `serviceName` é `service.internal_value`) |
| `request_body` | `RequestBody` | Corpo da requisição (criado vazio por padrão) |
| `no_auth` | `bool` | Se não requer autenticação |

Serialização: `to_xml()`, `to_xml_string()`, `to_xml_bytes()`; leitura:
`ServiceRequest.from_xml_string(xml)`.

---

### RequestBody

Corpo da requisição. Cada serviço usa um subconjunto dos campos:

| Campo | Usado por |
|-------|-----------|
| `data_set` (`DataSet`) | `CRUDServiceProvider.loadRecords`/`saveRecord`/`removeRecord` |
| `entity` (`Entity`) | `crud.find`/`crud.save`/`crud.remove` |
| `invoice`, `invoices`, `single_numbers`, `client_events`... | Serviços de nota (`KnowServicesRequestWrapper`) |
| `config`, `paths` | Arquivos (`RepositorioArquivoSP.abreArquivo`...) |
| `session`, `system_warning`, `system_message` | Sessões, avisos e mensagens |
| `username`, `password` | Login |
| `custom_query` | `DbExplorerSP.executeQuery` |

Para escolher campos e critério à mão, monte o `DataSet` (veja
[Queries Avançadas](../examples/advanced-queries.md#requisicao-manual)).

---

### ServiceResponse

Resposta da API (`<serviceResponse>`), retornada por `service_invoker`.
Respostas com erro (`status="0"`) não chegam ao chamador: o `SankhyaWrapper`
as transforma em exceções (veja [Exceções](exceptions.md)).

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import (
    EntityDynamicSerialization,
    LiteralCriteria,
    ServiceRequestExtensions,
)
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_literal_criteria(
    request, Partner, LiteralCriteria("CODPARC > 0")
)

with SankhyaContext.from_settings() as wrapper:
    response = wrapper.service_invoker(request)

print(response.is_success, response.status)
for entity in response.entities:
    # Valores em texto bruto; converta para a entidade tipada
    partner = EntityDynamicSerialization(dict(entity.fields)).convert_to_type(Partner)
    print(partner.code, partner.name)
```

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `service` | `ServiceName \| None` | Serviço |
| `status` | `ServiceResponseStatus` | `OK` (1), `ERROR` (0), `INFO` (2), `TIMEOUT` (3), `SERVICE_CANCELED` (4) |
| `status_message` | `StatusMessage \| None` | Mensagem de status (decodificada de Base64) |
| `response_body` | `ResponseBody \| None` | Corpo da resposta |
| `transaction_id`, `error_code`, `error_level`, `pending_printing` | | Atributos do `<serviceResponse>` |

#### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `is_success` / `is_error` | `bool` | Status `OK` / `ERROR` |
| `status_message_text` | `str \| None` | Texto da mensagem de status |
| `entities` | `list` | Entidades de `crud.find` e do `loadRecords` (`EntityDynamic`) |
| `first_entity` | | Primeira entidade (ou `None`) |

A `statusMessage` chega do servidor em Base64 (como no SDK .NET, que sempre
a decodifica); o SDK a decodifica ao ler a resposta, e um texto que não é
Base64 válido é mantido como veio.

---

### ResponseBody

Corpo da resposta. Os campos mais usados:

| Campo | Conteúdo |
|-------|----------|
| `crud_service_provider_entities` | Entidades do `loadRecords` (com `pager_id`, `total_pages`) |
| `crud_service_entities` | Entidades do `crud.find` |
| `pager` | Dados de paginação |
| `primary_key` (`<pk>`), `key` | Chave primária retornada / chave de arquivo (`open_file`) |
| `sessions`, `warnings`, `messages`, `invoices`, `client_events`... | Respostas dos serviços específicos |
| `jsession_id`, `code_user` | Login |

---

## Entidades de Transporte

### TransportEntityBase

Classe base (Pydantic) das entidades de `sankhya_sdk.models.transport`. Cada
entidade é decorada com `@entity("NomeNoSankhya")` e declara os campos com
`entity_key`, `entity_element`, `entity_reference`, `entity_ignore` e
`entity_custom_data` (veja
[Sistema de Entidades](../core-concepts/entity-system.md)).

- Validação na criação e na atribuição (`validate_assignment`), sem campos
  extras (`extra="forbid"`).
- Só os campos atribuídos são enviados ao servidor (`model_fields_set`).
- Campos `entity_ignore` (ex.: `Product.quantity`) não são enviados ao
  servidor e ficam fora de `model_dump()`/`model_dump_json()`; o valor
  continua acessível pelo atributo.

Entidades disponíveis: `Partner`, `Product`, `InvoiceHeader`, `Address`,
`City`, `State`, `Region`, `Neighborhood`, `PartnerComplement`, `Seller`,
`ProductCost`, `CodeBars`, `ProductSuggestedSale` e `ServiceFile`.

### Partner, Product e InvoiceHeader

```python
from datetime import datetime
from decimal import Decimal

from sankhya_sdk.enums import FiscalPersonType
from sankhya_sdk.models.transport import InvoiceHeader, Partner, Product

partner = Partner(
    code=1,
    name="Cliente LTDA",
    document="12345678000199",
    fiscal_type=FiscalPersonType.CORPORATION,
    is_client=True,
)

product = Product(code=100, name="Produto Exemplo", code_volume="UN", is_active=True)

header = InvoiceHeader(
    single_number=12345,
    code_partner=1,
    code_company=1,
    operation_type=1001,
    date_traded=datetime.now(),
    invoice_value=Decimal("1500.50"),
)
```

#### Campos

#### Partner (Parceiro)

| Campo | Tipo | Elemento | Observação |
|-------|------|----------|------------|
| `code` | `int` | `CODPARC` | chave |
| `name` | `str` | `NOMEPARC` |  |
| `company_name` | `str` | `RAZAOSOCIAL` |  |
| `fiscal_type` | `FiscalPersonType` | `TIPPESSOA` |  |
| `fiscal_classification` | `FiscalClassification` | `CLASSIFICMS` |  |
| `email_address` | `str` | `EMAIL` |  |
| `email_address_fiscal_invoice` | `str` | `EMAILNFE` |  |
| `is_active` | `bool` | `ATIVO` |  |
| `is_client` | `bool` | `CLIENTE` |  |
| `is_seller` | `bool` | `VENDEDOR` |  |
| `is_user` | `bool` | `USUARIO` |  |
| `is_supplier` | `bool` | `FORNECEDOR` |  |
| `send_fiscal_invoice_by_email` | `bool` | `EMAILDANFE` |  |
| `document` | `str` | `CGC_CPF` |  |
| `identity` | `str` | `IDENTINSCESTAD` |  |
| `state_inscription` | `str` | `INSCESTADNAUF` |  |
| `zip_code` | `str` | `CEP` |  |
| `code_address` | `int` | `CODEND` |  |
| `address_number` | `str` | `NUMEND` |  |
| `address_complement` | `str` | `COMPLEMENTO` |  |
| `code_neighborhood` | `int` | `CODBAI` |  |
| `code_city` | `int` | `CODCID` |  |
| `code_region` | `int` | `CODREG` |  |
| `telephone` | `str` | `TELEFONE` |  |
| `telephone_extension_line` | `str` | `RAMAL` |  |
| `mobile_phone` | `str` | `FAX` |  |
| `date_created` | `datetime` | `DTCAD` |  |
| `date_changed` | `datetime` | `DTALTER` |  |
| `authorization_group` | `str` | `GRUPOAUTOR` |  |
| `latitude` | `str` | `LATITUDE` |  |
| `longitude` | `str` | `LONGITUDE` |  |
| `notes` | `str` | `OBSERVACOES` |  |
| `address` | `Address` | - | referência |
| `neighborhood` | `Neighborhood` | - | referência |
| `city` | `City` | - | referência |
| `region` | `Region` | - | referência |
| `complement` | `PartnerComplement` | - | referência |

#### Product (Produto)

| Campo | Tipo | Elemento | Observação |
|-------|------|----------|------------|
| `code` | `int` | `CODPROD` | chave |
| `is_active` | `bool` | `ATIVO` |  |
| `name` | `str` | `DESCRPROD` |  |
| `complement` | `str` | `COMPLDESC` |  |
| `description` | `str` | `CARACTERISTICAS` |  |
| `code_volume` | `str` | `CODVOL` |  |
| `code_volume_component` | `str` | - | `entity_ignore` |
| `code_group` | `int` | `CODGRUPOPROD` |  |
| `net_weight` | `Decimal` | `PESOLIQ` |  |
| `gross_weight` | `Decimal` | `PESOBRUTO` |  |
| `quantity` | `Decimal` | - | `entity_ignore` |
| `brand` | `str` | `MARCA` |  |
| `reference` | `str` | `REFERENCIA` |  |
| `width` | `Decimal` | `LARGURA` |  |
| `height` | `Decimal` | `ALTURA` |  |
| `length` | `Decimal` | `ESPESSURA` |  |
| `ncm` | `str` | `NCM` |  |
| `source` | `ProductSource` | `ORIGPROD` |  |
| `use` | `ProductUse` | `USOPROD` |  |
| `is_sale_allowed_outside_kit` | `bool` | `VENCOMPINDIV` |  |
| `product_father` | `Product` | - | referência |
| `product_replacement` | `Product` | - | referência |
| `cost` | `ProductCost` | - | `entity_ignore` |
| `components` | `List[Product]` | - | coleção |
| `codes_bars` | `List[CodeBars]` | - | coleção |
| `suggestions` | `List[ProductSuggestedSale]` | - | coleção |
| `alternative_images` | `List[ServiceFile]` | - | coleção |
| `image` | `ServiceFile` | - | `entity_ignore` |

#### InvoiceHeader (CabecalhoNota)

| Campo | Tipo | Elemento | Observação |
|-------|------|----------|------------|
| `single_number` | `int` | `NUNOTA` | chave |
| `code_company` | `int` | `CODEMP` |  |
| `code_partner` | `int` | `CODPARC` |  |
| `code_partner_destination` | `int` | `CODPARCDEST` |  |
| `code_contact` | `int` | `CODCONTATO` |  |
| `operation_type` | `int` | `CODTIPOPER` |  |
| `code_trade_type` | `int` | `CODTIPVENDA` |  |
| `invoice_number` | `int` | `NUMNOTA` |  |
| `code_seller` | `int` | `CODVEND` |  |
| `code_result_center` | `int` | `CODCENCUS` |  |
| `code_nature` | `int` | `CODNAT` |  |
| `code_partner_carrier` | `int` | `CODPARCTRANSP` |  |
| `date_traded` | `datetime` | `DTNEG` |  |
| `date_imported` | `datetime` | `DTENTSAI` |  |
| `date_billed` | `datetime` | `DTFATUR` |  |
| `date_expected_delivery` | `datetime` | `DTPREVENT` |  |
| `date_changed` | `datetime` | `DTALTER` |  |
| `freight_value` | `Decimal` | `VLRFRETE` |  |
| `invoice_value` | `Decimal` | `VLRNOTA` |  |
| `note` | `str` | `OBSERVACAO` |  |
| `fiscal_invoice_key` | `str` | `CHAVENFE` |  |
| `movement_type` | `MovementType` | `TIPMOV` |  |
| `freight_type` | `FreightType` | `CIF_FOB` |  |
| `invoice_status` | `InvoiceStatus` | `STATUSNOTA` |  |
| `invoice_freight_type` | `InvoiceFreightType` | `TIPFRETE` |  |
| `fiscal_invoice_status` | `FiscalInvoiceStatus` | `STATUSNFE` |  |
| `confirmed` | `bool` | `CONFIRMADA` |  |
| `pending` | `bool` | `PENDENTE` |  |
| `movement_time` | `timedelta` | `HRMOV` |  |
| `partner` | `Partner` | - | referência |
| `partner_destination` | `Partner` | - | referência |
| `partner_carrier` | `Partner` | - | referência |
| `partner_royalties` | `Partner` | - | referência |
| `seller` | `Seller` | - | referência |

Não há entidade de transporte para itens de nota: os itens usados pelo
`KnowServicesRequestWrapper` (`create_invoice`, `add_invoice_items`) são o
modelo de serviço `sankhya_sdk.models.service.InvoiceItem`.

---

## Filtros e Opções

`LiteralCriteria` e `EntityQueryOptions` estão documentados em
[Helpers](helpers.md).

```python
from sankhya_sdk.helpers import EntityQueryOptions, LiteralCriteria

criteria = (
    LiteralCriteria.equals("CODPARC", 1)
    .and_(LiteralCriteria.greater_than("VLRNOTA", 1000))
    .and_(LiteralCriteria.like("NOMEPARC", "%LTDA%"))
)
print(criteria.build_expression())
# CODPARC = 1 AND VLRNOTA > 1000 AND NOMEPARC LIKE '%LTDA%'

options = EntityQueryOptions(max_results=100, include_references=True)
```

---

## Criando Entidades Customizadas

```python
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.models.transport import TransportEntityBase


@entity("AD_CONTATO")
class Contato(TransportEntityBase):
    """Entidade customizada para contatos."""

    id_contato: Optional[int] = entity_key(entity_element("IDCONTATO", default=None))
    code_partner: Optional[int] = entity_element("CODPARC", default=None)
    nome: Optional[str] = entity_element("NOME", default=None)
    email: Optional[str] = entity_element("EMAIL", default=None)
    telefone: Optional[str] = entity_element("TELEFONE", default=None)


contato = Contato(id_contato=1, nome="Maria")
print(contato.model_dump(exclude_unset=True))  # {'id_contato': 1, 'nome': 'Maria'}
```

Veja [Entidades Customizadas](../examples/custom-entities.md) para o uso com
os wrappers.

## Próximos Passos

- [Request Wrappers](request-wrappers.md) - Wrappers de operação
- [Sistema de Entidades](../core-concepts/entity-system.md) - Criação de entidades
- [Helpers](helpers.md) - Utilitários
