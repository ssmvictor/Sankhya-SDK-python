"""
Classes de usuários e sessões para serviços Sankhya.

Inclui tipos para usuários, sessões ativas e liberações.

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


class User(BaseModel):
    """
    Usuário do sistema.
    
    Representa informações de um usuário Sankhya.
    """

    model_config = ConfigDict(frozen=False)

    user_id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    active: bool = True
    admin: bool = False
    company_id: Optional[int] = None
    department: Optional[str] = None
    last_login: Optional[str] = None
    extra_data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("usuario")
        
        if self.user_id is not None:
            elem.set("idusu", str(self.user_id))
        if self.code:
            elem.set("codusu", self.code)
        if self.name:
            create_xml_element("nomeUsu", self.name, parent=elem)
        if self.email:
            create_xml_element("email", self.email, parent=elem)
        elem.set("ativo", serialize_bool(self.active))
        elem.set("admin", serialize_bool(self.admin))
        if self.company_id is not None:
            elem.set("codemp", str(self.company_id))
        if self.department:
            create_xml_element("departamento", self.department, parent=elem)
        if self.last_login:
            create_xml_element("ultimoLogin", self.last_login, parent=elem)
        
        for key, value in self.extra_data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "User":
        """Deserializa de elemento XML."""
        extra_data: Dict[str, Any] = {}
        known_elements = {"nomeUsu", "email", "departamento", "ultimoLogin"}
        
        for child in element:
            if child.tag not in known_elements:
                extra_data[child.tag] = get_element_text(child)
        
        return cls(
            user_id=deserialize_optional_int(get_element_attr(element, "idusu")),
            code=get_element_attr(element, "codusu"),
            name=get_element_text(element.find("nomeUsu")),
            email=get_element_text(element.find("email")),
            active=deserialize_bool(get_element_attr(element, "ativo", ""), default=True),
            admin=deserialize_bool(get_element_attr(element, "admin", "")),
            company_id=deserialize_optional_int(get_element_attr(element, "codemp")),
            department=get_element_text(element.find("departamento")),
            last_login=get_element_text(element.find("ultimoLogin")),
            extra_data=extra_data,
        )


class Users(BaseModel):
    """Lista de usuários."""

    model_config = ConfigDict(frozen=False)

    items: List[User] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("usuarios")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Users":
        """Deserializa de elemento XML."""
        items = [User.from_xml(child) for child in element.findall("usuario")]
        return cls(items=items)


class SessionInfo(BaseModel):
    """
    Informações de sessão ativa.
    
    Representa uma sessão de usuário conectado.
    """

    model_config = ConfigDict(frozen=False)

    session_id: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    company_id: Optional[int] = None
    ip_address: Optional[str] = None
    start_time: Optional[str] = None
    last_activity: Optional[str] = None
    application: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("sessao")
        
        if self.session_id:
            elem.set("sessionId", self.session_id)
        if self.user_id is not None:
            elem.set("idusu", str(self.user_id))
        if self.user_name:
            elem.set("nomeUsu", self.user_name)
        if self.company_id is not None:
            elem.set("codemp", str(self.company_id))
        if self.ip_address:
            elem.set("ip", self.ip_address)
        if self.start_time:
            elem.set("inicio", self.start_time)
        if self.last_activity:
            elem.set("ultimaAtividade", self.last_activity)
        if self.application:
            elem.set("aplicacao", self.application)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SessionInfo":
        """Deserializa de elemento XML."""
        return cls(
            session_id=get_element_attr(element, "sessionId"),
            user_id=deserialize_optional_int(get_element_attr(element, "idusu")),
            user_name=get_element_attr(element, "nomeUsu"),
            company_id=deserialize_optional_int(get_element_attr(element, "codemp")),
            ip_address=get_element_attr(element, "ip"),
            start_time=get_element_attr(element, "inicio"),
            last_activity=get_element_attr(element, "ultimaAtividade"),
            application=get_element_attr(element, "aplicacao"),
        )


class SessionsResponse(BaseModel):
    """Resposta contendo lista de sessões ativas."""

    model_config = ConfigDict(frozen=False)

    sessions: List[SessionInfo] = PydanticField(default_factory=list)
    total: Optional[int] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("SESSIONS")
        
        if self.total is not None:
            elem.set("total", str(self.total))
        
        for session in self.sessions:
            elem.append(session.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SessionsResponse":
        """Deserializa de elemento XML."""
        sessions = [SessionInfo.from_xml(child) for child in element.findall("sessao")]
        
        return cls(
            sessions=sessions,
            total=deserialize_optional_int(get_element_attr(element, "total")),
        )


class Release(BaseModel):
    """
    Liberação de documento/operação.
    
    Representa uma liberação pendente ou concedida.
    """

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    sequence: Optional[int] = None
    type: Optional[str] = None
    status: Optional[str] = None
    document_number: Optional[int] = None
    document_type: Optional[str] = None
    requester_id: Optional[int] = None
    requester_name: Optional[str] = None
    request_date: Optional[str] = None
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_date: Optional[str] = None
    observation: Optional[str] = None
    extra_data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("liberacao")
        
        if self.code:
            elem.set("codigo", self.code)
        if self.sequence is not None:
            elem.set("sequencia", str(self.sequence))
        if self.type:
            elem.set("tipo", self.type)
        if self.status:
            elem.set("status", self.status)
        if self.document_number is not None:
            elem.set("numDoc", str(self.document_number))
        if self.document_type:
            elem.set("tipoDoc", self.document_type)
        if self.requester_id is not None:
            create_xml_element("idSolicitante", str(self.requester_id), parent=elem)
        if self.requester_name:
            create_xml_element("nomeSolicitante", self.requester_name, parent=elem)
        if self.request_date:
            create_xml_element("dtSolicitacao", self.request_date, parent=elem)
        if self.approver_id is not None:
            create_xml_element("idAprovador", str(self.approver_id), parent=elem)
        if self.approver_name:
            create_xml_element("nomeAprovador", self.approver_name, parent=elem)
        if self.approval_date:
            create_xml_element("dtAprovacao", self.approval_date, parent=elem)
        if self.observation:
            create_xml_element("observacao", self.observation, parent=elem)
        
        for key, value in self.extra_data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Release":
        """Deserializa de elemento XML."""
        extra_data: Dict[str, Any] = {}
        known_elements = {
            "idSolicitante", "nomeSolicitante", "dtSolicitacao",
            "idAprovador", "nomeAprovador", "dtAprovacao", "observacao"
        }
        
        for child in element:
            if child.tag not in known_elements:
                extra_data[child.tag] = get_element_text(child)
        
        return cls(
            code=get_element_attr(element, "codigo"),
            sequence=deserialize_optional_int(get_element_attr(element, "sequencia")),
            type=get_element_attr(element, "tipo"),
            status=get_element_attr(element, "status"),
            document_number=deserialize_optional_int(get_element_attr(element, "numDoc")),
            document_type=get_element_attr(element, "tipoDoc"),
            requester_id=deserialize_optional_int(
                get_element_text(element.find("idSolicitante"))
            ),
            requester_name=get_element_text(element.find("nomeSolicitante")),
            request_date=get_element_text(element.find("dtSolicitacao")),
            approver_id=deserialize_optional_int(
                get_element_text(element.find("idAprovador"))
            ),
            approver_name=get_element_text(element.find("nomeAprovador")),
            approval_date=get_element_text(element.find("dtAprovacao")),
            observation=get_element_text(element.find("observacao")),
            extra_data=extra_data,
        )


class Releases(BaseModel):
    """Lista de liberações."""

    model_config = ConfigDict(frozen=False)

    items: List[Release] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("liberacoes")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Releases":
        """Deserializa de elemento XML."""
        items = [Release.from_xml(child) for child in element.findall("liberacao")]
        return cls(items=items)


class MessageUnlinkShipping(BaseModel):
    """
    Mensagem de desvincular remessa.
    
    Usada em operações de desvinculação de remessa de notas.
    """

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    message: Optional[str] = None
    invoice_number: Optional[int] = None
    shipping_number: Optional[int] = None
    success: bool = False

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("msgDesvincularRemessa")
        
        if self.code:
            elem.set("codigo", self.code)
        elem.set("sucesso", serialize_bool(self.success))
        if self.invoice_number is not None:
            elem.set("nunota", str(self.invoice_number))
        if self.shipping_number is not None:
            elem.set("numRemessa", str(self.shipping_number))
        if self.message:
            elem.text = self.message
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "MessageUnlinkShipping":
        """Deserializa de elemento XML."""
        return cls(
            code=get_element_attr(element, "codigo"),
            message=get_element_text(element),
            invoice_number=deserialize_optional_int(get_element_attr(element, "nunota")),
            shipping_number=deserialize_optional_int(
                get_element_attr(element, "numRemessa")
            ),
            success=deserialize_bool(get_element_attr(element, "sucesso", "")),
        )


class LowData(BaseModel):
    """
    Dados de baixa de títulos.
    
    Usado em operações de baixa financeira.
    """

    model_config = ConfigDict(frozen=False)

    type: Optional[str] = None
    date: Optional[str] = None
    value: Optional[float] = None
    discount: Optional[float] = None
    interest: Optional[float] = None
    fine: Optional[float] = None
    bank_account: Optional[str] = None
    history: Optional[str] = None
    data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("dadosBaixa")
        
        if self.type:
            elem.set("tipo", self.type)
        if self.date:
            create_xml_element("dtBaixa", self.date, parent=elem)
        if self.value is not None:
            create_xml_element("vlrBaixa", str(self.value), parent=elem)
        if self.discount is not None:
            create_xml_element("vlrDesconto", str(self.discount), parent=elem)
        if self.interest is not None:
            create_xml_element("vlrJuros", str(self.interest), parent=elem)
        if self.fine is not None:
            create_xml_element("vlrMulta", str(self.fine), parent=elem)
        if self.bank_account:
            create_xml_element("contaBanco", self.bank_account, parent=elem)
        if self.history:
            create_xml_element("historico", self.history, parent=elem)
        
        for key, value in self.data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "LowData":
        """Deserializa de elemento XML."""
        from .xml_serialization import deserialize_optional_float
        
        data: Dict[str, Any] = {}
        known_elements = {
            "dtBaixa", "vlrBaixa", "vlrDesconto", 
            "vlrJuros", "vlrMulta", "contaBanco", "historico"
        }
        
        for child in element:
            if child.tag not in known_elements:
                data[child.tag] = get_element_text(child)
        
        return cls(
            type=get_element_attr(element, "tipo"),
            date=get_element_text(element.find("dtBaixa")),
            value=deserialize_optional_float(get_element_text(element.find("vlrBaixa"))),
            discount=deserialize_optional_float(
                get_element_text(element.find("vlrDesconto"))
            ),
            interest=deserialize_optional_float(get_element_text(element.find("vlrJuros"))),
            fine=deserialize_optional_float(get_element_text(element.find("vlrMulta"))),
            bank_account=get_element_text(element.find("contaBanco")),
            history=get_element_text(element.find("historico")),
            data=data,
        )
