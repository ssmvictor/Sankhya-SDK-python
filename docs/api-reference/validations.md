# Validações

Documentação das validações da API XML legada.

## Visão Geral

O SDK valida em três níveis:

| Nível | Onde | O que valida |
|-------|------|--------------|
| Valores da entidade | Pydantic, na criação e na atribuição | Tipos e limites (`entity_custom_data(max_length=...)`) |
| Estrutura do tipo de entidade | `EntityValidator` | Se a classe segue as regras do SDK (`@entity`, base, campos) |
| Mensagens de erro do servidor | `EntityValidation` | Padrões regex para interpretar a `statusMessage` |

```python
from sankhya_sdk.validations import EntityValidation, EntityValidator
```

Não existem `ValidationResult`, `validate(entity)` nem regras de campos
obrigatórios por operação: os dados são validados pelo Pydantic, e o
servidor valida as regras de negócio (os erros viram exceções, veja
[Exceções](exceptions.md)).

---

## Validação de Valores (Pydantic)

As entidades de transporte (`sankhya_sdk.models.transport`) são modelos
Pydantic com `validate_assignment`: tipos inválidos e limites de tamanho
lançam `pydantic.ValidationError` (subclasse de `ValueError`) antes de
qualquer requisição.

```python
from pydantic import ValidationError

from sankhya_sdk.models.transport import Partner

try:
    # COMPLEMENTO aceita no máximo 30 caracteres
    Partner(name="Cliente", address_complement="x" * 40)
except ValidationError as e:
    print(f"Inválido: {e.errors()[0]['msg']}")

partner = Partner(code=1)
try:
    partner.code = "não é número"  # Também validado na atribuição
except ValidationError as e:
    print(f"Inválido: {e.errors()[0]['type']}")
```

---

## EntityValidator

Valida a **estrutura de classes** de entidade (porta do `EntityValidator` do
.NET), útil em testes de entidades customizadas. Não valida valores de uma
instância.

| Método | Descrição |
|--------|-----------|
| `validate_entity(entity_type)` | Valida uma classe; lança `EntityValidationError` (ou subclasse) se inválida |
| `validate_entities(module)` | Valida as classes de entidade definidas no módulo; retorna os nomes validados |
| `implements_equality(entity_type)` | Se a classe define `__eq__` e `__hash__` |

Regras verificadas:

| Regra | Exceção |
|-------|---------|
| Construtor sem parâmetros obrigatórios | `MissingConstructorError` |
| Decorador `@entity` | `MissingEntityAttributeError` |
| Herança de `TransportEntityBase` | `MissingBaseClassError` |
| `__eq__` e `__hash__` | `MissingEqualityMethodsError` |
| Campos com metadados válidos (elemento, referência ou ignorado) | `InvalidPropertyAttributeError` |
| Método de serialização | `MissingSerializeMethodError` |

Todas derivam de `EntityValidationError` (`sankhya_sdk.validations`), que
tem o atributo `entity_type`.

```python
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.models.transport.base import TransportEntityBase
from sankhya_sdk.validations import EntityValidationError, EntityValidator


@entity("MinhaEntidade")
class MinhaEntidade(TransportEntityBase):
    code: Optional[int] = entity_key(entity_element("CODIGO", default=None))
    name: Optional[str] = entity_element("NOME", default=None)


class SemDecorador(TransportEntityBase):
    code: Optional[int] = entity_key(entity_element("CODIGO", default=None))


EntityValidator.validate_entity(MinhaEntidade)  # OK, sem exceção

try:
    EntityValidator.validate_entity(SemDecorador)
except EntityValidationError as e:
    print(f"{type(e).__name__}: {e}")
    # MissingEntityAttributeError: Validation error for entity 'SemDecorador': ...
```

Para validar todas as entidades de um módulo (ex.: num teste):

```python
import sankhya_sdk.models.transport.partner as partner_module
from sankhya_sdk.validations import EntityValidator

print(EntityValidator.validate_entities(partner_module))  # ['Partner']
```

---

## EntityValidation

Padrões regex (pré-compilados) para interpretar mensagens de erro do
servidor, usados pelo `StatusMessageHelper` (porta do `EntityValidation` do
.NET). Cada padrão tem um método `match_*` que retorna um `re.Match` (ou
`None`) com grupos nomeados.

| Método | Mensagem reconhecida | Grupos |
|--------|----------------------|--------|
| `match_property_value_error` | `erro ao obter valor da propriedade 'X'` | `propertyName` |
| `match_property_name_error` | `Descritor do campo 'X' inválido` | `propertyName` |
| `match_property_name_invalid` | `Nome de coluna 'X' inválido` | `propertyName` |
| `match_property_name_association` | `O identificador de várias partes "E.X" não pôde ser associado` | `entity`, `propertyName` |
| `match_property_not_found` | `Campo não existe: E->X` | `entity`, `propertyName` |
| `match_property_width_error` | `Propriedade 'X' com largura acima do limite: (40 > 30)` | `propertyName`, `currentWidth`, `widthAllowed` |
| `match_foreign_key_restriction` | conflito com restrição `FOREIGN KEY` | `constraintName`, ... |
| `match_missing_attribute` | `É necessário informar o atributo 'X'` | `attributeName` |
| `match_missing_relation` | `Relacionamento: 'R' não encontrado em: 'E'` | `missingRelation`, `entity` |
| `match_business_rule_restriction` | `A regra "R" não permitiu a operação.` | `ruleName`, `errorMessage` |
| `match_duplicated_document` | `CNPJ/CPF já existente para o parceiro: 'N'` | `name` |
| `match_full_transaction_logs` | `Log de transações do banco de dados 'D' cheio` | `database` |
| `match_reference_first_level` / `match_reference_second_level` | Nomes de campo de referência (`ENTIDADE_CAMPO`) | `entity`, `field` (e `parentEntity`) |

Os padrões também estão disponíveis como atributos
(`EntityValidation.PROPERTY_WIDTH_ERROR_PATTERN`, ...).

```python
from sankhya_sdk.validations import EntityValidation

error_text = "Propriedade 'COMPLEMENTO' com largura acima do limite: (40 > 30)"

match = EntityValidation.match_property_width_error(error_text)
if match:
    print(
        f"{match['propertyName']}: {match['currentWidth']} caracteres "
        f"(máximo {match['widthAllowed']})"
    )
```

---

## Padrões de Validação

### Validar Antes de Persistir

```python
from pydantic import ValidationError

from sankhya_sdk.exceptions import ServiceRequestGeneralException
from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


def save_partner(data: dict) -> Partner | None:
    """Cria o parceiro validando os dados antes da requisição."""
    try:
        partner = Partner(**data)
    except ValidationError as e:
        print(f"Parceiro inválido: {e.errors()}")
        return None

    try:
        return SimpleCRUDRequestWrapper.update(partner)
    except ServiceRequestGeneralException as e:
        # Regras de negócio do servidor (ex.: CNPJ/CPF duplicado)
        print(f"Recusado pelo servidor: {e}")
        return None


created = save_partner({"name": "Novo Cliente", "is_client": True})
```

### Validar em Lote

```python
from typing import List, Tuple

from pydantic import ValidationError

from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


def save_partners_batch(rows: List[dict]) -> Tuple[int, int]:
    """Valida todas as linhas e envia apenas as válidas."""
    valid: List[Partner] = []
    invalid: List[Tuple[dict, str]] = []

    for row in rows:
        try:
            valid.append(Partner(**row))
        except ValidationError as e:
            invalid.append((row, str(e)))

    for partner in valid:
        SimpleCRUDRequestWrapper.update(partner)

    for row, error in invalid:
        print(f"Parceiro {row.get('name')}: {error}")

    return len(valid), len(invalid)


print(save_partners_batch([{"name": "A"}, {"name": "B", "address_complement": "x" * 40}]))
```

---

## Integração com Formulários

### Exemplo Web

```python
from flask import Flask, jsonify, request
from pydantic import ValidationError

from sankhya_sdk.models.transport import Partner
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

app = Flask(__name__)  # SimpleCRUDRequestWrapper.initialize(ctx) na inicialização


@app.route("/api/partners", methods=["POST"])
def create_partner():
    data = request.json or {}

    try:
        partner = Partner(name=data.get("name"), document=data.get("document"))
    except ValidationError as e:
        return jsonify({
            "success": False,
            "errors": [
                {"field": ".".join(map(str, err["loc"])), "message": err["msg"]}
                for err in e.errors()
            ],
        }), 400

    created = SimpleCRUDRequestWrapper.update(partner)
    return jsonify({"success": True, "id": created.code})
```

## Próximos Passos

- [Sistema de Entidades](../core-concepts/entity-system.md) - Criação de entidades
- [Tratamento de Erros](../core-concepts/error-handling.md) - Estratégias de erro
- [Exemplos](../examples/index.md) - Exemplos práticos
