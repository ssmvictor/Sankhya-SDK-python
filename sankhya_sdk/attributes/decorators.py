from typing import Any, Callable, Optional, Type, TypeVar, Dict
from pydantic import Field, BaseModel
from pydantic.fields import FieldInfo
from .metadata import (
    EntityMetadata,
    EntityElementMetadata,
    EntityReferenceMetadata,
    EntityCustomDataMetadata,
)
from .validators import validate_element_name_format

T = TypeVar("T")

def entity(name: str) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        if not (isinstance(cls, type) and issubclass(cls, BaseModel)):
            raise TypeError(
                f"The @entity decorator can only be applied to classes that inherit from BaseModel or EntityBase. "
                f"'{cls.__name__}' does not."
            )
        setattr(cls, "__entity_metadata__", EntityMetadata(name=name))
        return cls
    return decorator

def _get_json_schema_extra(field: FieldInfo) -> Dict[str, Any]:
    if field.json_schema_extra is None:
        field.json_schema_extra = {}
    if not isinstance(field.json_schema_extra, dict):
        # Handle cases where it might be a callable, though usually it's a dict or None
        field.json_schema_extra = {}
    return field.json_schema_extra

def _apply_kwargs_to_field(field: FieldInfo, kwargs: Dict[str, Any]) -> None:
    for key, value in kwargs.items():
        setattr(field, key, value)

def entity_key(field: Optional[FieldInfo] = None, **kwargs: Any) -> Any:
    if field is None:
        field = Field(**kwargs)
    else:
        _apply_kwargs_to_field(field, kwargs)
    extra = _get_json_schema_extra(field)
    extra["is_key"] = True
    return field

def entity_element(
    element_name: str, ignore_inline_reference: bool = False, field: Optional[FieldInfo] = None, **kwargs: Any
) -> Any:
    validate_element_name_format(element_name)
    if field is None:
        field = Field(**kwargs)
    else:
        _apply_kwargs_to_field(field, kwargs)
    extra = _get_json_schema_extra(field)
    extra["element"] = EntityElementMetadata(
        element_name=element_name, ignore_inline_reference=ignore_inline_reference
    )
    return field

def entity_reference(
    custom_relation_name: Optional[str] = None, field: Optional[FieldInfo] = None, **kwargs: Any
) -> Any:
    if field is None:
        field = Field(**kwargs)
    else:
        _apply_kwargs_to_field(field, kwargs)
    extra = _get_json_schema_extra(field)
    extra["reference"] = EntityReferenceMetadata(
        custom_relation_name=custom_relation_name
    )
    return field

def entity_ignore(field: Optional[FieldInfo] = None, **kwargs: Any) -> Any:
    if field is None:
        field = Field(**kwargs)
    else:
        _apply_kwargs_to_field(field, kwargs)
    field.exclude = True
    extra = _get_json_schema_extra(field)
    extra["is_ignored"] = True
    return field

def entity_custom_data(
    max_length: Optional[int] = None, field: Optional[FieldInfo] = None, **kwargs: Any
) -> Any:
    if field is None:
        field = Field(**kwargs)
    else:
        _apply_kwargs_to_field(field, kwargs)
    extra = _get_json_schema_extra(field)
    extra["custom_data"] = EntityCustomDataMetadata(max_length=max_length)
    return field
