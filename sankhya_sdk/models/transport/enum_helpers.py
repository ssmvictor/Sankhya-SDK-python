"""
Helpers para conversão de enums MetadataEnum.

Funções auxiliares para serialização/deserialização de enums
na camada de transporte.
"""

from typing import Optional, Type, TypeVar

from ...enums._metadata import MetadataEnum

T = TypeVar("T", bound=MetadataEnum)


def serialize_enum(value: Optional[MetadataEnum]) -> Optional[str]:
    """
    Serializa um enum MetadataEnum para seu internal_value.
    
    Args:
        value: Valor enum a ser serializado
        
    Returns:
        internal_value do enum ou None
    """
    if value is None:
        return None
    return value.internal_value


def deserialize_enum(
    value: Optional[str], 
    enum_class: Type[T]
) -> Optional[T]:
    """
    Deserializa um internal_value para o membro correspondente do enum.
    
    Args:
        value: String internal_value
        enum_class: Classe do enum MetadataEnum
        
    Returns:
        Membro do enum correspondente ou None
    """
    if value is None or not value:
        return None
    
    return get_enum_by_internal_value(enum_class, value)


def get_enum_by_internal_value(
    enum_class: Type[T], 
    internal_value: str
) -> Optional[T]:
    """
    Busca um membro do enum pelo internal_value.
    
    Args:
        enum_class: Classe do enum MetadataEnum
        internal_value: Valor interno a buscar
        
    Returns:
        Membro do enum ou None se não encontrado
    """
    for member in enum_class:
        if member.internal_value == internal_value:
            return member
    
    # Fallback: tenta pelo value direto
    try:
        for member in enum_class:
            if member.value == internal_value:
                return member
    except (ValueError, KeyError):
        pass
    
    return None
