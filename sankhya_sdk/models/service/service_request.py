"""
Classe ServiceRequest para serviços Sankhya.

Encapsula uma requisição completa para a API Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/ServiceRequest.cs
"""

from __future__ import annotations

from typing import Optional

from lxml import etree
from lxml.etree import Element
from pydantic import ConfigDict, Field as PydanticField

from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.enums.service_name import ServiceName
from .request_body import RequestBody
from .constants import SankhyaConstants


class ServiceRequest(EntityBase):
    """
    Requisição de serviço Sankhya.
    
    Encapsula o nome do serviço e o corpo da requisição para
    comunicação com a API Sankhya via XML.
    
    Attributes:
        service: Nome do serviço a ser chamado
        request_body: Corpo da requisição com os dados
    
    Example:
        >>> request = ServiceRequest(service=ServiceName.CRUD_FIND)
        >>> request.request_body.entity = Entity(name="Parceiro")
        >>> xml = request.to_xml_string()
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    service: ServiceName = PydanticField(
        default=ServiceName.TEST,
        description="Nome do serviço a ser chamado"
    )
    request_body: RequestBody = PydanticField(
        default_factory=RequestBody,
        description="Corpo da requisição"
    )
    no_auth: bool = PydanticField(
        default=False,
        description="Se True, a requisição não requer autenticação prévia (ex: login)"
    )

    def __init__(
        self, 
        service: ServiceName = ServiceName.TEST, 
        request_body: Optional[RequestBody] = None,
        **data
    ):
        """
        Inicializa uma nova requisição de serviço.
        
        Args:
            service: Nome do serviço a ser chamado
            request_body: Corpo da requisição (criado automaticamente se None)
            **data: Dados adicionais para o modelo
        """
        if request_body is None:
            request_body = RequestBody()
        super().__init__(service=service, request_body=request_body, **data)

    def to_xml(self) -> Element:
        """
        Serializa a requisição para um elemento XML.
        
        Returns:
            Elemento XML representando a requisição completa
            
        Example:
            <serviceRequest serviceName="CRUDServiceProvider.findRecords">
                <requestBody>
                    ...
                </requestBody>
            </serviceRequest>
        """
        elem = etree.Element(SankhyaConstants.SERVICE_REQUEST)
        
        # Define o atributo serviceName usando o internal_value do enum
        elem.set(SankhyaConstants.SERVICE_NAME, self.service.internal_value)
        
        # Adiciona o corpo da requisição
        body_elem = self.request_body.to_xml()
        elem.append(body_elem)
        
        return elem

    def to_xml_string(self, pretty_print: bool = False) -> str:
        """
        Serializa a requisição para uma string XML.
        
        Args:
            pretty_print: Se True, formata o XML com indentação
            
        Returns:
            String XML representando a requisição
        """
        element = self.to_xml()
        return etree.tostring(element, pretty_print=pretty_print, encoding="unicode")

    def to_xml_bytes(self, pretty_print: bool = False) -> bytes:
        """
        Serializa a requisição para bytes XML com declaração.
        
        Args:
            pretty_print: Se True, formata o XML com indentação
            
        Returns:
            Bytes XML com encoding UTF-8
        """
        element = self.to_xml()
        return etree.tostring(
            element, 
            pretty_print=pretty_print, 
            encoding="UTF-8",
            xml_declaration=True
        )

    @classmethod
    def from_xml(cls, element: Element) -> "ServiceRequest":
        """
        Deserializa um elemento XML para ServiceRequest.
        
        Args:
            element: Elemento XML a ser deserializado
            
        Returns:
            Instância de ServiceRequest
        """
        from .xml_serialization import get_element_attr
        
        # Obtém o nome do serviço
        service_name_str = get_element_attr(element, SankhyaConstants.SERVICE_NAME, "")
        service = ServiceName.from_internal_value(service_name_str)
        
        # Obtém o corpo da requisição
        body_elem = element.find(SankhyaConstants.REQUEST_BODY)
        request_body = RequestBody()
        if body_elem is not None:
            request_body = RequestBody.from_xml(body_elem)
        
        return cls(service=service, request_body=request_body)

    @classmethod
    def from_xml_string(cls, xml_string: str) -> "ServiceRequest":
        """
        Deserializa uma string XML para ServiceRequest.
        
        Args:
            xml_string: String XML a ser deserializada
            
        Returns:
            Instância de ServiceRequest
        """
        element = etree.fromstring(
            xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string
        )
        return cls.from_xml(element)
