from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Type, TypeVar, Union

T = TypeVar("T", bound="MetadataEnum")


@dataclass(frozen=True)
class EnumMetadata:
    """Metadados para enums do Sankhya."""

    internal_value: Optional[str] = None
    human_readable: Optional[str] = None
    service_module: Optional[Any] = None
    service_category: Optional[Any] = None
    service_type: Optional[Any] = None


class MetadataEnum(Enum):
    """Classe base para enums com metadados."""

    _metadata: EnumMetadata

    def __new__(cls, value: str, metadata: Optional[EnumMetadata] = None) -> "MetadataEnum":
        obj = object.__new__(cls)
        obj._value_ = value
        obj._metadata = metadata or EnumMetadata()
        return obj

    @property
    def metadata(self) -> EnumMetadata:
        """Retorna os metadados do membro do enum."""
        return self._metadata

    @property
    def internal_value(self) -> str:
        """Retorna o valor interno usado na API."""
        return self._metadata.internal_value if self._metadata.internal_value is not None else str(self.value)

    @property
    def human_readable(self) -> str:
        """Retorna a descrição legível para humanos."""
        return self._metadata.human_readable or self.name

    @classmethod
    def from_internal_value(cls: Type[T], value: str) -> T:
        """
        Busca um membro do enum pelo seu valor interno.
        
        Args:
            value: Valor interno usado na API
            
        Returns:
            Membro do enum correspondente
            
        Raises:
            ValueError: Se nenhum membro for encontrado
        """
        for member in cls:
            if member.internal_value == value:
                return member
        raise ValueError(f"No {cls.__name__} member with internal_value '{value}'")

    def __str__(self) -> str:
        return self.internal_value

