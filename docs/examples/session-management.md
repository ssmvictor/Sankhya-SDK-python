# Gerenciamento de Sessões

Exemplos de gerenciamento de sessões, multi-threading e async/await.

## Sessão Única

```python
from sankhya_sdk import SankhyaContext
from dotenv import load_dotenv

load_dotenv()

# Context manager gerencia login/logout automaticamente
with SankhyaContext.from_settings() as ctx:
    print(f"Conectado: {ctx.user_code}")
    # Operações...
# Logout automático
```

---

## Múltiplas Sessões

### Adquirir e Finalizar

```python
from sankhya_sdk import SankhyaContext

ctx = SankhyaContext.from_settings()

# Adquire sessões paralelas
token1 = ctx.acquire_session()
token2 = ctx.acquire_session()

print(f"Sessão 1: {token1}")
print(f"Sessão 2: {token2}")

# Usa sessões específicas
result1 = ctx.invoke_with_token(token1, "ServiceName", request1)
result2 = ctx.invoke_with_token(token2, "ServiceName", request2)

# Finaliza sessões
ctx.finalize_session(token1)
ctx.finalize_session(token2)

# Fecha contexto principal
ctx.dispose()
```

---

## Multi-threading

### ThreadPoolExecutor

```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner

def process_partner(ctx, partner_id):
    """Processa parceiro em thread separada."""
    token = ctx.acquire_session()
    try:
        # Cada thread tem sessão própria
        wrapper = ctx.get_wrapper_for_token(token)
        crud = SimpleCRUDRequestWrapper(wrapper)
        
        partners = crud.find(Partner, f"CODPARC = {partner_id}")
        if partners:
            partner = partners[0]
            partner.email = f"updated_{partner_id}@email.com"
            crud.update(partner)
            return f"Atualizado: {partner_id}"
        return f"Não encontrado: {partner_id}"
    finally:
        ctx.finalize_session(token)

# Uso
ctx = SankhyaContext.from_settings()
partner_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

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

ctx.dispose()
```

### Thread Locks

```python
import threading
from sankhya_sdk import SankhyaContext

ctx = SankhyaContext.from_settings()
results = []
results_lock = threading.Lock()

def worker(thread_id, items):
    """Worker thread com lock para resultados."""
    token = ctx.acquire_session()
    local_results = []
    
    try:
        for item in items:
            result = process_item(ctx, token, item)
            local_results.append(result)
    finally:
        ctx.finalize_session(token)
    
    # Adiciona resultados de forma thread-safe
    with results_lock:
        results.extend(local_results)

# Divide trabalho
all_items = list(range(100))
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

### Básico

```python
import asyncio
from sankhya_sdk import AsyncSankhyaContext
from sankhya_sdk.request_wrappers import AsyncSimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner

async def main():
    async with AsyncSankhyaContext.from_settings() as ctx:
        crud = AsyncSimpleCRUDRequestWrapper(ctx.wrapper)
        
        # Busca assíncrona
        partners = await crud.find(Partner, "ATIVO = 'S'")
        
        for partner in partners[:5]:
            print(f"{partner.code_partner}: {partner.name}")

asyncio.run(main())
```

### Operações Paralelas

```python
import asyncio
from sankhya_sdk import AsyncSankhyaContext

async def fetch_partner(ctx, partner_id):
    """Busca parceiro de forma assíncrona."""
    partners = await ctx.wrapper.find_async(Partner, f"CODPARC = {partner_id}")
    return partners[0] if partners else None

async def main():
    async with AsyncSankhyaContext.from_settings() as ctx:
        # Busca múltiplos parceiros em paralelo
        partner_ids = [1, 2, 3, 4, 5]
        
        tasks = [fetch_partner(ctx, pid) for pid in partner_ids]
        partners = await asyncio.gather(*tasks)
        
        for partner in partners:
            if partner:
                print(f"{partner.code_partner}: {partner.name}")

asyncio.run(main())
```

### Semaphore para Limite de Concorrência

```python
import asyncio
from sankhya_sdk import AsyncSankhyaContext

async def process_with_semaphore(sem, ctx, item):
    """Processa com limite de concorrência."""
    async with sem:
        result = await ctx.wrapper.find_async(Partner, f"CODPARC = {item}")
        return result

async def main():
    async with AsyncSankhyaContext.from_settings() as ctx:
        # Máximo 10 requisições simultâneas
        sem = asyncio.Semaphore(10)
        
        items = list(range(1, 101))
        
        tasks = [process_with_semaphore(sem, ctx, item) for item in items]
        results = await asyncio.gather(*tasks)
        
        print(f"Processados: {len(results)}")

asyncio.run(main())
```

---

## Sessões Detachadas

### Detach e Attach

```python
import pickle
from sankhya_sdk import SankhyaContext

# Processo 1: Cria e detacha sessão
ctx1 = SankhyaContext.from_settings()
token = ctx1.acquire_session()

# Serializa sessão para transferência
session_data = ctx1.detach_session(token)
serialized = pickle.dumps(session_data)

# Simula envio para outro processo
# send_to_other_process(serialized)

# Processo 2: Recebe e usa sessão
received = pickle.loads(serialized)
ctx2 = SankhyaContext.from_settings()
ctx2.attach_session(token, received)

# Usa sessão do processo 1
result = ctx2.invoke_with_token(token, "ServiceName", request)

ctx2.dispose()
ctx1.dispose()
```

---

## Tratamento de Sessão Expirada

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import ServiceRequestInvalidAuthorizationException

ctx = SankhyaContext.from_settings()

def execute_with_retry(operation, max_retries=3):
    """Executa operação com retry para sessão expirada."""
    for attempt in range(max_retries):
        try:
            return operation()
        except ServiceRequestInvalidAuthorizationException:
            if attempt < max_retries - 1:
                print(f"Sessão expirada, reconectando (tentativa {attempt + 1})")
                ctx.wrapper.login()  # Reconecta
            else:
                raise

# Uso
result = execute_with_retry(lambda: ctx.wrapper.find(Partner, "CODPARC > 0"))
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de gerenciamento de sessões.

Demonstra multi-threading com pool de sessões.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionPool:
    """Pool de sessões para uso multi-thread."""
    
    def __init__(self, context, pool_size=5):
        self.context = context
        self.pool_size = pool_size
        self._lock = threading.Lock()
        self._available = []
        self._in_use = set()
        
        # Cria sessões
        for _ in range(pool_size):
            token = context.acquire_session()
            self._available.append(token)
        
        logger.info(f"Pool criado com {pool_size} sessões")
    
    def acquire(self):
        """Adquire sessão do pool."""
        with self._lock:
            if not self._available:
                raise RuntimeError("Sem sessões disponíveis")
            
            token = self._available.pop()
            self._in_use.add(token)
            return token
    
    def release(self, token):
        """Devolve sessão ao pool."""
        with self._lock:
            if token in self._in_use:
                self._in_use.remove(token)
                self._available.append(token)
    
    def dispose(self):
        """Fecha todas as sessões."""
        for token in self._available + list(self._in_use):
            try:
                self.context.finalize_session(token)
            except Exception as e:
                logger.error(f"Erro ao fechar sessão {token}: {e}")


def process_batch(pool, context, batch_id, items):
    """Processa lote usando sessão do pool."""
    token = pool.acquire()
    try:
        wrapper = context.get_wrapper_for_token(token)
        crud = SimpleCRUDRequestWrapper(wrapper)
        
        processed = 0
        for item in items:
            partners = crud.find(Partner, f"CODPARC = {item}")
            if partners:
                processed += 1
        
        logger.info(f"Batch {batch_id}: processados {processed}/{len(items)}")
        return processed
    finally:
        pool.release(token)


def main():
    ctx = SankhyaContext.from_settings()
    pool = SessionPool(ctx, pool_size=5)
    
    try:
        # Divide trabalho em lotes
        items = list(range(1, 101))
        batches = [items[i:i+10] for i in range(0, len(items), 10)]
        
        total = 0
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(process_batch, pool, ctx, i, batch): i
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

- [Operações com Arquivos](file-operations.md) - Download/upload
- [Tratamento de Erros](error-handling.md) - Exceções
- [Arquitetura](../core-concepts/architecture.md) - Detalhes
