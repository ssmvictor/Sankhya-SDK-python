# Tratamento de Erros

Exemplos de tratamento de exceções e retry.

## Tratamento Básico

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestException,
    ServiceRequestInvalidAuthorizationException,
)

try:
    with SankhyaContext.from_settings() as ctx:
        result = ctx.wrapper.find(Partner, "CODPARC > 0")
        
except ServiceRequestInvalidAuthorizationException:
    print("Credenciais inválidas")
    
except ServiceRequestException as e:
    print(f"Erro de serviço: {e.status_message}")
    
except SankhyaException as e:
    print(f"Erro SDK: {e.message}")
```

---

## Retry com Backoff

```python
import time

def execute_with_retry(func, max_retries=3, delay=1.0):
    """Executa função com retry exponencial."""
    for attempt in range(max_retries):
        try:
            return func()
        except ServiceRequestException as e:
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)
                print(f"Retry em {wait}s...")
                time.sleep(wait)
            else:
                raise

# Uso
result = execute_with_retry(lambda: crud.find(Partner))
```

---

## Retry por Tipo de Erro

```python
from sankhya_sdk.exceptions import (
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
)

def smart_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except ServiceRequestInvalidAuthorizationException:
            raise  # Não retry
        except ServiceRequestCompetitionException as e:
            time.sleep(e.retry_after or 5)
        except ServiceRequestDeadlockException:
            time.sleep(1)
```

---

## Processamento em Lote

```python
def process_batch(crud, items, operation):
    """Processa lote coletando erros."""
    success, failed = [], []
    
    for item in items:
        try:
            if operation == "update":
                crud.update(item)
            success.append(item)
        except ServiceRequestException as e:
            failed.append((item, str(e)))
    
    return {"success": len(success), "failed": len(failed)}
```

## Próximos Passos

- [Entidades Customizadas](custom-entities.md)
- [Exceções](../api-reference/exceptions.md)
