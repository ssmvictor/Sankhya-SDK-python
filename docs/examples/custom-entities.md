# Entidades Customizadas

Exemplos de criação de entidades para tabelas customizadas (API XML
legada). Veja [Sistema de Entidades](../core-concepts/entity-system.md) para
os metadados disponíveis.

## Estrutura Básica

```python
from decimal import Decimal
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.models.transport import TransportEntityBase


@entity("AD_MEUCAMPO")
class MinhaEntidade(TransportEntityBase):
    """Entidade para a tabela customizada AD_MEUCAMPO."""

    id_campo: Optional[int] = entity_key(entity_element("IDCAMPO", default=None))
    descricao: Optional[str] = entity_element("DESCRICAO", default=None)
    valor: Optional[Decimal] = entity_element("VALOR", default=None)
```

Os campos são declarados com `Optional[...]` e `default=None`: só os campos
atribuídos são enviados ao servidor, e o construtor sem argumentos é exigido
pelo `EntityValidator`.

---

## Com Tipos Complexos

```python
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key, entity_reference
from sankhya_sdk.models.transport import Partner, TransportEntityBase


@entity("AD_CONTRATO")
class Contrato(TransportEntityBase):
    id: Optional[int] = entity_key(entity_element("IDCONTRATO", default=None))
    code_partner: Optional[int] = entity_element("CODPARC", default=None)
    data_inicio: Optional[datetime] = entity_element("DTINICIO", default=None)
    data_fim: Optional[datetime] = entity_element("DTFIM", default=None)
    valor_total: Optional[Decimal] = entity_element("VLRTOTAL", default=None)
    ativo: Optional[bool] = entity_element("ATIVO", default=None)

    # Referência ao parceiro (buscada junto quando o servidor a retorna)
    parceiro: Optional[Partner] = entity_reference(default=None)
```

Datas usam `datetime` (enviadas como `dd/MM/yyyy HH:mm:ss`), booleanos viram
`S`/`N` e `Decimal` é enviado como texto.

---

## Uso com CRUD

```python
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sankhya_sdk import SankhyaContext
from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.helpers import EntityQueryOptions
from sankhya_sdk.models.transport import TransportEntityBase
from sankhya_sdk.request_wrappers import SimpleCRUDRequestWrapper


@entity("AD_CONTRATO")
class Contrato(TransportEntityBase):
    id: Optional[int] = entity_key(entity_element("IDCONTRATO", default=None))
    code_partner: Optional[int] = entity_element("CODPARC", default=None)
    data_inicio: Optional[datetime] = entity_element("DTINICIO", default=None)
    valor_total: Optional[Decimal] = entity_element("VLRTOTAL", default=None)
    ativo: Optional[bool] = entity_element("ATIVO", default=None)


ctx = SankhyaContext.from_settings()
try:
    SimpleCRUDRequestWrapper.initialize(ctx)

    # Find (ATIVO = 'S')
    contratos = SimpleCRUDRequestWrapper.find_all(
        Contrato(ativo=True), EntityQueryOptions(max_results=50)
    )

    # Insert (update sem chave)
    novo = Contrato(
        code_partner=1,
        data_inicio=datetime.now(),
        valor_total=Decimal("10000.00"),
        ativo=True,
    )
    criado = SimpleCRUDRequestWrapper.update(novo)

    # Update apenas do campo alterado
    if contratos:
        SimpleCRUDRequestWrapper.update(Contrato(id=contratos[0].id, ativo=False))
finally:
    SimpleCRUDRequestWrapper.dispose()
    ctx.dispose()
```

---

## Com Validação Customizada

As regras de valor usam os validadores do Pydantic, executados na criação e
na atribuição:

```python
from datetime import datetime
from typing import Optional

from pydantic import ValidationError, model_validator

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.models.transport import TransportEntityBase


@entity("AD_CONTRATO")
class Contrato(TransportEntityBase):
    id: Optional[int] = entity_key(entity_element("IDCONTRATO", default=None))
    data_inicio: Optional[datetime] = entity_element("DTINICIO", default=None)
    data_fim: Optional[datetime] = entity_element("DTFIM", default=None)

    @model_validator(mode="after")
    def validar_periodo(self) -> "Contrato":
        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError("Data fim não pode ser anterior à data início")
        return self


try:
    Contrato(data_inicio=datetime(2024, 2, 1), data_fim=datetime(2024, 1, 1))
except ValidationError as e:
    print(f"Inválido: {e.errors()[0]['msg']}")
```

Para validar a estrutura da classe (decorador, base, campos), use o
`EntityValidator` (veja [Validações](../api-reference/validations.md)):

```python
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.models.transport import TransportEntityBase
from sankhya_sdk.validations import EntityValidator


@entity("AD_MEUCAMPO")
class MinhaEntidade(TransportEntityBase):
    id_campo: Optional[int] = entity_key(entity_element("IDCAMPO", default=None))


EntityValidator.validate_entity(MinhaEntidade)  # Lança EntityValidationError se inválida
```

---

## Chave Composta

Marque cada campo da chave com `entity_key`:

```python
from decimal import Decimal
from typing import Optional

from sankhya_sdk.attributes import entity, entity_element, entity_key
from sankhya_sdk.helpers import extract_keys
from sankhya_sdk.models.transport import TransportEntityBase


@entity("AD_ITEMCONTRATO")
class ItemContrato(TransportEntityBase):
    id_contrato: Optional[int] = entity_key(entity_element("IDCONTRATO", default=None))
    sequencia: Optional[int] = entity_key(entity_element("SEQUENCIA", default=None))
    code_product: Optional[int] = entity_element("CODPROD", default=None)
    quantidade: Optional[Decimal] = entity_element("QTDE", default=None)


print(extract_keys(ItemContrato(id_contrato=1, sequencia=2)).keys)
# [{'name': 'IDCONTRATO', 'value': '1'}, {'name': 'SEQUENCIA', 'value': '2'}]
```

!!! warning "Nomes de elemento com `_`"
    `ENTIDADE_CAMPO` é interpretado como referência inline, exceto em campos
    `AD_*`. Para um campo comum com `_` no nome, use
    `entity_element("NOME_CAMPO", ignore_inline_reference=True, default=None)`.

## Próximos Passos

- [Sistema de Entidades](../core-concepts/entity-system.md)
- [Validações](../api-reference/validations.md)
