# -*- coding: utf-8 -*-
"""
Testes unitários para service_request_extensions.py
"""

import pytest
from unittest.mock import Mock, MagicMock

from sankhya_sdk.helpers.service_request_extensions import (
    ServiceRequestExtensions,
    ParsePropertyModel,
    EntityResolverResult,
    resolve,
    _reference_level_to_int,
    _int_to_reference_level,
)
from sankhya_sdk.enums.reference_level import ReferenceLevel


class TestParsePropertyModel:
    """Testes para ParsePropertyModel."""

    def test_initialization(self):
        """Verifica inicialização do modelo."""
        model = ParsePropertyModel()
        
        assert model.property_name == ""
        assert model.is_ignored is False
        assert model.is_entity_key is False
        assert model.is_entity_reference is False
        assert model.is_entity_reference_inline is False
        assert model.ignore_entity_reference_inline is False
        assert model.custom_relation_name == ""
        assert model.is_criteria is False
        assert model.custom_data is None


class TestEntityResolverResult:
    """Testes para EntityResolverResult."""

    def test_initialization(self):
        """Verifica inicialização do resultado."""
        result = EntityResolverResult("TestEntity")
        
        assert result.name == "TestEntity"
        assert result.fields == []
        assert result.keys == []
        assert result.criteria == []
        assert result.references == {}
        assert result.literal_criteria == ""


class TestReferenceLevelConversion:
    """Testes para conversão de ReferenceLevel."""

    def test_level_to_int(self):
        """Verifica conversão de ReferenceLevel para int."""
        assert _reference_level_to_int(ReferenceLevel.NONE) == 0
        assert _reference_level_to_int(ReferenceLevel.FIRST) == 1
        assert _reference_level_to_int(ReferenceLevel.SECOND) == 2
        assert _reference_level_to_int(ReferenceLevel.THIRD) == 3
        assert _reference_level_to_int(ReferenceLevel.FOURTH) == 4
        assert _reference_level_to_int(ReferenceLevel.FIFTH) == 5
        assert _reference_level_to_int(ReferenceLevel.SIXTH) == 6

    def test_int_to_level(self):
        """Verifica conversão de int para ReferenceLevel."""
        assert _int_to_reference_level(0) == ReferenceLevel.NONE
        assert _int_to_reference_level(1) == ReferenceLevel.FIRST
        assert _int_to_reference_level(2) == ReferenceLevel.SECOND
        assert _int_to_reference_level(3) == ReferenceLevel.THIRD
        assert _int_to_reference_level(4) == ReferenceLevel.FOURTH
        assert _int_to_reference_level(5) == ReferenceLevel.FIFTH
        assert _int_to_reference_level(6) == ReferenceLevel.SIXTH


class TestServiceRequestExtensions:
    """Testes para ServiceRequestExtensions."""

    def test_get_unix_timestamp_returns_string(self):
        """Verifica que _get_unix_timestamp retorna string."""
        timestamp = ServiceRequestExtensions._get_unix_timestamp()
        
        assert isinstance(timestamp, str)
        assert timestamp.isdigit()
