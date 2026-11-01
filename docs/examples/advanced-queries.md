# Queries Avançadas

Exemplos de filtros com `LiteralCriteria`, opções de consulta e montagem
manual de requisições (API XML legada).

Existem duas classes com o nome `LiteralCriteria`:

- `sankhya_sdk.helpers.LiteralCriteria`: construtor de expressões
  (`equals`, `like`, `in_`, `and_`, ...), aceito por
  `SimpleCRUDRequestWrapper.*_with_criteria` e por
  `ServiceRequestExtensions.resolve_with_literal_criteria`;
- `sankhya_sdk.models.service.LiteralCriteria`: modelo do XML
  (`expression` e `parameters`), usado ao montar um `DataSet` à mão.

## LiteralCriteria

### Operadores Básicos

```python
from sankhya_sdk.helpers import LiteralCriteria

# Igualdade (strings recebem aspas, com escape de aspas simples)
criteria = LiteralCriteria.equals("CODPARC", 1)
# CODPARC = 1

# Diferença
criteria = LiteralCriteria.not_equals("STATUSNOTA", "P")
# STATUSNOTA <> 'P'

# Maior que
criteria = LiteralCriteria.greater_than("VLRNOTA", 1000)
# VLRNOTA > 1000

# Menor ou igual
criteria = LiteralCriteria.less_or_equal("ESTOQUE", 10)
# ESTOQUE <= 10

# LIKE
criteria = LiteralCriteria.like("NOMEPARC", "%LTDA%")
# NOMEPARC LIKE '%LTDA%'

# IN
criteria = LiteralCriteria.in_("CODPARC", [1, 2, 3])
# CODPARC IN (1, 2, 3)

# BETWEEN (valores numéricos)
criteria = LiteralCriteria.between("VLRNOTA", 1000, 5000)
# VLRNOTA BETWEEN 1000 AND 5000

# IS NULL / IS NOT NULL
criteria = LiteralCriteria.is_null("EMAIL")
# EMAIL IS NULL

criteria = LiteralCriteria.is_not_null("CGC_CPF")
# CGC_CPF IS NOT NULL

# Expressão livre
criteria = LiteralCriteria("DTNEG >= '01/01/2024'")

print(criteria.build_expression())
```

---

## Filtros Compostos

### AND / OR

```python
from sankhya_sdk.helpers import LiteralCriteria

# Combinação AND
criteria = LiteralCriteria.equals("ATIVO", "S").and_(
    LiteralCriteria.equals("TIPPESSOA", "J")
)
# ATIVO = 'S' AND TIPPESSOA = 'J'

# Combinação OR (cada lado fica entre parênteses)
criteria = LiteralCriteria.equals("CLIENTE", "S").or_(
    LiteralCriteria.equals("FORNECEDOR", "S")
)
# (CLIENTE = 'S') OR (FORNECEDOR = 'S')

# Negação
criteria = LiteralCriteria.is_null("EMAIL").not_()
# NOT (EMAIL IS NULL)
```

### Grupos (Parênteses)

`or_` e `not_` já colocam parênteses; `and_` não. Para agrupar uma
expressão, crie um `LiteralCriteria` com os parênteses:

```python
from sankhya_sdk.helpers import LiteralCriteria

tipo = LiteralCriteria.equals("CLIENTE", "S").or_(LiteralCriteria.equals("FORNECEDOR", "S"))
criteria = LiteralCriteria.equals("ATIVO", "S").and_(LiteralCriteria(f"({tipo})"))
# ATIVO = 'S' AND ((CLIENTE = 'S') OR (FORNECEDOR = 'S'))
```

### Exemplo Complexo

```python
from datetime import date, timedelta

from sankhya_sdk.helpers import LiteralCriteria

hoje = date.today()
mes_passado = hoje - timedelta(days=30)

criteria = (
    LiteralCriteria.equals("STATUSNOTA", "L")
    .and_(LiteralCriteria.in_("TIPMOV", ["V", "D"]))
    .and_(LiteralCriteria(f"DTNEG >= '{mes_passado:%d/%m/%Y}'"))
    .and_(LiteralCriteria.greater_than("VLRNOTA", 1000))
)

print(criteria.build_expression())
# STATUSNOTA = 'L' AND TIPMOV IN ('V', 'D') AND DTNEG >= '...' AND VLRNOTA > 1000
```

---

## EntityQueryOptions

`EntityQueryOptions` (`sankhya_sdk.helpers`) é aceito por `try_find`,
`find`, `find_all` e pelos métodos `*_with_criteria` do
`SimpleCRUDRequestWrapper`. Os campos são `max_results`,
`include_references`, `max_reference_depth`, `include_presentation_fields`,
`use_wildcard_fields` e `timeout`. Não há opções de seleção de campos ou de
ordenação; para isso, monte a requisição à mão (próxima seção).

### Limite de Resultados

```python
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

options = EntityQueryOptions(max_results=100)  # rowsLimit

partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=True), options)
```

### Referências

```python
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Sem entidades referenciadas (apenas os campos de Parceiro)
options = EntityQueryOptions(include_references=False)
partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=True), options)

# Referências até o 2º nível (0 a 6; sem a opção, o loadRecords usa o 3º nível)
options = EntityQueryOptions(max_reference_depth=2)
partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=True), options)

for partner in partners:
    # Referências preenchidas quando o servidor as retorna
    if partner.city is not None:
        print(partner.city.name)
```

---

## Requisição Manual

Para escolher os campos retornados, monte o `DataSet` com os modelos de
`sankhya_sdk.models.service` e invoque o serviço pelo contexto. As entidades
da resposta trazem os valores como texto bruto; converta-as com
`EntityDynamicSerialization.convert_to_type`:

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import EntityDynamicSerialization
from sankhya_sdk.models.service import DataSet, Entity, Field, ServiceRequest
from sankhya_sdk.models.service import LiteralCriteria as CriteriaModel
from sankhya_sdk.models.transport import Partner

request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
request.request_body.data_set = DataSet(
    root_entity="Parceiro",
    include_presentation_fields=False,
    rows_limit=50,
    entities=[
        Entity(
            path="",
            fields=[Field(name="CODPARC"), Field(name="NOMEPARC"), Field(name="EMAIL")],
        )
    ],
    literal_criteria=CriteriaModel(expression="ATIVO = 'S' AND EMAIL IS NOT NULL"),
)

with SankhyaContext.from_settings() as wrapper:
    response = wrapper.service_invoker(request)

partners = [
    EntityDynamicSerialization(dict(entity.fields)).convert_to_type(Partner)
    for entity in response.entities
]

# Ordenação no cliente
for partner in sorted(partners, key=lambda p: p.name or ""):
    print(f"{partner.code}: {partner.name} - {partner.email_address}")
```

---

## Queries com Datas

Os construtores numéricos não aceitam datas: formate a data no padrão do
servidor (`dd/mm/aaaa`) e use uma expressão livre:

```python
from datetime import date, timedelta

from sankhya_sdk.helpers import LiteralCriteria


def on_or_after(field: str, value: date) -> LiteralCriteria:
    return LiteralCriteria(f"{field} >= '{value:%d/%m/%Y}'")


def on_or_before(field: str, value: date) -> LiteralCriteria:
    return LiteralCriteria(f"{field} <= '{value:%d/%m/%Y}'")


# Hoje
today = date.today()

# Últimos 7 dias
last_week = today - timedelta(days=7)
criteria = on_or_after("DTNEG", last_week)

# Mês atual
first_day = date(today.year, today.month, 1)
criteria = on_or_after("DTNEG", first_day).and_(on_or_before("DTNEG", today))

# Ano específico
criteria = LiteralCriteria("DTNEG BETWEEN '01/01/2024' AND '31/12/2024'")
```

---

## Queries com Valores Numéricos

```python
from sankhya_sdk.helpers import LiteralCriteria

# Valor exato
criteria = LiteralCriteria.equals("VLRNOTA", 1500.00)

# Faixa de valores
criteria = LiteralCriteria.between("VLRNOTA", 1000, 5000)

# Maior que zero
criteria = LiteralCriteria.greater_than("ESTOQUE", 0)

# Porcentagem
criteria = LiteralCriteria.less_than("PERCDESC", 50)
```

---

## Queries com Texto

```python
from sankhya_sdk.helpers import LiteralCriteria

# Contém texto
criteria = LiteralCriteria.like("NOMEPARC", "%COMERCIO%")

# Começa com
criteria = LiteralCriteria.like("NOMEPARC", "EMPRESA%")

# Termina com
criteria = LiteralCriteria.like("EMAIL", "%@gmail.com")

# Case insensitive (depende do banco)
criteria = LiteralCriteria.like("UPPER(NOMEPARC)", "%LTDA%")
```

---

## Exemplo com CRUD

`SimpleCRUDRequestWrapper.try_find_with_criteria`/`find_with_criteria`
retornam no máximo um registro. Para listas, resolva a requisição com o
critério e use o `PagedRequestWrapper`:

```python
from datetime import date, timedelta

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import InvoiceHeader, Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

ctx = SankhyaContext.from_settings()
try:
    # Query de parceiros
    partner_filter = (
        LiteralCriteria.equals("ATIVO", "S")
        .and_(LiteralCriteria.in_("TIPPESSOA", ["F", "J"]))
        .and_(LiteralCriteria.is_not_null("EMAIL"))
    )

    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    ServiceRequestExtensions.resolve_with_literal_criteria(request, Partner, partner_filter)

    partners = list(
        PagedRequestWrapper.get_paged_results(request, Partner, ctx.token, max_results=50)
    )
    print(f"Parceiros: {len(partners)}")

    # Query de notas do último mês
    last_month = date.today() - timedelta(days=30)

    invoice_filter = (
        LiteralCriteria(f"DTNEG >= '{last_month:%d/%m/%Y}'")
        .and_(LiteralCriteria.equals("STATUSNOTA", "L"))
        .and_(LiteralCriteria.greater_than("VLRNOTA", 1000))
    )

    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    ServiceRequestExtensions.resolve_with_literal_criteria(
        request, InvoiceHeader, invoice_filter
    )

    invoices = list(
        PagedRequestWrapper.get_paged_results(request, InvoiceHeader, ctx.token, max_results=100)
    )
    print(f"Notas: {len(invoices)}")

    # Maiores valores primeiro (ordenação no cliente)
    invoices.sort(key=lambda inv: inv.invoice_value or 0, reverse=True)
    for invoice in invoices[:5]:
        print(f"  {invoice.single_number}: R${invoice.invoice_value}")
finally:
    ctx.dispose()
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de queries avançadas.

Demonstra construção de filtros com LiteralCriteria e relatórios.
"""

import logging
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Type, TypeVar

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import InvoiceHeader, Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=EntityBase)


def combine(parts: List[LiteralCriteria]) -> Optional[LiteralCriteria]:
    """Combina critérios com AND (None se não houver critérios)."""
    if not parts:
        return None
    criteria = parts[0]
    for part in parts[1:]:
        criteria = criteria.and_(part)
    return criteria


def build_partner_query(
    active_only: bool = True,
    person_types: Optional[List[str]] = None,
    has_email: bool = False,
) -> Optional[LiteralCriteria]:
    """Constrói query de parceiros com filtros opcionais."""
    parts: List[LiteralCriteria] = []
    if active_only:
        parts.append(LiteralCriteria.equals("ATIVO", "S"))
    if person_types:
        parts.append(LiteralCriteria.in_("TIPPESSOA", list(person_types)))
    if has_email:
        parts.append(LiteralCriteria.is_not_null("EMAIL"))
    return combine(parts)


def build_invoice_query(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_value: Optional[float] = None,
    statuses: Optional[List[str]] = None,
    partner_id: Optional[int] = None,
) -> Optional[LiteralCriteria]:
    """Constrói query de notas com filtros opcionais."""
    parts: List[LiteralCriteria] = []
    if start_date:
        parts.append(LiteralCriteria(f"DTNEG >= '{start_date:%d/%m/%Y}'"))
    if end_date:
        parts.append(LiteralCriteria(f"DTNEG <= '{end_date:%d/%m/%Y}'"))
    if min_value is not None:
        parts.append(LiteralCriteria.greater_than("VLRNOTA", min_value))
    if statuses:
        parts.append(LiteralCriteria.in_("STATUSNOTA", list(statuses)))
    if partner_id:
        parts.append(LiteralCriteria.equals("CODPARC", partner_id))
    return combine(parts)


def load(
    entity_type: Type[T],
    criteria: Optional[LiteralCriteria],
    token: uuid.UUID,
    max_results: int,
) -> List[T]:
    """Carrega entidades pelo PagedRequestWrapper."""
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    if criteria is not None:
        ServiceRequestExtensions.resolve_with_literal_criteria(request, entity_type, criteria)
    else:
        ServiceRequestExtensions.resolve_generic(request, entity_type)
    return list(
        PagedRequestWrapper.get_paged_results(request, entity_type, token, max_results=max_results)
    )


def main() -> None:
    ctx = SankhyaContext.from_settings()
    try:
        # 1. Parceiros ativos com email
        logger.info("=== Parceiros Ativos com Email ===")
        criteria = build_partner_query(active_only=True, person_types=["F", "J"], has_email=True)
        partners = load(Partner, criteria, ctx.token, max_results=10)
        for p in sorted(partners, key=lambda p: p.name or ""):
            logger.info(f"  {p.code}: {p.name} - {p.email_address}")

        # 2. Notas do último mês acima de R$5.000
        logger.info("=== Notas do Último Mês > R$5.000 ===")
        criteria = build_invoice_query(
            start_date=date.today() - timedelta(days=30),
            min_value=5000,
            statuses=["L", "P"],
        )
        invoices = load(InvoiceHeader, criteria, ctx.token, max_results=10)

        total = Decimal("0")
        for inv in sorted(invoices, key=lambda i: i.invoice_value or 0, reverse=True):
            logger.info(f"  {inv.single_number}: R${inv.invoice_value}")
            total += inv.invoice_value or Decimal("0")

        logger.info(f"  Total: R${total:,.2f}")
    finally:
        ctx.dispose()


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Tratamento de Erros](error-handling.md) - Exceções
- [Helpers](../api-reference/helpers.md) - API completa
- [Exemplos CRUD](crud-operations.md) - Operações básicas
