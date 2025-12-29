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

from .entity_validator import EntityValidator
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
