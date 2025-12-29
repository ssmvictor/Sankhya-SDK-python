"""
Classe ServiceResponse para serviços Sankhya.

Encapsula uma resposta completa da API Sankhya com parsing XML customizado.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/ServiceResponse.cs
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from lxml import etree
from lxml.etree import Element
from pydantic import ConfigDict, Field as PydanticField

from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_response_status import ServiceResponseStatus
from .response_body import ResponseBody
from .metadata_types import StatusMessage
from .constants import SankhyaConstants
from .xml_serialization import (
    get_element_attr,
    get_element_text,
    deserialize_bool,
    deserialize_optional_int,
)


logger = logging.getLogger(__name__)


class ServiceResponse(EntityBase):
    """
    Resposta de serviço Sankhya.
    
    Encapsula todos os dados retornados pela API Sankhya,
    incluindo status, mensagens de erro e corpo da resposta.
    
    Attributes:
        service: Nome do serviço chamado
        pending_printing: Indica se há impressão pendente
        transaction_id: ID da transação
        status: Status da resposta (OK, ERROR, etc.)
        error_code: Código de erro (se houver)
        error_level: Nível do erro
        status_message: Mensagem de status
        response_body: Corpo da resposta com os dados
    
    Example:
        >>> response = ServiceResponse.from_xml_string(xml_string)
        >>> if response.status == ServiceResponseStatus.OK:
        ...     entities = response.entities
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    service: Optional[ServiceName] = PydanticField(
        default=None,
        description="Nome do serviço chamado"
    )
    pending_printing: bool = PydanticField(
        default=False,
        description="Indica se há impressão pendente"
    )
    transaction_id: Optional[str] = PydanticField(
        default=None,
        description="ID da transação"
    )
    status: ServiceResponseStatus = PydanticField(
        default=ServiceResponseStatus.ERROR,
        description="Status da resposta"
    )
    error_code: Optional[str] = PydanticField(
        default=None,
        description="Código de erro"
    )
    error_level: Optional[str] = PydanticField(
        default=None,
        description="Nível do erro"
    )
    status_message: Optional[StatusMessage] = PydanticField(
        default=None,
        description="Mensagem de status"
    )
    response_body: Optional[ResponseBody] = PydanticField(
        default=None,
        description="Corpo da resposta"
    )

    @property
    def is_success(self) -> bool:
        """Verifica se a resposta indica sucesso."""
        return self.status == ServiceResponseStatus.OK

    @property
    def is_error(self) -> bool:
        """Verifica se a resposta indica erro."""
        return self.status == ServiceResponseStatus.ERROR

    @property
    def status_message_text(self) -> str:
        """Retorna o texto da mensagem de status decodificado."""
        if self.status_message:
            return self.status_message.decoded_value
        return ""

    @property
    def entities(self) -> List[Any]:
        """
        Retorna as entidades do corpo da resposta.
        
        Unifica entidades em português e inglês.
        
        Returns:
            Lista de entidades dinâmicas
        """
        if not self.response_body:
            return []
        
        entities = []
        
        if self.response_body.crud_service_entities:
            entities.extend(self.response_body.crud_service_entities.entities)
        
        if self.response_body.crud_service_provider_entities:
            entities.extend(self.response_body.crud_service_provider_entities.entities)
        
        return entities

    @property
    def first_entity(self) -> Optional[Any]:
        """Retorna a primeira entidade ou None."""
        entities = self.entities
        return entities[0] if entities else None

    def to_xml(self) -> Element:
        """
        Serializa a resposta para um elemento XML.
        
        Returns:
            Elemento XML representando a resposta
        """
        elem = etree.Element(SankhyaConstants.SERVICE_RESPONSE)
        
        # Atributos
        if self.service:
            elem.set(SankhyaConstants.SERVICE_NAME, self.service.internal_value)
        elem.set(SankhyaConstants.STATUS, str(self.status.value))
        elem.set(SankhyaConstants.PENDING_PRINTING, str(self.pending_printing).lower())
        
        if self.transaction_id:
            elem.set(SankhyaConstants.TRANSACTION_ID, self.transaction_id)
        if self.error_code:
            elem.set(SankhyaConstants.ERROR_CODE, self.error_code)
        if self.error_level:
            elem.set(SankhyaConstants.ERROR_LEVEL, self.error_level)
        
        # Mensagem de status
        if self.status_message:
            elem.append(self.status_message.to_xml())
        
        # Corpo da resposta
        if self.response_body:
            elem.append(self.response_body.to_xml())
        
        return elem

    def to_xml_string(self, pretty_print: bool = False) -> str:
        """
        Serializa a resposta para uma string XML.
        
        Args:
            pretty_print: Se True, formata o XML com indentação
            
        Returns:
            String XML representando a resposta
        """
        element = self.to_xml()
        return etree.tostring(element, pretty_print=pretty_print, encoding="unicode")

    @classmethod
    def from_xml(cls, element: Element) -> "ServiceResponse":
        """
        Deserializa um elemento XML para ServiceResponse.
        
        Args:
            element: Elemento XML a ser deserializado
            
        Returns:
            Instância de ServiceResponse
        """
        instance = cls()
        
        # Parse atributos
        instance._parse_attributes(element)
        
        # Parse elementos filhos
        for child in element:
            if child.tag == SankhyaConstants.STATUS_MESSAGE:
                instance.status_message = StatusMessage.from_xml(child)
            elif child.tag == SankhyaConstants.RESPONSE_BODY:
                instance.response_body = cls._parse_response_body(child)
            else:
                # Log elemento não esperado, mas não falha
                logger.debug(f"Elemento não esperado na resposta: {child.tag}")
        
        return instance

    def _parse_attributes(self, element: Element) -> None:
        """
        Faz o parsing dos atributos do elemento raiz.
        
        Args:
            element: Elemento XML
        """
        # Nome do serviço
        service_name_str = get_element_attr(element, SankhyaConstants.SERVICE_NAME)
        if service_name_str:
            try:
                self.service = ServiceName.from_internal_value(service_name_str)
            except ValueError:
                logger.warning(f"ServiceName desconhecido: {service_name_str}")
        
        # Status
        status_str = get_element_attr(element, SankhyaConstants.STATUS)
        if status_str:
            try:
                self.status = ServiceResponseStatus(int(status_str))
            except (ValueError, TypeError):
                logger.warning(f"Status inválido: {status_str}")
        
        # Pending printing
        pending_str = get_element_attr(element, SankhyaConstants.PENDING_PRINTING)
        self.pending_printing = deserialize_bool(pending_str or "")
        
        # Transaction ID
        self.transaction_id = get_element_attr(element, SankhyaConstants.TRANSACTION_ID)
        
        # Error code e level
        self.error_code = get_element_attr(element, SankhyaConstants.ERROR_CODE)
        self.error_level = get_element_attr(element, SankhyaConstants.ERROR_LEVEL)

    @classmethod
    def _parse_response_body(cls, element: Element) -> ResponseBody:
        """
        Faz o parsing do elemento responseBody.
        
        Args:
            element: Elemento XML do responseBody
            
        Returns:
            Instância de ResponseBody
        """
        return ResponseBody.from_xml(element)

    @classmethod
    def from_xml_string(cls, xml_string: str) -> "ServiceResponse":
        """
        Deserializa uma string XML para ServiceResponse.
        
        Args:
            xml_string: String XML a ser deserializada
            
        Returns:
            Instância de ServiceResponse
        """
        element = etree.fromstring(
            xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string
        )
        return cls.from_xml(element)

    @classmethod
    def from_xml_bytes(cls, xml_bytes: bytes) -> "ServiceResponse":
        """
        Deserializa bytes XML para ServiceResponse.
        
        Args:
            xml_bytes: Bytes XML a ser deserializados
            
        Returns:
            Instância de ServiceResponse
        """
        element = etree.fromstring(xml_bytes)
        return cls.from_xml(element)

    def get_entity_field(self, field_name: str, default: Any = None) -> Any:
        """
        Obtém um campo da primeira entidade.
        
        Args:
            field_name: Nome do campo
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do campo ou default
        """
        entity = self.first_entity
        if entity and hasattr(entity, "get"):
            return entity.get(field_name, default)
        return default

    def get_all_entity_fields(self, field_name: str) -> List[Any]:
        """
        Obtém um campo de todas as entidades.
        
        Args:
            field_name: Nome do campo
            
        Returns:
            Lista de valores do campo
        """
        values = []
        for entity in self.entities:
            if hasattr(entity, "get"):
                value = entity.get(field_name)
                if value is not None:
                    values.append(value)
        return values

    def raise_for_status(self) -> None:
        """
        Levanta uma exceção se a resposta indica erro.
        
        Raises:
            SankhyaServiceError: Se o status indica erro
        """
        if self.is_error:
            from sankhya_sdk.exceptions import SankhyaServiceError
            raise SankhyaServiceError(
                message=self.status_message_text or "Erro desconhecido",
                error_code=self.error_code,
                error_level=self.error_level,
                service_name=self.service.internal_value if self.service else None,
            )

    def __repr__(self) -> str:
        """Representação string do objeto."""
        return (
            f"ServiceResponse("
            f"service={self.service.name if self.service else None}, "
            f"status={self.status.name}, "
            f"entities_count={len(self.entities)})"
        )
