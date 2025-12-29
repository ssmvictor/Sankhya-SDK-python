# -*- coding: utf-8 -*-
"""
Interface para expressões de filtro.

Define o contrato para objetos que constroem expressões de filtro
para queries no Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/IFilterExpression.cs
"""

from typing import List, Protocol, Union, runtime_checkable


@runtime_checkable
class IFilterExpression(Protocol):
    """
    Protocolo que define a interface para expressões de filtro.
    
    Classes que implementam este protocolo devem fornecer um método
    `build_expression()` que retorna uma string representando a
    expressão de filtro a ser usada em queries.
    
    Example:
        >>> class MyFilter:
        ...     def build_expression(self) -> str:
        ...         return "CODPARC = 123"
        >>> filter = MyFilter()
        >>> isinstance(filter, IFilterExpression)
        True
    """
    
    def build_expression(self) -> str:
        """
        Constrói e retorna a expressão de filtro como string.
        
        Returns:
            String contendo a expressão de filtro SQL-like
        """
        ...


# Alias for backward compatibility - ILiteralCriteria is the .NET name
ILiteralCriteria = IFilterExpression


class LiteralCriteria:
    """
    Implementação concreta de critério literal SQL-like.
    
    Permite a criação de expressões de filtro SQL-like para queries
    complexas no Sankhya. Suporta operadores básicos e combinadores.
    
    Attributes:
        expression: A expressão de filtro SQL-like
    
    Example:
        >>> criteria = LiteralCriteria("CODPARC = 123")
        >>> criteria.build_expression()
        'CODPARC = 123'
        
        >>> criteria = LiteralCriteria.equals("CODPARC", 123)
        >>> criteria.build_expression()
        'CODPARC = 123'
    """
    
    def __init__(self, expression: str = "") -> None:
        """
        Inicializa um critério literal.
        
        Args:
            expression: A expressão de filtro SQL-like
        """
        self._expression = expression
    
    @property
    def expression(self) -> str:
        """Retorna a expressão atual."""
        return self._expression
    
    def build_expression(self) -> str:
        """
        Constrói e retorna a expressão de filtro.
        
        Returns:
            String contendo a expressão de filtro SQL-like
        """
        return self._expression
    
    # =========================================================================
    # Factory Methods - Operators
    # =========================================================================
    
    @classmethod
    def equals(cls, field: str, value: Union[str, int, float]) -> "LiteralCriteria":
        """
        Cria um critério de igualdade.
        
        Args:
            field: Nome do campo
            value: Valor para comparar
            
        Returns:
            Novo LiteralCriteria com a expressão '='
            
        Example:
            >>> LiteralCriteria.equals("CODPARC", 123).build_expression()
            'CODPARC = 123'
        """
        str_value = cls._format_value(value)
        return cls(f"{field} = {str_value}")
    
    @classmethod
    def not_equals(cls, field: str, value: Union[str, int, float]) -> "LiteralCriteria":
        """
        Cria um critério de diferença.
        
        Args:
            field: Nome do campo
            value: Valor para comparar
            
        Returns:
            Novo LiteralCriteria com a expressão '<>'
        """
        str_value = cls._format_value(value)
        return cls(f"{field} <> {str_value}")
    
    @classmethod
    def greater_than(cls, field: str, value: Union[int, float]) -> "LiteralCriteria":
        """
        Cria um critério maior que.
        
        Args:
            field: Nome do campo
            value: Valor numérico para comparar
            
        Returns:
            Novo LiteralCriteria com a expressão '>'
        """
        return cls(f"{field} > {value}")
    
    @classmethod
    def greater_or_equal(cls, field: str, value: Union[int, float]) -> "LiteralCriteria":
        """
        Cria um critério maior ou igual.
        
        Args:
            field: Nome do campo
            value: Valor numérico para comparar
            
        Returns:
            Novo LiteralCriteria com a expressão '>='
        """
        return cls(f"{field} >= {value}")
    
    @classmethod
    def less_than(cls, field: str, value: Union[int, float]) -> "LiteralCriteria":
        """
        Cria um critério menor que.
        
        Args:
            field: Nome do campo
            value: Valor numérico para comparar
            
        Returns:
            Novo LiteralCriteria com a expressão '<'
        """
        return cls(f"{field} < {value}")
    
    @classmethod
    def less_or_equal(cls, field: str, value: Union[int, float]) -> "LiteralCriteria":
        """
        Cria um critério menor ou igual.
        
        Args:
            field: Nome do campo
            value: Valor numérico para comparar
            
        Returns:
            Novo LiteralCriteria com a expressão '<='
        """
        return cls(f"{field} <= {value}")
    
    @classmethod
    def like(cls, field: str, pattern: str) -> "LiteralCriteria":
        """
        Cria um critério LIKE.
        
        Args:
            field: Nome do campo
            pattern: Padrão LIKE (use % como wildcard)
            
        Returns:
            Novo LiteralCriteria com a expressão 'LIKE'
            
        Example:
            >>> LiteralCriteria.like("NOMEPARC", "%NOME%").build_expression()
            "NOMEPARC LIKE '%NOME%'"
        """
        return cls(f"{field} LIKE '{pattern}'")
    
    @classmethod
    def in_(cls, field: str, values: List[Union[str, int, float]]) -> "LiteralCriteria":
        """
        Cria um critério IN.
        
        Args:
            field: Nome do campo
            values: Lista de valores
            
        Returns:
            Novo LiteralCriteria com a expressão 'IN'
            
        Example:
            >>> LiteralCriteria.in_("CODPARC", [1, 2, 3]).build_expression()
            'CODPARC IN (1, 2, 3)'
        """
        formatted = [cls._format_value(v) for v in values]
        values_str = ", ".join(formatted)
        return cls(f"{field} IN ({values_str})")
    
    @classmethod
    def between(
        cls, field: str, start: Union[int, float], end: Union[int, float]
    ) -> "LiteralCriteria":
        """
        Cria um critério BETWEEN.
        
        Args:
            field: Nome do campo
            start: Valor inicial
            end: Valor final
            
        Returns:
            Novo LiteralCriteria com a expressão 'BETWEEN'
        """
        return cls(f"{field} BETWEEN {start} AND {end}")
    
    @classmethod
    def is_null(cls, field: str) -> "LiteralCriteria":
        """
        Cria um critério IS NULL.
        
        Args:
            field: Nome do campo
            
        Returns:
            Novo LiteralCriteria com a expressão 'IS NULL'
        """
        return cls(f"{field} IS NULL")
    
    @classmethod
    def is_not_null(cls, field: str) -> "LiteralCriteria":
        """
        Cria um critério IS NOT NULL.
        
        Args:
            field: Nome do campo
            
        Returns:
            Novo LiteralCriteria com a expressão 'IS NOT NULL'
        """
        return cls(f"{field} IS NOT NULL")
    
    # =========================================================================
    # Combinators
    # =========================================================================
    
    def and_(self, other: "LiteralCriteria") -> "LiteralCriteria":
        """
        Combina com outro critério usando AND.
        
        Args:
            other: Outro critério para combinar
            
        Returns:
            Novo LiteralCriteria com as expressões combinadas
            
        Example:
            >>> c1 = LiteralCriteria.equals("CODPARC", 1)
            >>> c2 = LiteralCriteria.equals("ATIVO", "S")
            >>> c1.and_(c2).build_expression()
            "CODPARC = 1 AND ATIVO = 'S'"
        """
        return LiteralCriteria(f"{self._expression} AND {other._expression}")
    
    def or_(self, other: "LiteralCriteria") -> "LiteralCriteria":
        """
        Combina com outro critério usando OR.
        
        Args:
            other: Outro critério para combinar
            
        Returns:
            Novo LiteralCriteria com as expressões combinadas
        """
        return LiteralCriteria(f"({self._expression}) OR ({other._expression})")
    
    def not_(self) -> "LiteralCriteria":
        """
        Nega o critério atual.
        
        Returns:
            Novo LiteralCriteria com a expressão negada
        """
        return LiteralCriteria(f"NOT ({self._expression})")
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    @staticmethod
    def _format_value(value: Union[str, int, float]) -> str:
        """
        Formata um valor para uso em expressão SQL.
        
        Args:
            value: Valor a formatar
            
        Returns:
            Valor formatado como string
        """
        if isinstance(value, str):
            # Escapa aspas simples
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        return str(value)
    
    def __str__(self) -> str:
        """Representação string."""
        return self._expression
    
    def __repr__(self) -> str:
        """Representação para debug."""
        return f"LiteralCriteria('{self._expression}')"
    
    def __eq__(self, other: object) -> bool:
        """Comparação de igualdade."""
        if not isinstance(other, LiteralCriteria):
            return False
        return self._expression == other._expression
    
    def __hash__(self) -> int:
        """Hash para uso em dicionários."""
        return hash(self._expression)
