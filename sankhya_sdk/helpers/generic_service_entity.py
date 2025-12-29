# -*- coding: utf-8 -*-
"""
Entidade de serviço genérica com serialização XML.

Fornece uma classe base abstrata para entidades que precisam
de serialização XML customizada para interação com APIs Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/GenericServiceEntity.cs
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Optional, Type, TypeVar

from lxml import etree
from lxml.etree import Element

from sankhya_sdk.models.base import EntityBase

# TypeVar para tipo próprio
T = TypeVar("T", bound="GenericServiceEntity")


class GenericServiceEntity(EntityBase, ABC):
    """
    Entidade de serviço genérica com serialização XML.
    
    Fornece implementação de serialização/deserialização XML
    baseada em metadados dos campos da entidade.
    
    Esta classe deve ser herdada por entidades que precisam
    interagir diretamente com a API Sankhya via XML.
    
    Example:
        >>> class MyEntity(GenericServiceEntity):
        ...     code: int = entity_key()
        ...     name: str = entity_element("NOME")
        >>> 
        >>> entity = MyEntity(code=1, name="Test")
        >>> xml = entity.to_xml_string()
    """

    def to_xml(self) -> Element:
        """
        Serializa a entidade para um elemento XML.
        
        Utiliza os metadados dos campos para determinar
        nomes de elementos e quais campos serializar.
        
        Returns:
            Elemento XML representando a entidade
        """
        from sankhya_sdk.attributes.reflection import (
            get_entity_name,
            get_field_metadata,
        )
        
        entity_type = type(self)
        entity_name = get_entity_name(entity_type)
        custom_data = self._get_entity_custom_data()
        
        root = etree.Element(entity_name)
        
        for field_name, field_info in entity_type.model_fields.items():
            self._write_xml_element(
                root, 
                field_name, 
                field_info, 
                entity_type, 
                entity_name,
                custom_data,
            )
        
        return root

    def _write_xml_element(
        self,
        parent: Element,
        field_name: str,
        field_info: Any,
        entity_type: Type,
        entity_name: str,
        custom_data: Optional[Any],
    ) -> None:
        """
        Escreve um campo como elemento XML.
        
        Args:
            parent: Elemento pai
            field_name: Nome do campo
            field_info: Informações do campo Pydantic
            entity_type: Tipo da entidade
            entity_name: Nome da entidade
            custom_data: Dados customizados da entidade
        """
        from sankhya_sdk.attributes.reflection import get_field_metadata
        
        metadata = get_field_metadata(field_info)
        
        # Verifica se deve ignorar
        if metadata.is_ignored:
            return
        
        # Obtém nome do elemento
        property_name = metadata.element_name or field_name
        
        # Verifica se deve serializar
        if not self._validate_should_serialize(field_name, entity_type, entity_name):
            return
        
        # Serializa o valor
        self._serialize_value(parent, property_name, field_name, metadata, custom_data)

    def _validate_should_serialize(
        self,
        field_name: str,
        entity_type: Type,
        entity_name: str,
    ) -> bool:
        """
        Valida se o campo deve ser serializado.
        
        Args:
            field_name: Nome do campo
            entity_type: Tipo da entidade
            entity_name: Nome da entidade
            
        Returns:
            True se deve serializar
        """
        # Remove sufixo Internal se existir
        base_name = field_name
        if field_name.endswith("Internal"):
            base_name = field_name[:-8]
        
        # Usa método should_serialize_field se disponível
        if hasattr(self, "should_serialize_field"):
            return self.should_serialize_field(field_name)
        
        return True

    def _serialize_value(
        self,
        parent: Element,
        element_name: str,
        field_name: str,
        metadata: Any,
        custom_data: Optional[Any],
    ) -> None:
        """
        Serializa um valor para o elemento XML.
        
        Args:
            parent: Elemento pai
            element_name: Nome do elemento XML
            field_name: Nome do campo Python
            metadata: Metadados do campo
            custom_data: Dados customizados
        """
        value = getattr(self, field_name, None)
        
        elem = etree.SubElement(parent, element_name)
        
        if value is None:
            return
        
        # Aplica max_length se configurado
        str_value = str(value)
        max_length = None
        
        if custom_data and hasattr(custom_data, "max_length"):
            max_length = custom_data.max_length
        
        if metadata.custom_data and hasattr(metadata.custom_data, "max_length"):
            max_length = metadata.custom_data.max_length
        
        if max_length and max_length > 0 and len(str_value) > max_length:
            str_value = str_value[:max_length]
        
        elem.text = str_value

    def _get_entity_custom_data(self) -> Optional[Any]:
        """
        Obtém dados customizados da entidade.
        
        Returns:
            Dados customizados ou None
        """
        entity_type = type(self)
        if hasattr(entity_type, "__entity_custom_data__"):
            return entity_type.__entity_custom_data__
        return None

    def to_xml_string(self, pretty_print: bool = False) -> str:
        """
        Serializa a entidade para uma string XML.
        
        Args:
            pretty_print: Se True, formata com indentação
            
        Returns:
            String XML
        """
        element = self.to_xml()
        return etree.tostring(element, pretty_print=pretty_print, encoding="unicode")

    def to_xml_bytes(self, pretty_print: bool = False) -> bytes:
        """
        Serializa a entidade para bytes XML.
        
        Args:
            pretty_print: Se True, formata com indentação
            
        Returns:
            Bytes XML com encoding UTF-8
        """
        element = self.to_xml()
        return etree.tostring(
            element,
            pretty_print=pretty_print,
            encoding="UTF-8",
            xml_declaration=True,
        )

    @classmethod
    def from_xml(cls: Type[T], element: Element) -> T:
        """
        Deserializa um elemento XML para uma instância da entidade.
        
        Args:
            element: Elemento XML a deserializar
            
        Returns:
            Instância da entidade
        """
        from sankhya_sdk.attributes.reflection import get_field_metadata
        
        data = {}
        
        for field_name, field_info in cls.model_fields.items():
            metadata = get_field_metadata(field_info)
            element_name = metadata.element_name or field_name
            
            # Busca o elemento filho
            child = element.find(element_name)
            if child is None:
                # Tenta busca case-insensitive
                for elem in element:
                    if elem.tag.lower() == element_name.lower():
                        child = elem
                        break
            
            if child is None:
                continue
            
            # Obtém o texto
            text = child.text
            if text is None:
                continue
            
            # Converte para o tipo apropriado
            value = cls._convert_value(text.strip(), field_info)
            if value is not None:
                data[field_name] = value
        
        return cls(**data)

    @classmethod
    def _convert_value(cls, text: str, field_info: Any) -> Any:
        """
        Converte texto para o tipo do campo.
        
        Args:
            text: Texto a converter
            field_info: Informações do campo
            
        Returns:
            Valor convertido
        """
        from typing import get_origin, get_args
        
        annotation = field_info.annotation
        
        # Remove Optional
        origin = get_origin(annotation)
        if origin is not None:
            args = get_args(annotation)
            if type(None) in args:
                # É Optional, pega o primeiro tipo não-None
                for arg in args:
                    if arg is not type(None):
                        annotation = arg
                        break
        
        try:
            if annotation is str:
                return text
            elif annotation is int:
                return int(text)
            elif annotation is float:
                return float(text)
            elif annotation is bool:
                return text.lower() in ("true", "1", "s", "sim", "yes")
            elif hasattr(annotation, "__origin__"):
                # Tipos genéricos complexos
                return text
            else:
                return text
        except (ValueError, TypeError):
            return text

    @classmethod
    def from_xml_string(cls: Type[T], xml_string: str) -> T:
        """
        Deserializa uma string XML para uma instância da entidade.
        
        Args:
            xml_string: String XML a deserializar
            
        Returns:
            Instância da entidade
        """
        element = etree.fromstring(
            xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string
        )
        return cls.from_xml(element)
