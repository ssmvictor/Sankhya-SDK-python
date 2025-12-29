# -*- coding: utf-8 -*-
"""
Testes unitários para filter_expression.py
"""

import pytest
from typing import Protocol

from sankhya_sdk.helpers.filter_expression import IFilterExpression


class TestIFilterExpression:
    """Testes para o protocolo IFilterExpression."""

    def test_protocol_is_runtime_checkable(self):
        """Verifica se o protocolo é runtime_checkable."""
        assert hasattr(IFilterExpression, "__protocol_attrs__") or hasattr(IFilterExpression, "_is_runtime_protocol")

    def test_class_implementing_protocol_is_recognized(self):
        """Classe que implementa build_expression deve ser reconhecida."""
        
        class MyFilter:
            def build_expression(self) -> str:
                return "CODPARC = 123"
        
        filter_instance = MyFilter()
        assert isinstance(filter_instance, IFilterExpression)

    def test_class_not_implementing_protocol_is_not_recognized(self):
        """Classe que não implementa build_expression não deve ser reconhecida."""
        
        class NotAFilter:
            def some_other_method(self) -> str:
                return "something"
        
        instance = NotAFilter()
        assert not isinstance(instance, IFilterExpression)

    def test_filter_expression_returns_string(self):
        """build_expression deve retornar uma string."""
        
        class SimpleFilter:
            def build_expression(self) -> str:
                return "ATIVO = 'S'"
        
        filter_instance = SimpleFilter()
        result = filter_instance.build_expression()
        
        assert isinstance(result, str)
        assert result == "ATIVO = 'S'"

    def test_complex_filter_expression(self):
        """Teste com expressão de filtro complexa."""
        
        class ComplexFilter:
            def __init__(self, field: str, operator: str, value: str):
                self.field = field
                self.operator = operator
                self.value = value
            
            def build_expression(self) -> str:
                return f"{self.field} {self.operator} '{self.value}'"
        
        filter_instance = ComplexFilter("NOMEPARC", "LIKE", "%Test%")
        result = filter_instance.build_expression()
        
        assert result == "NOMEPARC LIKE '%Test%'"
        assert isinstance(filter_instance, IFilterExpression)
