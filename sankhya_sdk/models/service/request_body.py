"""
Classe RequestBody para serviços Sankhya.

Encapsula todos os possíveis campos de corpo de requisição.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/RequestBody.cs
"""

from __future__ import annotations

from typing import Any, Optional

from lxml import etree
from lxml.etree import Element
from pydantic import ConfigDict, Field as PydanticField

from sankhya_sdk.models.base import EntityBase
from .xml_serialization import create_xml_element, serialize_bool
from .constants import SankhyaConstants


class RequestBody(EntityBase):
    """
    Corpo de requisição para serviços Sankhya.
    
    Contém todos os campos possíveis que podem ser enviados em uma requisição.
    Apenas campos que foram explicitamente definidos são serializados.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        populate_by_name=True,
    )

    # Campos de nota fiscal
    invoice: Optional[Any] = PydanticField(default=None, alias="nota")
    invoices: Optional[Any] = PydanticField(default=None, alias="notas")
    cancelled_invoices: Optional[Any] = PydanticField(default=None, alias="notasCanceladas")
    
    # Campos de entidade
    entity: Optional[Any] = PydanticField(default=None, alias="entity")
    data_set: Optional[Any] = PydanticField(default=None, alias="dataSet")
    
    # Campos de parâmetros
    param: Optional[Any] = PydanticField(default=None, alias="param")
    params: Optional[Any] = PydanticField(default=None, alias="params")
    
    # Campos de sessão
    session: Optional[Any] = PydanticField(default=None, alias="session")
    
    # Campos de dados auxiliares
    low_data: Optional[Any] = PydanticField(default=None, alias="dadosBaixa")
    
    # Campos de mensagens do sistema
    system_warning: Optional[Any] = PydanticField(default=None, alias="avisoSistema")
    system_message: Optional[Any] = PydanticField(default=None, alias="mensagemSistema")
    
    # Campos de configuração
    config: Optional[Any] = PydanticField(default=None, alias="config")
    
    # Campos de autenticação
    username: Optional[str] = PydanticField(default=None, alias="NOMUSU")
    password: Optional[str] = PydanticField(default=None, alias="INTERNO")
    
    # Campos de numeração
    single_numbers: Optional[Any] = PydanticField(default=None, alias="singleNumbers")
    
    # Campos de eventos
    client_events: Optional[Any] = PydanticField(default=None, alias="clientEvents")
    
    # Campos de notificação
    notification_elem: Optional[Any] = PydanticField(default=None, alias="notificacao")
    
    # Campos de caminhos
    paths: Optional[Any] = PydanticField(default=None, alias="paths")

    def to_xml(self) -> Element:
        """
        Serializa o RequestBody para um elemento XML.
        
        Apenas campos que foram explicitamente definidos (presentes em _fields_set)
        são incluídos na serialização.
        
        Returns:
            Elemento XML representando o corpo da requisição
        """
        elem = etree.Element(SankhyaConstants.REQUEST_BODY)
        
        # Mapeia campos para suas tags XML
        field_mappings = {
            "invoice": "nota",
            "invoices": "notas",
            "cancelled_invoices": "notasCanceladas",
            "entity": "entity",
            "data_set": "dataSet",
            "param": "param",
            "params": "params",
            "session": "session",
            "low_data": "dadosBaixa",
            "system_warning": "avisoSistema",
            "system_message": "mensagemSistema",
            "config": "config",
            "username": "NOMUSU",
            "password": "INTERNO",
            "single_numbers": "singleNumbers",
            "client_events": "clientEvents",
            "notification_elem": "notificacao",
            "paths": "paths",
        }
        
        for field_name, xml_tag in field_mappings.items():
            if not self.should_serialize_field(field_name):
                continue
            
            value = getattr(self, field_name)
            if value is None:
                continue
            
            # Se o valor tem método to_xml, usa ele
            if hasattr(value, "to_xml"):
                child = value.to_xml()
                # Ajusta a tag se necessário
                if child.tag != xml_tag:
                    child.tag = xml_tag
                elem.append(child)
            elif isinstance(value, str):
                create_xml_element(xml_tag, value, parent=elem)
            elif isinstance(value, bool):
                create_xml_element(xml_tag, serialize_bool(value), parent=elem)
            elif isinstance(value, (int, float)):
                create_xml_element(xml_tag, str(value), parent=elem)
            elif isinstance(value, dict):
                # Serializa dicionário como elemento com filhos
                child = etree.SubElement(elem, xml_tag)
                for k, v in value.items():
                    if v is not None:
                        create_xml_element(k, str(v), parent=child)
            elif isinstance(value, list):
                # Serializa lista como elementos filhos
                child = etree.SubElement(elem, xml_tag)
                for item in value:
                    if hasattr(item, "to_xml"):
                        child.append(item.to_xml())
                    else:
                        create_xml_element("item", str(item), parent=child)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "RequestBody":
        """
        Deserializa um elemento XML para RequestBody.
        
        Args:
            element: Elemento XML a ser deserializado
            
        Returns:
            Instância de RequestBody
        """
        from .xml_serialization import get_element_text
        from .entity_types import Entity, DataSet
        from .invoice_types import Invoice, Invoices, CancelledInvoices
        from .metadata_types import Config, Session, SingleNumbers
        from .query_types import Param, Params
        from .event_types import ClientEvents, SystemMessage, SystemWarning, NotificationElem
        from .user_types import LowData
        from .basic_types import Paths
        
        instance = cls()
        
        # Processa cada elemento filho
        for child in element:
            tag = child.tag
            
            if tag == "nota":
                instance.invoice = Invoice.from_xml(child)
            elif tag == "notas":
                instance.invoices = Invoices.from_xml(child)
            elif tag == "notasCanceladas":
                instance.cancelled_invoices = CancelledInvoices.from_xml(child)
            elif tag == "entity":
                instance.entity = Entity.from_xml(child)
            elif tag == "dataSet":
                instance.data_set = DataSet.from_xml(child)
            elif tag == "param":
                instance.param = Param.from_xml(child)
            elif tag == "params":
                instance.params = Params.from_xml(child)
            elif tag == "session":
                instance.session = Session.from_xml(child)
            elif tag == "dadosBaixa":
                instance.low_data = LowData.from_xml(child)
            elif tag == "avisoSistema":
                instance.system_warning = SystemWarning.from_xml(child)
            elif tag == "mensagemSistema":
                instance.system_message = SystemMessage.from_xml(child)
            elif tag == "config":
                instance.config = Config.from_xml(child)
            elif tag == "NOMUSU":
                instance.username = get_element_text(child)
            elif tag == "INTERNO":
                instance.password = get_element_text(child)
            elif tag == "singleNumbers":
                instance.single_numbers = SingleNumbers.from_xml(child)
            elif tag == "clientEvents":
                instance.client_events = ClientEvents.from_xml(child)
            elif tag == "notificacao":
                instance.notification_elem = NotificationElem.from_xml(child)
            elif tag == "paths":
                instance.paths = Paths.from_xml(child)
        
        return instance
