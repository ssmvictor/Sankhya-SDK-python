"""
Classes de Invoice (notas fiscais) e acompanhamentos para serviços Sankhya.

Inclui tipos para notas fiscais, itens, acompanhamentos e operações de cancelamento.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict, Field as PydanticField, field_validator

from sankhya_sdk.enums.billing_type import BillingType
from .constants import SankhyaConstants
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


# Formato de DateTime.ToString(CultureInfo.InvariantCulture) do .NET
# (padrão "G" da cultura invariante), usado em Invoices.cs nos atributos
# dataSaida/dtFaturamento.
_DOTNET_INVARIANT_DATETIME_FORMAT = "%m/%d/%Y %H:%M:%S"

# Formato constante ("c") de TimeSpan.ToString() do .NET:
# [-][d.]hh:mm:ss[.fffffff]
_DOTNET_TIMESPAN_PATTERN = re.compile(
    r"^(?P<sign>-)?(?:(?P<days>\d+)\.)?(?P<hours>\d{1,2}):(?P<minutes>\d{2})"
    r"(?::(?P<seconds>\d{2})(?:\.(?P<fraction>\d{1,7}))?)?$"
)


def _format_dotnet_datetime(value: Optional[datetime]) -> str:
    """
    Formata uma data como o .NET faz em Invoices.cs.

    Equivale a ``DateTime?.ToString(CultureInfo.InvariantCulture) ?? string.Empty``:
    ``None`` vira string vazia.
    """
    if value is None:
        return ""
    return value.strftime(_DOTNET_INVARIANT_DATETIME_FORMAT)


def _parse_dotnet_datetime(value: Optional[str]) -> Optional[datetime]:
    """Interpreta datas no formato invariante do .NET (ou ISO 8601)."""
    if value is None or not value.strip():
        return None
    text = value.strip()
    try:
        return datetime.strptime(text, _DOTNET_INVARIANT_DATETIME_FORMAT)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _format_dotnet_timespan(value: Optional[timedelta]) -> str:
    """
    Formata um intervalo como ``TimeSpan?.ToString() ?? string.Empty`` do .NET.

    Formato constante ("c"): ``[-][d.]hh:mm:ss[.fffffff]``.
    """
    if value is None:
        return ""
    total_microseconds = (
        (value.days * 86400 + value.seconds) * 1_000_000 + value.microseconds
    )
    sign = "-" if total_microseconds < 0 else ""
    total_microseconds = abs(total_microseconds)
    total_seconds, microseconds = divmod(total_microseconds, 1_000_000)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    result = sign + (f"{days}." if days else "")
    result += f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if microseconds:
        # Ticks do .NET têm resolução de 100ns (7 casas decimais)
        result += f".{microseconds * 10:07d}"
    return result


def _parse_dotnet_timespan(value: Optional[str]) -> Optional[timedelta]:
    """Interpreta um intervalo no formato constante ("c") do .NET."""
    if value is None or not value.strip():
        return None
    match = _DOTNET_TIMESPAN_PATTERN.match(value.strip())
    if match is None:
        return None
    fraction = match.group("fraction") or ""
    result = timedelta(
        days=int(match.group("days") or 0),
        hours=int(match.group("hours")),
        minutes=int(match.group("minutes")),
        seconds=int(match.group("seconds") or 0),
        microseconds=int(fraction.ljust(7, "0")[:6]) if fraction else 0,
    )
    return -result if match.group("sign") else result


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

    Campos portados de Sankhya-SDK-dotnet/Src/Sankhya/Service/Invoice.cs:

    - ``value``: texto do elemento ``<nota>`` (.NET ``Value``, ``[XmlText]``),
      ex.: o NUNOTA retornado pelo faturamento (``<nota>123</nota>``);
    - ``single_number_duplication``: atributo ``NUNOTA``
      (.NET ``SingleNumberDuplication``);
    - ``single_number_duplication_destiny``: atributo ``nuNota``
      (.NET ``SingleNumberDuplicationDestiny``), NUNOTA da nota gerada na
      duplicação;
    - ``single_number_duplication_source``: atributo ``nuNotaOrig``
      (.NET ``SingleNumberDuplicationSource``), NUNOTA da nota de origem.
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
    value: Optional[str] = None
    single_number_duplication: Optional[int] = None
    single_number_duplication_destiny: Optional[int] = None
    single_number_duplication_source: Optional[int] = None
    items: List[InvoiceItem] = PydanticField(default_factory=list)
    accompaniments: List[Accompaniment] = PydanticField(default_factory=list)
    extra_data: Dict[str, Any] = PydanticField(default_factory=dict)

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_value(cls, value: Any) -> Any:
        """Aceita inteiros (o .NET tipa ``Value`` como int) convertendo para texto."""
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        return value

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("nota")
        
        if self.value is not None:
            elem.text = str(self.value)
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
        if self.single_number_duplication is not None:
            elem.set("NUNOTA", str(self.single_number_duplication))
        if self.single_number_duplication_destiny is not None:
            elem.set("nuNota", str(self.single_number_duplication_destiny))
        if self.single_number_duplication_source is not None:
            elem.set("nuNotaOrig", str(self.single_number_duplication_source))
        
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
            value=(element.text or "").strip() or None,
            single_number_duplication=deserialize_optional_int(
                get_element_attr(element, "NUNOTA")
            ),
            single_number_duplication_destiny=deserialize_optional_int(
                get_element_attr(element, "nuNota")
            ),
            single_number_duplication_source=deserialize_optional_int(
                get_element_attr(element, "nuNotaOrig")
            ),
            items=items,
            accompaniments=accompaniments,
            extra_data=extra_data,
        )


class Invoices(BaseModel):
    """
    Lista de notas fiscais (elemento ``<notas>``).

    Além das notas (``items``, elementos ``<nota>``), carrega os parâmetros de
    faturamento/duplicação que o .NET serializa como ATRIBUTOS de ``<notas>``
    (Sankhya-SDK-dotnet/Src/Sankhya/Service/Invoices.cs). Cada atributo só é
    serializado quando o campo foi informado (equivalente aos ``ShouldSerialize*``
    do .NET):

    - ``code_operation_type`` -> ``codTipOper``
    - ``code_operation_type_duplication`` -> ``top``
    - ``series`` -> ``serie``
    - ``return_disapproved_invoices`` -> ``retNotasReprovadas`` (``S``/``N``)
    - ``should_update_price`` -> ``atualizaPreco`` (``true``/``false``)
    - ``should_duplicate_all_items`` -> ``duplicarTodosItens`` (``true``/``false``)
    - ``is_date_validated`` -> ``dataValidada`` (``S``/``N``)
    - ``one_invoice_for_each`` -> ``umaNotaParaCada`` (``S``/``N``)
    - ``date_exit_duplication`` -> ``dataSaida``
    - ``date_billing`` -> ``dtFaturamento``
    - ``date_exit`` -> ``dtSaida``
    - ``time_exit`` -> ``hrSaida`` (formato ``TimeSpan`` ``[-][d.]hh:mm:ss``)
    - ``billing_type`` -> ``tipoFaturamento`` (valor interno de ``BillingType``)

    Datas usam o formato de ``DateTime.ToString(CultureInfo.InvariantCulture)``
    (``MM/dd/yyyy HH:mm:ss``). Como no .NET (que define ``*Nullable = null``
    no faturamento), um campo de data/hora informado explicitamente como
    ``None`` é serializado como atributo vazio (ex.: ``dtFaturamento=""``).

    Elementos filhos, na ordem do .NET: ``single_numbers`` (``<nunota>``),
    ``invoices_with_currency`` (``<notasComMoeda>``) e ``items`` (``<nota>``).
    """

    model_config = ConfigDict(frozen=False)

    single_numbers: List[int] = PydanticField(default_factory=list)
    code_operation_type: Optional[int] = None
    code_operation_type_duplication: Optional[int] = None
    series: Optional[int] = None
    return_disapproved_invoices: Optional[bool] = None
    should_update_price: Optional[bool] = None
    should_duplicate_all_items: Optional[bool] = None
    is_date_validated: Optional[bool] = None
    one_invoice_for_each: Optional[bool] = None
    date_exit_duplication: Optional[datetime] = None
    date_billing: Optional[datetime] = None
    date_exit: Optional[datetime] = None
    time_exit: Optional[timedelta] = None
    billing_type: Optional[BillingType] = None
    invoices_with_currency: Optional["InvoicesWithCurrency"] = None
    items: List[Invoice] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notas")

        if self.code_operation_type is not None:
            elem.set("codTipOper", str(self.code_operation_type))
        if self.code_operation_type_duplication is not None:
            elem.set("top", str(self.code_operation_type_duplication))
        if self.series is not None:
            elem.set("serie", str(self.series))
        if self.return_disapproved_invoices is not None:
            elem.set(
                "retNotasReprovadas",
                serialize_bool(
                    self.return_disapproved_invoices, SankhyaConstants.BOOL_FORMAT_S_N
                ),
            )
        if self.should_update_price is not None:
            elem.set("atualizaPreco", serialize_bool(self.should_update_price))
        if self.should_duplicate_all_items is not None:
            elem.set("duplicarTodosItens", serialize_bool(self.should_duplicate_all_items))
        if self.is_date_validated is not None:
            elem.set(
                "dataValidada",
                serialize_bool(self.is_date_validated, SankhyaConstants.BOOL_FORMAT_S_N),
            )
        if self.one_invoice_for_each is not None:
            elem.set(
                "umaNotaParaCada",
                serialize_bool(self.one_invoice_for_each, SankhyaConstants.BOOL_FORMAT_S_N),
            )

        # Datas/horas: serializadas quando informadas, mesmo que como None
        fields_set = self.model_fields_set
        if self.date_exit_duplication is not None or "date_exit_duplication" in fields_set:
            elem.set("dataSaida", _format_dotnet_datetime(self.date_exit_duplication))
        if self.date_billing is not None or "date_billing" in fields_set:
            elem.set("dtFaturamento", _format_dotnet_datetime(self.date_billing))
        if self.date_exit is not None or "date_exit" in fields_set:
            elem.set("dtSaida", _format_dotnet_datetime(self.date_exit))
        if self.time_exit is not None or "time_exit" in fields_set:
            elem.set("hrSaida", _format_dotnet_timespan(self.time_exit))

        if self.billing_type is not None:
            elem.set("tipoFaturamento", self.billing_type.internal_value)

        for single_number in self.single_numbers:
            create_xml_element("nunota", str(single_number), parent=elem)
        if self.invoices_with_currency is not None:
            elem.append(self.invoices_with_currency.to_xml())
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Invoices":
        """Deserializa de elemento XML."""
        items = [Invoice.from_xml(child) for child in element.findall("nota")]

        data: Dict[str, Any] = {"items": items}

        single_numbers = [
            number
            for number in (
                deserialize_optional_int(get_element_text(child))
                for child in element.findall("nunota")
            )
            if number is not None
        ]
        if single_numbers:
            data["single_numbers"] = single_numbers

        currency_elem = element.find("notasComMoeda")
        if currency_elem is not None:
            data["invoices_with_currency"] = InvoicesWithCurrency.from_xml(currency_elem)

        int_attributes = {
            "codTipOper": "code_operation_type",
            "top": "code_operation_type_duplication",
            "serie": "series",
        }
        for attr_name, field_name in int_attributes.items():
            attr_value = deserialize_optional_int(get_element_attr(element, attr_name))
            if attr_value is not None:
                data[field_name] = attr_value

        bool_attributes = {
            "retNotasReprovadas": "return_disapproved_invoices",
            "atualizaPreco": "should_update_price",
            "duplicarTodosItens": "should_duplicate_all_items",
            "dataValidada": "is_date_validated",
            "umaNotaParaCada": "one_invoice_for_each",
        }
        for attr_name, field_name in bool_attributes.items():
            attr_value = get_element_attr(element, attr_name)
            if attr_value is not None:
                data[field_name] = deserialize_bool(attr_value)

        # Atributos de data/hora presentes (mesmo vazios) são considerados
        # informados, preservando o "ShouldSerialize" na reserialização
        date_attributes = {
            "dataSaida": "date_exit_duplication",
            "dtFaturamento": "date_billing",
            "dtSaida": "date_exit",
        }
        for attr_name, field_name in date_attributes.items():
            attr_value = get_element_attr(element, attr_name)
            if attr_value is not None:
                data[field_name] = _parse_dotnet_datetime(attr_value)

        time_exit = get_element_attr(element, "hrSaida")
        if time_exit is not None:
            data["time_exit"] = _parse_dotnet_timespan(time_exit)

        billing_type = get_element_attr(element, "tipoFaturamento")
        if billing_type is not None:
            try:
                data["billing_type"] = BillingType.from_internal_value(billing_type)
            except ValueError:
                pass

        return cls(**data)


class InvoicesWithCurrency(BaseModel):
    """
    Notas fiscais com informações de moeda (elemento ``<notasComMoeda>``).

    ``currency_value`` corresponde ao atributo ``valorMoeda`` do .NET
    (Sankhya-SDK-dotnet/Src/Sankhya/Service/InvoicesWithCurrency.cs), enviado
    como ``"undefined"`` no faturamento.
    """

    model_config = ConfigDict(frozen=False)

    currency_value: Optional[str] = None
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    invoices: List[Invoice] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("notasComMoeda")
        
        if self.currency_value is not None:
            elem.set("valorMoeda", self.currency_value)
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
            currency_value=get_element_attr(element, "valorMoeda"),
            currency_code=get_element_attr(element, "codMoeda"),
            exchange_rate=deserialize_optional_float(
                get_element_attr(element, "taxaCambio")
            ),
            invoices=invoices,
        )


# Invoices referencia InvoicesWithCurrency (definida depois dela)
Invoices.model_rebuild()


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
