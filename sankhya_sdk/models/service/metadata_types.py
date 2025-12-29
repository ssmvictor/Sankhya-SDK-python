"""
Classes de metadados e configuração para serviços Sankhya.

Inclui tipos para status, sessão, chaves e configurações de serviço.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict, Field as PydanticField

from sankhya_sdk.models.base import EntityBase
from .xml_serialization import (
    create_xml_element,
    get_element_attr,
    get_element_text,
    to_base64,
    from_base64,
    serialize_bool,
    deserialize_bool,
)
from .basic_types import Field


class StatusMessage(BaseModel):
    """
    Mensagem de status retornada pelo serviço.
    
    O valor pode ser codificado em Base64 dependendo do contexto.
    """

    model_config = ConfigDict(frozen=False)

    value: str = ""
    is_encoded: bool = False

    @property
    def decoded_value(self) -> str:
        """Retorna o valor decodificado se necessário."""
        if self.is_encoded and self.value:
            return from_base64(self.value)
        return self.value

    @classmethod
    def from_encoded(cls, encoded_value: str) -> "StatusMessage":
        """Cria uma instância a partir de um valor codificado em Base64."""
        return cls(value=encoded_value, is_encoded=True)

    @classmethod
    def from_plain(cls, plain_value: str) -> "StatusMessage":
        """Cria uma instância a partir de um valor não codificado."""
        return cls(value=plain_value, is_encoded=False)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("statusMessage")
        if self.is_encoded:
            elem.set("encoded", "true")
        elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "StatusMessage":
        """Deserializa de elemento XML."""
        is_encoded = deserialize_bool(get_element_attr(element, "encoded", ""))
        return cls(
            value=get_element_text(element, ""),
            is_encoded=is_encoded,
        )


class Metadata(BaseModel):
    """
    Metadados de campos e entidades.
    
    Contém informações sobre a estrutura de dados retornada.
    """

    model_config = ConfigDict(frozen=False)

    fields: List[Field] = PydanticField(default_factory=list)
    total_records: Optional[int] = None
    page_size: Optional[int] = None
    current_page: Optional[int] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("metadata")
        if self.total_records is not None:
            elem.set("totalRecords", str(self.total_records))
        if self.page_size is not None:
            elem.set("pageSize", str(self.page_size))
        if self.current_page is not None:
            elem.set("currentPage", str(self.current_page))
        
        if self.fields:
            fields_elem = etree.SubElement(elem, "fields")
            for field in self.fields:
                fields_elem.append(field.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Metadata":
        """Deserializa de elemento XML."""
        fields = []
        fields_elem = element.find("fields")
        if fields_elem is not None:
            for field_elem in fields_elem:
                fields.append(Field.from_xml(field_elem))
        
        total_records = None
        page_size = None
        current_page = None
        
        if element.get("totalRecords"):
            try:
                total_records = int(element.get("totalRecords"))
            except (ValueError, TypeError):
                pass
        
        if element.get("pageSize"):
            try:
                page_size = int(element.get("pageSize"))
            except (ValueError, TypeError):
                pass
        
        if element.get("currentPage"):
            try:
                current_page = int(element.get("currentPage"))
            except (ValueError, TypeError):
                pass
        
        return cls(
            fields=fields,
            total_records=total_records,
            page_size=page_size,
            current_page=current_page,
        )


class Config(BaseModel):
    """
    Configurações de serviço.
    
    Define parâmetros de comportamento para operações CRUD e arquivos.
    """

    model_config = ConfigDict(frozen=False)

    include_presentation: bool = False
    return_fields: bool = True
    generate_records: bool = False
    validate_access: bool = True
    calculate_expressions: bool = False
    path: Optional[str] = None  # File path for file operations

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("config")
        elem.set("includePresentation", serialize_bool(self.include_presentation))
        elem.set("returnFields", serialize_bool(self.return_fields))
        elem.set("generateRecords", serialize_bool(self.generate_records))
        elem.set("validateAccess", serialize_bool(self.validate_access))
        elem.set("calculateExpressions", serialize_bool(self.calculate_expressions))
        if self.path:
            elem.set("path", self.path)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Config":
        """Deserializa de elemento XML."""
        return cls(
            include_presentation=deserialize_bool(
                get_element_attr(element, "includePresentation", "")
            ),
            return_fields=deserialize_bool(
                get_element_attr(element, "returnFields", ""), default=True
            ),
            generate_records=deserialize_bool(
                get_element_attr(element, "generateRecords", "")
            ),
            validate_access=deserialize_bool(
                get_element_attr(element, "validateAccess", ""), default=True
            ),
            calculate_expressions=deserialize_bool(
                get_element_attr(element, "calculateExpressions", "")
            ),
            path=get_element_attr(element, "path"),
        )


class Key(BaseModel):
    """
    Chave de entidade.
    
    Representa a chave primária ou única de um registro.
    """

    model_config = ConfigDict(frozen=False)

    name: Optional[str] = None
    values: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("chave")
        if self.name:
            elem.set("nome", self.name)
        for key, value in self.values.items():
            create_xml_element(key, value, parent=elem)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Key":
        """Deserializa de elemento XML."""
        values: Dict[str, Any] = {}
        for child in element:
            values[child.tag] = get_element_text(child)
        
        return cls(
            name=get_element_attr(element, "nome"),
            values=values,
        )


class Session(BaseModel):
    """
    Informações de sessão do usuário.
    
    Contém dados de autenticação e contexto do usuário logado.
    """

    model_config = ConfigDict(frozen=False)

    jsession_id: Optional[str] = None
    user_id: Optional[int] = None
    user_code: Optional[str] = None
    user_name: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    call_id: Optional[str] = None
    transaction_id: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("session")
        if self.jsession_id:
            elem.set("jsessionid", self.jsession_id)
        if self.user_id is not None:
            elem.set("userId", str(self.user_id))
        if self.user_code:
            elem.set("userCode", self.user_code)
        if self.user_name:
            elem.set("userName", self.user_name)
        if self.company_id is not None:
            elem.set("companyId", str(self.company_id))
        if self.company_name:
            elem.set("companyName", self.company_name)
        if self.call_id:
            elem.set("callId", self.call_id)
        if self.transaction_id:
            elem.set("transactionId", self.transaction_id)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Session":
        """Deserializa de elemento XML."""
        user_id = None
        company_id = None
        
        user_id_str = get_element_attr(element, "userId")
        if user_id_str:
            try:
                user_id = int(user_id_str)
            except ValueError:
                pass
        
        company_id_str = get_element_attr(element, "companyId")
        if company_id_str:
            try:
                company_id = int(company_id_str)
            except ValueError:
                pass
        
        return cls(
            jsession_id=get_element_attr(element, "jsessionid"),
            user_id=user_id,
            user_code=get_element_attr(element, "userCode"),
            user_name=get_element_attr(element, "userName"),
            company_id=company_id,
            company_name=get_element_attr(element, "companyName"),
            call_id=get_element_attr(element, "callId"),
            transaction_id=get_element_attr(element, "transactionId"),
        )


class SingleNumber(BaseModel):
    """Número único retornado por operações de geração de sequência."""

    model_config = ConfigDict(frozen=False)

    name: Optional[str] = None
    value: Optional[int] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("singleNumber")
        if self.name:
            elem.set("name", self.name)
        if self.value is not None:
            elem.text = str(self.value)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SingleNumber":
        """Deserializa de elemento XML."""
        value = None
        text = get_element_text(element)
        if text:
            try:
                value = int(text)
            except ValueError:
                pass
        
        return cls(
            name=get_element_attr(element, "name"),
            value=value,
        )


class SingleNumbers(BaseModel):
    """Lista de números únicos."""

    model_config = ConfigDict(frozen=False)

    items: List[SingleNumber] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("singleNumbers")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SingleNumbers":
        """Deserializa de elemento XML."""
        items = [
            SingleNumber.from_xml(child)
            for child in element.findall("singleNumber")
        ]
        return cls(items=items)


class Warning(BaseModel):
    """Aviso retornado pelo serviço."""

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    message: Optional[str] = None
    level: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("aviso")
        if self.code:
            elem.set("codigo", self.code)
        if self.level:
            elem.set("nivel", self.level)
        if self.message:
            elem.text = self.message
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Warning":
        """Deserializa de elemento XML."""
        return cls(
            code=get_element_attr(element, "codigo"),
            level=get_element_attr(element, "nivel"),
            message=get_element_text(element),
        )


class Warnings(BaseModel):
    """Lista de avisos."""

    model_config = ConfigDict(frozen=False)

    items: List[Warning] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("avisos")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Warnings":
        """Deserializa de elemento XML."""
        items = [Warning.from_xml(child) for child in element]
        return cls(items=items)
