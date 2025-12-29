"""
Tipos básicos para serialização de serviços Sankhya.

Inclui classes para campos, critérios, parâmetros e outros tipos fundamentais.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TypeVar

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict, Field as PydanticField

from sankhya_sdk.enums.parameter_type import ParameterType
from .xml_serialization import (
    XmlSerializableBase,
    create_xml_element,
    get_element_attr,
    get_element_text,
    serialize_bool,
    deserialize_bool,
)


T = TypeVar("T")


class FieldValue(BaseModel):
    """Representa o valor de um campo em um serviço Sankhya."""

    model_config = ConfigDict(frozen=False)

    name: str
    value: Optional[str] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FieldValue):
            return NotImplemented
        return self.name.lower() == other.name.lower()

    def __hash__(self) -> int:
        return hash(self.name.lower())

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("campo")
        elem.set("nome", self.name)
        if self.value is not None:
            elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "FieldValue":
        """Deserializa de elemento XML."""
        return cls(
            name=get_element_attr(element, "nome", "") or element.tag,
            value=get_element_text(element) or None,
        )


class Criteria(BaseModel):
    """Representa um critério de filtragem em um serviço Sankhya."""

    model_config = ConfigDict(frozen=False)

    name: Optional[str] = None
    value: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("criterio")
        if self.name:
            elem.set("nome", self.name)
        if self.value is not None:
            elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Criteria":
        """Deserializa de elemento XML."""
        return cls(
            name=get_element_attr(element, "nome"),
            value=get_element_text(element) or None,
        )


class Field(BaseModel):
    """Representa um campo a ser retornado ou processado em um serviço Sankhya."""

    model_config = ConfigDict(frozen=False, populate_by_name=True)

    name: str
    list: Optional[str] = None
    except_: bool = PydanticField(default=False, alias="except")
    value: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("field")
        elem.set("name", self.name)
        if self.list:
            elem.set("list", self.list)
        if self.except_:
            elem.set("except", serialize_bool(self.except_))
        if self.value is not None:
            elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Field":
        """Deserializa de elemento XML."""
        return cls(
            name=get_element_attr(element, "name", ""),
            list=get_element_attr(element, "list"),
            except_=deserialize_bool(get_element_attr(element, "except", "")),
            value=get_element_text(element) or None,
        )


class Parameter(BaseModel):
    """Representa um parâmetro de um critério literal."""

    model_config = ConfigDict(frozen=False)

    type: ParameterType
    value: str

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("parameter")
        elem.set("type", self.type.value)
        elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Parameter":
        """Deserializa de elemento XML."""
        type_str = get_element_attr(element, "type", "S")
        return cls(
            type=ParameterType(type_str) if type_str else ParameterType.TEXT,
            value=get_element_text(element, ""),
        )


class LiteralCriteria(BaseModel):
    """Representa um critério literal (SQL) em um serviço Sankhya."""

    model_config = ConfigDict(frozen=False)

    expression: Optional[str] = None
    parameters: List[Parameter] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("literalCriteria")
        if self.expression:
            expr_elem = create_xml_element("expression", self.expression, parent=elem)
        if self.parameters:
            params_elem = etree.SubElement(elem, "parameters")
            for param in self.parameters:
                params_elem.append(param.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "LiteralCriteria":
        """Deserializa de elemento XML."""
        expr_elem = element.find("expression")
        params_elem = element.find("parameters")
        
        parameters = []
        if params_elem is not None:
            for param_elem in params_elem.findall("parameter"):
                parameters.append(Parameter.from_xml(param_elem))
        
        return cls(
            expression=get_element_text(expr_elem) if expr_elem is not None else None,
            parameters=parameters,
        )


class LiteralCriteriaSql(BaseModel):
    """
    Critério SQL literal (variante portuguesa).
    
    Similar a LiteralCriteria mas usa tags em português.
    """

    model_config = ConfigDict(frozen=False)

    expression: Optional[str] = None
    parameters: List[Parameter] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML com tags em português."""
        elem = etree.Element("criterioLiteralSql")
        if self.expression:
            create_xml_element("expressao", self.expression, parent=elem)
        if self.parameters:
            params_elem = etree.SubElement(elem, "parametros")
            for param in self.parameters:
                params_elem.append(param.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "LiteralCriteriaSql":
        """Deserializa de elemento XML."""
        expr_elem = element.find("expressao")
        params_elem = element.find("parametros")
        
        parameters = []
        if params_elem is not None:
            for param_elem in params_elem.findall("parameter"):
                parameters.append(Parameter.from_xml(param_elem))
        
        return cls(
            expression=get_element_text(expr_elem) if expr_elem is not None else None,
            parameters=parameters,
        )


class DataRow(BaseModel):
    """
    Representa uma linha de dados com campos dinâmicos.
    
    Usado em respostas de consultas onde os campos variam.
    """

    model_config = ConfigDict(frozen=False, extra="allow")

    fields: Dict[str, Any] = PydanticField(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Acesso a campos por chave."""
        return self.fields.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Define valor de campo."""
        self.fields[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de campo com default."""
        return self.fields.get(key, default)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("row")
        for key, value in self.fields.items():
            field_elem = etree.SubElement(elem, key)
            if value is not None:
                field_elem.text = str(value)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "DataRow":
        """Deserializa de elemento XML."""
        fields: Dict[str, Any] = {}
        
        # Inclui atributos como campos
        for attr_name, attr_value in element.attrib.items():
            fields[attr_name] = attr_value
        
        # Inclui elementos filhos como campos
        for child in element:
            fields[child.tag] = get_element_text(child) or None
        
        return cls(fields=fields)


class ReferenceFetch(BaseModel):
    """
    Configuração de busca de referências.
    
    Define se e como buscar registros relacionados.
    """

    model_config = ConfigDict(frozen=False)

    mode: Optional[str] = None
    entity_name: Optional[str] = None
    fields: List[str] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("referenceFetch")
        if self.mode:
            elem.set("mode", self.mode)
        if self.entity_name:
            elem.set("entityName", self.entity_name)
        for field in self.fields:
            create_xml_element("field", field, parent=elem)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "ReferenceFetch":
        """Deserializa de elemento XML."""
        fields = [
            get_element_text(f) 
            for f in element.findall("field") 
            if get_element_text(f)
        ]
        return cls(
            mode=get_element_attr(element, "mode"),
            entity_name=get_element_attr(element, "entityName"),
            fields=fields,
        )


class Prop(BaseModel):
    """
    Propriedade genérica chave-valor.
    
    Usada para configurações e metadados diversos.
    """

    model_config = ConfigDict(frozen=False)

    name: str
    value: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("prop")
        elem.set("name", self.name)
        if self.value is not None:
            elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Prop":
        """Deserializa de elemento XML."""
        return cls(
            name=get_element_attr(element, "name", ""),
            value=get_element_text(element) or None,
        )


class Path(BaseModel):
    """
    Representa um caminho de arquivo.
    
    Usado em operações de upload/download de arquivos.
    """

    model_config = ConfigDict(frozen=False)

    value: str
    type: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("path")
        if self.type:
            elem.set("type", self.type)
        elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Path":
        """Deserializa de elemento XML."""
        return cls(
            value=get_element_text(element, ""),
            type=get_element_attr(element, "type"),
        )


class Paths(BaseModel):
    """Lista de caminhos de arquivo."""

    model_config = ConfigDict(frozen=False)

    items: List[Path] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("paths")
        for path in self.items:
            elem.append(path.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Paths":
        """Deserializa de elemento XML."""
        items = [Path.from_xml(p) for p in element.findall("path")]
        return cls(items=items)
