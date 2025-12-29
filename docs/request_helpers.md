# Request Helpers - Sistema de Retry

O módulo `request_helpers` fornece utilitários para gerenciar retentativas de requisições HTTP com backoff exponencial, tratamento de exceções e configuração de comportamento de requisições.

## Visão Geral

Este módulo implementa um sistema de retry robusto para lidar com falhas temporárias nas requisições à API Sankhya. O sistema é configurável e segue padrões de resiliência como:

- **Backoff Exponencial**: Delays progressivos entre tentativas
- **Limite de Retentativas**: Configuração máxima de tentativas
- **Tratamento de Exceções Específicas**: Lógica diferenciada por tipo de exceção

## Componentes

### RequestBehaviorOptions

Configurações imutáveis para o comportamento de retry.

```python
from sankhya_sdk.request_helpers import RequestBehaviorOptions

# Usar valores padrão (3 tentativas)
options = RequestBehaviorOptions()

# Personalizar número máximo de retentativas
options = RequestBehaviorOptions(max_retry_count=5)
```

| Atributo | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `max_retry_count` | `int` | `3` | Número máximo de tentativas de retry |

---

### RequestRetryData

Classe mutável para rastrear o estado atual das retentativas.

```python
from sankhya_sdk.request_helpers import RequestRetryData

retry_data = RequestRetryData()
print(retry_data.retry_count)  # 0

# Incrementar após cada tentativa
retry_data.retry_count += 1
retry_data.retry_delay = 10  # segundos até próxima tentativa
```

| Atributo | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `lock_key` | `str` | `""` | Identificador único para a requisição |
| `retry_count` | `int` | `0` | Número atual de tentativas realizadas |
| `retry_delay` | `int` | `0` | Delay em segundos antes da próxima tentativa |

---

### RequestRetryDelay

Constantes de delay baseadas na estabilidade do sistema.

```python
from sankhya_sdk.request_helpers import RequestRetryDelay

# Usar delay apropriado baseado na condição do sistema
delay = RequestRetryDelay.FREE      # 10 segundos - sistema livre
delay = RequestRetryDelay.STABLE    # 15 segundos - sistema estável
delay = RequestRetryDelay.UNSTABLE  # 30 segundos - sistema instável
delay = RequestRetryDelay.BREAKDOWN # 90 segundos - sistema em crise
```

| Constante | Valor (segundos) | Uso Recomendado |
|-----------|------------------|-----------------|
| `FREE` | 10 | Sistema saudável, erros transientes ocasionais |
| `STABLE` | 15 | Sistema operacional com alguma carga |
| `UNSTABLE` | 30 | Sistema com problemas intermitentes ou alta carga |
| `BREAKDOWN` | 90 | Sistema em recuperação ou problemas severos |

---

### RequestExceptionDetails

Contexto sobre uma exceção ocorrida durante uma requisição.

```python
from sankhya_sdk.request_helpers import RequestExceptionDetails
from sankhya_sdk.enums import ServiceName

try:
    # operação que falha
    raise ValueError("Erro de teste")
except Exception as e:
    details = RequestExceptionDetails(
        exception=e,
        service_name=ServiceName.CRUD_FIND,
        request=None,  # opcional
    )
    print(details.service_type)  # ServiceType.RETRIEVE
```

| Atributo/Propriedade | Tipo | Descrição |
|---------------------|------|-----------|
| `exception` | `Exception` | A exceção capturada |
| `service_name` | `ServiceName` | Enum do serviço chamado |
| `request` | `Optional[Any]` | Dados da requisição (opcional) |
| `service_type` | `ServiceType` | Tipo do serviço extraído dos metadados |

---

### RequestExceptionHandler

Handler principal para decidir se uma requisição deve ser retentada.

```python
from sankhya_sdk.request_helpers import (
    RequestBehaviorOptions,
    RequestExceptionHandler,
    RequestExceptionDetails,
    RequestRetryData,
)
from sankhya_sdk.enums import ServiceName

# Configurar handler
options = RequestBehaviorOptions(max_retry_count=3)
handler = RequestExceptionHandler(options)

# Ao capturar uma exceção
details = RequestExceptionDetails(
    exception=some_exception,
    service_name=ServiceName.CRUD_FIND,
)
retry_data = RequestRetryData()

# Decidir se deve retentar
should_retry = handler.handle(details, retry_data)
```

#### Interface IRequestExceptionHandler

O handler implementa o protocolo `IRequestExceptionHandler`:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class IRequestExceptionHandler(Protocol):
    def handle(
        self,
        details: RequestExceptionDetails,
        retry_data: RequestRetryData,
    ) -> bool:
        """Retorna True se deve retentar, False caso contrário."""
        ...
```

---

## Diagrama de Fluxo

```mermaid
sequenceDiagram
    participant Client
    participant Handler as RequestExceptionHandler
    participant Details as RequestExceptionDetails
    participant RetryData as RequestRetryData
    participant Options as RequestBehaviorOptions

    Client->>Handler: handle(details, retry_data)
    Handler->>RetryData: verificar retry_count
    alt retry_count > max_retry_count
        Handler-->>Client: return False (parar retry)
    else
        Handler->>Details: verificar service_type
        alt é TRANSACTIONAL + exceção específica
            Handler-->>Client: return False (parar retry)
        else
            Handler->>Handler: _handle_internal()
            Note over Handler: NotImplementedError<br/>(futuro: backoff exponencial)
            Handler-->>Client: return True (continuar retry)
        end
    end
```

## Regras de Retry

### Condições para NÃO Retentar

1. **Limite Excedido**: Quando `retry_count > max_retry_count`
2. **Serviço Transacional**: Quando `service_type == TRANSACTIONAL` E exceção é:
   - `ServiceRequestCompetitionException`
   - `ServiceRequestDeadlockException`
   - `ServiceRequestTimeoutException`

### Exceções Relacionadas

O módulo trabalha em conjunto com as seguintes exceções de `sankhya_sdk.exceptions`:

- **`ServiceRequestCompetitionException`**: Erro de competição/concorrência
- **`ServiceRequestDeadlockException`**: Deadlock em transação
- **`ServiceRequestTimeoutException`**: Timeout na requisição

## Exemplo Completo

```python
from sankhya_sdk.request_helpers import (
    RequestBehaviorOptions,
    RequestExceptionHandler,
    RequestExceptionDetails,
    RequestRetryData,
    RequestRetryDelay,
)
from sankhya_sdk.enums import ServiceName
import time

# Configuração
options = RequestBehaviorOptions(max_retry_count=3)
handler = RequestExceptionHandler(options)

def make_request_with_retry():
    retry_data = RequestRetryData()
    
    while True:
        try:
            # Fazer requisição
            result = perform_request()
            return result
        except Exception as e:
            details = RequestExceptionDetails(
                exception=e,
                service_name=ServiceName.CRUD_SAVE,
            )
            
            # Decidir se deve retentar
            # (NotImplementedError será lançado até implementação futura)
            try:
                should_retry = handler.handle(details, retry_data)
            except NotImplementedError:
                # Lógica de retry ainda não implementada
                should_retry = retry_data.retry_count < options.max_retry_count
            
            if not should_retry:
                raise
            
            # Aplicar delay antes de retentar
            time.sleep(RequestRetryDelay.STABLE)
            retry_data.retry_count += 1
```

## Status de Implementação

| Componente | Status |
|------------|--------|
| `RequestBehaviorOptions` | ✅ Completo |
| `RequestRetryData` | ✅ Completo |
| `RequestRetryDelay` | ✅ Completo |
| `RequestExceptionDetails` | ✅ Completo |
| `IRequestExceptionHandler` | ✅ Completo |
| `RequestExceptionHandler` | ⚠️ Parcial (backoff pendente) |

> [!NOTE]
> O método `_handle_internal` do `RequestExceptionHandler` ainda não está implementado. 
> A lógica de backoff exponencial será adicionada em fases futuras.
