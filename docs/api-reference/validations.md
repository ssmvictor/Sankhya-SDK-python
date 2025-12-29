# Validações

Documentação do sistema de validação de entidades.

## Visão Geral

O SDK inclui um sistema de validação para garantir integridade dos dados antes de enviar à API:

```python
from sankhya_sdk.validations import EntityValidator, EntityValidation
```

---

## EntityValidator

Validador principal de entidades.

### Uso Básico

```python
from sankhya_sdk.validations import EntityValidator
from sankhya_sdk.transport_entities import Partner

validator = EntityValidator()

partner = Partner()
partner.name = "Cliente"  # Faltando código (chave)

result = validator.validate(partner)

if not result.is_valid:
    for error in result.errors:
        print(f"Campo: {error.field}")
        print(f"Erro: {error.message}")
```

### Métodos

#### `validate(entity) -> ValidationResult`

Valida uma entidade.

```python
result = validator.validate(partner)
```

#### `validate_many(entities) -> list[ValidationResult]`

Valida múltiplas entidades.

```python
results = validator.validate_many(partners)
for i, result in enumerate(results):
    if not result.is_valid:
        print(f"Entidade {i}: {result.errors}")
```

#### `validate_for_operation(entity, operation) -> ValidationResult`

Valida para operação específica.

```python
from sankhya_sdk.enums import OperationType

# Insert requer mais campos que Update
result = validator.validate_for_operation(partner, OperationType.INSERT)
```

### Regras de Validação

| Regra | Descrição |
|-------|-----------|
| Campos obrigatórios | Verifica se campos `required=True` estão preenchidos |
| Tipos de dados | Verifica se tipos estão corretos |
| Tamanho máximo | Verifica `max_length` em strings |
| Chaves | Verifica se chaves estão preenchidas (para update/delete) |
| Referências | Valida referências entre entidades |

---

## ValidationResult

Resultado de uma validação.

### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `is_valid` | `bool` | Se validação passou |
| `errors` | `list[EntityValidation]` | Lista de erros |
| `warnings` | `list[EntityValidation]` | Lista de avisos |

### Métodos

#### `raise_if_invalid() -> None`

Lança exceção se inválido.

```python
result = validator.validate(partner)
result.raise_if_invalid()  # Lança OperationException se inválido
```

#### `to_dict() -> dict`

Converte para dicionário.

```python
data = result.to_dict()
# {"is_valid": False, "errors": [...], "warnings": [...]}
```

---

## EntityValidation

Representa um erro ou aviso de validação.

### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `field` | `str` | Nome do campo |
| `message` | `str` | Mensagem de erro |
| `severity` | `str` | Severidade (ERROR/WARNING) |
| `code` | `str \| None` | Código do erro |

### Factory Methods

```python
from sankhya_sdk.validations import EntityValidation

# Erro de campo obrigatório
error = EntityValidation.required_field("NOMEPARC", "Nome do parceiro é obrigatório")

# Erro de tipo
error = EntityValidation.invalid_type("CODPARC", "int", "str")

# Erro de tamanho
error = EntityValidation.max_length_exceeded("DESCRICAO", 100, 150)

# Erro customizado
error = EntityValidation.custom("VALOR", "Valor não pode ser negativo")
```

---

## Validações Customizadas

### Em Entidades

Implemente o método `validate` na entidade:

```python
from sankhya_sdk.transport_entities import EntityBase
from sankhya_sdk.validations import EntityValidation

class MinhaEntidade(EntityBase):
    @entity_key("ID")
    id: int
    
    @entity_element("VALOR")
    valor: float
    
    @entity_element("DATA_INICIO")
    data_inicio: date
    
    @entity_element("DATA_FIM")
    data_fim: date
    
    def validate(self) -> list[EntityValidation]:
        """Validações customizadas."""
        errors = super().validate()
        
        # Validação de negócio
        if self.valor < 0:
            errors.append(EntityValidation.custom(
                "VALOR",
                "Valor não pode ser negativo"
            ))
        
        # Validação de intervalo de datas
        if self.data_fim < self.data_inicio:
            errors.append(EntityValidation.custom(
                "DATA_FIM",
                "Data fim não pode ser anterior à data início"
            ))
        
        return errors
```

### Com Validator Customizado

```python
from sankhya_sdk.validations import EntityValidator, EntityValidation

class MeuValidator(EntityValidator):
    """Validator com regras adicionais."""
    
    def validate(self, entity) -> ValidationResult:
        # Validação padrão
        result = super().validate(entity)
        
        # Regras adicionais
        if isinstance(entity, Partner):
            self._validate_partner_rules(entity, result)
        
        return result
    
    def _validate_partner_rules(self, partner: Partner, result: ValidationResult):
        # Validação de CNPJ/CPF
        if partner.cgc_cpf and not self._is_valid_cpf_cnpj(partner.cgc_cpf):
            result.errors.append(EntityValidation.custom(
                "CGC_CPF",
                "CPF/CNPJ inválido"
            ))
        
        # Email obrigatório para clientes
        if partner.type_partner == "C" and not partner.email:
            result.warnings.append(EntityValidation.custom(
                "EMAIL",
                "Email recomendado para clientes",
                severity="WARNING"
            ))
    
    def _is_valid_cpf_cnpj(self, value: str) -> bool:
        # Implementação de validação
        return len(value) in [11, 14]
```

---

## Padrões de Validação

### Validar Antes de Persistir

```python
def save_partner(crud: SimpleCRUDRequestWrapper, partner: Partner):
    """Salva parceiro com validação."""
    validator = EntityValidator()
    result = validator.validate(partner)
    
    if not result.is_valid:
        raise ValueError(f"Parceiro inválido: {result.errors}")
    
    if result.warnings:
        for warning in result.warnings:
            logging.warning(f"Aviso: {warning.message}")
    
    return crud.insert(partner)
```

### Validar em Lote

```python
def save_partners_batch(crud, partners: list[Partner]):
    """Salva parceiros em lote com validação."""
    validator = EntityValidator()
    
    valid_partners = []
    invalid_partners = []
    
    for partner in partners:
        result = validator.validate(partner)
        if result.is_valid:
            valid_partners.append(partner)
        else:
            invalid_partners.append((partner, result.errors))
    
    # Processa válidos
    for partner in valid_partners:
        crud.insert(partner)
    
    # Reporta inválidos
    if invalid_partners:
        for partner, errors in invalid_partners:
            logging.error(f"Parceiro {partner.name}: {errors}")
    
    return len(valid_partners), len(invalid_partners)
```

---

## Patterns de Erro

### Padrões de Mensagem

O SDK usa padrões regex para identificar tipos de erro:

```python
from sankhya_sdk.validations import EntityValidation

# Verifica se é erro de propriedade ausente
if EntityValidation.match_property_name_association(error_text):
    # Erro de referência/associação
    pass

# Verifica se é erro de nome inválido
if EntityValidation.match_property_name_invalid(error_text):
    # Erro de nome de propriedade
    pass
```

---

## Integração com Formulários

### Exemplo Web

```python
from flask import request, jsonify

@app.route('/api/partners', methods=['POST'])
def create_partner():
    data = request.json
    
    partner = Partner()
    partner.name = data.get('name')
    partner.cgc_cpf = data.get('cgc_cpf')
    
    validator = EntityValidator()
    result = validator.validate(partner)
    
    if not result.is_valid:
        return jsonify({
            'success': False,
            'errors': [
                {'field': e.field, 'message': e.message}
                for e in result.errors
            ]
        }), 400
    
    crud.insert(partner)
    return jsonify({'success': True, 'id': partner.code_partner})
```

## Próximos Passos

- [Sistema de Entidades](../core-concepts/entity-system.md) - Criação de entidades
- [Tratamento de Erros](../core-concepts/error-handling.md) - Estratégias de erro
- [Exemplos](../examples/index.md) - Exemplos práticos
