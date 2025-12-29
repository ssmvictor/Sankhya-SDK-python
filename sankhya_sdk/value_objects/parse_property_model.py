from typing import Optional
from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo
from sankhya_sdk.attributes.metadata import EntityCustomDataMetadata
from sankhya_sdk.attributes.reflection import get_field_metadata


class ParsePropertyModel(BaseModel):
    """Representa o modelo de parse de uma propriedade de entidade."""

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    is_ignored: bool = False
    is_criteria: bool = True
    is_entity_key: bool = False
    is_entity_reference: bool = False
    is_entity_reference_inline: bool = False
    ignore_entity_reference_inline: bool = False
    property_name: Optional[str] = None
    custom_relation_name: Optional[str] = None
    custom_data: Optional[EntityCustomDataMetadata] = None

    @classmethod
    def from_field_info(
        cls, field_name: str, field_info: FieldInfo
    ) -> "ParsePropertyModel":
        """Cria um modelo de parse a partir das informações de um campo Pydantic."""
        metadata = get_field_metadata(field_info)
        is_reference = metadata.reference is not None
        ignore_inline = metadata.element.ignore_inline_reference if metadata.element else False

        return cls(
            is_ignored=metadata.is_ignored,
            is_entity_key=metadata.is_key,
            is_entity_reference=is_reference,
            is_entity_reference_inline=is_reference and not ignore_inline,
            property_name=metadata.element.element_name if metadata.element else field_name,
            custom_relation_name=metadata.reference.custom_relation_name
            if metadata.reference
            else None,
            custom_data=metadata.custom_data,
            ignore_entity_reference_inline=ignore_inline,
        )
