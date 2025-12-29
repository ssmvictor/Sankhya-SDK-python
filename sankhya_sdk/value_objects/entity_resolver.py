from dataclasses import dataclass, field
from typing import List, Optional, Dict
from sankhya_sdk.models.service.basic_types import (
    FieldValue,
    Field,
    Criteria,
    LiteralCriteria,
)


@dataclass
class EntityResolverResult:
    """Resultado da resolução de uma entidade para uso em serviços."""

    entity_name: str
    field_values: List[FieldValue] = field(default_factory=list)
    keys: List[FieldValue] = field(default_factory=list)
    criteria: List[Criteria] = field(default_factory=list)
    fields: List[Field] = field(default_factory=list)
    references: Dict[str, List[Field]] = field(default_factory=dict)
    literal_criteria: Optional[LiteralCriteria] = None

    def add_field_value(self, name: str, value: str) -> None:
        """Adiciona um valor de campo ao resultado."""
        self.field_values.append(FieldValue(name=name, value=value))

    def add_key(self, name: str, value: str) -> None:
        """Adiciona uma chave ao resultado."""
        self.keys.append(FieldValue(name=name, value=value))

    def add_criteria(self, name: str, value: str) -> None:
        """Adiciona um critério de filtragem ao resultado."""
        self.criteria.append(Criteria(name=name, value=value))

    def add_field(self, name: str) -> None:
        """Adiciona um campo a ser retornado ao resultado."""
        self.fields.append(Field(name=name))

    def add_reference(self, relation_name: str, field_name: str) -> None:
        """Adiciona um campo de referência ao resultado."""
        if relation_name not in self.references:
            self.references[relation_name] = []
        self.references[relation_name].append(Field(name=field_name))