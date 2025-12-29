"""
Classe base para entidades de transporte Sankhya.

Estende EntityBase e adiciona funcionalidade de serialização XML genérica
usando os metadados dos decoradores de atributos.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints, get_origin, get_args

from lxml import etree
from lxml.etree import Element

from ..base import EntityBase
from ..service.xml_serialization import (
    XmlSerializableBase,
    create_xml_element,
    get_element_text,
    deserialize_optional_int,
    serialize_bool,
    deserialize_bool,
)
from ...attributes.reflection import (
    get_entity_name,
    get_field_metadata,
    get_element_name,
)
from ...attributes.metadata import EntityFieldMetadata
from ...enums._metadata import MetadataEnum

T = TypeVar("T", bound="TransportEntityBase")


# Constantes para formato de data Sankhya
SANKHYA_DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
SANKHYA_DATE_FORMAT_SHORT = "%d/%m/%Y"


def serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    """
    Serializa um datetime para string no formato Sankhya.
    
    Args:
        value: Valor datetime a ser serializado
        
    Returns:
        String no formato dd/mm/yyyy HH:MM:SS ou None
    """
    if value is None:
        return None
    return value.strftime(SANKHYA_DATE_FORMAT)


def deserialize_datetime(value: Optional[str]) -> Optional[datetime]:
    """
    Deserializa uma string de data Sankhya para datetime.
    
    Args:
        value: String de data no formato Sankhya
        
    Returns:
        Objeto datetime ou None
    """
    if not value or not value.strip():
        return None
    
    value = value.strip()
    
    # Tenta formato longo primeiro
    try:
        return datetime.strptime(value, SANKHYA_DATE_FORMAT)
    except ValueError:
        pass
    
    # Tenta formato curto
    try:
        return datetime.strptime(value, SANKHYA_DATE_FORMAT_SHORT)
    except ValueError:
        pass
    
    # Tenta formatos ISO
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class TransportEntityBase(EntityBase, XmlSerializableBase):
    """
    Classe base abstrata para entidades de transporte.
    
    Combina EntityBase (rastreamento de campos modificados) com XmlSerializableBase
    (serialização XML) para entidades que representam objetos de domínio.
    
    Features:
        - Rastreamento automático de campos modificados via _fields_set
        - Serialização/deserialização XML genérica baseada em metadados
        - Suporte a relacionamentos (entity_reference)
        - Validação de campos customizada
    """
    
    def to_xml(self) -> Element:
        """
        Serializa a entidade para um elemento XML.
        
        Usa os metadados dos decoradores (entity_element, entity_reference, etc.)
        para determinar nomes de elementos e comportamento de serialização.
        
        Apenas campos em _fields_set são serializados (equivalente a ShouldSerialize*).
        
        Returns:
            Elemento XML representando a entidade
        """
        entity_name = get_entity_name(type(self))
        root = etree.Element(entity_name)
        
        for field_name, field_info in self.model_fields.items():
            # Verifica se deve serializar o campo
            if not self.should_serialize_field(field_name):
                continue
            
            metadata = get_field_metadata(field_info)
            
            # Ignora campos marcados com entity_ignore
            if metadata.is_ignored:
                continue
            
            value = getattr(self, field_name)
            
            # Trata entidades relacionadas (entity_reference)
            if metadata.reference is not None:
                if value is not None and isinstance(value, TransportEntityBase):
                    # Use custom wrapper tag if specified, otherwise use entity name
                    wrapper_tag = metadata.reference.custom_relation_name or get_entity_name(type(value))
                    wrapper = etree.Element(wrapper_tag)
                    wrapper.append(value.to_xml())
                    root.append(wrapper)
                continue
            
            # Trata campos de lista (coleções)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, TransportEntityBase):
                        root.append(item.to_xml())
                continue
            
            # Obtém nome do elemento XML
            element_name = metadata.element.element_name if metadata.element else field_name.upper()
            
            # Serializa o valor
            serialized_value = self._serialize_value(value, field_name)
            
            if serialized_value is not None:
                create_xml_element(element_name, serialized_value, parent=root)
        
        return root
    
    def _serialize_value(self, value: Any, field_name: str) -> Optional[str]:
        """
        Serializa um valor para string XML.
        
        Args:
            value: Valor a ser serializado
            field_name: Nome do campo (para contexto)
            
        Returns:
            String serializada ou None
        """
        if value is None:
            return None
        
        if isinstance(value, bool):
            return serialize_bool(value, "S|N")
        
        if isinstance(value, MetadataEnum):
            return value.internal_value
        
        if isinstance(value, datetime):
            return serialize_datetime(value)
        
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}{minutes:02d}{seconds:02d}"
        
        if isinstance(value, Decimal):
            return str(value)
        
        if isinstance(value, (int, float)):
            return str(value)
        
        return str(value)
    
    @classmethod
    def from_xml(cls: Type[T], element: Element) -> T:
        """
        Deserializa um elemento XML para uma instância da entidade.
        
        Args:
            element: Elemento XML a ser deserializado
            
        Returns:
            Instância da entidade preenchida com dados do XML
        """
        import sys
        import typing
        
        kwargs: Dict[str, Any] = {}
        
        # Build namespace for resolving forward references
        # Include typing module for Optional, etc.
        namespace: Dict[str, Any] = {}
        namespace.update(vars(typing))  # Add Optional, Union, etc.
        
        # Add all transport entity classes
        transport_module = sys.modules.get('sankhya_sdk.models.transport')
        if transport_module:
            namespace.update({
                name: getattr(transport_module, name)
                for name in dir(transport_module)
                if not name.startswith('_')
            })
        
        try:
            type_hints = get_type_hints(cls, globalns=namespace, localns=namespace)
        except NameError:
            # Fallback if forward references can't be resolved
            type_hints = {}
        
        for field_name, field_info in cls.model_fields.items():
            metadata = get_field_metadata(field_info)
            
            # Ignora campos marcados com entity_ignore
            if metadata.is_ignored:
                continue
            
            # Obtém o tipo do campo
            field_type = type_hints.get(field_name, str)
            origin = get_origin(field_type)
            args = get_args(field_type)
            
            # Para Optional[X], obtém o tipo X
            if origin is type(None) or (args and type(None) in args):
                # É Optional
                inner_type = args[0] if args and args[0] is not type(None) else (
                    args[1] if len(args) > 1 and args[1] is not type(None) else str
                )
            else:
                inner_type = field_type if not origin else origin
            
            # Trata entidades relacionadas (entity_reference)
            if metadata.reference is not None:
                # Procura elemento filho pelo nome customizado ou nome da entidade
                if hasattr(inner_type, 'from_xml'):
                    search_tag = metadata.reference.custom_relation_name or get_entity_name(inner_type)
                    ref_element = element.find(search_tag)
                    if ref_element is not None:
                        # Check if wrapper contains nested entity element
                        entity_name = get_entity_name(inner_type)
                        nested = ref_element.find(entity_name)
                        if nested is not None:
                            kwargs[field_name] = inner_type.from_xml(nested)
                        else:
                            kwargs[field_name] = inner_type.from_xml(ref_element)
                continue
            
            # Trata campos de lista (coleções)
            origin = get_origin(field_type)
            if origin is list:
                list_args = get_args(field_type)
                if list_args:
                    list_inner_type = list_args[0]
                    if hasattr(list_inner_type, 'from_xml'):
                        child_tag = get_entity_name(list_inner_type)
                        items = []
                        for child in element.findall(child_tag):
                            items.append(list_inner_type.from_xml(child))
                        if items:
                            kwargs[field_name] = items
                continue
            
            # Obtém nome do elemento XML
            element_name = metadata.element.element_name if metadata.element else field_name.upper()
            
            # Busca o elemento filho
            child_element = element.find(element_name)
            
            if child_element is not None:
                text_value = get_element_text(child_element)
                
                if text_value:
                    # Deserializa baseado no tipo
                    deserialized = cls._deserialize_value(text_value, inner_type)
                    if deserialized is not None:
                        kwargs[field_name] = deserialized
        
        return cls(**kwargs)
    
    @classmethod
    def _deserialize_value(cls, value: str, target_type: type) -> Any:
        """
        Deserializa uma string para o tipo alvo.
        
        Args:
            value: String a ser deserializada
            target_type: Tipo alvo da conversão
            
        Returns:
            Valor deserializado
        """
        if not value:
            return None
        
        # Boolean
        if target_type is bool:
            return deserialize_bool(value, "S|N")
        
        # MetadataEnum - check if target_type inherits from MetadataEnum
        try:
            if isinstance(target_type, type) and issubclass(target_type, MetadataEnum):
                for member in target_type:
                    if member.internal_value == value:
                        return member
                # Fallback to value
                for member in target_type:
                    if member.value == value:
                        return member
                return None
        except TypeError:
            pass
        
        # Integer
        if target_type is int:
            return deserialize_optional_int(value)
        
        # Float
        if target_type is float:
            try:
                return float(value)
            except ValueError:
                return None
        
        # Decimal
        if target_type is Decimal:
            try:
                return Decimal(value)
            except (ValueError, InvalidOperation):
                return None
        
        # Datetime
        if target_type is datetime:
            return deserialize_datetime(value)
        
        # timedelta (HHMMSS format)
        if target_type is timedelta:
            if len(value) == 6:
                try:
                    h = int(value[0:2])
                    m = int(value[2:4])
                    s = int(value[4:6])
                    return timedelta(hours=h, minutes=m, seconds=s)
                except ValueError:
                    return None
            return None
        
        # String por padrão
        return value
    
    def __eq__(self, other: object) -> bool:
        """
        Compara duas entidades.
        
        Subclasses devem sobrescrever para comparação customizada
        (ex: case-insensitive para strings).
        """
        if not isinstance(other, type(self)):
            return False
        
        return self._compare_fields(other)
    
    def _compare_fields(self, other: "TransportEntityBase") -> bool:
        """
        Compara campos entre duas entidades.
        
        Compara strings de forma case-insensitive.
        """
        for field_name in self.model_fields:
            self_value = getattr(self, field_name)
            other_value = getattr(other, field_name)
            
            # Comparação case-insensitive para strings
            if isinstance(self_value, str) and isinstance(other_value, str):
                if self_value.lower() != other_value.lower():
                    return False
            elif self_value != other_value:
                return False
        
        return True
    
    def __hash__(self) -> int:
        """
        Calcula hash da entidade.
        
        Usa campos imutáveis (chave primária) para o cálculo.
        """
        hash_values = []
        
        for field_name, field_info in self.model_fields.items():
            metadata = get_field_metadata(field_info)
            
            if metadata.is_key:
                value = getattr(self, field_name)
                if isinstance(value, str):
                    hash_values.append(value.lower())
                else:
                    hash_values.append(value)
        
        # Se não houver chaves, usa o id do objeto
        if not hash_values:
            return id(self)
        
        return hash(tuple(hash_values))
