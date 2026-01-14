# Exemplos

Exemplos práticos de uso do Sankhya SDK Python.

## Categorias

<div class="grid cards" markdown>

-   :material-api:{ .lg .middle } __Gateway Client__

    ---

    API JSON moderna com GatewayClient e DTOs.

    [:octicons-arrow-right-24: Gateway](gateway-usage.md)

-   :material-database:{ .lg .middle } __Operações CRUD__

    ---

    Find, Insert, Update, Remove com entidades.

    [:octicons-arrow-right-24: CRUD](crud-operations.md)

-   :material-page-next:{ .lg .middle } __Requisições Paginadas__

    ---

    Consultas com grandes volumes de dados.

    [:octicons-arrow-right-24: Paginação](paged-requests.md)

-   :material-connection:{ .lg .middle } __Gerenciamento de Sessões__

    ---

    Múltiplas sessões, threading, async.

    [:octicons-arrow-right-24: Sessões](session-management.md)

-   :material-file:{ .lg .middle } __Operações com Arquivos__

    ---

    Download/upload de arquivos e imagens.

    [:octicons-arrow-right-24: Arquivos](file-operations.md)

-   :material-filter:{ .lg .middle } __Queries Avançadas__

    ---

    Filtros complexos, joins, ordenação.

    [:octicons-arrow-right-24: Queries](advanced-queries.md)

-   :material-alert:{ .lg .middle } __Tratamento de Erros__

    ---

    Exceções, retry, circuit breaker.

    [:octicons-arrow-right-24: Erros](error-handling.md)

-   :material-code-tags:{ .lg .middle } __Entidades Customizadas__

    ---

    Criação de entidades para tabelas customizadas.

    [:octicons-arrow-right-24: Entidades](custom-entities.md)

</div>

## Por Nível

### Básico

| Exemplo | Descrição |
|---------|-----------|
| [Gateway Client](gateway-usage.md#setup-inicial) | Setup e primeira consulta |
| [Hello World](crud-operations.md#exemplo-basico) | Primeira conexão (legado) |
| [Find simples](crud-operations.md#find) | Busca de entidades |
| [Insert básico](crud-operations.md#insert) | Criação de entidades |

### Intermediário

| Exemplo | Descrição |
|---------|-----------|
| [DTOs e Validação](gateway-usage.md#usando-dtos) | Validação com Pydantic |
| [Paginação](paged-requests.md) | Grandes volumes |
| [Filtros complexos](advanced-queries.md#filtros-compostos) | FilterExpression |
| [Tratamento de erros](error-handling.md) | Exceções e retry |

### Avançado

| Exemplo | Descrição |
|---------|-----------|
| [Migração XML → JSON](gateway-usage.md#migracao-de-codigo-legado) | Converter código legado |
| [Multi-threading](session-management.md#multi-threading) | Processamento paralelo |
| [Async/await](session-management.md#asyncawait) | Operações assíncronas |
| [Entidades customizadas](custom-entities.md) | Tabelas personalizadas |

## Código Fonte

Todos os exemplos estão disponíveis como arquivos Python executáveis:

```
examples/
├── partner_example.py           # Gateway Client com parceiros
├── crud_operations_example.py
├── paged_request_example.py
├── session_management_example.py
├── file_operations_example.py
├── advanced_queries_example.py
├── error_handling_example.py
└── custom_entities_example.py
```

### Executar Exemplos

```bash
# Ative o ambiente virtual
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Execute um exemplo
python examples/crud_operations_example.py
```

!!! note "Configuração Necessária"
    Todos os exemplos requerem um arquivo `.env` configurado com credenciais válidas.
