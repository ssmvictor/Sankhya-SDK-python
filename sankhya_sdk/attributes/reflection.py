from typing import Any, Optional, Type, Dict
from pydantic.fields import FieldInfo
from .metadata import (
    EntityMetadata,
    EntityFieldMetadata,
    EntityElementMetadata,
    EntityReferenceMetadata,
    EntityCustomDataMetadata,
)
from ..value_objects.entity_resolver import EntityResolverResult
from ..models.service.basic_types import FieldValue, Field
from ..models.base import EntityBase


def get_entity_name(cls: Type[Any]) -> str:
    metadata: Optional[EntityMetadata] = getattr(cls, "__entity_metadata__", None)
    if metadata:
        return metadata.name
    return cls.__name__


def get_field_metadata(field_info: FieldInfo) -> EntityFieldMetadata:
    extra = field_info.json_schema_extra
    if not isinstance(extra, dict):
        return EntityFieldMetadata()

    return EntityFieldMetadata(
        element=extra.get("element"),
        reference=extra.get("reference"),
        custom_data=extra.get("custom_data"),
        is_key=extra.get("is_key", False),
        is_ignored=extra.get("is_ignored", False) or field_info.exclude is True,
    )


def is_entity_key(field_info: FieldInfo) -> bool:
    return get_field_metadata(field_info).is_key


def get_element_name(field_info: FieldInfo) -> Optional[str]:
    metadata = get_field_metadata(field_info)
    if metadata.element:
        return metadata.element.element_name
    return None


def extract_keys(entity: EntityBase) -> EntityResolverResult:
    entity_name = get_entity_name(type(entity))
    result = EntityResolverResult(entity_name=entity_name)

    for field_name, field_info in entity.model_fields.items():
        metadata = get_field_metadata(field_info)
        element_name = metadata.element.element_name if metadata.element else field_name

        if metadata.is_key:
            value = getattr(entity, field_name)
            result.keys.append(FieldValue(name=element_name, value=str(value) if value is not None else None))
        
        if not metadata.is_ignored:
            result.fields.append(Field(name=element_name))

    return result
