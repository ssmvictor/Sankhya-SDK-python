# Validações de Entidades

O módulo `sankhya_sdk.validations` fornece utilitários para validar classes de entidade e analisar mensagens de erro da API Sankhya.

## Visão Geral

O módulo consiste em duas classes principais:

1. **`EntityValidator`**: Validação estrutural de entidades usando reflection
2. **`EntityValidation`**: Padrões Regex compilados para análise de mensagens de erro

## EntityValidator

A classe `EntityValidator` fornece métodos estáticos para validar que classes de entidade implementam corretamente todos os requisitos do SDK.

### Validações Realizadas

| Validação | Descrição | Exceção |
|-----------|-----------|---------|
| Construtor | Entidade deve ter construtor sem parâmetros obrigatórios | `MissingConstructorError` |
| Decorador | Entidade deve ter decorador `@entity` | `MissingEntityAttributeError` |
| Classe Base | Entidade deve herdar de `TransportEntityBase` | `MissingBaseClassError` |
| Igualdade | Entidade deve implementar `__eq__` e `__hash__` | `MissingEqualityMethodsError` |
| Propriedades | Cada campo deve ter atributo válido | `InvalidPropertyAttributeError` |

### Uso Básico

```python
from sankhya_sdk.validations import EntityValidator, EntityValidationError

# Validar uma única entidade
try:
    EntityValidator.validate_entity(MyEntity)
except EntityValidationError as e:
    print(f"Entidade inválida: {e}")

# Validar todas as entidades em um módulo
import mymodule
EntityValidator.validate_entities(mymodule)
```

### Verificação de Igualdade

```python
from sankhya_sdk.validations import EntityValidator

# Verificar se uma entidade implementa métodos de igualdade
if EntityValidator.implements_equality(MyEntity):
    print("Entidade implementa __eq__ e __hash__")
```

### Integração com Validators

O módulo também pode ser usado através da função de conveniência em `validators`:

```python
from sankhya_sdk.attributes.validators import validate_entity_class

# Valida a classe de entidade
validate_entity_class(MyEntity)
```

## EntityValidation

A classe `EntityValidation` contém padrões Regex compilados para extrair informações de mensagens de erro da API Sankhya.

### Padrões Disponíveis

| Padrão | Descrição | Grupos Nomeados |
|--------|-----------|-----------------|
| `REFERENCE_FIELDS_FIRST_LEVEL_PATTERN` | Campos de referência de primeiro nível | `entity`, `field` |
| `REFERENCE_FIELDS_SECOND_LEVEL_PATTERN` | Campos de referência de segundo nível | `parentEntity`, `entity`, `field` |
| `PROPERTY_VALUE_ERROR_PATTERN` | Erro ao obter valor de propriedade | `propertyName` |
| `PROPERTY_NAME_ERROR_PATTERN` | Descritor de campo inválido | `propertyName` |
| `PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN` | Identificador não associado | `entity`, `propertyName` |
| `PROPERTY_NOT_FOUND_PATTERN` | Campo não existe | `entity`, `propertyName` |
| `PROPERTY_NAME_INVALID_ERROR_PATTERN` | Nome de coluna inválido | `propertyName` |
| `PROPERTY_WIDTH_ERROR_PATTERN` | Largura acima do limite | `propertyName`, `currentWidth`, `widthAllowed` |
| `PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN` | Conflito de chave estrangeira | `constraintName`, `database`, `table`, `column` |
| `DUPLICATED_DOCUMENT_PATTERN` | CNPJ/CPF duplicado | `name` |
| `BUSINESS_RULE_RESTRICTION_PATTERN` | Regra de negócio bloqueou operação | `ruleName`, `errorMessage` |
| `FULL_TRANSACTION_LOGS_PATTERN` | Log de transações cheio | `database` |
| `MISSING_RELATION_PATTERN` | Relacionamento não encontrado | `missingRelation`, `entity` |
| `MISSING_ATTRIBUTE_PATTERN` | Atributo obrigatório faltando | `attributeName` |

### Uso Básico

```python
from sankhya_sdk.validations import EntityValidation

# Verificar se uma mensagem de erro indica campo não encontrado
error_message = "Campo não existe: PARCEIRO->NOMEPARC"
match = EntityValidation.match_property_not_found(error_message)
if match:
    entity = match.group("entity")       # "PARCEIRO"
    field = match.group("propertyName")  # "NOMEPARC"
    print(f"Campo '{field}' não existe na entidade '{entity}'")
```

### Métodos de Conveniência

A classe fornece métodos estáticos para cada padrão:

```python
# Correspondência de primeiro nível
match = EntityValidation.match_reference_first_level("Parceiro_NOMEPARC")

# Erro de valor de propriedade
match = EntityValidation.match_property_value_error(
    "erro ao obter valor da propriedade 'CODPROD'"
)

# Restrição de regra de negócio
match = EntityValidation.match_business_rule_restriction(
    'A regra "Validação de Crédito" não permitiu a operação.\n'
    'Cliente sem limite disponível.'
)
if match:
    rule = match.group("ruleName")          # "Validação de Crédito"
    message = match.group("errorMessage")   # "Cliente sem limite disponível."
```

### Exemplo de Tratamento de Erros

```python
from sankhya_sdk.validations import EntityValidation
from sankhya_sdk.exceptions import SankhyaException

def handle_sankhya_error(error: SankhyaException) -> None:
    """Trata erros da API Sankhya de forma inteligente."""
    message = str(error)
    
    # Verifica documento duplicado
    if match := EntityValidation.match_duplicated_document(message):
        name = match.group("name")
        raise ValueError(f"Parceiro '{name}' já possui este documento")
    
    # Verifica violação de chave estrangeira
    if match := EntityValidation.match_foreign_key_restriction(message):
        table = match.group("table")
        raise ValueError(f"Registro referenciado não existe na tabela {table}")
    
    # Verifica regra de negócio
    if match := EntityValidation.match_business_rule_restriction(message):
        rule = match.group("ruleName")
        details = match.group("errorMessage")
        raise ValueError(f"Regra '{rule}' bloqueou: {details}")
    
    # Erro genérico
    raise error
```

## Exceções

### Hierarquia de Exceções

```
EntityValidationError (base)
├── MissingConstructorError
├── MissingEntityAttributeError
├── MissingBaseClassError
├── MissingEqualityMethodsError
├── InvalidPropertyAttributeError
└── MissingSerializeMethodError
```

### Tratamento de Exceções

```python
from sankhya_sdk.validations import (
    EntityValidationError,
    MissingEntityAttributeError,
    MissingBaseClassError,
)

try:
    EntityValidator.validate_entity(MyEntity)
except MissingEntityAttributeError:
    print("Adicione o decorador @entity à classe")
except MissingBaseClassError:
    print("A classe deve herdar de TransportEntityBase")
except EntityValidationError as e:
    print(f"Erro de validação: {e}")
```

## Boas Práticas

1. **Valide entidades durante o desenvolvimento**: Use `EntityValidator.validate_entities()` em testes para garantir que todas as entidades estão corretas.

2. **Trate erros da API de forma inteligente**: Use `EntityValidation` para extrair informações úteis de mensagens de erro.

3. **Implemente `__eq__` e `__hash__`**: Mesmo que `TransportEntityBase` forneça implementações padrão, considere sobrescrever para comparação customizada.

4. **Use atributos corretos em campos**: Cada campo deve ter `entity_element`, `entity_key`, `entity_reference`, ou `entity_ignore`.

```python
from sankhya_sdk.attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_ignore,
)
from sankhya_sdk.models.transport.base import TransportEntityBase
from pydantic import Field
from typing import Optional


@entity("Parceiro")
class Partner(TransportEntityBase):
    # Chave primária
    code: Optional[int] = Field(
        default=None,
        json_schema_extra=entity_key("CODPARC"),
    )
    
    # Campo simples
    name: Optional[str] = Field(
        default=None,
        json_schema_extra=entity_element("NOMEPARC"),
    )
    
    # Referência a outra entidade
    city: Optional["City"] = Field(
        default=None,
        json_schema_extra=entity_reference("Cidade"),
    )
    
    # Campo ignorado na serialização
    internal_cache: Optional[dict] = Field(
        default=None,
        json_schema_extra=entity_ignore(),
    )
```
