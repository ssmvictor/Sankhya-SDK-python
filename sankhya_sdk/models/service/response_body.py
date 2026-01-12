"""
Classe ResponseBody para serviços Sankhya.

Encapsula todos os possíveis campos de corpo de resposta.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/ResponseBody.cs
"""

from __future__ import annotations

from typing import Any, Optional

from lxml import etree
from lxml.etree import Element
from pydantic import ConfigDict, Field as PydanticField

from sankhya_sdk.models.base import EntityBase
from .xml_serialization import (
    create_xml_element,
    get_element_attr,
    get_element_text,
    to_base64,
    from_base64,
    deserialize_optional_int,
)
from .constants import SankhyaConstants


def _parse_pk_element(element: Element) -> list[dict[str, Any]]:
    """
    Parseia elemento <PK> para lista de dicts com dados dinâmicos.
    
    O elemento PK pode conter múltiplos registros de chave primária.
    
    Args:
        element: Elemento XML <PK>
        
    Returns:
        Lista de dicionários com os campos de cada registro
    """
    result: list[dict[str, Any]] = []
    for child in element:
        record: dict[str, Any] = {}
        # Cada filho pode ter atributos ou sub-elementos
        if len(child) == 0:
            # Elemento simples com texto
            record[child.tag] = child.text
        else:
            # Elemento com sub-elementos
            for sub in child:
                record[sub.tag] = sub.text
        # Também inclui atributos
        for attr_name, attr_val in child.attrib.items():
            record[attr_name] = attr_val
        if record:
            result.append(record)
    return result


class ResponseBody(EntityBase):
    """
    Corpo de resposta de serviços Sankhya.
    
    Contém todos os campos possíveis que podem ser retornados em uma resposta.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        populate_by_name=True,
    )

    # Campos de identificação de usuário
    code_user_logged_in: Optional[int] = PydanticField(
        default=None, 
        alias="codUsuLogado"
    )
    code_user: Optional[int] = PydanticField(default=None, alias="idusu")
    _code_user_internal: Optional[str] = None  # Valor Base64 interno
    
    # Campos de sessão
    call_id: Optional[str] = PydanticField(default=None, alias="callID")
    jsession_id: Optional[str] = PydanticField(default=None, alias="jsessionid")
    
    # Campos de entidades CRUD
    crud_service_entities: Optional[Any] = PydanticField(
        default=None, 
        alias="entidades"
    )
    crud_service_provider_entities: Optional[Any] = PydanticField(
        default=None, 
        alias="entities"
    )
    
    # Campos de notas fiscais
    invoice_accompaniments: Optional[Any] = PydanticField(
        default=None, 
        alias="acompanhamentosNotas"
    )
    invoices: Optional[Any] = PydanticField(default=None, alias="notas")
    cancellation_result: Optional[Any] = PydanticField(
        default=None, 
        alias="resultadoCancelamento"
    )
    
    # Campos de usuários e sessões
    users: Optional[Any] = PydanticField(default=None, alias="usuarios")
    sessions: Optional[Any] = PydanticField(default=None, alias="SESSIONS")
    
    # Campos de avisos e mensagens
    warnings: Optional[Any] = PydanticField(default=None, alias="avisos")
    messages: Optional[Any] = PydanticField(default=None, alias="mensagens")
    
    # Campos de chaves
    key: Optional[Any] = PydanticField(default=None, alias="chave")
    primary_key: Optional[Any] = PydanticField(default=None, alias="pk")
    
    # Campos de eventos e liberações
    client_events: Optional[Any] = PydanticField(default=None, alias="clientEvents")
    releases: Optional[Any] = PydanticField(default=None, alias="liberacoes")
    
    # Campo de mensagem de desvincular remessa
    message_unlink_shipping: Optional[Any] = PydanticField(
        default=None, 
        alias="msgDesvincularRemessa"
    )

    pager: Optional[Any] = PydanticField(default=None, alias="pager")

    @property
    def code_user_internal(self) -> Optional[str]:
        """
        Retorna o código de usuário interno decodificado de Base64.
        
        Returns:
            Valor decodificado ou None
        """
        if self._code_user_internal:
            return from_base64(self._code_user_internal)
        return None

    @property
    def user_code(self) -> Optional[int]:
        """
        Alias para code_user para compatibilidade com o wrapper.
        
        Returns:
            Código do usuário ou None
        """
        return self.code_user

    @code_user_internal.setter
    def code_user_internal(self, value: str) -> None:
        """
        Define o código de usuário interno, codificando em Base64.
        
        Args:
            value: Valor a ser codificado
        """
        if value:
            self._code_user_internal = to_base64(value)
        else:
            self._code_user_internal = None

    def to_xml(self) -> Element:
        """
        Serializa o ResponseBody para um elemento XML.
        
        Returns:
            Elemento XML representando o corpo da resposta
        """
        elem = etree.Element(SankhyaConstants.RESPONSE_BODY)
        
        # Elementos de identificação/sessão (conforme .NET contract)
        if self.code_user_logged_in is not None:
            cul_elem = etree.SubElement(elem, SankhyaConstants.CODE_USER_LOGGED_ID)
            cul_elem.text = str(self.code_user_logged_in)
        
        # idusu é serializado como elemento com valor Base64
        if self.code_user is not None:
            idusu_elem = etree.SubElement(elem, SankhyaConstants.CODE_USER)
            idusu_elem.text = to_base64(str(self.code_user))
        
        if self.call_id:
            call_elem = etree.SubElement(elem, SankhyaConstants.CALL_ID)
            call_elem.text = self.call_id
        if self.jsession_id:
            jsess_elem = etree.SubElement(elem, SankhyaConstants.JSESSION_ID)
            jsess_elem.text = self.jsession_id
        
        # Elementos complexos
        complex_fields = {
            "crud_service_entities": SankhyaConstants.ENTITIES_PT_BR,
            "crud_service_provider_entities": SankhyaConstants.ENTITIES_EN,
            "invoice_accompaniments": SankhyaConstants.INVOICE_ACCOMPANIMENTS,
            "invoices": SankhyaConstants.INVOICES,
            "cancellation_result": SankhyaConstants.CANCELLATION_RESULT,
            "users": SankhyaConstants.USERS,
            "sessions": SankhyaConstants.SESSIONS,
            "warnings": SankhyaConstants.WARNINGS,
            "messages": SankhyaConstants.MESSAGES,
            "key": SankhyaConstants.KEY,
            "primary_key": SankhyaConstants.PRIMARY_KEY,
            "client_events": SankhyaConstants.CLIENT_EVENTS,
            "releases": SankhyaConstants.RELEASES,
            "message_unlink_shipping": SankhyaConstants.MESSAGE_UNLINK_SHIPPING,
        }
        
        for field_name, xml_tag in complex_fields.items():
            value = getattr(self, field_name)
            if value is None:
                continue
            
            if hasattr(value, "to_xml"):
                child = value.to_xml()
                child.tag = xml_tag
                elem.append(child)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "ResponseBody":
        """
        Deserializa um elemento XML para ResponseBody.
        
        Args:
            element: Elemento XML a ser deserializado
            
        Returns:
            Instância de ResponseBody
        """
        from .entity_types import CrudServiceEntities, CrudServiceProviderEntities
        from .invoice_types import Invoices, InvoiceAccompaniments, CancellationResult
        from .metadata_types import Key, Warnings
        from .user_types import Users, SessionsResponse, Releases, MessageUnlinkShipping
        from .event_types import ClientEvents, Messages
        from .metadata_types import Key, Warnings, Pager
        
        instance = cls()
        
        # codUsuLogado: elemento primeiro, fallback para atributo
        cul_elem = element.find(SankhyaConstants.CODE_USER_LOGGED_ID)
        if cul_elem is not None and cul_elem.text:
            instance.code_user_logged_in = deserialize_optional_int(cul_elem.text)
        else:
            instance.code_user_logged_in = deserialize_optional_int(
                get_element_attr(element, SankhyaConstants.CODE_USER_LOGGED_ID)
            )
        
        # idusu: tenta Base64 primeiro, fallback para inteiro simples
        idusu_elem = element.find(SankhyaConstants.CODE_USER)
        idusu_raw = None
        if idusu_elem is not None and idusu_elem.text:
            idusu_raw = idusu_elem.text
        else:
            idusu_raw = get_element_attr(element, SankhyaConstants.CODE_USER)
        
        if idusu_raw:
            instance._code_user_internal = idusu_raw
            # Tenta decodificar Base64 primeiro
            try:
                decoded = from_base64(idusu_raw)
                if decoded:
                    try:
                        instance.code_user = int(decoded)
                    except ValueError:
                        # Base64 decodificou mas não é inteiro, tenta valor original
                        try:
                            instance.code_user = int(idusu_raw)
                        except ValueError:
                            instance.code_user = None
            except Exception:
                # Base64 decode falhou, assume valor original é inteiro
                try:
                    instance.code_user = int(idusu_raw)
                except ValueError:
                    instance.code_user = None
        
        # callID: elemento primeiro, fallback para atributo
        call_elem = element.find(SankhyaConstants.CALL_ID)
        if call_elem is not None and call_elem.text:
            instance.call_id = call_elem.text
        else:
            instance.call_id = get_element_attr(element, SankhyaConstants.CALL_ID)
        
        # jsessionid: elemento primeiro, fallback para atributo
        jsess_elem = element.find(SankhyaConstants.JSESSION_ID)
        if jsess_elem is not None and jsess_elem.text:
            instance.jsession_id = jsess_elem.text
        else:
            instance.jsession_id = get_element_attr(element, SankhyaConstants.JSESSION_ID)
        
        # Processa elementos filhos
        for child in element:
            tag = child.tag
            
            if tag == SankhyaConstants.ENTITIES_PT_BR:
                instance.crud_service_entities = CrudServiceEntities.from_xml(child)
            elif tag == SankhyaConstants.ENTITIES_EN:
                instance.crud_service_provider_entities = CrudServiceProviderEntities.from_xml(child)
            elif tag == SankhyaConstants.INVOICE_ACCOMPANIMENTS:
                instance.invoice_accompaniments = InvoiceAccompaniments.from_xml(child)
            elif tag == SankhyaConstants.INVOICES:
                instance.invoices = Invoices.from_xml(child)
            elif tag == SankhyaConstants.CANCELLATION_RESULT:
                instance.cancellation_result = CancellationResult.from_xml(child)
            elif tag == SankhyaConstants.USERS:
                instance.users = Users.from_xml(child)
            elif tag == SankhyaConstants.SESSIONS:
                instance.sessions = SessionsResponse.from_xml(child)
            elif tag == SankhyaConstants.WARNINGS:
                instance.warnings = Warnings.from_xml(child)
            elif tag == SankhyaConstants.MESSAGES:
                instance.messages = Messages.from_xml(child)
            elif tag == SankhyaConstants.KEY:
                instance.key = Key.from_xml(child)
            elif tag == SankhyaConstants.PRIMARY_KEY:
                instance.primary_key = Key.from_xml(child)
            elif tag == SankhyaConstants.PRIMARY_KEY_UPPER:
                # <PK> uppercase: parse como lista de dicts para dados dinâmicos
                instance.primary_key = _parse_pk_element(child)
            elif tag == SankhyaConstants.CLIENT_EVENTS:
                instance.client_events = ClientEvents.from_xml(child)
            elif tag == SankhyaConstants.RELEASES:
                instance.releases = Releases.from_xml(child)
            elif tag == SankhyaConstants.MESSAGE_UNLINK_SHIPPING:
                instance.message_unlink_shipping = MessageUnlinkShipping.from_xml(child)
            elif tag == "pager":
                instance.pager = Pager.from_xml(child)
        
        return instance
