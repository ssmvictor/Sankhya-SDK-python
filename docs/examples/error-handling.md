# Tratamento de Erros

Exemplos de tratamento de exceções e retry (stack XML legada). A política
de retry automática do `SankhyaWrapper` está descrita em
[Tratamento de Erros](../core-concepts/error-handling.md#retry-automatico).

## Tratamento Básico

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestGeneralException,
    ServiceRequestInvalidCredentialsException,
)
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

try:
    ctx = SankhyaContext.from_settings()
except ServiceRequestInvalidCredentialsException:
    print("Credenciais inválidas")
    raise

try:
    SimpleCRUDRequestWrapper.initialize(ctx)
    partner = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

except ServiceRequestGeneralException as e:
    print(f"Erro de serviço: {e}")
    if e.response is not None:
        print(f"Mensagem do servidor: {e.response.status_message_text}")

except SankhyaException as e:
    print(f"Erro SDK: {e}")

finally:
    SimpleCRUDRequestWrapper.dispose()
    ctx.dispose()
```

---

## Retry com Backoff

O `SankhyaWrapper` já repete erros temporários (deadlock, timeout, serviço
indisponível, erro de rede...). Um retry adicional na aplicação só faz
sentido para operações idempotentes:

```python
import time
from typing import Callable, TypeVar

from sankhya_sdk.exceptions import ServiceRequestTemporarilyException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

T = TypeVar("T")


def execute_with_retry(func: Callable[[], T], max_retries: int = 3, delay: float = 1.0) -> T:
    """Executa função com retry exponencial para erros temporários."""
    for attempt in range(max_retries):
        try:
            return func()
        except ServiceRequestTemporarilyException:
            if attempt == max_retries - 1:
                raise
            wait = delay * (2 ** attempt)
            print(f"Retry em {wait}s...")
            time.sleep(wait)
    raise RuntimeError("max_retries deve ser maior que zero")


# Uso
partner = execute_with_retry(lambda: SimpleCRUDRequestWrapper.try_find(Partner(code=1)))
```

---

## Retry por Tipo de Erro

```python
import time
from typing import Callable, TypeVar

from sankhya_sdk.exceptions import (
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestInvalidCredentialsException,
)

T = TypeVar("T")


def smart_retry(func: Callable[[], T], max_retries: int = 3) -> T:
    for attempt in range(max_retries):
        try:
            return func()
        except ServiceRequestInvalidCredentialsException:
            raise  # Não retry
        except (ServiceRequestCompetitionException, ServiceRequestDeadlockException):
            # Chegam aqui em gravações (serviços transacionais), que o
            # SankhyaWrapper não repete
            if attempt == max_retries - 1:
                raise
            time.sleep(5)
    raise RuntimeError("max_retries deve ser maior que zero")
```

---

## Processamento em Lote

```python
from typing import Dict, List, Tuple

from sankhya_sdk.exceptions import ServiceRequestGeneralException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


def process_batch(items: List[Partner]) -> Dict[str, int]:
    """Atualiza um lote coletando erros."""
    success: List[Partner] = []
    failed: List[Tuple[Partner, str]] = []

    for item in items:
        try:
            SimpleCRUDRequestWrapper.update(item)
            success.append(item)
        except ServiceRequestGeneralException as e:
            failed.append((item, str(e)))

    return {"success": len(success), "failed": len(failed)}
```

## Próximos Passos

- [Entidades Customizadas](custom-entities.md)
- [Exceções](../api-reference/exceptions.md)
