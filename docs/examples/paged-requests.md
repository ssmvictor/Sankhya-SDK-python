# Requisições Paginadas

Exemplos de consultas paginadas para grandes volumes de dados.

## Uso Básico

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import PagedRequestWrapper
from sankhya_sdk.transport_entities import Partner
from dotenv import load_dotenv

load_dotenv()

with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(ctx.wrapper)
    
    # Itera sobre todos os parceiros ativos
    count = 0
    for partner in paged.get_paged_results(Partner, "ATIVO = 'S'"):
        count += 1
        print(f"{partner.code_partner}: {partner.name}")
    
    print(f"Total: {count} parceiros")
```

---

## Configuração

### Parâmetros do Wrapper

```python
paged = PagedRequestWrapper(
    wrapper=ctx.wrapper,
    page_size=100,        # Itens por página
    max_results=5000,     # Limite total (0 = sem limite)
    timeout=600,          # Timeout em segundos
    enable_cache=True     # Cache em memória
)
```

### Com Opções de Query

```python
from sankhya_sdk.helpers import EntityQueryOptions

options = EntityQueryOptions(
    include_fields=["CODPARC", "NOMEPARC", "EMAIL"],
    order_by="NOMEPARC ASC"
)

for partner in paged.get_paged_results_with_options(
    Partner,
    "ATIVO = 'S'",
    options
):
    process(partner)
```

---

## Callbacks

### Monitorando Progresso

```python
from sankhya_sdk.value_objects import PagedRequestEventArgs

def on_page_loaded(args: PagedRequestEventArgs):
    """Chamado quando uma página é carregada."""
    print(f"Página {args.current_page}/{args.total_pages}")
    print(f"  Itens na página: {args.items_in_page}")
    print(f"  Total processado: {args.total_processed}")

def on_page_processed(args: PagedRequestEventArgs):
    """Chamado quando uma página é processada."""
    elapsed = args.elapsed_time_ms / 1000
    print(f"  Processada em {elapsed:.2f}s")

def on_error(args: PagedRequestEventArgs):
    """Chamado em caso de erro."""
    print(f"Erro na página {args.current_page}: {args.error}")
    # Retorne True para continuar, False para parar
    return True

# Configura callbacks
paged.on_page_loaded = on_page_loaded
paged.on_page_processed = on_page_processed
paged.on_error = on_error

# Executa
for partner in paged.get_paged_results(Partner, "CODPARC > 0"):
    process(partner)
```

---

## Processamento em Lote

### Processar por Lotes

```python
def process_batch(partners: list[Partner]):
    """Processa um lote de parceiros."""
    for partner in partners:
        # Lógica de processamento
        update_external_system(partner)
    
    return len(partners)

with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(ctx.wrapper, page_size=50)
    
    batch = []
    processed = 0
    
    for partner in paged.get_paged_results(Partner, "ATIVO = 'S'"):
        batch.append(partner)
        
        # Processa a cada 50 itens
        if len(batch) >= 50:
            processed += process_batch(batch)
            print(f"Processados: {processed}")
            batch = []
    
    # Processa últimos itens
    if batch:
        processed += process_batch(batch)
    
    print(f"Total processado: {processed}")
```

---

## Limitando Resultados

### Com max_results

```python
with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(
        ctx.wrapper,
        page_size=100,
        max_results=500  # Máximo 500 resultados
    )
    
    count = 0
    for partner in paged.get_paged_results(Partner, "CODPARC > 0"):
        count += 1
        print(f"{count}: {partner.name}")
    
    print(f"Total: {count}")  # Máximo 500
```

### Interrupção Manual

```python
with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(ctx.wrapper)
    
    found_target = False
    
    for partner in paged.get_paged_results(Partner, "CODPARC > 0"):
        if partner.name == "ALVO":
            print(f"Encontrado: {partner.code_partner}")
            found_target = True
            break  # Para a iteração
    
    if not found_target:
        print("Alvo não encontrado")
```

---

## Versão Assíncrona

```python
import asyncio
from sankhya_sdk import AsyncSankhyaContext
from sankhya_sdk.request_wrappers import AsyncPagedRequestWrapper

async def process_partners():
    async with AsyncSankhyaContext.from_settings() as ctx:
        paged = AsyncPagedRequestWrapper(ctx.wrapper)
        
        count = 0
        async for partner in paged.get_paged_results_async(
            Partner,
            "ATIVO = 'S'"
        ):
            count += 1
            await process_async(partner)
        
        print(f"Processados: {count}")

asyncio.run(process_partners())
```

---

## Cache de Resultados

```python
with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(
        ctx.wrapper,
        enable_cache=True  # Habilita cache
    )
    
    # Primeira iteração - carrega da API
    partners_1 = list(paged.get_paged_results(Partner, "ATIVO = 'S'"))
    print(f"Primeira: {len(partners_1)} parceiros")
    
    # Segunda iteração - usa cache
    partners_2 = list(paged.get_paged_results(Partner, "ATIVO = 'S'"))
    print(f"Segunda: {len(partners_2)} parceiros (do cache)")
    
    # Limpar cache
    paged.clear_cache()
```

---

## Tratamento de Erros

```python
from sankhya_sdk.exceptions import PagedRequestException

def on_error(args):
    """Handler de erro que tenta recuperar."""
    print(f"Erro na página {args.current_page}: {args.error}")
    
    # Tenta até 3 vezes
    if args.retry_count < 3:
        args.should_retry = True
        args.retry_delay_ms = 1000 * (args.retry_count + 1)
        return True  # Continuar
    
    return False  # Parar

with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(ctx.wrapper)
    paged.on_error = on_error
    
    try:
        for partner in paged.get_paged_results(Partner, "CODPARC > 0"):
            process(partner)
    except PagedRequestException as e:
        print(f"Falha após retries: {e}")
        print(f"Última página: {e.page_number}/{e.total_pages}")
```

---

## Exportação para Arquivo

```python
import csv

with SankhyaContext.from_settings() as ctx:
    paged = PagedRequestWrapper(ctx.wrapper, page_size=500)
    
    with open("partners.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Código", "Nome", "CNPJ/CPF", "Email"])
        
        count = 0
        for partner in paged.get_paged_results(Partner, "ATIVO = 'S'"):
            writer.writerow([
                partner.code_partner,
                partner.name,
                partner.cgc_cpf or "",
                partner.email or ""
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

from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import PagedRequestWrapper
from sankhya_sdk.transport_entities import Partner
from sankhya_sdk.value_objects import PagedRequestEventArgs
from sankhya_sdk.exceptions import PagedRequestException
from dotenv import load_dotenv
import json
import logging
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PartnerExporter:
    """Exporta parceiros com paginação."""
    
    def __init__(self, context):
        self.context = context
        self.paged = PagedRequestWrapper(
            context.wrapper,
            page_size=100,
            timeout=600
        )
        self.paged.on_page_loaded = self._on_page_loaded
        self.paged.on_error = self._on_error
        self.total = 0
        self.errors = 0
    
    def _on_page_loaded(self, args: PagedRequestEventArgs):
        elapsed = args.elapsed_time_ms / 1000
        logger.info(
            f"Página {args.current_page}/{args.total_pages} "
            f"({args.items_in_page} itens) em {elapsed:.2f}s"
        )
    
    def _on_error(self, args: PagedRequestEventArgs):
        self.errors += 1
        logger.error(f"Erro página {args.current_page}: {args.error}")
        return True  # Continuar
    
    def export(self, criteria: str, output_file: str):
        """Exporta parceiros para JSON."""
        partners = []
        
        try:
            for partner in self.paged.get_paged_results(Partner, criteria):
                partners.append({
                    "codigo": partner.code_partner,
                    "nome": partner.name,
                    "cnpj_cpf": partner.cgc_cpf,
                    "email": partner.email,
                    "tipo": partner.type_partner,
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
                "partners": partners
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exportados {self.total} parceiros para {output_file}")


def main():
    with SankhyaContext.from_settings() as ctx:
        exporter = PartnerExporter(ctx)
        exporter.export("ATIVO = 'S'", "partners_export.json")


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Gerenciamento de Sessões](session-management.md) - Multi-threading
- [Queries Avançadas](advanced-queries.md) - Filtros complexos
- [Tratamento de Erros](error-handling.md) - Exceções
