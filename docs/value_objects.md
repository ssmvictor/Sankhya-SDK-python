# ValueObjects

Este módulo contém objetos de valor (ValueObjects) que representam conceitos importantes do ecossistema Sankhya, usados principalmente para transferência de dados entre o SDK e os serviços da Sankhya.

## ServiceFile

Representa um arquivo que pode ser enviado para ou recebido de um serviço Sankhya.

### Propriedades
- `content_type`: Tipo MIME do arquivo (ex: `application/pdf`).
- `file_name`: Nome do arquivo com extensão.
- `file_extension`: Extensão do arquivo (sempre começa com `.`).
- `data`: Conteúdo binário do arquivo.

### Exemplo de Uso
```python
from pathlib import Path
from sankhya_sdk import ServiceFile

# Criar a partir de um arquivo local
sf = ServiceFile.from_path(Path("relatorio.pdf"))

# Salvar em um diretório
sf.save_to(Path("./downloads"))
```

## ParsePropertyModel

Modelo usado internamente para descrever como uma propriedade de uma entidade deve ser processada (parse) durante a resolução da entidade.

### Propriedades
- `is_ignored`: Se a propriedade deve ser ignorada.
- `is_criteria`: Se pode ser usada como critério de busca.
- `is_entity_key`: Se é uma chave primária.
- `is_entity_reference`: Se é uma referência para outra entidade.
- `property_name`: Nome da propriedade no Sankhya (mapeado pelo decorator `@entity_element`).
- `custom_data`: Metadados customizados (como tamanho máximo).

## EntityResolverResult

Resultado consolidado da análise de uma instância de entidade, preparando-a para ser enviada em uma requisição de serviço.

### Métodos Principais
- `add_field_value(name, value)`: Adiciona um valor de campo.
- `add_key(name, value)`: Adiciona uma chave primária.
- `add_criteria(name, value)`: Adiciona um critério de filtragem.
- `add_field(name)`: Adiciona um campo na lista de campos a retornar.
- `add_reference(relation_name, field_name)`: Adiciona um campo de uma entidade relacionada.

## Diagrama de Relacionamentos

```mermaid
classDiagram
    class ServiceFile {
        +str content_type
        +str file_name
        +str file_extension
        +bytes data
        +from_path(Path) ServiceFile
        +save_to(Path) Path
    }
    
    class ParsePropertyModel {
        +bool is_ignored
        +bool is_criteria
        +bool is_entity_key
        +bool is_entity_reference
        +str property_name
        +EntityCustomDataMetadata custom_data
        +from_field_info(str, FieldInfo) ParsePropertyModel
    }
    
    class EntityResolverResult {
        +str entity_name
        +List~FieldValue~ field_values
        +List~FieldValue~ keys
        +List~Criteria~ criteria
        +List~Field~ fields
        +Dict~str,List~Field~~ references
        +LiteralCriteria literal_criteria
        +add_field_value(str, str)
        +add_key(str, str)
        +add_criteria(str, str)
    }
    
    class FieldValue {
        +str name
        +Optional~str~ value
    }
    
    class Criteria {
        +str name
        +str value
    }
    
    class Field {
        +str name
        +Optional~str~ list
        +bool except_
        +Optional~str~ value
    }
    
    class LiteralCriteria {
        +Optional~str~ expression
        +List~Parameter~ parameters
    }
    
    class Parameter {
        +ParameterType type
        +str value
    }
    
    EntityResolverResult --> FieldValue
    EntityResolverResult --> Criteria
    EntityResolverResult --> Field
    EntityResolverResult --> LiteralCriteria
    LiteralCriteria --> Parameter
    ParsePropertyModel --> EntityCustomDataMetadata
```

## Comparativo .NET vs Python

| .NET SDK | Python SDK | Observação |
|----------|------------|------------|
| `ServiceFile` | `ServiceFile` | Implementado como Pydantic model. |
| `ParsePropertyModel` | `ParsePropertyModel` | Integrado com metadados Pydantic. |
| `EntityResolverResult` | `EntityResolverResult` | Dataclass com coleções tipadas. |
| `FieldValue` | `FieldValue` | Comparação case-insensitive no Python. |
| `Criteria` | `Criteria` | Campos opcionais. |
| `Field` | `Field` | Usa `except_` para evitar palavra reservada. |
