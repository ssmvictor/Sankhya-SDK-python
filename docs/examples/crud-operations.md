# Operações CRUD

Exemplos de operações Create, Read, Update e Delete.

## Exemplo Básico

```python
#!/usr/bin/env python3
"""Exemplo básico de CRUD com Sankhya SDK."""

from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner
from dotenv import load_dotenv

# Carrega configurações
load_dotenv()

# Conecta à API
with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Busca parceiros
    partners = crud.find(Partner, "CODPARC > 0", max_results=5)
    
    for partner in partners:
        print(f"{partner.code_partner}: {partner.name}")
```

---

## Find

### Busca Simples

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Todos os parceiros ativos
    partners = crud.find(Partner, "ATIVO = 'S'")
    
    # Com limite de resultados
    partners = crud.find(Partner, "ATIVO = 'S'", max_results=100)
    
    # Por código específico
    partners = crud.find(Partner, "CODPARC = 1")
    if partners:
        partner = partners[0]
        print(f"Nome: {partner.name}")
```

### Busca com Opções

```python
from sankhya_sdk.helpers import EntityQueryOptions

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Opções de consulta
    options = EntityQueryOptions(
        include_fields=["CODPARC", "NOMEPARC", "CGC_CPF", "EMAIL"],
        order_by="NOMEPARC ASC",
        max_results=50,
        include_references=False
    )
    
    partners = crud.find_with_options(
        Partner,
        "ATIVO = 'S' AND TIPPESSOA = 'C'",
        options
    )
    
    for partner in partners:
        print(f"{partner.name} - {partner.email or 'Sem email'}")
```

### Busca com FilterExpression

```python
from sankhya_sdk.helpers import FilterExpression
from datetime import date

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Construir filtro com fluent API
    filter_expr = (
        FilterExpression()
        .equals("ATIVO", "S")
        .and_()
        .in_("TIPPESSOA", ["C", "A"])
        .and_()
        .is_not_null("EMAIL")
    )
    
    partners = crud.find(Partner, filter_expr.build())
    print(f"Encontrados: {len(partners)} parceiros")
```

---

## Insert

### Inserção Simples

```python
from sankhya_sdk.transport_entities import Partner

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Cria novo parceiro
    partner = Partner()
    partner.name = "Novo Cliente LTDA"
    partner.cgc_cpf = "12345678000199"
    partner.type_partner = "C"  # Cliente
    partner.active = True
    
    # Insere
    created = crud.insert(partner)
    print(f"Parceiro criado com código: {created.code_partner}")
```

### Inserção com Validação

```python
from sankhya_sdk.validations import EntityValidator

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    validator = EntityValidator()
    
    # Cria parceiro
    partner = Partner()
    partner.name = "Novo Fornecedor LTDA"
    partner.cgc_cpf = "98765432000111"
    partner.type_partner = "F"  # Fornecedor
    
    # Valida antes de inserir
    result = validator.validate(partner)
    
    if result.is_valid:
        created = crud.insert(partner)
        print(f"Criado: {created.code_partner}")
    else:
        for error in result.errors:
            print(f"Erro: {error.field} - {error.message}")
```

### Inserção em Lote

```python
partners_data = [
    {"name": "Cliente 1", "type": "C"},
    {"name": "Cliente 2", "type": "C"},
    {"name": "Fornecedor 1", "type": "F"},
]

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    created_count = 0
    for data in partners_data:
        try:
            partner = Partner()
            partner.name = data["name"]
            partner.type_partner = data["type"]
            partner.active = True
            
            crud.insert(partner)
            created_count += 1
        except Exception as e:
            print(f"Erro ao criar {data['name']}: {e}")
    
    print(f"Criados: {created_count}/{len(partners_data)}")
```

---

## Update

### Atualização Simples

```python
with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Busca parceiro
    partners = crud.find(Partner, "CODPARC = 1")
    
    if partners:
        partner = partners[0]
        
        # Altera campos
        partner.email = "novo.email@empresa.com"
        partner.phone = "11999998888"
        
        # Atualiza
        updated = crud.update(partner)
        print(f"Atualizado: {updated.name}")
```

### Atualização Condicional

```python
with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Busca parceiros sem email
    partners = crud.find(Partner, "EMAIL IS NULL AND ATIVO = 'S'")
    
    updated_count = 0
    for partner in partners:
        # Define email padrão baseado no nome
        partner.email = f"contato@{partner.name.lower().replace(' ', '')}.com"
        
        try:
            crud.update(partner)
            updated_count += 1
        except Exception as e:
            print(f"Erro ao atualizar {partner.code_partner}: {e}")
    
    print(f"Atualizados: {updated_count}/{len(partners)}")
```

### Atualização com Histórico

```python
from sankhya_sdk.helpers import EntityExtensions
from datetime import datetime

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    partners = crud.find(Partner, "CODPARC = 1")
    
    if partners:
        original = partners[0]
        
        # Clone para comparação
        modified = EntityExtensions.clone(original)
        modified.email = "atualizado@email.com"
        
        # Verifica mudanças
        changes = EntityExtensions.get_changed_fields(original, modified)
        
        if changes:
            print(f"Campos alterados: {changes}")
            
            # Atualiza
            crud.update(modified)
            print(f"Atualizado em {datetime.now()}")
```

---

## Remove

### Remoção Simples

```python
with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Busca parceiro para remover
    partners = crud.find(Partner, "CODPARC = 999")
    
    if partners:
        partner = partners[0]
        
        # Remove
        success = crud.remove(partner)
        
        if success:
            print(f"Parceiro {partner.code_partner} removido")
        else:
            print("Falha ao remover")
```

### Remoção com Confirmação

```python
with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Busca parceiros inativos há muito tempo
    partners = crud.find(
        Partner,
        "ATIVO = 'N' AND DTALTER < '01/01/2020'"
    )
    
    print(f"Parceiros para remover: {len(partners)}")
    
    for partner in partners:
        confirm = input(f"Remover {partner.name}? (s/n): ")
        
        if confirm.lower() == 's':
            try:
                crud.remove(partner)
                print(f"  Removido: {partner.code_partner}")
            except Exception as e:
                print(f"  Erro: {e}")
```

### Soft Delete (Inativação)

```python
with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Em vez de remover, inativa
    partners = crud.find(Partner, "CODPARC = 999")
    
    if partners:
        partner = partners[0]
        partner.active = False  # Inativa em vez de remover
        
        crud.update(partner)
        print(f"Parceiro {partner.code_partner} inativado")
```

---

## Exemplo Completo

```python
#!/usr/bin/env python3
"""
Exemplo completo de operações CRUD.

Demonstra todas as operações básicas com tratamento de erros.
"""

from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper
from sankhya_sdk.transport_entities import Partner
from sankhya_sdk.validations import EntityValidator
from sankhya_sdk.exceptions import (
    SankhyaException,
    ServiceRequestException,
    OperationException,
)
from dotenv import load_dotenv
import logging

# Configuração
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        with SankhyaContext.from_settings() as ctx:
            crud = SimpleCRUDRequestWrapper(ctx.wrapper)
            validator = EntityValidator()
            
            # 1. CREATE
            logger.info("=== CREATE ===")
            new_partner = Partner()
            new_partner.name = "Teste CRUD Python"
            new_partner.type_partner = "C"
            new_partner.active = True
            
            result = validator.validate(new_partner)
            if result.is_valid:
                created = crud.insert(new_partner)
                partner_id = created.code_partner
                logger.info(f"Criado parceiro: {partner_id}")
            else:
                logger.error(f"Validação falhou: {result.errors}")
                return
            
            # 2. READ
            logger.info("=== READ ===")
            partners = crud.find(Partner, f"CODPARC = {partner_id}")
            if partners:
                partner = partners[0]
                logger.info(f"Lido: {partner.name}")
            
            # 3. UPDATE
            logger.info("=== UPDATE ===")
            partner.email = "teste@example.com"
            updated = crud.update(partner)
            logger.info(f"Atualizado email: {updated.email}")
            
            # 4. DELETE
            logger.info("=== DELETE ===")
            success = crud.remove(partner)
            logger.info(f"Removido: {success}")
            
            logger.info("CRUD completo!")
            
    except ServiceRequestException as e:
        logger.error(f"Erro de serviço: {e.status_message}")
    except OperationException as e:
        logger.error(f"Erro de operação: {e.message}")
    except SankhyaException as e:
        logger.error(f"Erro SDK: {e.message}")
    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()
```

## Próximos Passos

- [Requisições Paginadas](paged-requests.md) - Grandes volumes
- [Queries Avançadas](advanced-queries.md) - Filtros complexos
- [Tratamento de Erros](error-handling.md) - Exceções
