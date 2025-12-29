# -*- coding: utf-8 -*-
"""
Testes unitários para entity_dynamic_serialization.py
"""

import pytest
from datetime import datetime
from decimal import Decimal

from sankhya_sdk.helpers.entity_dynamic_serialization import (
    EntityDynamicSerialization,
    Metadata,
)
from sankhya_sdk.enums.reference_level import ReferenceLevel


class TestMetadata:
    """Testes para Metadata."""

    def test_initialization_empty(self):
        """Verifica inicialização vazia."""
        metadata = Metadata()
        assert metadata.fields == []

    def test_initialization_with_fields(self):
        """Verifica inicialização com campos."""
        fields = [{"name": "CODPARC"}, {"name": "NOMEPARC"}]
        metadata = Metadata(fields=fields)
        
        assert len(metadata.fields) == 2


class TestEntityDynamicSerialization:
    """Testes para EntityDynamicSerialization."""

    def test_initialization_empty(self):
        """Verifica inicialização vazia."""
        serializer = EntityDynamicSerialization()
        
        assert serializer.dictionary == {}

    def test_initialization_with_data(self):
        """Verifica inicialização com dados."""
        data = {"CODPARC": "123", "NOMEPARC": "Test"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.dictionary == data

    def test_get_member(self):
        """Verifica get_member."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.get_member("CODPARC") == "123"

    def test_get_member_case_insensitive(self):
        """Verifica get_member com fallback para uppercase."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.get_member("codparc") is None
        # Busca por uppercase como fallback
        assert serializer.dictionary.get("CODPARC") == "123"

    def test_set_member(self):
        """Verifica set_member."""
        serializer = EntityDynamicSerialization()
        serializer.set_member("CODPARC", "123")
        
        assert serializer.dictionary["CODPARC"] == "123"

    def test_set_member_uppercase_filter(self):
        """Verifica set_member com filtro uppercase."""
        serializer = EntityDynamicSerialization(key_filter="uppercase")
        serializer.set_member("codparc", "123")
        
        assert "CODPARC" in serializer.dictionary

    def test_set_member_lowercase_filter(self):
        """Verifica set_member com filtro lowercase."""
        serializer = EntityDynamicSerialization(key_filter="lowercase")
        serializer.set_member("CODPARC", "123")
        
        assert "codparc" in serializer.dictionary

    def test_contains(self):
        """Verifica operador __contains__."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert "CODPARC" in serializer

    def test_getitem(self):
        """Verifica operador __getitem__."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer["CODPARC"] == "123"

    def test_setitem(self):
        """Verifica operador __setitem__."""
        serializer = EntityDynamicSerialization()
        serializer["CODPARC"] = "123"
        
        assert serializer["CODPARC"] == "123"

    def test_repr(self):
        """Verifica __repr__."""
        data = {"key": "value"}
        serializer = EntityDynamicSerialization(data)
        
        assert "EntityDynamicSerialization" in repr(serializer)
        assert "key" in repr(serializer)


class TestValueConversion:
    """Testes para conversão de valores."""

    @pytest.fixture
    def serializer(self):
        return EntityDynamicSerialization()

    def test_convert_to_bool_true(self, serializer):
        """Verifica conversão para bool True."""
        assert serializer._convert_to_bool("true") is True
        assert serializer._convert_to_bool("1") is True
        assert serializer._convert_to_bool("s") is True
        assert serializer._convert_to_bool("sim") is True
        assert serializer._convert_to_bool("yes") is True
        assert serializer._convert_to_bool("y") is True

    def test_convert_to_bool_false(self, serializer):
        """Verifica conversão para bool False."""
        assert serializer._convert_to_bool("false") is False
        assert serializer._convert_to_bool("0") is False
        assert serializer._convert_to_bool("n") is False
        assert serializer._convert_to_bool("no") is False

    def test_convert_to_datetime_formats(self, serializer):
        """Verifica conversão de diferentes formatos de data."""
        # Formato brasileiro
        dt = serializer._convert_to_datetime("25/12/2024")
        assert dt.day == 25
        assert dt.month == 12
        assert dt.year == 2024
        
        # Formato ISO
        dt = serializer._convert_to_datetime("2024-12-25")
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 25

    def test_convert_to_datetime_with_time(self, serializer):
        """Verifica conversão de data com hora."""
        dt = serializer._convert_to_datetime("25/12/2024 14:30:45")
        
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 45

    def test_convert_to_datetime_invalid(self, serializer):
        """Verifica erro com formato inválido."""
        with pytest.raises(ValueError):
            serializer._convert_to_datetime("invalid-date")


class TestChangeKeys:
    """Testes para change_keys."""

    def test_change_keys_success(self):
        """Verifica renomeação de chaves."""
        data = {"f0": "123", "f1": "Test"}
        serializer = EntityDynamicSerialization(data)
        
        new_keys = Metadata(fields=[
            {"name": "CODPARC"},
            {"name": "NOMEPARC"},
        ])
        
        serializer.change_keys(new_keys)
        
        assert "CODPARC" in serializer.dictionary
        assert serializer.dictionary["CODPARC"] == "123"

    def test_change_keys_mismatch(self):
        """Verifica erro com contagem de chaves diferente."""
        data = {"f0": "123"}
        serializer = EntityDynamicSerialization(data)
        
        new_keys = Metadata(fields=[
            {"name": "CODPARC"},
            {"name": "NOMEPARC"},
        ])
        
        with pytest.raises(ValueError, match="Key count mismatch"):
            serializer.change_keys(new_keys)

    def test_change_keys_none(self):
        """Verifica que None é tratado corretamente."""
        serializer = EntityDynamicSerialization({"key": "value"})
        
        # Não deve lançar exceção
        serializer.change_keys(None)


class TestLevelConversion:
    """Testes para conversão de níveis."""

    def test_level_to_int(self):
        """Verifica conversão de ReferenceLevel para int."""
        assert EntityDynamicSerialization._level_to_int(ReferenceLevel.NONE) == 0
        assert EntityDynamicSerialization._level_to_int(ReferenceLevel.FIFTH) == 5

    def test_int_to_level(self):
        """Verifica conversão de int para ReferenceLevel."""
        assert EntityDynamicSerialization._int_to_level(0) == ReferenceLevel.NONE
        assert EntityDynamicSerialization._int_to_level(5) == ReferenceLevel.FIFTH
