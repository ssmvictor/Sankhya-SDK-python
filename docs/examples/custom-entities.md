# Entidades Customizadas

Exemplos de criação de entidades para tabelas customizadas.

## Estrutura Básica

```python
from sankhya_sdk.attributes import entity, entity_key, entity_element
from sankhya_sdk.transport_entities import EntityBase

@entity("MeuCampo", "AD_MEUCAMPO")
class MinhaEntidade(EntityBase):
    """Entidade para tabela customizada AD_MEUCAMPO."""
    
    @entity_key("IDCAMPO")
    id_campo: int
    
    @entity_element("DESCRICAO")
    descricao: str
    
    @entity_element("VALOR", required=False)
    valor: float = 0.0
```

---

## Com Tipos Complexos

```python
from datetime import date, datetime
from decimal import Decimal

@entity("Contrato", "AD_CONTRATO")
class Contrato(EntityBase):
    @entity_key("IDCONTRATO")
    id: int
    
    @entity_element("CODPARC")
    code_partner: int
    
    @entity_element("DTINICIO")
    data_inicio: date
    
    @entity_element("DTFIM")
    data_fim: date
    
    @entity_element("VLRTOTAL")
    valor_total: Decimal
    
    @entity_element("ATIVO", required=False)
    ativo: bool = True
```

---

## Uso com CRUD

```python
from sankhya_sdk import SankhyaContext
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper

with SankhyaContext.from_settings() as ctx:
    crud = SimpleCRUDRequestWrapper(ctx.wrapper)
    
    # Find
    contratos = crud.find(Contrato, "ATIVO = 'S'")
    
    # Insert
    novo = Contrato()
    novo.code_partner = 1
    novo.data_inicio = date.today()
    novo.valor_total = Decimal("10000.00")
    crud.insert(novo)
    
    # Update
    contrato = contratos[0]
    contrato.ativo = False
    crud.update(contrato)
```

---

## Com Validação Customizada

```python
from sankhya_sdk.validations import EntityValidation

@entity("Contrato", "AD_CONTRATO")
class Contrato(EntityBase):
    @entity_key("IDCONTRATO")
    id: int
    
    @entity_element("DTINICIO")
    data_inicio: date
    
    @entity_element("DTFIM")
    data_fim: date
    
    def validate(self) -> list[EntityValidation]:
        errors = super().validate()
        
        if self.data_fim < self.data_inicio:
            errors.append(EntityValidation.custom(
                "DTFIM",
                "Data fim não pode ser anterior à data início"
            ))
        
        return errors
```

---

## Chave Composta

```python
@entity("ItemContrato", "AD_ITEMCONTRATO")
class ItemContrato(EntityBase):
    @entity_key("IDCONTRATO")
    id_contrato: int
    
    @entity_key("SEQUENCIA")
    sequencia: int
    
    @entity_element("CODPROD")
    code_product: int
    
    @entity_element("QTDE")
    quantidade: Decimal
```

## Próximos Passos

- [Sistema de Entidades](../core-concepts/entity-system.md)
- [Validações](../api-reference/validations.md)
