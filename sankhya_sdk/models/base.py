from typing import Any, Dict, Set
from pydantic import BaseModel, ConfigDict, PrivateAttr


class EntityBase(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    _fields_set: Set[str] = PrivateAttr(default_factory=set)

    def model_post_init(self, __context: Any) -> None:
        self._fields_set.update(self.model_fields_set)
        self._validate_entity()

    def _validate_entity(self) -> None:
        from ..attributes.reflection import get_field_metadata
        from ..attributes.validators import validate_max_length, validate_entity_key_required

        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            metadata = get_field_metadata(field_info)

            if metadata.is_key:
                validate_entity_key_required(value, field_name)
            
            if metadata.custom_data:
                validate_max_length(value, metadata.custom_data)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name in self.model_fields:
            self._fields_set.add(name)
            # Re-validate this field
            from ..attributes.reflection import get_field_metadata
            from ..attributes.validators import validate_max_length, validate_entity_key_required
            
            field_info = self.model_fields[name]
            metadata = get_field_metadata(field_info)
            if metadata.is_key:
                validate_entity_key_required(value, name)
            if metadata.custom_data:
                validate_max_length(value, metadata.custom_data)

    def should_serialize_field(self, field_name: str) -> bool:
        # Custom logic can be added here, e.g. checking EntityIgnoreAttribute
        if field_name not in self.model_fields:
            return False
        
        field_info = self.model_fields[field_name]
        if field_info.exclude:
            return False
            
        return field_name in self._fields_set

    def get_modified_fields(self) -> Dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self._fields_set
            if name in self.model_fields
        }
