"""Entity validator for structural validation of transport entities.

This module provides static methods to validate that entity classes
conform to the SDK requirements including proper decorators, base class
inheritance, and field configuration.

Migrated from: Sankhya-SDK-dotnet/Src/Sankhya/Validations/EntityValidator.cs
"""

from __future__ import annotations

import inspect
from types import ModuleType
from typing import Any, Type, List

from pydantic.fields import FieldInfo

from .exceptions import (
    EntityValidationError,
    MissingConstructorError,
    MissingEntityAttributeError,
    MissingBaseClassError,
    MissingEqualityMethodsError,
    InvalidPropertyAttributeError,
    MissingSerializeMethodError,
)
from ..attributes.reflection import get_entity_name, get_field_metadata
from ..models.transport.base import TransportEntityBase


class EntityValidator:
    """Static class for validating entity types against SDK requirements.

    This validator ensures that entity classes properly implement:
    - Parameterless constructor (all parameters with defaults)
    - @entity decorator for XML serialization
    - TransportEntityBase inheritance
    - __eq__ and __hash__ for equality
    - Valid field attributes (element, is_ignored, or reference)
    """

    @staticmethod
    def validate_entities(module: ModuleType) -> List[str]:
        """Validate all entity classes in a module.

        Iterates through all classes in the module that have the @entity
        decorator or inherit from TransportEntityBase and validates them.

        Args:
            module: Python module containing entity classes to validate.

        Returns:
            List of validated entity class names.

        Raises:
            EntityValidationError: If any entity fails validation.
        """
        validated: List[str] = []
        errors: List[EntityValidationError] = []

        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip imported classes (only validate classes defined in this module)
            if obj.__module__ != module.__name__:
                continue

            # Check if it's a transport entity
            is_transport_entity = False
            try:
                if issubclass(obj, TransportEntityBase) and obj is not TransportEntityBase:
                    is_transport_entity = True
            except TypeError:
                pass

            # Check if it has @entity decorator
            has_entity_decorator = hasattr(obj, "__entity_metadata__")

            if is_transport_entity or has_entity_decorator:
                try:
                    EntityValidator._validate_entity_type(obj)
                    validated.append(name)
                except EntityValidationError as e:
                    errors.append(e)

        if errors:
            # Raise the first error with all error messages combined
            error_messages = [str(e) for e in errors]
            combined_message = "\n".join(error_messages)
            raise EntityValidationError(
                errors[0].entity_type,
                f"Multiple validation errors:\n{combined_message}"
            )

        return validated

    @staticmethod
    def validate_entity(entity_type: Type[Any]) -> None:
        """Validate a single entity type.

        Args:
            entity_type: The entity class to validate.

        Raises:
            EntityValidationError: If the entity fails validation.
        """
        EntityValidator._validate_entity_type(entity_type)

    @staticmethod
    def _validate_entity_type(entity_type: Type[Any]) -> None:
        """Validate a single entity type against all requirements.

        Args:
            entity_type: The entity class to validate.

        Raises:
            MissingConstructorError: If no parameterless constructor.
            MissingEntityAttributeError: If no @entity decorator.
            MissingBaseClassError: If doesn't inherit TransportEntityBase.
            MissingEqualityMethodsError: If missing __eq__ or __hash__.
            InvalidPropertyAttributeError: If property lacks valid attributes.
        """
        # 1. Check for parameterless constructor
        EntityValidator._validate_constructor(entity_type)

        # 2. Check for @entity decorator
        EntityValidator._validate_entity_decorator(entity_type)

        # 3. Check for TransportEntityBase inheritance
        EntityValidator._validate_base_class(entity_type)

        # 4. Check for __eq__ and __hash__
        EntityValidator._validate_equality_methods(entity_type)

        # 5. Validate each property
        EntityValidator._validate_properties(entity_type)

    @staticmethod
    def _validate_constructor(entity_type: Type[Any]) -> None:
        """Validate that entity has a parameterless constructor.

        A parameterless constructor means all __init__ parameters must have
        default values, allowing instantiation with Entity().

        Args:
            entity_type: The entity class to validate.

        Raises:
            MissingConstructorError: If constructor requires parameters.
        """
        try:
            sig = inspect.signature(entity_type.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                # Check if parameter has a default value
                if param.default is inspect.Parameter.empty and param.kind not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                ):
                    raise MissingConstructorError(entity_type)
        except ValueError:
            # If signature can't be inspected, assume it's okay
            pass

    @staticmethod
    def _validate_entity_decorator(entity_type: Type[Any]) -> None:
        """Validate that entity has the @entity decorator.

        Args:
            entity_type: The entity class to validate.

        Raises:
            MissingEntityAttributeError: If @entity decorator is missing.
        """
        if not hasattr(entity_type, "__entity_metadata__"):
            raise MissingEntityAttributeError(entity_type)

    @staticmethod
    def _validate_base_class(entity_type: Type[Any]) -> None:
        """Validate that entity inherits from TransportEntityBase.

        Args:
            entity_type: The entity class to validate.

        Raises:
            MissingBaseClassError: If not a subclass of TransportEntityBase.
        """
        try:
            if not issubclass(entity_type, TransportEntityBase):
                raise MissingBaseClassError(entity_type)
        except TypeError:
            raise MissingBaseClassError(entity_type)

    @staticmethod
    def _validate_equality_methods(entity_type: Type[Any]) -> None:
        """Validate that entity implements __eq__ and __hash__.

        Checks that the methods are defined in the class itself or in
        TransportEntityBase, not just inherited from object.

        Args:
            entity_type: The entity class to validate.

        Raises:
            MissingEqualityMethodsError: If __eq__ or __hash__ is missing.
        """
        missing_methods: List[str] = []

        if not EntityValidator._has_method(entity_type, "__eq__"):
            missing_methods.append("__eq__")

        if not EntityValidator._has_method(entity_type, "__hash__"):
            missing_methods.append("__hash__")

        if missing_methods:
            raise MissingEqualityMethodsError(entity_type, missing_methods)

    @staticmethod
    def _has_method(entity_type: Type[Any], method_name: str) -> bool:
        """Check if a method is defined in the class hierarchy (not just object).

        Args:
            entity_type: The class to check.
            method_name: The method name to look for.

        Returns:
            True if the method is defined in the class or TransportEntityBase.
        """
        # Check if method exists
        if not hasattr(entity_type, method_name):
            return False

        method = getattr(entity_type, method_name)

        # Check if it's defined in the class hierarchy above object
        for cls in entity_type.__mro__:
            if cls is object:
                continue
            if method_name in cls.__dict__:
                return True

        return False

    @staticmethod
    def _validate_properties(entity_type: Type[Any]) -> None:
        """Validate all properties of the entity have valid attributes.

        Args:
            entity_type: The entity class to validate.

        Raises:
            InvalidPropertyAttributeError: If a property lacks valid attributes.
            MissingSerializeMethodError: If serialization method is missing.
        """
        # Check if entity has model_fields (Pydantic model)
        if not hasattr(entity_type, "model_fields"):
            return

        for field_name, field_info in entity_type.model_fields.items():
            EntityValidator._validate_property(entity_type, field_name, field_info)

    @staticmethod
    def _validate_property(
        entity_type: Type[Any],
        field_name: str,
        field_info: FieldInfo
    ) -> None:
        """Validate a single property has valid attributes.

        A property is valid if it has at least one of:
        - element attribute (entity_element or entity_key)
        - is_ignored flag set to True
        - reference attribute (entity_reference)

        Args:
            entity_type: The entity class containing the property.
            field_name: The name of the property.
            field_info: Pydantic FieldInfo for the property.

        Raises:
            InvalidPropertyAttributeError: If property lacks valid attributes.
        """
        metadata = get_field_metadata(field_info)

        # Check if property has at least one valid attribute
        has_element = metadata.element is not None
        has_reference = metadata.reference is not None
        is_ignored = metadata.is_ignored

        if not (has_element or has_reference or is_ignored):
            raise InvalidPropertyAttributeError(entity_type, field_name)

        # If has element, check for serialization method
        if has_element:
            if not hasattr(entity_type, "should_serialize_field"):
                raise MissingSerializeMethodError(entity_type, "should_serialize_field")

    @staticmethod
    def implements_equality(entity_type: Type[Any]) -> bool:
        """Check if an entity type implements equality methods.

        Args:
            entity_type: The class to check.

        Returns:
            True if both __eq__ and __hash__ are properly implemented.
        """
        has_eq = EntityValidator._has_method(entity_type, "__eq__")
        has_hash = EntityValidator._has_method(entity_type, "__hash__")
        return has_eq and has_hash
