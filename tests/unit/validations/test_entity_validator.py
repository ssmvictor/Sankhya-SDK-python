"""Unit tests for EntityValidator class.

Tests validation of entity classes against SDK requirements including
proper decorators, base class inheritance, and field configuration.
"""

from types import ModuleType
from typing import Optional
import pytest

from sankhya_sdk.validations.entity_validator import EntityValidator
from sankhya_sdk.validations.exceptions import (
    EntityValidationError,
    MissingConstructorError,
    MissingEntityAttributeError,
    MissingBaseClassError,
    MissingEqualityMethodsError,
    InvalidPropertyAttributeError,
    MissingSerializeMethodError,
)
from sankhya_sdk.models.transport.base import TransportEntityBase
from sankhya_sdk.attributes.decorators import entity, entity_key, entity_element


# =============================================================================
# Test fixtures - Valid and Invalid Entity Classes
# =============================================================================

@entity("ValidTestEntity")
class ValidEntity(TransportEntityBase):
    """A valid entity with all requirements met."""

    code: Optional[int] = entity_key(
        entity_element("CODENT", default=None)
    )
    name: Optional[str] = entity_element(
        "NOME",
        default=None
    )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValidEntity):
            return False
        return self.code == other.code

    def __hash__(self) -> int:
        return hash(self.code)


class InvalidEntityNoDecorator(TransportEntityBase):
    """Entity without @entity decorator."""

    code: Optional[int] = entity_key(
        entity_element("CODENT", default=None)
    )

class InvalidEntityNoBaseClass:
    """Entity that doesn't inherit from TransportEntityBase.
    
    We manually set __entity_metadata__ to simulate a class that has
    the entity marker but doesn't properly inherit from TransportEntityBase.
    """

    code: Optional[int] = None




# Manually set entity metadata to simulate @entity decorator
from sankhya_sdk.attributes.metadata import EntityMetadata
InvalidEntityNoBaseClass.__entity_metadata__ = EntityMetadata(name="InvalidNoBase")


@entity("InvalidNoEquality")
class InvalidEntityNoEquality(TransportEntityBase):
    """Entity without __eq__ and __hash__ methods.

    Note: TransportEntityBase provides default implementations,
    so this entity actually passes the equality check.
    This test fixture demonstrates that inherited methods are valid.
    """

    code: Optional[int] = entity_key(
        entity_element("CODENT", default=None)
    )


@entity("InvalidProperty")
class InvalidEntityInvalidProperty(TransportEntityBase):
    """Entity with a property lacking valid attributes."""

    code: Optional[int] = entity_key(
        entity_element("CODENT", default=None)
    )
    # This field has no entity_element, entity_key, or entity_ignore
    # Using plain Field without any entity metadata
    invalid_field: Optional[str] = None


# =============================================================================
# Test Class: EntityValidator
# =============================================================================

class TestEntityValidator:
    """Test suite for EntityValidator class."""

    # -------------------------------------------------------------------------
    # Constructor Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_constructor_valid_entity_passes(self) -> None:
        """Valid entity with default parameters passes constructor validation."""
        # Should not raise
        EntityValidator._validate_constructor(ValidEntity)

    def test_validate_constructor_all_defaults_passes(self) -> None:
        """Entity with all default parameters is valid."""

        @entity("AllDefaults")
        class AllDefaultsEntity(TransportEntityBase):
            field1: Optional[str] = entity_element(
                "FIELD1",
                default=None
            )
            field2: Optional[int] = entity_element(
                "FIELD2",
                default=0
            )

        EntityValidator._validate_constructor(AllDefaultsEntity)

    # -------------------------------------------------------------------------
    # Entity Decorator Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_entity_decorator_valid_entity_passes(self) -> None:
        """Entity with @entity decorator passes validation."""
        EntityValidator._validate_entity_decorator(ValidEntity)

    def test_validate_entity_decorator_no_decorator_raises(self) -> None:
        """Entity without @entity decorator raises MissingEntityAttributeError."""
        with pytest.raises(MissingEntityAttributeError) as exc_info:
            EntityValidator._validate_entity_decorator(InvalidEntityNoDecorator)

        assert exc_info.value.entity_type is InvalidEntityNoDecorator
        assert "@entity" in str(exc_info.value)

    # -------------------------------------------------------------------------
    # Base Class Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_base_class_valid_entity_passes(self) -> None:
        """Entity inheriting TransportEntityBase passes validation."""
        EntityValidator._validate_base_class(ValidEntity)

    def test_validate_base_class_no_base_class_raises(self) -> None:
        """Entity not inheriting TransportEntityBase raises MissingBaseClassError."""
        with pytest.raises(MissingBaseClassError) as exc_info:
            EntityValidator._validate_base_class(InvalidEntityNoBaseClass)

        assert exc_info.value.entity_type is InvalidEntityNoBaseClass
        assert "TransportEntityBase" in str(exc_info.value)

    # -------------------------------------------------------------------------
    # Equality Methods Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_equality_methods_valid_entity_passes(self) -> None:
        """Entity with __eq__ and __hash__ passes validation."""
        EntityValidator._validate_equality_methods(ValidEntity)

    def test_validate_equality_methods_inherited_passes(self) -> None:
        """Entity inheriting __eq__ and __hash__ from TransportEntityBase passes."""
        # InvalidEntityNoEquality inherits from TransportEntityBase which has
        # __eq__ and __hash__, so it should pass
        EntityValidator._validate_equality_methods(InvalidEntityNoEquality)

    def test_implements_equality_returns_true_for_valid(self) -> None:
        """implements_equality returns True for valid entity."""
        assert EntityValidator.implements_equality(ValidEntity) is True

    def test_implements_equality_returns_true_for_inherited(self) -> None:
        """implements_equality returns True for entity with inherited methods."""
        # TransportEntityBase provides __eq__ and __hash__
        assert EntityValidator.implements_equality(InvalidEntityNoEquality) is True

    # -------------------------------------------------------------------------
    # Property Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_properties_valid_entity_passes(self) -> None:
        """Entity with valid property attributes passes validation."""
        EntityValidator._validate_properties(ValidEntity)

    def test_validate_property_invalid_property_raises(self) -> None:
        """Property without valid attributes raises InvalidPropertyAttributeError."""
        with pytest.raises(InvalidPropertyAttributeError) as exc_info:
            EntityValidator._validate_properties(InvalidEntityInvalidProperty)

        assert exc_info.value.entity_type is InvalidEntityInvalidProperty
        assert "invalid_field" in str(exc_info.value)

    # -------------------------------------------------------------------------
    # Full Entity Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_entity_valid_entity_passes(self) -> None:
        """Full validation of valid entity passes without exception."""
        EntityValidator.validate_entity(ValidEntity)

    def test_validate_entity_no_decorator_raises(self) -> None:
        """Entity without @entity decorator raises MissingEntityAttributeError."""
        with pytest.raises(MissingEntityAttributeError):
            EntityValidator.validate_entity(InvalidEntityNoDecorator)

    def test_validate_entity_no_base_class_raises(self) -> None:
        """Entity not inheriting TransportEntityBase raises MissingBaseClassError."""
        with pytest.raises(MissingBaseClassError):
            EntityValidator.validate_entity(InvalidEntityNoBaseClass)

    def test_validate_entity_invalid_property_raises(self) -> None:
        """Entity with invalid property raises InvalidPropertyAttributeError."""
        with pytest.raises(InvalidPropertyAttributeError):
            EntityValidator.validate_entity(InvalidEntityInvalidProperty)

    # -------------------------------------------------------------------------
    # Module-Level Validation Tests
    # -------------------------------------------------------------------------

    def test_validate_entities_returns_validated_names(self) -> None:
        """validate_entities returns list of validated entity class names."""
        # Create a mock module with valid entities
        mock_module = ModuleType("mock_module")
        mock_module.__name__ = "mock_module"

        # Add a valid entity to the mock module
        @entity("MockEntity")
        class MockEntity(TransportEntityBase):
            code: Optional[int] = entity_key(
                entity_element("CODENT", default=None)
            )

        MockEntity.__module__ = "mock_module"
        setattr(mock_module, "MockEntity", MockEntity)

        validated = EntityValidator.validate_entities(mock_module)
        assert "MockEntity" in validated

    def test_validate_entities_ignores_imported_classes(self) -> None:
        """validate_entities ignores classes imported from other modules."""
        mock_module = ModuleType("mock_module")
        mock_module.__name__ = "mock_module"

        # ValidEntity is from this test module, not mock_module
        setattr(mock_module, "ValidEntity", ValidEntity)

        # Should return empty list since ValidEntity is from another module
        validated = EntityValidator.validate_entities(mock_module)
        assert "ValidEntity" not in validated


class TestEntityValidatorHasMethod:
    """Test suite for _has_method helper."""

    def test_has_method_finds_class_method(self) -> None:
        """_has_method returns True for method defined in class."""
        assert EntityValidator._has_method(ValidEntity, "__eq__") is True

    def test_has_method_finds_inherited_method(self) -> None:
        """_has_method returns True for method inherited from TransportEntityBase."""
        assert EntityValidator._has_method(InvalidEntityNoEquality, "__eq__") is True

    def test_has_method_excludes_object_method(self) -> None:
        """_has_method returns False for method only defined in object."""

        class PlainClass:
            """A class with no custom __eq__ or __hash__."""
            pass

        # object.__eq__ exists but should not count
        assert EntityValidator._has_method(PlainClass, "__eq__") is False

    def test_has_method_returns_false_for_nonexistent(self) -> None:
        """_has_method returns False for nonexistent method."""
        assert EntityValidator._has_method(ValidEntity, "nonexistent_method") is False


class TestExceptions:
    """Test suite for validation exceptions."""

    def test_entity_validation_error_str(self) -> None:
        """EntityValidationError __str__ formats correctly."""
        error = EntityValidationError(ValidEntity, "Test message")
        assert "ValidEntity" in str(error)
        assert "Test message" in str(error)

    def test_missing_constructor_error_message(self) -> None:
        """MissingConstructorError has descriptive message."""
        error = MissingConstructorError(ValidEntity)
        assert "parameterless constructor" in str(error)

    def test_missing_entity_attribute_error_message(self) -> None:
        """MissingEntityAttributeError has descriptive message."""
        error = MissingEntityAttributeError(ValidEntity)
        assert "@entity" in str(error)

    def test_missing_base_class_error_message(self) -> None:
        """MissingBaseClassError has descriptive message."""
        error = MissingBaseClassError(ValidEntity)
        assert "TransportEntityBase" in str(error)

    def test_missing_equality_methods_error_message(self) -> None:
        """MissingEqualityMethodsError lists missing methods."""
        error = MissingEqualityMethodsError(ValidEntity, ["__eq__", "__hash__"])
        assert "__eq__" in str(error)
        assert "__hash__" in str(error)

    def test_invalid_property_attribute_error_message(self) -> None:
        """InvalidPropertyAttributeError includes property name."""
        error = InvalidPropertyAttributeError(ValidEntity, "test_property")
        assert "test_property" in str(error)

    def test_missing_serialize_method_error_message(self) -> None:
        """MissingSerializeMethodError includes method name."""
        error = MissingSerializeMethodError(ValidEntity, "should_serialize")
        assert "should_serialize" in str(error)
