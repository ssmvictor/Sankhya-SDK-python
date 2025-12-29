# Sistema de Atributos (Decoradores)

O Sankhya SDK para Python utiliza um sistema de decoradores baseado em Pydantic v2 para mapear classes Python para entidades da API Sankhya, replicando a funcionalidade do SDK .NET.

## Visão Geral

Os decoradores permitem definir metadados em classes e campos, que são usados para:
1. Mapear nomes de classes para nomes de entidades Sankhya.
2. Mapear nomes de propriedades para nomes de campos XML.
3. Identificar chaves primárias.
4. Controlar a serialização e o rastreamento de modificações (dirty tracking).
5. Validar restrições de dados (ex: tamanho máximo).

## Decoradores Disponíveis

### Decoradores de Classe

| Decorador | Descrição | Exemplo |
|-----------|-----------|---------|
| `@entity(name)` | Define o nome da entidade Sankhya. | `@entity("Parceiro")` |

### Decoradores de Campo

| Decorador | Descrição | Exemplo |
|-----------|-----------|---------|
| `entity_key()` | Marca o campo como chave primária. | `id: int = entity_key()` |
| `entity_element(name)` | Mapeia o campo para um elemento XML específico. | `name: str = entity_element("NOMEPARC")` |
| `entity_reference()` | Marca um relacionamento com outra entidade. | `partner: Partner = entity_reference()` |
| `entity_ignore()` | Ignora o campo na serialização. | `temp: str = entity_ignore()` |
| `entity_custom_data(max_length)` | Adiciona metadados de validação. | `code: str = entity_custom_data(max_length=10)` |

## Exemplo de Uso

```python
from typing import Optional
from sankhya_sdk.attributes import entity, entity_key, entity_element, entity_custom_data
from sankhya_sdk.models import EntityBase

@entity("Parceiro")
class Partner(EntityBase):
    code: int = entity_key(entity_element("CODPARC"))
    name: str = entity_element("NOMEPARC")
    document: Optional[str] = entity_custom_data(max_length=14, field=entity_element("CGC_CPF"))
```

## Comparativo .NET vs Python

| Recurso | .NET (Atributos) | Python (Decoradores) |
|---------|-----------------|---------------------|
| Entidade | `[Entity("Nome")]` | `@entity("Nome")` |
| Chave | `[EntityKey]` | `entity_key()` |
| Elemento XML | `[EntityElement("XML")]` | `entity_element("XML")` |
| Ignorar | `[EntityIgnore]` | `entity_ignore()` |
| Validação | `[EntityCustomData(MaxLength=10)]` | `entity_custom_data(max_length=10)` |
| Dirty Tracking | Flags `_fieldSet` | Atributo `_fields_set` e `model_fields_set` |

## Introspecção e Reflexão

O módulo `sankhya_sdk.attributes.reflection` fornece funções para extrair esses metadados em tempo de execução:

- `get_entity_name(cls)`: Retorna o nome mapeado da entidade.
- `extract_keys(entity)`: Extrai as chaves primárias e seus valores.
- `get_field_metadata(field_info)`: Retorna todos os metadados associados a um campo.
