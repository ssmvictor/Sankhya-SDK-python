# -*- coding: utf-8 -*-
"""
Testes unitários para entity_query_options.py
"""

import pytest
from datetime import timedelta

from sankhya_sdk.helpers.entity_query_options import EntityQueryOptions


class TestEntityQueryOptions:
    """Testes para EntityQueryOptions."""

    def test_default_values(self):
        """Verifica valores padrão."""
        options = EntityQueryOptions()
        
        assert options.max_results is None
        assert options.include_references is None
        assert options.max_reference_depth is None
        assert options.include_presentation_fields is None
        assert options.use_wildcard_fields is None
        assert options.timeout == timedelta(minutes=30)

    def test_custom_values(self):
        """Verifica valores customizados."""
        options = EntityQueryOptions(
            max_results=100,
            include_references=True,
            max_reference_depth=3,
            include_presentation_fields=False,
            use_wildcard_fields=True,
            timeout=timedelta(seconds=60),
        )
        
        assert options.max_results == 100
        assert options.include_references is True
        assert options.max_reference_depth == 3
        assert options.include_presentation_fields is False
        assert options.use_wildcard_fields is True
        assert options.timeout == timedelta(seconds=60)

    def test_get_timeout_seconds(self):
        """Verifica conversão de timeout para segundos."""
        options = EntityQueryOptions(timeout=timedelta(minutes=5))
        
        assert options.get_timeout_seconds() == 300.0

    def test_default_timeout_30_minutes(self):
        """Timeout padrão deve ser 30 minutos."""
        options = EntityQueryOptions()
        
        assert options.get_timeout_seconds() == 1800.0

    def test_with_max_results(self):
        """Verifica método with_max_results."""
        options = EntityQueryOptions()
        new_options = options.with_max_results(50)
        
        # Original não deve mudar
        assert options.max_results is None
        # Nova instância deve ter o valor
        assert new_options.max_results == 50

    def test_with_references(self):
        """Verifica método with_references."""
        options = EntityQueryOptions()
        new_options = options.with_references(include=True, max_depth=2)
        
        assert new_options.include_references is True
        assert new_options.max_reference_depth == 2

    def test_with_timeout(self):
        """Verifica método with_timeout."""
        options = EntityQueryOptions()
        new_options = options.with_timeout(timedelta(minutes=10))
        
        assert options.timeout == timedelta(minutes=30)
        assert new_options.timeout == timedelta(minutes=10)

    def test_timeout_validator_with_none(self):
        """Validator deve retornar 30 minutos para None."""
        options = EntityQueryOptions(timeout=None)
        
        assert options.timeout == timedelta(minutes=30)

    def test_timeout_validator_with_int(self):
        """Validator deve converter int para timedelta."""
        options = EntityQueryOptions(timeout=120)
        
        assert options.timeout == timedelta(seconds=120)

    def test_max_results_validation_ge_1(self):
        """max_results deve ser >= 1."""
        with pytest.raises(ValueError):
            EntityQueryOptions(max_results=0)

    def test_max_reference_depth_validation_range(self):
        """max_reference_depth deve estar entre 0 e 6."""
        # Valor válido
        options = EntityQueryOptions(max_reference_depth=3)
        assert options.max_reference_depth == 3
        
        # Valor inválido
        with pytest.raises(ValueError):
            EntityQueryOptions(max_reference_depth=7)

    def test_immutability_with_methods(self):
        """Métodos with_* devem retornar novas instâncias."""
        original = EntityQueryOptions(max_results=10)
        
        modified = original.with_max_results(20)
        
        assert original.max_results == 10
        assert modified.max_results == 20
        assert original is not modified
