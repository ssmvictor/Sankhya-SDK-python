"""
Helpers de serialização/deserialização XML para serviços Sankhya.

Implementa funções auxiliares e protocolo XmlSerializable para conversão
entre objetos Python e elementos XML usando lxml.etree.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol, Type, TypeVar, runtime_checkable

from lxml import etree
from lxml.etree import Element

from .constants import SankhyaConstants


T = TypeVar("T", bound="XmlSerializable")


# ============================================================
# Funções de Encoding Base64
# ============================================================


def to_base64(value: str, encoding: str = "utf-8") -> str:
    """
    Codifica uma string em Base64.
    
    Args:
        value: String a ser codificada
        encoding: Encoding da string (default: utf-8)
        
    Returns:
        String codificada em Base64
    """
    if not value:
        return ""
    return base64.b64encode(value.encode(encoding)).decode("ascii")


def from_base64(value: str, encoding: str = "utf-8") -> str:
    """
    Decodifica uma string de Base64.
    
    Args:
        value: String em Base64 a ser decodificada
        encoding: Encoding esperado da string (default: utf-8)
        
    Returns:
        String decodificada
    """
    if not value:
        return ""
    return base64.b64decode(value.encode("ascii")).decode(encoding)


# ============================================================
# Funções de Serialização Booleana
# ============================================================


def serialize_bool(value: bool, format_: str = SankhyaConstants.BOOL_FORMAT_TRUE_FALSE) -> str:
    """
    Serializa um booleano para string no formato especificado.
    
    Args:
        value: Valor booleano
        format_: Formato de serialização (ex: "true|false", "S|N", "1|0")
        
    Returns:
        String representando o valor booleano
    """
    parts = format_.split("|")
    if len(parts) != 2:
        parts = ["true", "false"]
    
    return parts[0] if value else parts[1]


def deserialize_bool(
    value: str, 
    format_: str = SankhyaConstants.BOOL_FORMAT_TRUE_FALSE,
    default: bool = False
) -> bool:
    """
    Deserializa uma string para booleano.
    
    Args:
        value: String a ser convertida
        format_: Formato esperado (usado como hint)
        default: Valor padrão se não puder ser determinado
        
    Returns:
        Valor booleano
    """
    if not value:
        return default
    
    normalized = value.strip().lower()
    
    # Verifica valores conhecidos como True
    if normalized in ("true", "1", "s", "sim", "yes", "y"):
        return True
    
    # Verifica valores conhecidos como False
    if normalized in ("false", "0", "n", "nao", "não", "no"):
        return False
    
    return default


# ============================================================
# Funções de Criação/Parsing de Elementos XML
# ============================================================


def create_xml_element(
    tag: str,
    value: Optional[Any] = None,
    attributes: Optional[Dict[str, str]] = None,
    parent: Optional[Element] = None
) -> Element:
    """
    Cria um elemento XML com tag, valor e atributos.
    
    Args:
        tag: Nome da tag XML
        value: Valor do texto do elemento (opcional)
        attributes: Dicionário de atributos (opcional)
        parent: Elemento pai para anexar (opcional)
        
    Returns:
        Elemento XML criado
    """
    if parent is not None:
        element = etree.SubElement(parent, tag)
    else:
        element = etree.Element(tag)
    
    if attributes:
        for key, attr_value in attributes.items():
            if attr_value is not None:
                element.set(key, str(attr_value))
    
    if value is not None:
        element.text = str(value)
    
    return element


def parse_xml_element(element: Element) -> Dict[str, Any]:
    """
    Converte um elemento XML para dicionário.
    
    Args:
        element: Elemento XML a ser convertido
        
    Returns:
        Dicionário com tag, atributos, texto e filhos
    """
    result: Dict[str, Any] = {
        "tag": element.tag,
        "attributes": dict(element.attrib),
        "text": element.text.strip() if element.text else None,
    }
    
    children = []
    for child in element:
        children.append(parse_xml_element(child))
    
    if children:
        result["children"] = children
    
    return result


def get_element_text(element: Optional[Element], default: str = "") -> str:
    """
    Obtém o texto de um elemento XML de forma segura.
    
    Args:
        element: Elemento XML (pode ser None)
        default: Valor padrão se não houver texto
        
    Returns:
        Texto do elemento ou valor padrão
    """
    if element is None:
        return default
    return (element.text or "").strip() or default


def get_element_attr(
    element: Element,
    attr_name: str,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Obtém um atributo de um elemento XML de forma segura.
    
    Args:
        element: Elemento XML
        attr_name: Nome do atributo
        default: Valor padrão se atributo não existir
        
    Returns:
        Valor do atributo ou valor padrão
    """
    return element.get(attr_name, default)


def find_child_element(
    parent: Element,
    tag: str,
    namespace: Optional[str] = None
) -> Optional[Element]:
    """
    Encontra um elemento filho por tag.
    
    Args:
        parent: Elemento pai
        tag: Tag do elemento filho
        namespace: Namespace opcional
        
    Returns:
        Elemento filho ou None
    """
    if namespace:
        return parent.find(f"{{{namespace}}}{tag}")
    return parent.find(tag)


def find_all_child_elements(
    parent: Element,
    tag: str,
    namespace: Optional[str] = None
) -> list[Element]:
    """
    Encontra todos os elementos filhos por tag.
    
    Args:
        parent: Elemento pai
        tag: Tag dos elementos filhos
        namespace: Namespace opcional
        
    Returns:
        Lista de elementos filhos
    """
    if namespace:
        return list(parent.findall(f"{{{namespace}}}{tag}"))
    return list(parent.findall(tag))


# ============================================================
# Protocolo XmlSerializable
# ============================================================


@runtime_checkable
class XmlSerializable(Protocol):
    """
    Protocolo para classes que podem ser serializadas/deserializadas de XML.
    
    Similar à interface IXmlSerializable do .NET.
    """
    
    def to_xml(self) -> Element:
        """
        Serializa o objeto para um elemento XML.
        
        Returns:
            Elemento XML representando o objeto
        """
        ...
    
    @classmethod
    def from_xml(cls: Type[T], element: Element) -> T:
        """
        Deserializa um elemento XML para um objeto.
        
        Args:
            element: Elemento XML a ser deserializado
            
        Returns:
            Instância da classe
        """
        ...


class XmlSerializableBase(ABC):
    """
    Classe base abstrata para objetos serializáveis em XML.
    
    Fornece implementação padrão para alguns métodos auxiliares.
    """
    
    @abstractmethod
    def to_xml(self) -> Element:
        """Serializa o objeto para um elemento XML."""
        ...
    
    @classmethod
    @abstractmethod
    def from_xml(cls: Type[T], element: Element) -> T:
        """Deserializa um elemento XML para um objeto."""
        ...
    
    def to_xml_string(self, pretty_print: bool = False, encoding: str = "unicode") -> str:
        """
        Serializa o objeto para uma string XML.
        
        Args:
            pretty_print: Se True, formata o XML com indentação
            encoding: Encoding da string de saída
            
        Returns:
            String XML
        """
        element = self.to_xml()
        return etree.tostring(element, pretty_print=pretty_print, encoding=encoding)
    
    @classmethod
    def from_xml_string(cls: Type[T], xml_string: str) -> T:
        """
        Deserializa uma string XML para um objeto.
        
        Args:
            xml_string: String XML a ser deserializada
            
        Returns:
            Instância da classe
        """
        element = etree.fromstring(xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string)
        return cls.from_xml(element)


# ============================================================
# Funções de Serialização de Tipos Comuns
# ============================================================


def serialize_optional_int(value: Optional[int]) -> Optional[str]:
    """Serializa um inteiro opcional para string."""
    return str(value) if value is not None else None


def deserialize_optional_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    """Deserializa uma string opcional para inteiro."""
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def serialize_optional_float(value: Optional[float]) -> Optional[str]:
    """Serializa um float opcional para string."""
    return str(value) if value is not None else None


def deserialize_optional_float(value: Optional[str], default: Optional[float] = None) -> Optional[float]:
    """Deserializa uma string opcional para float."""
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default
