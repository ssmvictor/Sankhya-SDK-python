# -*- coding: utf-8 -*-
"""
Serialização dinâmica de entidades.

Fornece conversão dinâmica de dicionários para entidades tipadas,
com suporte a referências aninhadas e conversão de tipos.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/EntityDynamicSerialization.cs
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    get_args,
    get_origin,
)

from sankhya_sdk.enums.reference_level import ReferenceLevel

# TypeVar para entidades genéricas
T = TypeVar("T")


class Metadata:
    """Representa metadados de campos."""
    
    def __init__(self, fields: Optional[List[Dict[str, str]]] = None):
        self.fields = fields or []


class EntityDynamicSerialization:
    """
    Serialização dinâmica de entidades.
    
    Converte dicionários dinâmicos para entidades tipadas,
    suportando conversão de tipos, referências aninhadas
    e manipulação de chaves.
    
    Attributes:
        dictionary: Dicionário interno com os dados
        key_filter: Filtro de chaves (uppercase, lowercase, etc.)
    
    Example:
        >>> data = {"CODPARC": "123", "NOMEPARC": "Test"}
        >>> serializer = EntityDynamicSerialization(data)
        >>> partner = serializer.convert_to_type(Partner)
        >>> partner.code
        123
    """

    def __init__(
        self,
        data: Optional[Dict[str, Any]] = None,
        key_filter: str = "none",
    ):
        """
        Inicializa o serializador.
        
        Args:
            data: Dicionário com os dados
            key_filter: Filtro de chaves ('uppercase', 'lowercase', 'none')
        """
        self._dictionary: Dict[str, Any] = data or {}
        self._key_filter = key_filter

    @property
    def dictionary(self) -> Dict[str, Any]:
        """Retorna o dicionário interno."""
        return self._dictionary

    def get_member(self, name: str) -> Optional[Any]:
        """
        Obtém um membro do dicionário.
        
        Args:
            name: Nome do membro
            
        Returns:
            Valor ou None se não existir
        """
        return self._dictionary.get(name) or self._dictionary.get(name.upper())

    def set_member(self, name: str, value: Any) -> None:
        """
        Define um membro no dicionário.
        
        Args:
            name: Nome do membro
            value: Valor a definir
        """
        key = name
        if self._key_filter == "uppercase":
            key = name.upper()
        elif self._key_filter == "lowercase":
            key = name.lower()
        
        self._dictionary[key] = value

    def convert_to_type(self, entity_type: Type[T]) -> T:
        """
        Converte o dicionário para uma entidade tipada.
        
        Args:
            entity_type: Tipo da entidade de destino
            
        Returns:
            Instância da entidade com valores preenchidos
        """
        instance = entity_type()
        instance, _ = self._parse_entity(
            instance, 
            entity_type, 
            ReferenceLevel.FIFTH,
        )
        return instance

    def _parse_entity(
        self,
        instance: T,
        entity_type: Type[T],
        max_inner_level: ReferenceLevel,
        prefix: Optional[str] = None,
        current_level: ReferenceLevel = ReferenceLevel.NONE,
    ) -> tuple[Optional[T], bool]:
        """
        Faz o parsing recursivo da entidade.
        
        Args:
            instance: Instância da entidade
            entity_type: Tipo da entidade
            max_inner_level: Nível máximo de recursão
            prefix: Prefixo para os nomes de campos
            current_level: Nível atual de recursão
            
        Returns:
            Tuple of (instance preenchida ou None se nível excedido, 
                      flag indicando se ao menos um campo foi preenchido)
        """
        current_int = self._level_to_int(current_level)
        max_int = self._level_to_int(max_inner_level)
        
        if current_int >= max_int:
            return None, False
        
        has_fields_set = False
        for field_name, field_info in entity_type.model_fields.items():
            field_set = self._parse_property(
                instance,
                max_inner_level,
                prefix,
                current_level,
                field_name,
                field_info,
            )
            if field_set:
                has_fields_set = True
        
        return instance, has_fields_set

    def _parse_property(
        self,
        instance: T,
        max_inner_level: ReferenceLevel,
        prefix: Optional[str],
        current_level: ReferenceLevel,
        field_name: str,
        field_info: Any,
    ) -> bool:
        """
        Processa uma propriedade individual.
        
        Args:
            instance: Instância da entidade
            max_inner_level: Nível máximo de recursão
            prefix: Prefixo para os nomes
            current_level: Nível atual
            field_name: Nome do campo Python
            field_info: Informações do campo
            
        Returns:
            True se um valor foi definido, False caso contrário
        """
        from sankhya_sdk.attributes.reflection import (
            get_entity_name,
            get_field_metadata,
        )
        
        metadata = get_field_metadata(field_info)
        
        # Verifica se deve ignorar
        if metadata.is_ignored:
            return False
        
        property_name = metadata.element_name or field_name
        
        # Adiciona prefixo se existir
        if prefix:
            property_name = f"{prefix}_{property_name}"
        
        # Verifica se é referência
        if metadata.is_reference:
            return self._parse_entity_reference(
                instance,
                max_inner_level,
                prefix,
                current_level,
                field_name,
                field_info,
                metadata,
            )
        
        # Busca valor no dicionário
        value = self._get_value_from_dict(property_name)
        if value is None:
            return False
        
        # Converte e define o valor
        converted_value = self._convert_value(value, field_info)
        if converted_value is not None:
            try:
                setattr(instance, field_name, converted_value)
                return True
            except (ValueError, TypeError):
                pass
        
        return False

    def _parse_entity_reference(
        self,
        instance: T,
        max_inner_level: ReferenceLevel,
        prefix: Optional[str],
        current_level: ReferenceLevel,
        field_name: str,
        field_info: Any,
        metadata: Any,
    ) -> bool:
        """
        Processa uma referência de entidade.
        
        Args:
            instance: Instância da entidade
            max_inner_level: Nível máximo
            prefix: Prefixo atual
            current_level: Nível atual
            field_name: Nome do campo
            field_info: Informações do campo
            metadata: Metadados do campo
            
        Returns:
            True se a referência foi definida, False caso contrário
        """
        from sankhya_sdk.attributes.reflection import get_entity_name
        
        # Obtém tipo interno e verifica se é lista
        inner_type, is_list = self._get_inner_type_with_list_check(field_info)
        if inner_type is None:
            return False
        
        # Campos de referência do tipo lista não são suportados na
        # conversão dinâmica de dados flat. Seria necessário aceitar
        # múltiplos prefixos (e.g., Ref_0_, Ref_1_) ou uma lista de dicionários.
        if is_list:
            return False
        
        # Determina prefixo da referência
        custom_name = metadata.custom_relation_name
        if custom_name:
            ref_prefix = custom_name
        else:
            ref_prefix = get_entity_name(inner_type)
        
        if prefix:
            ref_prefix = f"{prefix}_{ref_prefix}"
        
        # Incrementa nível
        current_int = self._level_to_int(current_level)
        inner_level = self._int_to_level(current_int + 1)
        
        # Parse recursivo
        inner_instance = inner_type()
        ref_value, has_fields = self._parse_entity(
            inner_instance,
            inner_type,
            max_inner_level,
            ref_prefix,
            inner_level,
        )
        
        # Só atribui a referência se houver campos efetivamente preenchidos
        if ref_value is not None and has_fields:
            try:
                setattr(instance, field_name, ref_value)
                return True
            except (ValueError, TypeError):
                pass
        
        return False

    def _get_value_from_dict(self, property_name: str) -> Optional[Any]:
        """
        Obtém valor do dicionário com fallback para uppercase.
        
        Args:
            property_name: Nome da propriedade
            
        Returns:
            Valor ou None
        """
        if property_name in self._dictionary:
            return self._dictionary[property_name]
        
        upper_name = property_name.upper()
        if upper_name in self._dictionary:
            return self._dictionary[upper_name]
        
        return None

    def _convert_value(self, value: Any, field_info: Any) -> Any:
        """
        Converte um valor para o tipo do campo.
        
        Args:
            value: Valor a converter
            field_info: Informações do campo
            
        Returns:
            Valor convertido
        """
        if value is None:
            return None
        
        annotation = field_info.annotation
        
        # Remove Optional/Union
        origin = get_origin(annotation)
        if origin is not None:
            args = get_args(annotation)
            for arg in args:
                if arg is not type(None):
                    annotation = arg
                    break
        
        str_value = str(value)
        
        try:
            if annotation is str:
                return str_value
            
            elif annotation is int:
                return int(float(str_value))
            
            elif annotation is float:
                return float(str_value)
            
            elif annotation is Decimal:
                return Decimal(str_value)
            
            elif annotation is bool:
                return self._convert_to_bool(str_value)
            
            elif annotation is datetime:
                return self._convert_to_datetime(str_value)
            
            else:
                # Tenta conversão direta
                return annotation(str_value) if callable(annotation) else str_value
        
        except (ValueError, TypeError):
            return None

    def _convert_to_bool(self, value: str) -> bool:
        """
        Converte string para boolean.
        
        Args:
            value: String a converter
            
        Returns:
            Valor boolean
        """
        return value.lower() in ("true", "1", "s", "sim", "yes", "y")

    def _convert_to_datetime(self, value: str) -> datetime:
        """
        Converte string para datetime.
        
        Args:
            value: String a converter
            
        Returns:
            Valor datetime
        """
        formats = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Invalid date format: {value}")

    def _get_inner_type(self, field_info: Any) -> Optional[Type]:
        """
        Obtém o tipo interno de uma anotação.
        
        Args:
            field_info: Informações do campo
            
        Returns:
            Tipo interno ou None
        """
        inner_type, _ = self._get_inner_type_with_list_check(field_info)
        return inner_type
    
    def _get_inner_type_with_list_check(self, field_info: Any) -> tuple[Optional[Type], bool]:
        """
        Obtém o tipo interno de uma anotação e verifica se é uma lista.
        
        Args:
            field_info: Informações do campo
            
        Returns:
            Tuple de (tipo interno ou None, True se é lista)
        """
        annotation = field_info.annotation
        origin = get_origin(annotation)
        
        if origin is not None:
            # Verifica se é uma lista diretamente
            if origin is list:
                args = get_args(annotation)
                if args:
                    return args[0], True
                return None, True
            
            # Handle Optional[T] ou Union[T, None]
            args = get_args(annotation)
            for arg in args:
                if arg is not type(None):
                    # Verifica se o tipo interno é uma lista
                    inner_origin = get_origin(arg)
                    if inner_origin is list:
                        inner_args = get_args(arg)
                        if inner_args:
                            return inner_args[0], True
                        return None, True
                    return arg, False
        
        return annotation, False

    def change_keys(self, new_keys: Metadata) -> None:
        """
        Renomeia as chaves do dicionário.
        
        Substitui chaves no formato 'fN' pelos nomes em new_keys.
        
        Args:
            new_keys: Metadados com novos nomes
            
        Raises:
            ValueError: Se o número de chaves não corresponder
        """
        if new_keys is None:
            return
        
        if len(new_keys.fields) != len(self._dictionary):
            raise ValueError(
                f"Key count mismatch: {len(new_keys.fields)} vs {len(self._dictionary)}"
            )
        
        new_dict = {}
        
        for index, field in enumerate(new_keys.fields):
            old_key = f"f{index}"
            if old_key in self._dictionary:
                value = self._dictionary[old_key]
                new_dict[field.get("name", old_key)] = value
        
        self._dictionary = new_dict

    @staticmethod
    def _level_to_int(level: ReferenceLevel) -> int:
        """Converte ReferenceLevel para int."""
        mapping = {
            ReferenceLevel.NONE: 0,
            ReferenceLevel.FIRST: 1,
            ReferenceLevel.SECOND: 2,
            ReferenceLevel.THIRD: 3,
            ReferenceLevel.FOURTH: 4,
            ReferenceLevel.FIFTH: 5,
            ReferenceLevel.SIXTH: 6,
        }
        return mapping.get(level, 0)

    @staticmethod
    def _int_to_level(value: int) -> ReferenceLevel:
        """Converte int para ReferenceLevel."""
        mapping = {
            0: ReferenceLevel.NONE,
            1: ReferenceLevel.FIRST,
            2: ReferenceLevel.SECOND,
            3: ReferenceLevel.THIRD,
            4: ReferenceLevel.FOURTH,
            5: ReferenceLevel.FIFTH,
            6: ReferenceLevel.SIXTH,
        }
        return mapping.get(value, ReferenceLevel.NONE)

    def __contains__(self, key: str) -> bool:
        """Verifica se contém a chave."""
        return key in self._dictionary or key.upper() in self._dictionary

    def __getitem__(self, key: str) -> Any:
        """Obtém item por chave."""
        return self._dictionary.get(key) or self._dictionary.get(key.upper())

    def __setitem__(self, key: str, value: Any) -> None:
        """Define item por chave."""
        self.set_member(key, value)

    def __repr__(self) -> str:
        """Representação string."""
        return f"EntityDynamicSerialization({self._dictionary})"
