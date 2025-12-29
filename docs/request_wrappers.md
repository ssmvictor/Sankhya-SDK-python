# Request Wrappers

Este módulo fornece wrappers de alto nível para operações de serviço no Sankhya.

## SimpleCRUDRequestWrapper

Wrapper para operações CRUD simples (Find, Update, Remove) em entidades do Sankhya.

```python
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Inicialização
SimpleCRUDRequestWrapper.initialize()

# Buscar entidade
partner = Partner(code=123)
result = SimpleCRUDRequestWrapper.try_find(partner)

# Atualizar entidade
result.name = "Novo Nome"
SimpleCRUDRequestWrapper.update(result)

# Remover entidade
SimpleCRUDRequestWrapper.remove(partner)

# Liberar recursos
SimpleCRUDRequestWrapper.dispose()
```

---

## PagedRequestWrapper

Wrapper para requisições paginadas de grandes conjuntos de dados.

### Características

- **Carregamento paralelo**: Páginas são carregadas em thread/task separada
- **Generator/Async Generator**: Retorna resultados incrementalmente via yield
- **Callbacks de progresso**: Notifica sobre carregamento de páginas
- **Processamento on-demand**: Callback para processar lotes de dados
- **Timeout configurável**: Evita operações penduradas
- **Max results**: Limita quantidade de resultados retornados

### Uso Básico (Síncrono)

```python
from datetime import timedelta
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.request_wrappers import PagedRequestWrapper, SimpleCRUDRequestWrapper
from your_entities import Partner

# Inicializa wrapper
SimpleCRUDRequestWrapper.initialize()
token = SimpleCRUDRequestWrapper._session_token

# Configura requisição
request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
# ... configurar request_body conforme necessário

# Itera sobre resultados
for partner in PagedRequestWrapper.get_paged_results(
    request=request,
    entity_type=Partner,
    token=token,
    timeout=timedelta(minutes=5),
    max_results=1000,
):
    print(f"Parceiro: {partner.name}")

# Libera recursos
SimpleCRUDRequestWrapper.dispose()
```

### Uso com Callbacks

```python
from sankhya_sdk.value_objects import PagedRequestEventArgs

def on_page_loaded(args: PagedRequestEventArgs):
    print(f"Página {args.current_page}: {args.quantity_loaded} itens")
    if args.total_pages:
        progress = args.progress_percentage
        print(f"Progresso: {progress:.1f}%")

def on_error(args: PagedRequestEventArgs):
    print(f"Erro na página {args.current_page}: {args.exception}")

for partner in PagedRequestWrapper.get_paged_results(
    request=request,
    entity_type=Partner,
    token=token,
    on_page_loaded=on_page_loaded,
    on_page_error=on_error,
):
    process(partner)
```

### Processamento On-Demand

```python
def enrich_partners(batch: List[Partner]):
    """Enriquece lotes de parceiros com dados adicionais."""
    for partner in batch:
        # Buscar informações complementares
        partner.extra_info = fetch_extra_info(partner.code)

for partner in PagedRequestWrapper.get_paged_results(
    request=request,
    entity_type=Partner,
    token=token,
    process_data=enrich_partners,
):
    # Parceiro já enriquecido
    save_to_database(partner)
```

### Uso Assíncrono

```python
import asyncio

async def process_partners():
    async for partner in PagedRequestWrapper.get_paged_results_async(
        request=request,
        entity_type=Partner,
        token=token,
        timeout=timedelta(minutes=10),
    ):
        await process_async(partner)

asyncio.run(process_partners())
```

### Processamento Assíncrono On-Demand

```python
async def enrich_partners_async(batch: List[Partner]):
    """Enriquece lotes de forma assíncrona."""
    tasks = [fetch_extra_info_async(p.code) for p in batch]
    results = await asyncio.gather(*tasks)
    for partner, info in zip(batch, results):
        partner.extra_info = info

async for partner in PagedRequestWrapper.get_paged_results_async(
    request=request,
    entity_type=Partner,
    token=token,
    process_data=enrich_partners_async,
):
    await save_to_database_async(partner)
```

---

## PagedRequestEventArgs

Argumentos de evento para operações paginadas.

### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `entity_type` | `Type[EntityBase]` | Tipo da entidade sendo carregada |
| `current_page` | `int` | Número da página atual (1-indexed) |
| `total_loaded` | `int` | Total de itens carregados até o momento |
| `quantity_loaded` | `Optional[int]` | Quantidade de itens na página atual |
| `total_pages` | `Optional[int]` | Total de páginas (se disponível) |
| `exception` | `Optional[Exception]` | Exceção ocorrida (se houver) |

### Propriedades

| Propriedade | Tipo | Descrição |
|-------------|------|-----------|
| `has_error` | `bool` | Verifica se há erro associado |
| `is_complete` | `bool` | Verifica se carregamento está completo |
| `progress_percentage` | `Optional[float]` | Percentual de progresso (0-100) |

---

## PagedRequestException

Exceção específica para erros de requisição paginada.

```python
from sankhya_sdk.request_wrappers import PagedRequestException

try:
    for item in PagedRequestWrapper.get_paged_results(...):
        process(item)
except PagedRequestException as e:
    print(f"Erro na página {e.page}: {e}")
    if e.inner_exception:
        print(f"Causa: {e.inner_exception}")
```

---

## Comparação: SimpleCRUDRequestWrapper vs PagedRequestWrapper

| Característica | SimpleCRUD | PagedRequest |
|----------------|------------|--------------|
| **Uso** | Operações simples | Grandes conjuntos de dados |
| **Resultados** | Lista completa | Generator (lazy) |
| **Memória** | Carrega tudo | Streaming |
| **Timeout** | N/A | Configurável |
| **Callbacks** | N/A | Progresso, erro |
| **Async** | Sim | Sim |
| **Max Results** | Via options | Parâmetro direto |

---

## Boas Práticas

### Timeout

Configure timeout adequado para o volume esperado de dados:

```python
# Para datasets pequenos (<1000 registros)
timeout = timedelta(minutes=2)

# Para datasets grandes (>10000 registros)
timeout = timedelta(minutes=15)
```

### Max Results

Use `max_results` para limitar consumo de memória e tempo:

```python
# Limita a 1000 resultados
for item in PagedRequestWrapper.get_paged_results(
    ...,
    max_results=1000,
):
    process(item)
```

### Tratamento de Erros

Sempre trate exceções e use callbacks de erro:

```python
def on_error(args):
    logger.error(f"Página {args.current_page} falhou: {args.exception}")
    # Notificar monitoramento, etc.

try:
    for item in PagedRequestWrapper.get_paged_results(
        ...,
        on_page_error=on_error,
    ):
        process(item)
except PagedRequestException as e:
    handle_fatal_error(e)
```

### Processamento em Lotes

Use `process_data` para operações que se beneficiam de batching:

```python
def batch_insert(items: List[Partner]):
    """Insert otimizado em lote."""
    db.execute_many(
        "INSERT INTO partners ...",
        [(p.code, p.name) for p in items]
    )

for item in PagedRequestWrapper.get_paged_results(
    ...,
    process_data=batch_insert,
):
    pass  # Itens já foram inseridos no callback
```
