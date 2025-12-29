"""
Classes de Invoice (notas fiscais) e acompanhamentos para serviços Sankhya.

Inclui tipos para notas fiscais, itens, acompanhamentos e operações de cancelamento.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

from datetime import datetime
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
    deserialize_optional_float,
)
from .basic_types import DataRow


class InvoiceItem(BaseModel):
    """
    Item de nota fiscal.
    
    Representa um produto ou serviço em uma nota.
    """

    model_config = ConfigDict(frozen=False)

    sequence: Optional[int] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    unit: Optional[str] = None
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    extra_data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("item")
        
        if self.sequence is not None:
            elem.set("sequencia", str(self.sequence))
        if self.product_code:
            create_xml_element("codProd", self.product_code, parent=elem)
        if self.product_name:
            create_xml_element("nomeProd", self.product_name, parent=elem)
        if self.quantity is not None:
            create_xml_element("qtd", str(self.quantity), parent=elem)
        if self.unit_price is not None:
            create_xml_element("vlrUnit", str(self.unit_price), parent=elem)
        if self.total_price is not None:
            create_xml_element("vlrTotal", str(self.total_price), parent=elem)
        if self.unit:
            create_xml_element("unidade", self.unit, parent=elem)
        if self.ncm:
            create_xml_element("ncm", self.ncm, parent=elem)
        if self.cfop:
            create_xml_element("cfop", self.cfop, parent=elem)
        
        for key, value in self.extra_data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "InvoiceItem":
        """Deserializa de elemento XML."""
        extra_data: Dict[str, Any] = {}
        known_elements = {
            "codProd", "nomeProd", "qtd", "vlrUnit", 
            "vlrTotal", "unidade", "ncm", "cfop"
        }
        
        for child in element:
            if child.tag not in known_elements:
                extra_data[child.tag] = get_element_text(child)
        
        return cls(
            sequence=deserialize_optional_int(get_element_attr(element, "sequencia")),
            product_code=get_element_text(element.find("codProd")),
            product_name=get_element_text(element.find("nomeProd")),
            quantity=deserialize_optional_float(get_element_text(element.find("qtd"))),
            unit_price=deserialize_optional_float(get_element_text(element.find("vlrUnit"))),
            total_price=deserialize_optional_float(get_element_text(element.find("vlrTotal"))),
            unit=get_element_text(element.find("unidade")),
            ncm=get_element_text(element.find("ncm")),
            cfop=get_element_text(element.find("cfop")),
            extra_data=extra_data,
        )


class InvoiceItems(BaseModel):
    """Lista de itens de nota fiscal."""

    model_config = ConfigDict(frozen=False)

    items: List[InvoiceItem] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("itens")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "InvoiceItems":
        """Deserializa de elemento XML."""
        items = [InvoiceItem.from_xml(child) for child in element.findall("item")]
        return cls(items=items)


class Accompaniment(BaseModel):
    """
    Acompanhamento de nota fiscal.
    
    Representa informações adicionais de acompanhamento.
    """

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    description: Optional[str] = None
    sequence: Optional[int] = None
    value: Optional[float] = None
    observation: Optional[str] = None
    extra_data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("acompanhamento")
        
        if self.code:
            elem.set("codigo", self.code)
        if self.sequence is not None:
            elem.set("sequencia", str(self.sequence))
        if self.description:
            create_xml_element("descricao", self.description, parent=elem)
        if self.value is not None:
            create_xml_element("valor", str(self.value), parent=elem)
        if self.observation:
            create_xml_element("observacao", self.observation, parent=elem)
        
        for key, value in self.extra_data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Accompaniment":
        """Deserializa de elemento XML."""
        extra_data: Dict[str, Any] = {}
        known_elements = {"descricao", "valor", "observacao"}
        
        for child in element:
            if child.tag not in known_elements:
                extra_data[child.tag] = get_element_text(child)
        
        return cls(
            code=get_element_attr(element, "codigo"),
            sequence=deserialize_optional_int(get_element_attr(element, "sequencia")),
            description=get_element_text(element.find("descricao")),
            value=deserialize_optional_float(get_element_text(element.find("valor"))),
            observation=get_element_text(element.find("observacao")),
            extra_data=extra_data,
        )


class InvoiceAccompaniments(BaseModel):
    """
    Lista de acompanhamentos de notas.
    
    Container para acompanhamentos de múltiplas notas.
    """

    model_config = ConfigDict(frozen=False)

    items: List[Accompaniment] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("acompanhamentosNotas")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "InvoiceAccompaniments":
        """Deserializa de elemento XML."""
        items = [
            Accompaniment.from_xml(child) 
            for child in element.findall("acompanhamento")
        ]
        return cls(items=items)


class Invoice(BaseModel):
    """
    Nota fiscal.
    
    Representa uma nota fiscal completa com cabeçalho e itens.
    """

    model_config = ConfigDict(frozen=False)

    number: Optional[int] = None
    unique_number: Optional[int] = None
    series: Optional[str] = None
    company_code: Optional[int] = None
    partner_code: Optional[int] = None
    top_code: Optional[int] = None
    contact_code: Optional[int] = None
    issue_date: Optional[str] = None
    movement_date: Optional[str] = None
    total_value: Optional[float] = None
    items: List[InvoiceItem] = PydanticField(default_factory=list)
    accompaniments: List[Accompaniment] = PydanticField(default_factory=list)
    extra_data: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("nota")
        
        if self.number is not None:
            elem.set("numero", str(self.number))
        if self.unique_number is not None:
            elem.set("nunota", str(self.unique_number))
        if self.series:
            elem.set("serie", self.series)
        if self.company_code is not None:
            elem.set("codemp", str(self.company_code))
        if self.partner_code is not None:
            elem.set("codparc", str(self.partner_code))
        if self.top_code is not None:
            elem.set("codtipoper", str(self.top_code))
        
        if self.issue_date:
            create_xml_element("dtEmissao", self.issue_date, parent=elem)
        if self.movement_date:
            create_xml_element("dtMov", self.movement_date, parent=elem)
        if self.total_value is not None:
            create_xml_element("vlrNota", str(self.total_value), parent=elem)
        
        if self.items:
            items_elem = etree.SubElement(elem, "itens")
            for item in self.items:
                items_elem.append(item.to_xml())
        
        if self.accompaniments:
            acc_elem = etree.SubElement(elem, "acompanhamentos")
            for acc in self.accompaniments:
                acc_elem.append(acc.to_xml())
        
        for key, value in self.extra_data.items():
            if value is not None:
                create_xml_element(key, str(value), parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Invoice":
        """Deserializa de elemento XML."""
        items: List[InvoiceItem] = []
        accompaniments: List[Accompaniment] = []
        extra_data: Dict[str, Any] = {}
        
        items_elem = element.find("itens")
        if items_elem is not None:
            items = [InvoiceItem.from_xml(i) for i in items_elem.findall("item")]
        
        acc_elem = element.find("acompanhamentos")
        if acc_elem is not None:
            accompaniments = [
                Accompaniment.from_xml(a) 
                for a in acc_elem.findall("acompanhamento")
            ]
        
        known_elements = {"itens", "acompanhamentos", "dtEmissao", "dtMov", "vlrNota"}
        for child in element:
            if child.tag not in known_elements:
                extra_data[child.tag] = get_element_text(child)
        
        return cls(
            number=deserialize_optional_int(get_element_attr(element, "numero")),
            unique_number=deserialize_optional_int(get_element_attr(element, "nunota")),
            series=get_element_attr(element, "serie"),
            company_code=deserialize_optional_int(get_element_attr(element, "codemp")),
            partner_code=deserialize_optional_int(get_element_attr(element, "codparc")),
            top_code=deserialize_optional_int(get_element_attr(element, "codtipoper")),
            contact_code=deserialize_optional_int(get_element_attr(element, "codcontato")),
            issue_date=get_element_text(element.find("dtEmissao")),
            movement_date=get_element_text(element.find("dtMov")),
            total_value=deserialize_optional_float(get_element_text(element.find("vlrNota"))),
            items=items,
            accompaniments=accompaniments,
            extra_data=extra_data,
        )


class Invoices(BaseModel):
    """Lista de notas fiscais."""

    model_config = ConfigDict(frozen=False)

    items: List[Invoice] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notas")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Invoices":
        """Deserializa de elemento XML."""
        items = [Invoice.from_xml(child) for child in element.findall("nota")]
        return cls(items=items)


class InvoicesWithCurrency(BaseModel):
    """Notas fiscais com informações de moeda."""

    model_config = ConfigDict(frozen=False)

    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    invoices: List[Invoice] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notasComMoeda")
        
        if self.currency_code:
            elem.set("codMoeda", self.currency_code)
        if self.exchange_rate is not None:
            elem.set("taxaCambio", str(self.exchange_rate))
        
        for invoice in self.invoices:
            elem.append(invoice.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "InvoicesWithCurrency":
        """Deserializa de elemento XML."""
        invoices = [Invoice.from_xml(child) for child in element.findall("nota")]
        
        return cls(
            currency_code=get_element_attr(element, "codMoeda"),
            exchange_rate=deserialize_optional_float(
                get_element_attr(element, "taxaCambio")
            ),
            invoices=invoices,
        )


class CancelledInvoice(BaseModel):
    """Nota fiscal cancelada."""

    model_config = ConfigDict(frozen=False)

    unique_number: Optional[int] = None
    number: Optional[int] = None
    series: Optional[str] = None
    cancellation_date: Optional[str] = None
    reason: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notaCancelada")
        
        if self.unique_number is not None:
            elem.set("nunota", str(self.unique_number))
        if self.number is not None:
            elem.set("numero", str(self.number))
        if self.series:
            elem.set("serie", self.series)
        if self.cancellation_date:
            create_xml_element("dtCancelamento", self.cancellation_date, parent=elem)
        if self.reason:
            create_xml_element("motivo", self.reason, parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "CancelledInvoice":
        """Deserializa de elemento XML."""
        return cls(
            unique_number=deserialize_optional_int(get_element_attr(element, "nunota")),
            number=deserialize_optional_int(get_element_attr(element, "numero")),
            series=get_element_attr(element, "serie"),
            cancellation_date=get_element_text(element.find("dtCancelamento")),
            reason=get_element_text(element.find("motivo")),
        )


class CancelledInvoices(BaseModel):
    """Lista de notas fiscais canceladas."""

    model_config = ConfigDict(frozen=False)

    items: List[CancelledInvoice] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notasCanceladas")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "CancelledInvoices":
        """Deserializa de elemento XML."""
        items = [
            CancelledInvoice.from_xml(child) 
            for child in element.findall("notaCancelada")
        ]
        return cls(items=items)


class CancellationResult(BaseModel):
    """Resultado de operação de cancelamento."""

    model_config = ConfigDict(frozen=False)

    success: bool = False
    unique_number: Optional[int] = None
    protocol: Optional[str] = None
    message: Optional[str] = None
    error_code: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("resultadoCancelamento")
        
        elem.set("sucesso", serialize_bool(self.success))
        if self.unique_number is not None:
            elem.set("nunota", str(self.unique_number))
        if self.protocol:
            create_xml_element("protocolo", self.protocol, parent=elem)
        if self.message:
            create_xml_element("mensagem", self.message, parent=elem)
        if self.error_code:
            create_xml_element("codigoErro", self.error_code, parent=elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "CancellationResult":
        """Deserializa de elemento XML."""
        return cls(
            success=deserialize_bool(get_element_attr(element, "sucesso", "")),
            unique_number=deserialize_optional_int(get_element_attr(element, "nunota")),
            protocol=get_element_text(element.find("protocolo")),
            message=get_element_text(element.find("mensagem")),
            error_code=get_element_text(element.find("codigoErro")),
        )
