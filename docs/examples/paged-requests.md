# Requisições Paginadas

Exemplos de consultas paginadas para grandes volumes de dados com o
`PagedRequestWrapper` (API XML legada).

O `PagedRequestWrapper` é usado pelos métodos de classe
`get_paged_results` (generator) e `get_paged_results_async` (async
generator). Eles recebem uma requisição `CRUDServiceProvider.loadRecords` já
resolvida, o tipo da entidade e o token da sessão que fará as chamadas.
As páginas são carregadas numa thread separada enquanto os itens, já
convertidos para o tipo informado, são entregues.

## Uso Básico

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

# Requisição loadRecords com o critério literal
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_literal_criteria(
    request, Partner, LiteralCriteria("ATIVO = 'S'")
)

ctx = SankhyaContext.from_settings()
try:
    # Itera sobre todos os parceiros ativos (sessão principal: ctx.token)
    count = 0
    for partner in PagedRequestWrapper.get_paged_results(request, Partner, ctx.token):
        count += 1
        print(f"{partner.code}: {partner.name}")

    print(f"Total: {count} parceiros")
finally:
    ctx.dispose()
```

Os demais exemplos usam `request` e `ctx` como acima.

---

## Configuração

### Montando a Requisição

```python
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

# Todos os registros (sem critério)
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_generic(request, Partner)

# Critério a partir de uma entidade de exemplo (ATIVO = 'S' AND CLIENTE = 'S')
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_entity(request, Partner(is_active=True, is_client=True))

# Critério literal montado com a API fluente
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_literal_criteria(
    request,
    Partner,
    LiteralCriteria.equals("ATIVO", "S").and_(LiteralCriteria.is_not_null("EMAIL")),
)
```

Para escolher os campos retornados, monte o `DataSet` à mão (veja
[Queries Avançadas](advanced-queries.md#requisicao-manual)); o wrapper
preenche `page_number` e `pager_id` a cada página.

### Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `request` | - | Requisição `loadRecords` resolvida (é alterada a cada página) |
| `entity_type` | - | Tipo da entidade retornada |
| `token` | - | Token da sessão (`ctx.token` ou `ctx.acquire_new_session()`) |
| `timeout` | 5 minutos (`timedelta`) | Tempo total da iteração; excedido, lança `TimeoutError` |
| `process_data` | `None` | Recebe cada página antes que os itens dela sejam entregues |
| `max_results` | `-1` (sem limite) | Limite total de itens |
| `on_page_loaded` / `on_page_error` / `on_page_processed` | `None` | Callbacks de progresso |

O tamanho da página é definido pelo servidor: como no SDK .NET, uma página
com 150 ou 300 itens indica que há mais; qualquer outra quantidade (ou
`max_results` atingido) encerra a paginação. Não há cache: cada iteração
consulta o servidor de novo.

---

## Callbacks

### Monitorando Progresso

Os callbacks recebem um `PagedRequestEventArgs` e rodam na thread de
carregamento; o valor de retorno é ignorado e exceções são apenas
registradas no log.

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper
from sankhya_sdk.value_objects import PagedRequestEventArgs


def on_page_loaded(args: PagedRequestEventArgs) -> None:
    """Chamado quando uma página é carregada."""
    print(f"Página {args.current_page}/{args.total_pages or '?'}")
    print(f"  Itens na página: {args.quantity_loaded}")
    print(f"  Total carregado: {args.total_loaded}")


def on_page_processed(args: PagedRequestEventArgs) -> None:
    """Chamado depois que os itens da página entram na fila."""
    if args.progress_percentage is not None:
        print(f"  Progresso: {args.progress_percentage:.0f}%")


def on_error(args: PagedRequestEventArgs) -> None:
    """Chamado em caso de erro; a paginação é interrompida."""
    print(f"Erro na página {args.current_page}: {args.exception}")


partners = list(
    PagedRequestWrapper.get_paged_results(
        request,
        Partner,
        ctx.token,
        on_page_loaded=on_page_loaded,
        on_page_processed=on_page_processed,
        on_page_error=on_error,
    )
)
```

| Atributo | Descrição |
|----------|-----------|
| `entity_type` | Tipo da entidade |
| `current_page` | Página atual (começa em 1) |
| `quantity_loaded` | Itens da página |
| `total_loaded` | Itens carregados até agora |
| `total_pages` | Total informado pelo servidor (`None` se desconhecido) |
| `exception` | Erro (em `on_page_error`) |
| `has_error`, `is_complete`, `progress_percentage` | Propriedades derivadas |

---

## Processamento em Lote

### Processar por Página

`process_data` recebe cada página já convertida antes que os itens dela
sejam entregues pelo generator (como o `ProcessData` do .NET). Se
`process_data` lançar exceção, os itens daquela página não são entregues e a
exceção é propagada:

```python
from typing import List

from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

processed = 0


def process_batch(partners: List[Partner]) -> None:
    """Processa uma página de parceiros."""
    global processed
    for partner in partners:
        pass  # Lógica de processamento (ex.: enviar a um sistema externo)
    processed += len(partners)
    print(f"Processados: {processed}")


for partner in PagedRequestWrapper.get_paged_results(
    request, Partner, ctx.token, process_data=process_batch
):
    pass  # Os itens também são entregues aqui, depois de cada página

print(f"Total processado: {processed}")
```

---

## Limitando Resultados

### Com max_results

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

count = 0
for partner in PagedRequestWrapper.get_paged_results(
    request, Partner, ctx.token, max_results=500  # Máximo 500 resultados
):
    count += 1
    print(f"{count}: {partner.name}")

print(f"Total: {count}")  # Máximo 500
```

### Interrupção Manual

Interromper o `for` (ou fechar o generator) cancela o carregamento das
próximas páginas:

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

found_target = False

for partner in PagedRequestWrapper.get_paged_results(request, Partner, ctx.token):
    if partner.name == "ALVO":
        print(f"Encontrado: {partner.code}")
        found_target = True
        break  # Para a iteração e o carregamento

if not found_target:
    print("Alvo não encontrado")
```

---

## Versão Assíncrona

Não existem `AsyncSankhyaContext` nem `AsyncPagedRequestWrapper`: use
`get_paged_results_async` com `async for`. Nela, `process_data` deve ser uma
função assíncrona:

```python
import asyncio
from typing import List

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper


async def save_page(partners: List[Partner]) -> None:
    await asyncio.sleep(0)  # ex.: gravação assíncrona em outro sistema


async def process_partners() -> None:
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    ServiceRequestExtensions.resolve_with_literal_criteria(
        request, Partner, LiteralCriteria("ATIVO = 'S'")
    )

    ctx = SankhyaContext.from_settings()
    async with ctx:
        count = 0
        async for partner in PagedRequestWrapper.get_paged_results_async(
            request, Partner, ctx.token, process_data=save_page
        ):
            count += 1

        print(f"Processados: {count}")


asyncio.run(process_partners())
```

---

## Sessão Dedicada

O token define a sessão usada nas chamadas. Para não disputar a sessão
principal com outras operações, adquira uma sessão própria e finalize-a ao
terminar:

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

token = ctx.acquire_new_session()  # Login extra
try:
    partners = list(PagedRequestWrapper.get_paged_results(request, Partner, token))
finally:
    ctx.finalize_session(token)  # Logout
```

---

## Tratamento de Erros

Uma página que falha interrompe a paginação: o generator lança
`PagedRequestException` (`sankhya_sdk.request_wrappers`), com a exceção da
página em `inner_exception`. O wrapper não repete páginas; a única repetição
é a política de retry do `SankhyaWrapper` (deadlock, timeout, sessão
expirada...), aplicada a cada requisição antes de a página ser dada como
falha (veja [Tratamento de Erros](../core-concepts/error-handling.md)).

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestException, PagedRequestWrapper

try:
    for partner in PagedRequestWrapper.get_paged_results(request, Partner, ctx.token):
        print(partner.name)
except PagedRequestException as e:
    page_error = e.inner_exception  # Exceção da página (com .page preenchido)
    print(f"Falha na página {getattr(page_error, 'page', '?')}: {e}")
except TimeoutError as e:
    print(f"Tempo esgotado: {e}")
```

---

## Exportação para Arquivo

```python
import csv

from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestWrapper

with open("partners.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Código", "Nome", "CNPJ/CPF", "Email"])

    count = 0
    for partner in PagedRequestWrapper.get_paged_results(request, Partner, ctx.token):
        writer.writerow([
            partner.code,
            partner.name,
            partner.document or "",
            partner.email_address or "",
        ])
        count += 1

        if count % 1000 == 0:
            print(f"Exportados: {count}")

    print(f"Total exportado: {count}")
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de requisições paginadas.

Demonstra paginação com callbacks, progresso e exportação.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import LiteralCriteria, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import PagedRequestException, PagedRequestWrapper
from sankhya_sdk.value_objects import PagedRequestEventArgs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PartnerExporter:
    """Exporta parceiros com paginação."""

    def __init__(self, context: SankhyaContext):
        self.context = context
        self.total = 0
        self.errors = 0

    def _on_page_loaded(self, args: PagedRequestEventArgs) -> None:
        logger.info(
            f"Página {args.current_page}/{args.total_pages or '?'} "
            f"({args.quantity_loaded} itens, {args.total_loaded} no total)"
        )

    def _on_error(self, args: PagedRequestEventArgs) -> None:
        self.errors += 1
        logger.error(f"Erro página {args.current_page}: {args.exception}")

    def export(self, criteria: LiteralCriteria, output_file: str) -> None:
        """Exporta parceiros para JSON."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        ServiceRequestExtensions.resolve_with_literal_criteria(request, Partner, criteria)

        partners: List[Dict[str, Any]] = []

        try:
            for partner in PagedRequestWrapper.get_paged_results(
                request,
                Partner,
                self.context.token,
                timeout=timedelta(minutes=10),
                on_page_loaded=self._on_page_loaded,
                on_page_error=self._on_error,
            ):
                partners.append({
                    "codigo": partner.code,
                    "nome": partner.name,
                    "cnpj_cpf": partner.document,
                    "email": partner.email_address,
                    "tipo": partner.fiscal_type.value if partner.fiscal_type else None,
                })
                self.total += 1
        except PagedRequestException as e:
            logger.error(f"Paginação interrompida: {e}")

        # Salva resultado
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "total": self.total,
                "errors": self.errors,
                "partners": partners,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Exportados {self.total} parceiros para {output_file}")


def main() -> None:
    ctx = SankhyaContext.from_settings()
    try:
        exporter = PartnerExporter(ctx)
        exporter.export(LiteralCriteria("ATIVO = 'S'"), "partners_export.json")
    finally:
        ctx.dispose()


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Gerenciamento de Sessões](session-management.md) - Multi-threading
- [Queries Avançadas](advanced-queries.md) - Filtros complexos
- [Tratamento de Erros](error-handling.md) - Exceções
