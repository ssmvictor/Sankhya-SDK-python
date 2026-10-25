# Gerenciamento de Sessões

Exemplos de gerenciamento de sessões, multi-threading e async/await com a
API XML legada (`SankhyaContext`). Os conceitos estão em
[Gerenciamento de Sessões](../core-concepts/session-management.md).

## Sessão Única

```python
from sankhya_sdk import SankhyaContext

# Context manager gerencia login/logout automaticamente.
# A variável do `with` recebe o SankhyaWrapper da sessão principal.
with SankhyaContext.from_settings() as wrapper:
    print(f"Conectado: {wrapper.user_code}")
    # Operações...
# Logout automático
```

---

## Múltiplas Sessões

### Adquirir e Finalizar

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

request1 = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_entity(request1, Partner(code=1))
request2 = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
ServiceRequestExtensions.resolve_with_entity(request2, Partner(code=2))

ctx = SankhyaContext.from_settings()
try:
    # Adquire sessões paralelas (um login cada)
    token1 = ctx.acquire_new_session()
    token2 = ctx.acquire_new_session()

    print(f"Sessão 1: {token1}")
    print(f"Sessão 2: {token2}")

    # Usa sessões específicas
    result1 = SankhyaContext.service_invoker_with_token(request1, token1)
    result2 = SankhyaContext.service_invoker_with_token(request2, token2)

    # Finaliza sessões
    ctx.finalize_session(token1)
    ctx.finalize_session(token2)
finally:
    # Fecha contexto principal
    ctx.dispose()
```

---

## Multi-threading

O `SimpleCRUDRequestWrapper` guarda uma única sessão em atributos de classe,
compartilhada por todas as threads (as requisições dessa sessão são
serializadas). Para uma sessão por thread, monte as requisições e use
`SankhyaContext.service_invoker_with_token`. As entidades da resposta chegam
com os valores em texto bruto e são convertidas com
`EntityDynamicSerialization.convert_to_type`:

### ThreadPoolExecutor

```python
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import EntityDynamicSerialization, ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner


def find_partner(token: uuid.UUID, code: int) -> Optional[Partner]:
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    ServiceRequestExtensions.resolve_with_entity(request, Partner(code=code))
    response = SankhyaContext.service_invoker_with_token(request, token)
    if not response.entities:
        return None
    fields = dict(response.entities[0].fields)  # valores em texto bruto
    return EntityDynamicSerialization(fields).convert_to_type(Partner)


def save_partner(token: uuid.UUID, partner: Partner) -> None:
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
    ServiceRequestExtensions.resolve_with_entity(request, partner)
    SankhyaContext.service_invoker_with_token(request, token)


def process_partner(ctx: SankhyaContext, partner_id: int) -> str:
    """Processa parceiro em thread separada."""
    token = ctx.acquire_new_session()
    try:
        # Cada thread tem sessão própria
        partner = find_partner(token, partner_id)
        if partner:
            partner.email_address = f"updated_{partner_id}@email.com"
            save_partner(token, partner)
            return f"Atualizado: {partner_id}"
        return f"Não encontrado: {partner_id}"
    finally:
        ctx.finalize_session(token)


# Uso
ctx = SankhyaContext.from_settings()
partner_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

try:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_partner, ctx, pid): pid
            for pid in partner_ids
        }

        for future in as_completed(futures):
            pid = futures[future]
            try:
                result = future.result()
                print(result)
            except Exception as e:
                print(f"Erro {pid}: {e}")
finally:
    ctx.dispose()
```

### Thread Locks

```python
import threading
import uuid
from typing import List

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

ctx = SankhyaContext.from_settings()
results: List[int] = []
results_lock = threading.Lock()


def process_item(token: uuid.UUID, code: int) -> int:
    """Retorna quantos registros o servidor devolveu para o código."""
    request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
    ServiceRequestExtensions.resolve_with_entity(request, Partner(code=code))
    response = SankhyaContext.service_invoker_with_token(request, token)
    return len(response.entities)


def worker(thread_id: int, items: List[int]) -> None:
    """Worker thread com lock para resultados."""
    token = ctx.acquire_new_session()
    local_results = []

    try:
        for item in items:
            local_results.append(process_item(token, item))
    finally:
        ctx.finalize_session(token)

    # Adiciona resultados de forma thread-safe
    with results_lock:
        results.extend(local_results)


# Divide trabalho
all_items = list(range(1, 101))
chunks = [all_items[i:i+20] for i in range(0, len(all_items), 20)]

threads = [
    threading.Thread(target=worker, args=(i, chunk))
    for i, chunk in enumerate(chunks)
]

for t in threads:
    t.start()

for t in threads:
    t.join()

print(f"Total processado: {len(results)}")
ctx.dispose()
```

---

## Async/Await

O `SimpleCRUDRequestWrapper` tem versões assíncronas de `try_find`, `find`,
`update` e `remove` (`*_async`), que executam a chamada HTTP em uma thread.
Não há dependências extras.

### Básico

```python
import asyncio

from sankhya_sdk import SankhyaContext
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


async def main() -> None:
    ctx = SankhyaContext.from_settings()
    try:
        SimpleCRUDRequestWrapper.initialize(ctx)

        # Busca assíncrona
        partner = await SimpleCRUDRequestWrapper.try_find_async(Partner(code=1))
        if partner:
            print(f"{partner.code}: {partner.name}")
    finally:
        SimpleCRUDRequestWrapper.dispose()
        ctx.dispose()

asyncio.run(main())
```

### Operações Paralelas

```python
import asyncio
from typing import Optional

from sankhya_sdk import SankhyaContext
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


async def fetch_partner(partner_id: int) -> Optional[Partner]:
    """Busca parceiro de forma assíncrona."""
    return await SimpleCRUDRequestWrapper.try_find_async(Partner(code=partner_id))


async def main() -> None:
    ctx = SankhyaContext.from_settings()
    try:
        SimpleCRUDRequestWrapper.initialize(ctx)

        # Busca múltiplos parceiros sem bloquear o event loop
        # (as requisições da sessão do wrapper são serializadas)
        partner_ids = [1, 2, 3, 4, 5]

        tasks = [fetch_partner(pid) for pid in partner_ids]
        partners = await asyncio.gather(*tasks)

        for partner in partners:
            if partner:
                print(f"{partner.code}: {partner.name}")
    finally:
        SimpleCRUDRequestWrapper.dispose()
        ctx.dispose()

asyncio.run(main())
```

### Semaphore para Limite de Concorrência

```python
import asyncio
from typing import Optional

from sankhya_sdk import SankhyaContext
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


async def process_with_semaphore(sem: asyncio.Semaphore, item: int) -> Optional[Partner]:
    """Processa com limite de concorrência."""
    async with sem:
        return await SimpleCRUDRequestWrapper.try_find_async(Partner(code=item))


async def main() -> None:
    ctx = SankhyaContext.from_settings()
    try:
        SimpleCRUDRequestWrapper.initialize(ctx)

        # Máximo 10 tarefas simultâneas
        sem = asyncio.Semaphore(10)

        items = list(range(1, 101))

        tasks = [process_with_semaphore(sem, item) for item in items]
        results = await asyncio.gather(*tasks)

        print(f"Processados: {len(results)}")
    finally:
        SimpleCRUDRequestWrapper.dispose()
        ctx.dispose()

asyncio.run(main())
```

---

## Sessões entre Processos

Não há transferência de sessões entre processos: o registro de sessões do
`SankhyaContext` vive na memória do processo. Cada processo deve criar o seu
próprio contexto (`SankhyaContext.from_settings()`) e liberá-lo com
`dispose()`.

---

## Tratamento de Sessão Expirada

O `SankhyaWrapper` já trata sessões expiradas: ao receber
`não autorizado`, ele autentica de novo com as mesmas credenciais e repete a
requisição. Se a sessão continuar sendo recusada, a exceção chega ao seu
código, e uma saída é recriar o contexto:

```python
from typing import Optional

from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import ServiceRequestInvalidAuthorizationException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


def find_with_new_context(code: int) -> Optional[Partner]:
    """Busca recriando o contexto se a sessão continuar sendo recusada."""
    for attempt in range(2):
        ctx = SankhyaContext.from_settings()
        try:
            SimpleCRUDRequestWrapper.initialize(ctx)
            return SimpleCRUDRequestWrapper.try_find(Partner(code=code))
        except ServiceRequestInvalidAuthorizationException:
            if attempt == 1:
                raise
            print("Sessão recusada, recriando o contexto")
        finally:
            SimpleCRUDRequestWrapper.dispose()
            ctx.dispose()
    return None


# Uso
partner = find_with_new_context(1)
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de gerenciamento de sessões.

Demonstra multi-threading com pool de sessões.
"""

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set

from sankhya_sdk import SankhyaContext
from sankhya_sdk.enums import ServiceName
from sankhya_sdk.helpers import ServiceRequestExtensions
from sankhya_sdk.models.service import ServiceRequest
from sankhya_sdk.models.transport import Partner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionPool:
    """Pool de sessões para uso multi-thread."""

    def __init__(self, context: SankhyaContext, pool_size: int = 5) -> None:
        self.context = context
        self.pool_size = pool_size
        self._lock = threading.Lock()
        self._available: List[uuid.UUID] = []
        self._in_use: Set[uuid.UUID] = set()

        # Cria sessões
        for _ in range(pool_size):
            token = context.acquire_new_session()
            self._available.append(token)

        logger.info(f"Pool criado com {pool_size} sessões")

    def acquire(self) -> uuid.UUID:
        """Adquire sessão do pool."""
        with self._lock:
            if not self._available:
                raise RuntimeError("Sem sessões disponíveis")

            token = self._available.pop()
            self._in_use.add(token)
            return token

    def release(self, token: uuid.UUID) -> None:
        """Devolve sessão ao pool."""
        with self._lock:
            if token in self._in_use:
                self._in_use.remove(token)
                self._available.append(token)

    def dispose(self) -> None:
        """Fecha todas as sessões."""
        for token in self._available + list(self._in_use):
            try:
                self.context.finalize_session(token)
            except Exception as e:
                logger.error(f"Erro ao fechar sessão {token}: {e}")


def process_batch(pool: SessionPool, batch_id: int, items: List[int]) -> int:
    """Processa lote usando sessão do pool."""
    token = pool.acquire()
    try:
        processed = 0
        for item in items:
            request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
            ServiceRequestExtensions.resolve_with_entity(request, Partner(code=item))
            response = SankhyaContext.service_invoker_with_token(request, token)
            if response.entities:
                processed += 1

        logger.info(f"Batch {batch_id}: processados {processed}/{len(items)}")
        return processed
    finally:
        pool.release(token)


def main() -> None:
    ctx = SankhyaContext.from_settings()
    pool = SessionPool(ctx, pool_size=5)

    try:
        # Divide trabalho em lotes
        items = list(range(1, 101))
        batches = [items[i:i+10] for i in range(0, len(items), 10)]

        total = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(process_batch, pool, i, batch): i
                for i, batch in enumerate(batches)
            }

            for future in as_completed(futures):
                batch_id = futures[future]
                try:
                    result = future.result()
                    total += result
                except Exception as e:
                    logger.error(f"Erro batch {batch_id}: {e}")

        logger.info(f"Total processado: {total}")

    finally:
        pool.dispose()
        ctx.dispose()


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Operações com Arquivos](file-operations.md) - Download de arquivos e imagens
- [Tratamento de Erros](error-handling.md) - Exceções
- [Arquitetura](../core-concepts/architecture.md) - Detalhes
