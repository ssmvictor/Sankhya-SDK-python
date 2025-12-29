"""
Classes de parâmetros e critérios para consultas Sankhya.

Inclui tipos para construção de queries e parâmetros de filtro.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, Type, runtime_checkable

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict, Field as PydanticField

from sankhya_sdk.enums.parameter_type import ParameterType
from .xml_serialization import (
    create_xml_element,
    get_element_attr,
    get_element_text,
)
from .basic_types import Parameter


@runtime_checkable
class ILiteralCriteria(Protocol):
    """
    Protocolo para critérios literais.
    
    Define interface comum para diferentes tipos de critérios SQL.
    """
    
    expression: Optional[str]
    parameters: List[Parameter]
    
    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        ...
    
    @classmethod
    def from_xml(cls, element: Element) -> "ILiteralCriteria":
        """Deserializa de elemento XML."""
        ...


class Param(BaseModel):
    """
    Parâmetro único de requisição.
    
    Representa um par chave-valor para passagem de parâmetros.
    """

    model_config = ConfigDict(frozen=False)

    name: str
    value: Optional[str] = None
    type: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("param")
        elem.set("name", self.name)
        if self.type:
            elem.set("type", self.type)
        if self.value is not None:
            elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Param":
        """Deserializa de elemento XML."""
        return cls(
            name=get_element_attr(element, "name", ""),
            value=get_element_text(element) or None,
            type=get_element_attr(element, "type"),
        )


class Params(BaseModel):
    """
    Lista de parâmetros de requisição.
    
    Encapsula múltiplos parâmetros para passagem ao serviço.
    """

    model_config = ConfigDict(frozen=False)

    items: List[Param] = PydanticField(default_factory=list)

    def add(self, name: str, value: Optional[str] = None, type_: Optional[str] = None) -> "Params":
        """
        Adiciona um parâmetro à lista.
        
        Args:
            name: Nome do parâmetro
            value: Valor do parâmetro
            type_: Tipo do parâmetro
            
        Returns:
            Self para encadeamento
        """
        self.items.append(Param(name=name, value=value, type=type_))
        return self

    def get(self, name: str) -> Optional[Param]:
        """
        Obtém um parâmetro por nome.
        
        Args:
            name: Nome do parâmetro
            
        Returns:
            Parâmetro encontrado ou None
        """
        for param in self.items:
            if param.name == name:
                return param
        return None

    def get_value(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Obtém o valor de um parâmetro por nome.
        
        Args:
            name: Nome do parâmetro
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do parâmetro ou default
        """
        param = self.get(name)
        return param.value if param else default

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("params")
        for param in self.items:
            elem.append(param.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Params":
        """Deserializa de elemento XML."""
        items = [Param.from_xml(child) for child in element.findall("param")]
        return cls(items=items)


class QueryCriteria(BaseModel):
    """
    Critério de consulta com operador.
    
    Permite definir filtros com operadores de comparação.
    """

    model_config = ConfigDict(frozen=False)

    field: str
    operator: str = "="
    value: Optional[str] = None
    value_type: Optional[ParameterType] = None

    def to_sql(self) -> str:
        """Gera expressão SQL para o critério."""
        if self.value is None:
            if self.operator.upper() == "IS NULL":
                return f"{self.field} IS NULL"
            elif self.operator.upper() == "IS NOT NULL":
                return f"{self.field} IS NOT NULL"
            return f"{self.field} {self.operator} NULL"
        
        # Escape de valores string
        safe_value = str(self.value).replace("'", "''")
        
        if self.value_type == ParameterType.TEXT:
            return f"{self.field} {self.operator} '{safe_value}'"
        elif self.value_type == ParameterType.DATE:
            return f"{self.field} {self.operator} '{safe_value}'"
        elif self.value_type in (ParameterType.NUMERIC, ParameterType.DECIMAL):
            return f"{self.field} {self.operator} {self.value}"
        else:
            # Tenta inferir tipo
            if self.value.isdigit():
                return f"{self.field} {self.operator} {self.value}"
            return f"{self.field} {self.operator} '{safe_value}'"

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("criterio")
        elem.set("field", self.field)
        elem.set("operator", self.operator)
        if self.value_type:
            elem.set("type", self.value_type.value)
        if self.value is not None:
            elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "QueryCriteria":
        """Deserializa de elemento XML."""
        type_str = get_element_attr(element, "type")
        value_type = ParameterType(type_str) if type_str else None
        
        return cls(
            field=get_element_attr(element, "field", ""),
            operator=get_element_attr(element, "operator", "="),
            value=get_element_text(element) or None,
            value_type=value_type,
        )


class QueryBuilder:
    """
    Construtor de queries para entidades Sankhya.
    
    Fornece interface fluente para construção de consultas.
    """

    def __init__(self, entity_name: str):
        """
        Inicializa o construtor.
        
        Args:
            entity_name: Nome da entidade a consultar
        """
        self.entity_name = entity_name
        self._fields: List[str] = []
        self._criteria: List[QueryCriteria] = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None

    def select(self, *fields: str) -> "QueryBuilder":
        """
        Define campos a retornar.
        
        Args:
            fields: Nomes dos campos
            
        Returns:
            Self para encadeamento
        """
        self._fields.extend(fields)
        return self

    def where(
        self, 
        field: str, 
        value: Any, 
        operator: str = "=",
        value_type: Optional[ParameterType] = None
    ) -> "QueryBuilder":
        """
        Adiciona critério de filtro.
        
        Args:
            field: Nome do campo
            value: Valor para comparar
            operator: Operador de comparação
            value_type: Tipo do valor
            
        Returns:
            Self para encadeamento
        """
        self._criteria.append(QueryCriteria(
            field=field,
            operator=operator,
            value=str(value) if value is not None else None,
            value_type=value_type,
        ))
        return self

    def where_null(self, field: str) -> "QueryBuilder":
        """Adiciona critério IS NULL."""
        self._criteria.append(QueryCriteria(
            field=field,
            operator="IS NULL",
            value=None,
        ))
        return self

    def where_not_null(self, field: str) -> "QueryBuilder":
        """Adiciona critério IS NOT NULL."""
        self._criteria.append(QueryCriteria(
            field=field,
            operator="IS NOT NULL",
            value=None,
        ))
        return self

    def where_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """Adiciona critério IN."""
        if not values:
            return self
        
        # Formata valores para IN
        formatted = ", ".join(f"'{v}'" for v in values)
        self._criteria.append(QueryCriteria(
            field=field,
            operator="IN",
            value=f"({formatted})",
        ))
        return self

    def order_by(self, expression: str) -> "QueryBuilder":
        """
        Define ordenação.
        
        Args:
            expression: Expressão ORDER BY
            
        Returns:
            Self para encadeamento
        """
        self._order_by = expression
        return self

    def limit(self, n: int) -> "QueryBuilder":
        """
        Define limite de registros.
        
        Args:
            n: Número máximo de registros
            
        Returns:
            Self para encadeamento
        """
        self._limit = n
        return self

    def build_expression(self) -> str:
        """
        Constrói expressão SQL para critérios.
        
        Returns:
            Expressão SQL
        """
        if not self._criteria:
            return ""
        
        parts = [c.to_sql() for c in self._criteria]
        return " AND ".join(parts)

    def build_parameters(self) -> List[Parameter]:
        """
        Constrói lista de parâmetros.
        
        Returns:
            Lista de parâmetros
        """
        parameters: List[Parameter] = []
        for crit in self._criteria:
            if crit.value is not None:
                param_type = crit.value_type or ParameterType.TEXT
                parameters.append(Parameter(
                    type=param_type,
                    value=str(crit.value),
                ))
        return parameters
