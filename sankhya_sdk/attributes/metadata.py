from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EntityMetadata:
    name: str


@dataclass(frozen=True)
class EntityElementMetadata:
    element_name: str
    ignore_inline_reference: bool = False


@dataclass(frozen=True)
class EntityReferenceMetadata:
    custom_relation_name: Optional[str] = None


@dataclass(frozen=True)
class EntityCustomDataMetadata:
    max_length: Optional[int] = None


@dataclass(frozen=True)
class EntityFieldMetadata:
    element: Optional[EntityElementMetadata] = None
    reference: Optional[EntityReferenceMetadata] = None
    custom_data: Optional[EntityCustomDataMetadata] = None
    is_key: bool = False
    is_ignored: bool = False

    @property
    def element_name(self) -> Optional[str]:
        return self.element.element_name if self.element else None

    @property
    def is_reference(self) -> bool:
        return self.reference is not None

    @property
    def custom_relation_name(self) -> Optional[str]:
        return self.reference.custom_relation_name if self.reference else None
