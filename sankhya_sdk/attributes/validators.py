"""Validators for entity attributes and fields.

This module provides validation functions for entity fields and types,
including integration with the EntityValidator for full entity validation.
"""

import re
from typing import Any, Optional, Type, TYPE_CHECKING

from pydantic import ValidationError

from .metadata import EntityCustomDataMetadata
from .reflection import get_field_metadata, is_entity_key

if TYPE_CHECKING:
    from ..validations.entity_validator import EntityValidator
    from ..validations.exceptions import EntityValidationError


def validate_entity_class(entity_type: Type[Any]) -> None:
    """Validate an entity class against SDK requirements.

    This is a convenience wrapper around EntityValidator._validate_entity_type()
    that provides a simple interface for validating entity classes.

    Args:
        entity_type: The entity class to validate.

    Raises:
        EntityValidationError: If the entity fails any validation check.

    Example:
        >>> from sankhya_sdk.attributes.validators import validate_entity_class
        >>> from mymodule import MyEntity
        >>> validate_entity_class(MyEntity)  # Raises if invalid
    """
    # Lazy import to avoid circular dependency
    from ..validations.entity_validator import EntityValidator
    EntityValidator._validate_entity_type(entity_type)


def validate_max_length(value: Any, custom_data: EntityCustomDataMetadata) -> None:
    if custom_data.max_length is not None and value is not None:
        if len(str(value)) > custom_data.max_length:
            raise ValueError(f"Value too long. Max length is {custom_data.max_length}")


def validate_entity_key_required(value: Any, field_name: str) -> None:
    if value is None:
        # Allow None for keys (e.g. new entities or partial data)
        return


def validate_element_name_format(element_name: str) -> None:
    # Basic XML element name validation (no spaces, starts with letter/underscore)
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9._-]*$", element_name):
        raise ValueError(f"Invalid XML element name: {element_name}")
