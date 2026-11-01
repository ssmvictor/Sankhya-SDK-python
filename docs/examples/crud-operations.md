# Operações CRUD

Exemplos de operações Create, Read, Update e Delete com o
`SimpleCRUDRequestWrapper` (API XML legada).

O `SimpleCRUDRequestWrapper` é usado pelos seus métodos de classe:
`initialize(ctx)` adquire uma **sessão dedicada** do contexto (um login
extra, como `Context.AcquireNewSession(ServiceRequestType.SimpleCrud)` no SDK
.NET) e `dispose()` faz o logout dessa sessão. A sessão principal é
encerrada por `ctx.dispose()`.

## Exemplo Básico

```python
#!/usr/bin/env python3
"""Exemplo básico de CRUD com Sankhya SDK."""

from sankhya_sdk import SankhyaContext
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Conecta à API (configurações de SANKHYA_* / .env)
ctx = SankhyaContext.from_settings()
try:
    SimpleCRUDRequestWrapper.initialize(ctx)

    # Busca parceiros ativos (no máximo 5)
    partners = SimpleCRUDRequestWrapper.find_all(
        Partner(is_active=True), EntityQueryOptions(max_results=5)
    )

    for partner in partners:
        print(f"{partner.code}: {partner.name}")
finally:
    SimpleCRUDRequestWrapper.dispose()
    ctx.dispose()
```

Os demais exemplos assumem o wrapper inicializado como acima.

---

## Find

### Busca Simples

As buscas usam uma entidade de exemplo: os campos preenchidos viram o
critério (`CODPARC = 1`, `ATIVO = 'S'`...).

```python
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Todos os parceiros ativos
partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=True))

# Com limite de resultados
partners = SimpleCRUDRequestWrapper.find_all(
    Partner(is_active=True), EntityQueryOptions(max_results=100)
)

# Por código específico (None se não existir)
partner = SimpleCRUDRequestWrapper.try_find(Partner(code=1))
if partner:
    print(f"Nome: {partner.name}")
```

`try_find` e `find` esperam no máximo um resultado
(`ServiceRequestTooManyResultsException` se houver mais); `find` lança
`ServiceRequestUnexpectedResultException` quando não encontra.

### Busca com Opções

```python
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Opções de consulta
options = EntityQueryOptions(
    max_results=50,                    # rowsLimit
    include_references=False,          # sem entidades referenciadas
    include_presentation_fields=False,
)

partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=True, is_client=True), options)

for partner in partners:
    print(f"{partner.name} - {partner.email_address or 'Sem email'}")
```

### Busca com Critério Literal

Para filtros que não cabem numa entidade de exemplo, use `LiteralCriteria`
(`sankhya_sdk.helpers`), que monta a expressão:

```python
from sankhya_sdk.helpers import LiteralCriteria
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Construir filtro com a API fluente
criteria = (
    LiteralCriteria.equals("ATIVO", "S")
    .and_(LiteralCriteria.in_("TIPPESSOA", ["F", "J"]))
    .and_(LiteralCriteria.equals("CGC_CPF", "12345678000199"))
)
print(criteria.build_expression())
# ATIVO = 'S' AND TIPPESSOA IN ('F', 'J') AND CGC_CPF = '12345678000199'

# No máximo um resultado (None se não houver)
partner = SimpleCRUDRequestWrapper.try_find_with_criteria(Partner, criteria)
print(f"Encontrado: {partner.name if partner else 'nenhum'}")
```

Para critérios que retornam muitos registros, use o
[`PagedRequestWrapper`](paged-requests.md).

---

## Insert

### Inserção Simples

Não há método `insert`: `update` envia `CRUDServiceProvider.saveRecord` e,
sem chave primária preenchida, o servidor cria o registro (como no SDK
.NET):

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Cria novo parceiro (sem CODPARC)
partner = Partner(
    name="Novo Cliente LTDA",
    document="12345678000199",
    is_client=True,
    is_active=True,
)

# Insere
created = SimpleCRUDRequestWrapper.update(partner)
print(f"Parceiro criado com código: {created.code}")
```

### Inserção com Validação

As entidades de transporte são modelos Pydantic: tipos inválidos e limites
de tamanho (`entity_custom_data(max_length=...)`) são validados na criação e
na atribuição, antes de qualquer requisição:

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

try:
    # COMPLEMENTO aceita no máximo 30 caracteres
    partner = Partner(
        name="Novo Fornecedor LTDA",
        document="98765432000111",
        is_supplier=True,
        address_complement="Bloco B, sala 1201, torre norte, 12º andar",
    )
except ValueError as e:  # pydantic.ValidationError deriva de ValueError
    print(f"Erro de validação: {e}")
else:
    created = SimpleCRUDRequestWrapper.update(partner)
    print(f"Criado: {created.code}")
```

### Inserção em Lote

```python
from sankhya_sdk.exceptions import ServiceRequestGeneralException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# (nome, cliente, fornecedor)
partners_data = [
    ("Cliente 1", True, False),
    ("Cliente 2", True, False),
    ("Fornecedor 1", False, True),
]

created_count = 0
for name, is_client, is_supplier in partners_data:
    try:
        partner = Partner(
            name=name, is_client=is_client, is_supplier=is_supplier, is_active=True
        )
        SimpleCRUDRequestWrapper.update(partner)
        created_count += 1
    except (ValueError, ServiceRequestGeneralException) as e:
        print(f"Erro ao criar {name}: {e}")

print(f"Criados: {created_count}/{len(partners_data)}")
```

Para volumes grandes, o `OnDemandRequestWrapper` envia as entidades em lotes
em segundo plano (veja [Request Wrappers](../api-reference/request-wrappers.md)).

---

## Update

### Atualização Simples

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Busca parceiro
partner = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

if partner:
    # Altera campos
    partner.email_address = "novo.email@empresa.com"
    partner.telephone = "11999998888"

    # Atualiza
    updated = SimpleCRUDRequestWrapper.update(partner)
    print(f"Atualizado: {updated.name}")
```

### Atualização Parcial

O `saveRecord` envia apenas os campos preenchidos na entidade. Para alterar
só alguns campos, sem buscar o registro antes, crie a entidade com a chave e
os campos novos:

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Envia <key><CODPARC>1</CODPARC></key> e <localFields><EMAIL>...</EMAIL></localFields>
SimpleCRUDRequestWrapper.update(Partner(code=1, email_address="novo.email@empresa.com"))
```

### Atualização Condicional

```python
from sankhya_sdk.exceptions import ServiceRequestGeneralException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Busca parceiros ativos e filtra os que não têm email
partners = [
    p for p in SimpleCRUDRequestWrapper.find_all(Partner(is_active=True))
    if not p.email_address
]

updated_count = 0
for partner in partners:
    # Define email padrão baseado no nome
    name = (partner.name or "parceiro").lower().replace(" ", "")
    try:
        SimpleCRUDRequestWrapper.update(
            Partner(code=partner.code, email_address=f"contato@{name}.com")
        )
        updated_count += 1
    except ServiceRequestGeneralException as e:
        print(f"Erro ao atualizar {partner.code}: {e}")

print(f"Atualizados: {updated_count}/{len(partners)}")
```

### Atualização com Histórico

```python
from datetime import datetime

from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

original = SimpleCRUDRequestWrapper.try_find(Partner(code=1))

if original:
    # Cópia para comparação (modelo Pydantic)
    modified = original.model_copy(deep=True)
    modified.email_address = "atualizado@email.com"

    # Verifica mudanças
    before = original.model_dump()
    changes = {
        name: value
        for name, value in modified.model_dump().items()
        if before.get(name) != value
    }

    if changes:
        print(f"Campos alterados: {changes}")

        # Atualiza apenas os campos alterados
        SimpleCRUDRequestWrapper.update(Partner(code=original.code, **changes))
        print(f"Atualizado em {datetime.now()}")
```

---

## Remove

### Remoção Simples

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Busca parceiro para remover
partner = SimpleCRUDRequestWrapper.try_find(Partner(code=999))

if partner:
    # Remove (CRUDServiceProvider.removeRecord); erros viram exceções
    SimpleCRUDRequestWrapper.remove(partner)
    print(f"Parceiro {partner.code} removido")
```

### Remoção com Confirmação

```python
from sankhya_sdk.exceptions import ServiceRequestGeneralException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Busca parceiros inativos
partners = SimpleCRUDRequestWrapper.find_all(Partner(is_active=False))

print(f"Parceiros para remover: {len(partners)}")

for partner in partners:
    confirm = input(f"Remover {partner.name}? (s/n): ")

    if confirm.lower() == 's':
        try:
            SimpleCRUDRequestWrapper.remove(Partner(code=partner.code))
            print(f"  Removido: {partner.code}")
        except ServiceRequestGeneralException as e:
            print(f"  Erro: {e}")
```

### Soft Delete (Inativação)

```python
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Em vez de remover, inativa (ATIVO = 'N')
SimpleCRUDRequestWrapper.update(Partner(code=999, is_active=False))
print("Parceiro 999 inativado")
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de operações CRUD.

Demonstra todas as operações básicas com tratamento de erros.
"""

import logging

from sankhya_sdk import SankhyaContext
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestGeneralException,
    ServiceRequestInvalidCredentialsException,
)
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

# Configuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        ctx = SankhyaContext.from_settings()
    except ServiceRequestInvalidCredentialsException:
        logger.error("Credenciais inválidas")
        return

    try:
        SimpleCRUDRequestWrapper.initialize(ctx)

        # 1. CREATE (update sem chave)
        logger.info("=== CREATE ===")
        new_partner = Partner(name="Teste CRUD Python", is_client=True, is_active=True)
        created = SimpleCRUDRequestWrapper.update(new_partner)
        partner_id = created.code
        logger.info(f"Criado parceiro: {partner_id}")

        # 2. READ
        logger.info("=== READ ===")
        partner = SimpleCRUDRequestWrapper.find(Partner(code=partner_id))
        logger.info(f"Lido: {partner.name}")

        # 3. UPDATE
        logger.info("=== UPDATE ===")
        updated = SimpleCRUDRequestWrapper.update(
            Partner(code=partner_id, email_address="teste@example.com")
        )
        logger.info(f"Atualizado email: {updated.email_address}")

        # 4. DELETE
        logger.info("=== DELETE ===")
        SimpleCRUDRequestWrapper.remove(Partner(code=partner_id))
        logger.info(f"Removido: {partner_id}")

        logger.info("CRUD completo!")

    except ServiceRequestGeneralException as e:
        logger.error(f"Erro de serviço: {e}")
    except SankhyaException as e:
        logger.error(f"Erro SDK: {e}")
    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
    finally:
        SimpleCRUDRequestWrapper.dispose()
        ctx.dispose()


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Requisições Paginadas](paged-requests.md) - Grandes volumes
- [Queries Avançadas](advanced-queries.md) - Filtros complexos
- [Tratamento de Erros](error-handling.md) - Exceções
