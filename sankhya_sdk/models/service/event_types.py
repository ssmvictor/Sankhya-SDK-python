"""
Classes de eventos e mensagens para serviços Sankhya.

Inclui tipos para eventos de cliente, mensagens e avisos do sistema.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict, Field as PydanticField

from .xml_serialization import (
    create_xml_element,
    get_element_attr,
    get_element_text,
    serialize_bool,
    deserialize_bool,
    deserialize_optional_int,
)


class ClientEventInvoiceItem(BaseModel):
    """
    Item de nota em evento de cliente.
    
    Representa um item de nota associado a um evento.
    """

    model_config = ConfigDict(frozen=False)

    sequence: Optional[int] = None
    product_code: Optional[str] = None
    quantity: Optional[float] = None
    data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("itemNota")
        
        if self.sequence is not None:
            elem.set("sequencia", str(self.sequence))
        if self.product_code:
            elem.set("codProd", self.product_code)
        if self.quantity is not None:
            elem.set("qtd", str(self.quantity))
        
        for key, value in self.data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "ClientEventInvoiceItem":
        """Deserializa de elemento XML."""
        data: Dict[str, Any] = {}
        for child in element:
            data[child.tag] = get_element_text(child)
        
        qty_str = get_element_attr(element, "qtd")
        quantity = None
        if qty_str:
            try:
                quantity = float(qty_str)
            except ValueError:
                pass
        
        return cls(
            sequence=deserialize_optional_int(get_element_attr(element, "sequencia")),
            product_code=get_element_attr(element, "codProd"),
            quantity=quantity,
            data=data,
        )


class ClientEvent(BaseModel):
    """
    Evento de cliente.
    
    Representa um evento disparado pelo cliente para o servidor.
    """

    model_config = ConfigDict(frozen=False)

    type: Optional[str] = None
    code: Optional[str] = None
    invoice_number: Optional[int] = None
    items: List[ClientEventInvoiceItem] = PydanticField(default_factory=list)
    data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("clientEvent")
        
        if self.type:
            elem.set("type", self.type)
        if self.code:
            elem.set("code", self.code)
        if self.invoice_number is not None:
            elem.set("nunota", str(self.invoice_number))
        
        if self.items:
            items_elem = etree.SubElement(elem, "itensNota")
            for item in self.items:
                items_elem.append(item.to_xml())
        
        for key, value in self.data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "ClientEvent":
        """Deserializa de elemento XML."""
        items: List[ClientEventInvoiceItem] = []
        data: Dict[str, Any] = {}
        
        items_elem = element.find("itensNota")
        if items_elem is not None:
            items = [
                ClientEventInvoiceItem.from_xml(i) 
                for i in items_elem.findall("itemNota")
            ]
        
        known_elements = {"itensNota"}
        for child in element:
            if child.tag not in known_elements:
                data[child.tag] = get_element_text(child)
        
        return cls(
            type=get_element_attr(element, "type"),
            code=get_element_attr(element, "code"),
            invoice_number=deserialize_optional_int(
                get_element_attr(element, "nunota")
            ),
            items=items,
            data=data,
        )


class ClientEvents(BaseModel):
    """Lista de eventos de cliente."""

    model_config = ConfigDict(frozen=False)

    items: List[ClientEvent] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("clientEvents")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "ClientEvents":
        """Deserializa de elemento XML."""
        items = [ClientEvent.from_xml(child) for child in element.findall("clientEvent")]
        return cls(items=items)


class Event(BaseModel):
    """
    Evento genérico do sistema.
    
    Representa um evento do sistema Sankhya.
    """

    model_config = ConfigDict(frozen=False)

    type: Optional[str] = None
    code: Optional[str] = None
    timestamp: Optional[str] = None
    user_id: Optional[int] = None
    description: Optional[str] = None
    data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("evento")
        
        if self.type:
            elem.set("tipo", self.type)
        if self.code:
            elem.set("codigo", self.code)
        if self.timestamp:
            elem.set("timestamp", self.timestamp)
        if self.user_id is not None:
            elem.set("idusu", str(self.user_id))
        if self.description:
            create_xml_element("descricao", self.description, parent=elem)
        
        for key, value in self.data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Event":
        """Deserializa de elemento XML."""
        data: Dict[str, Any] = {}
        known_elements = {"descricao"}
        
        for child in element:
            if child.tag not in known_elements:
                data[child.tag] = get_element_text(child)
        
        return cls(
            type=get_element_attr(element, "tipo"),
            code=get_element_attr(element, "codigo"),
            timestamp=get_element_attr(element, "timestamp"),
            user_id=deserialize_optional_int(get_element_attr(element, "idusu")),
            description=get_element_text(element.find("descricao")),
            data=data,
        )


class Message(BaseModel):
    """
    Mensagem do sistema.
    
    Representa uma mensagem retornada pelo serviço.
    """

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    type: Optional[str] = None
    level: Optional[str] = None
    text: Optional[str] = None
    details: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("mensagem")
        
        if self.code:
            elem.set("codigo", self.code)
        if self.type:
            elem.set("tipo", self.type)
        if self.level:
            elem.set("nivel", self.level)
        if self.text:
            create_xml_element("texto", self.text, parent=elem)
        if self.details:
            create_xml_element("detalhes", self.details, parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Message":
        """Deserializa de elemento XML."""
        return cls(
            code=get_element_attr(element, "codigo"),
            type=get_element_attr(element, "tipo"),
            level=get_element_attr(element, "nivel"),
            text=get_element_text(element.find("texto")) or get_element_text(element),
            details=get_element_text(element.find("detalhes")),
        )


class Messages(BaseModel):
    """Lista de mensagens."""

    model_config = ConfigDict(frozen=False)

    items: List[Message] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("mensagens")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Messages":
        """Deserializa de elemento XML."""
        items = [Message.from_xml(child) for child in element.findall("mensagem")]
        return cls(items=items)


class SystemMessage(BaseModel):
    """
    Mensagem do sistema para broadcast.
    
    Usada para enviar mensagens a usuários conectados.
    """

    model_config = ConfigDict(frozen=False)

    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    target_users: List[int] = PydanticField(default_factory=list)
    expire_minutes: Optional[int] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("mensagemSistema")
        
        if self.title:
            create_xml_element("titulo", self.title, parent=elem)
        if self.content:
            create_xml_element("conteudo", self.content, parent=elem)
        if self.type:
            elem.set("tipo", self.type)
        if self.priority:
            elem.set("prioridade", self.priority)
        if self.expire_minutes is not None:
            elem.set("expiraMinutos", str(self.expire_minutes))
        if self.target_users:
            users_elem = etree.SubElement(elem, "usuarios")
            for user_id in self.target_users:
                create_xml_element("idusu", str(user_id), parent=users_elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SystemMessage":
        """Deserializa de elemento XML."""
        target_users: List[int] = []
        users_elem = element.find("usuarios")
        if users_elem is not None:
            for user_elem in users_elem.findall("idusu"):
                user_id = deserialize_optional_int(get_element_text(user_elem))
                if user_id is not None:
                    target_users.append(user_id)
        
        return cls(
            title=get_element_text(element.find("titulo")),
            content=get_element_text(element.find("conteudo")),
            type=get_element_attr(element, "tipo"),
            priority=get_element_attr(element, "prioridade"),
            expire_minutes=deserialize_optional_int(
                get_element_attr(element, "expiraMinutos")
            ),
            target_users=target_users,
        )


class SystemWarningRecipient(BaseModel):
    """Destinatário de aviso do sistema."""

    model_config = ConfigDict(frozen=False)

    user_id: Optional[int] = None
    user_name: Optional[str] = None
    email: Optional[str] = None
    read: bool = False

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("destinatario")
        
        if self.user_id is not None:
            elem.set("idusu", str(self.user_id))
        if self.user_name:
            elem.set("nomeUsu", self.user_name)
        if self.email:
            elem.set("email", self.email)
        elem.set("lido", serialize_bool(self.read))
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SystemWarningRecipient":
        """Deserializa de elemento XML."""
        return cls(
            user_id=deserialize_optional_int(get_element_attr(element, "idusu")),
            user_name=get_element_attr(element, "nomeUsu"),
            email=get_element_attr(element, "email"),
            read=deserialize_bool(get_element_attr(element, "lido", "")),
        )


class SystemWarning(BaseModel):
    """
    Aviso do sistema.
    
    Representa um aviso para ser exibido aos usuários.
    """

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    created_at: Optional[str] = None
    expire_at: Optional[str] = None
    recipients: List[SystemWarningRecipient] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("avisoSistema")
        
        if self.code:
            elem.set("codigo", self.code)
        if self.type:
            elem.set("tipo", self.type)
        if self.priority:
            elem.set("prioridade", self.priority)
        if self.created_at:
            elem.set("criadoEm", self.created_at)
        if self.expire_at:
            elem.set("expiraEm", self.expire_at)
        if self.title:
            create_xml_element("titulo", self.title, parent=elem)
        if self.content:
            create_xml_element("conteudo", self.content, parent=elem)
        if self.recipients:
            dest_elem = etree.SubElement(elem, "destinatarios")
            for recipient in self.recipients:
                dest_elem.append(recipient.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SystemWarning":
        """Deserializa de elemento XML."""
        recipients: List[SystemWarningRecipient] = []
        dest_elem = element.find("destinatarios")
        if dest_elem is not None:
            recipients = [
                SystemWarningRecipient.from_xml(r) 
                for r in dest_elem.findall("destinatario")
            ]
        
        return cls(
            code=get_element_attr(element, "codigo"),
            type=get_element_attr(element, "tipo"),
            priority=get_element_attr(element, "prioridade"),
            created_at=get_element_attr(element, "criadoEm"),
            expire_at=get_element_attr(element, "expiraEm"),
            title=get_element_text(element.find("titulo")),
            content=get_element_text(element.find("conteudo")),
            recipients=recipients,
        )


class NotificationElem(BaseModel):
    """
    Elemento de notificação.
    
    Usado para configuração de notificações.
    """

    model_config = ConfigDict(frozen=False)

    type: Optional[str] = None
    enabled: bool = True
    data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notificacao")
        
        if self.type:
            elem.set("tipo", self.type)
        elem.set("habilitado", serialize_bool(self.enabled))
        
        for key, value in self.data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "NotificationElem":
        """Deserializa de elemento XML."""
        data: Dict[str, Any] = {}
        for child in element:
            data[child.tag] = get_element_text(child)
        
        return cls(
            type=get_element_attr(element, "tipo"),
            enabled=deserialize_bool(get_element_attr(element, "habilitado", ""), default=True),
            data=data,
        )
