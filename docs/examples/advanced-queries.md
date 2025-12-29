# Queries Avançadas

Exemplos de filtros complexos, joins e ordenação.

## FilterExpression

### Operadores Básicos

```python
from sankhya_sdk.helpers import FilterExpression

# Igualdade
filter_expr = FilterExpression().equals("CODPARC", 1)
# CODPARC = 1

# Diferença
filter_expr = FilterExpression().not_equals("STATUS", "C")
# STATUS <> 'C'

# Maior que
filter_expr = FilterExpression().greater_than("VLRNOTA", 1000)
# VLRNOTA > 1000

# Menor ou igual
filter_expr = FilterExpression().less_or_equal("ESTOQUE", 10)
# ESTOQUE <= 10

# LIKE
filter_expr = FilterExpression().like("NOMEPARC", "%LTDA%")
# NOMEPARC LIKE '%LTDA%'

# IN
filter_expr = FilterExpression().in_("CODPARC", [1, 2, 3])
# CODPARC IN (1, 2, 3)

# BETWEEN
from datetime import date
filter_expr = FilterExpression().between(
    "DTMOV",
    date(2024, 1, 1),
    date(2024, 12, 31)
)
# DTMOV BETWEEN '01/01/2024' AND '31/12/2024'

# IS NULL / IS NOT NULL
filter_expr = FilterExpression().is_null("EMAIL")
# EMAIL IS NULL

filter_expr = FilterExpression().is_not_null("CGC_CPF")
# CGC_CPF IS NOT NULL
```

---

## Filtros Compostos

### AND / OR

```python
from sankhya_sdk.helpers import FilterExpression

# Combinação AND
filter_expr = (
    FilterExpression()
    .equals("ATIVO", "S")
    .and_()
    .equals("TIPPESSOA", "C")
)
# ATIVO = 'S' AND TIPPESSOA = 'C'

# Combinação OR
filter_expr = (
    FilterExpression()
    .equals("TIPPESSOA", "C")
    .or_()
    .equals("TIPPESSOA", "F")
)
# TIPPESSOA = 'C' OR TIPPESSOA = 'F'
```

### Grupos (Parênteses)

```python
filter_expr = (
    FilterExpression()
    .equals("ATIVO", "S")
    .and_()
    .group_start()
        .equals("TIPPESSOA", "C")
        .or_()
        .equals("TIPPESSOA", "A")
    .group_end()
)
# ATIVO = 'S' AND (TIPPESSOA = 'C' OR TIPPESSOA = 'A')
```

### Exemplo Complexo

```python
from datetime import date, timedelta

hoje = date.today()
mes_passado = hoje - timedelta(days=30)

filter_expr = (
    FilterExpression()
    .equals("ATIVO", "S")
    .and_()
    .group_start()
        .in_("TIPPESSOA", ["C", "A"])
    .group_end()
    .and_()
    .greater_or_equal("DTMOV", mes_passado)
    .and_()
    .greater_than("VLRNOTA", 1000)
    .and_()
    .is_not_null("EMAIL")
    .and_()
    .like("NOMEPARC", "%LTDA%")
)

criteria = filter_expr.build()
# ATIVO = 'S' AND (TIPPESSOA IN ('C', 'A')) AND DTMOV >= '...' ...
```

---

## EntityQueryOptions

### Campos Específicos

```python
from sankhya_sdk.helpers import EntityQueryOptions

options = EntityQueryOptions(
    include_fields=["CODPARC", "NOMEPARC", "CGC_CPF", "EMAIL"]
)

partners = crud.find_with_options(Partner, "ATIVO = 'S'", options)
```

### Ordenação

```python
options = EntityQueryOptions(
    order_by="NOMEPARC ASC"
)

# Múltiplas ordenações
options = EntityQueryOptions(
    order_by="ATIVO DESC, NOMEPARC ASC"
)
```

### Limite e Distinct

```python
options = EntityQueryOptions(
    max_results=100,
    distinct=True
)
```

### Incluir Referências

```python
options = EntityQueryOptions(
    include_references=True  # Carrega entidades relacionadas
)

partners = crud.find_with_options(Partner, "CODPARC > 0", options)

for partner in partners:
    # Referências carregadas
    print(partner.city_reference)  # Objeto City, não apenas código
```

---

## Queries com Datas

```python
from datetime import date, datetime, timedelta
from sankhya_sdk.helpers import FilterExpression

# Hoje
today = date.today()

# Últimos 7 dias
last_week = today - timedelta(days=7)
filter_expr = FilterExpression().greater_or_equal("DTMOV", last_week)

# Mês atual
first_day = date(today.year, today.month, 1)
filter_expr = (
    FilterExpression()
    .greater_or_equal("DTMOV", first_day)
    .and_()
    .less_or_equal("DTMOV", today)
)

# Ano específico
filter_expr = (
    FilterExpression()
    .between("DTMOV", date(2024, 1, 1), date(2024, 12, 31))
)
```

---

## Queries com Valores Numéricos

```python
from decimal import Decimal
from sankhya_sdk.helpers import FilterExpression

# Valor exato
filter_expr = FilterExpression().equals("VLRNOTA", Decimal("1500.00"))

# Faixa de valores
filter_expr = FilterExpression().between("VLRNOTA", 1000, 5000)

# Maior que zero
filter_expr = FilterExpression().greater_than("ESTOQUE", 0)

# Porcentagem
filter_expr = FilterExpression().less_than("PERCDESC", 50)
```

---

## Queries com Texto

```python
from sankhya_sdk.helpers import FilterExpression

# Contém texto
filter_expr = FilterExpression().like("NOMEPARC", "%COMERCIO%")

# Começa com
filter_expr = FilterExpression().like("NOMEPARC", "EMPRESA%")

# Termina com
filter_expr = FilterExpression().like("EMAIL", "%@gmail.com")

# Case insensitive (depende do banco)
filter_expr = FilterExpression().like("UPPER(NOMEPARC)", "%LTDA%")
```

---

## Exemplo com CRUD

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner, InvoiceHeader
from sankhya_sdk.helpers import FilterExpression, EntityQueryOptions
from datetime import date, timedelta

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Query complexa de parceiros
    partner_filter = (
        FilterExpression()
        .equals("ATIVO", "S")
        .and_()
        .in_("TIPPESSOA", ["C", "A"])
        .and_()
        .is_not_null("EMAIL")
    )
    
    partner_options = EntityQueryOptions(
        include_fields=["CODPARC", "NOMEPARC", "EMAIL", "TIPPESSOA"],
        order_by="NOMEPARC ASC",
        max_results=50
    )
    
    partners = crud.find_with_options(
        Partner,
        partner_filter.build(),
        partner_options
    )
    
    print(f"Parceiros: {len(partners)}")
    
    # Query de notas do último mês
    last_month = date.today() - timedelta(days=30)
    
    invoice_filter = (
        FilterExpression()
        .greater_or_equal("DTMOV", last_month)
        .and_()
        .equals("STATUSNOTA", "F")
        .and_()
        .greater_than("VLRNOTA", 1000)
    )
    
    invoice_options = EntityQueryOptions(
        order_by="VLRNOTA DESC",
        max_results=100
    )
    
    invoices = crud.find_with_options(
        InvoiceHeader,
        invoice_filter.build(),
        invoice_options
    )
    
    print(f"Notas: {len(invoices)}")
    
    for invoice in invoices[:5]:
        print(f"  {invoice.single_number}: R${invoice.total_value}")
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de queries avançadas.

Demonstra construção de filtros complexos e relatórios.
"""

from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner, InvoiceHeader
from sankhya_sdk.helpers import FilterExpression, EntityQueryOptions
from dotenv import load_dotenv
from datetime import date, timedelta
from decimal import Decimal
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_partner_query(
    active_only=True,
    partner_types=None,
    min_purchases=None,
    has_email=False
):
    """Constrói query de parceiros com filtros opcionais."""
    filter_expr = FilterExpression()
    
    if active_only:
        filter_expr.equals("ATIVO", "S")
    
    if partner_types:
        if active_only:
            filter_expr.and_()
        filter_expr.in_("TIPPESSOA", partner_types)
    
    if has_email:
        filter_expr.and_().is_not_null("EMAIL")
    
    if min_purchases:
        filter_expr.and_().greater_or_equal("VLRCOMPRAS", min_purchases)
    
    return filter_expr.build()


def build_invoice_query(
    start_date=None,
    end_date=None,
    min_value=None,
    status=None,
    partner_id=None
):
    """Constrói query de notas com filtros opcionais."""
    filter_expr = FilterExpression()
    has_filter = False
    
    if start_date:
        filter_expr.greater_or_equal("DTMOV", start_date)
        has_filter = True
    
    if end_date:
        if has_filter:
            filter_expr.and_()
        filter_expr.less_or_equal("DTMOV", end_date)
        has_filter = True
    
    if min_value:
        if has_filter:
            filter_expr.and_()
        filter_expr.greater_than("VLRNOTA", min_value)
        has_filter = True
    
    if status:
        if has_filter:
            filter_expr.and_()
        if isinstance(status, list):
            filter_expr.in_("STATUSNOTA", status)
        else:
            filter_expr.equals("STATUSNOTA", status)
        has_filter = True
    
    if partner_id:
        if has_filter:
            filter_expr.and_()
        filter_expr.equals("CODPARC", partner_id)
    
    return filter_expr.build() if has_filter else ""


def main():
    with SankhyaContext.from_settings() as ctx:
        crud = SimpleCRUDRequestWrapper(ctx.wrapper)
        
        # 1. Clientes ativos com email
        logger.info("=== Clientes Ativos com Email ===")
        criteria = build_partner_query(
            active_only=True,
            partner_types=["C", "A"],
            has_email=True
        )
        
        options = EntityQueryOptions(
            include_fields=["CODPARC", "NOMEPARC", "EMAIL"],
            order_by="NOMEPARC",
            max_results=10
        )
        
        partners = crud.find_with_options(Partner, criteria, options)
        for p in partners:
            logger.info(f"  {p.code_partner}: {p.name} - {p.email}")
        
        # 2. Notas do último mês acima de R$5.000
        logger.info("=== Notas do Último Mês > R$5.000 ===")
        criteria = build_invoice_query(
            start_date=date.today() - timedelta(days=30),
            min_value=Decimal("5000"),
            status=["F", "A"]
        )
        
        options = EntityQueryOptions(
            order_by="VLRNOTA DESC",
            max_results=10
        )
        
        invoices = crud.find_with_options(InvoiceHeader, criteria, options)
        
        total = Decimal("0")
        for inv in invoices:
            logger.info(f"  {inv.single_number}: R${inv.total_value}")
            total += inv.total_value or Decimal("0")
        
        logger.info(f"  Total: R${total:,.2f}")


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Tratamento de Erros](error-handling.md) - Exceções
- [Helpers](../api-reference/helpers.md) - API completa
- [Exemplos CRUD](crud-operations.md) - Operações básicas
