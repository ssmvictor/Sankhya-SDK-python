"""Custom exceptions for entity validation.

This module provides a hierarchy of exceptions for handling validation errors
when validating entity classes against the SDK requirements.
"""

from typing import Any, Type


class EntityValidationError(Exception):
    """Base exception for entity validation errors.

    Attributes:
        entity_type: The type of the entity that failed validation.
        message: The error message describing the validation failure.
    """

    def __init__(self, entity_type: Type[Any], message: str) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity that failed validation.
            message: The error message describing the validation failure.
        """
        self.entity_type = entity_type
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        """Return a formatted error message.

        Returns:
            A string containing the entity type name and the error message.
        """
        return f"Validation error for entity '{self.entity_type.__name__}': {self.message}"


class MissingConstructorError(EntityValidationError):
    """Raised when an entity class lacks a parameterless constructor.

    Entity classes must have a constructor that can be called without arguments
    to support deserialization and dynamic instantiation.
    """

    def __init__(self, entity_type: Type[Any]) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity missing a parameterless constructor.
        """
        super().__init__(
            entity_type,
            "Entity must have a parameterless constructor (all parameters must have defaults)."
        )


class MissingEntityAttributeError(EntityValidationError):
    """Raised when an entity class lacks the @entity decorator.

    All entity classes must be decorated with @entity to define their
    XML element name for serialization.
    """

    def __init__(self, entity_type: Type[Any]) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity missing the @entity decorator.
        """
        super().__init__(
            entity_type,
            "Entity must be decorated with @entity decorator."
        )


class MissingBaseClassError(EntityValidationError):
    """Raised when an entity class does not inherit from TransportEntityBase.

    All transport entities must inherit from TransportEntityBase to ensure
    proper serialization and equality behavior.
    """

    def __init__(self, entity_type: Type[Any]) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity not inheriting from TransportEntityBase.
        """
        super().__init__(
            entity_type,
            "Entity must inherit from TransportEntityBase."
        )


class MissingEqualityMethodsError(EntityValidationError):
    """Raised when an entity class lacks __eq__ or __hash__ methods.

    Entity classes must implement both __eq__ and __hash__ methods
    for proper comparison and hashing behavior.
    """

    def __init__(self, entity_type: Type[Any], missing_methods: list[str]) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity missing equality methods.
            missing_methods: List of missing method names.
        """
        methods_str = ", ".join(missing_methods)
        super().__init__(
            entity_type,
            f"Entity must implement the following methods: {methods_str}."
        )
        self.missing_methods = missing_methods


class InvalidPropertyAttributeError(EntityValidationError):
    """Raised when an entity property lacks valid attributes.

    Entity properties must have at least one valid attribute:
    element, is_ignored, or reference.
    """

    def __init__(self, entity_type: Type[Any], property_name: str) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity with the invalid property.
            property_name: The name of the property with invalid attributes.
        """
        super().__init__(
            entity_type,
            f"Property '{property_name}' must have at least one valid attribute "
            "(element, is_ignored, or reference)."
        )
        self.property_name = property_name


class MissingSerializeMethodError(EntityValidationError):
    """Raised when an entity class lacks a required serialization method.

    Entity classes with serializable properties must have the
    should_serialize_field method to control serialization behavior.
    """

    def __init__(self, entity_type: Type[Any], method_name: str) -> None:
        """Initialize the exception.

        Args:
            entity_type: The type of the entity missing the serialization method.
            method_name: The name of the missing method.
        """
        super().__init__(
            entity_type,
            f"Entity must implement '{method_name}' method for serialization control."
        )
        self.method_name = method_name
