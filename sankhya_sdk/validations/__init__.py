"""Validation module for Sankhya SDK.

This module provides utilities for validating entity classes and parsing
API error messages.

Classes:
    EntityValidator: Static class for validating entity types.
    EntityValidation: Static class with compiled regex patterns for error parsing.

Exceptions:
    EntityValidationError: Base exception for validation errors.
    MissingConstructorError: Entity lacks parameterless constructor.
    MissingEntityAttributeError: Entity lacks @entity decorator.
    MissingBaseClassError: Entity doesn't inherit TransportEntityBase.
    MissingEqualityMethodsError: Entity lacks __eq__ or __hash__.
    InvalidPropertyAttributeError: Property lacks valid attributes.
    MissingSerializeMethodError: Entity lacks serialization method.
"""

from typing import Any

from .entity_validation import EntityValidation
from .exceptions import (
    EntityValidationError,
    MissingConstructorError,
    MissingEntityAttributeError,
    MissingBaseClassError,
    MissingEqualityMethodsError,
    InvalidPropertyAttributeError,
    MissingSerializeMethodError,
)


def __getattr__(name: str) -> Any:
    """Lazily imports EntityValidator.

    EntityValidator depends on ``sankhya_sdk.attributes`` and the transport
    models, while EntityValidation (used by the StatusMessageHelper while the
    SDK is being imported) has no dependencies. Importing EntityValidator on
    demand keeps ``sankhya_sdk.validations.entity_validation`` importable
    without triggering the attributes/value_objects import cycle.
    """
    if name == "EntityValidator":
        from .entity_validator import EntityValidator

        return EntityValidator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "EntityValidator",
    "EntityValidation",
    "EntityValidationError",
    "MissingConstructorError",
    "MissingEntityAttributeError",
    "MissingBaseClassError",
    "MissingEqualityMethodsError",
    "InvalidPropertyAttributeError",
    "MissingSerializeMethodError",
]
