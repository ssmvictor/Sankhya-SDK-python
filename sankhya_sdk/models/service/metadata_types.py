"""
Classes de metadados e configuração para serviços Sankhya.

Inclui tipos para status, sessão, chaves e configurações de serviço.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

import base64
import binascii
import re
from typing import Any, Dict, List, Optional

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField

from .basic_types import Field
from .xml_serialization import (
    create_xml_element,
    deserialize_bool,
    deserialize_optional_int,
    from_base64,
    get_element_attr,
    get_element_text,
    serialize_bool,
)

# ============================================================
# Decodificação Base64 da mensagem de status
# ============================================================

#: Base64 do alfabeto padrão, com padding apenas no final.
_BASE64_TEXT_PATTERN = re.compile(r"\A[A-Za-z0-9+/]*={0,2}\Z")

#: Abaixo deste tamanho o texto decodificado segue regras mais estritas.
_STATUS_SHORT_TEXT_LENGTH = 16

#: Pontuação comum (aceita também em textos curtos).
_STATUS_COMMON_PUNCTUATION = frozenset(" .,:;!?'\"()/-_%<>$")

#: Letras acentuadas do português (únicas aceitas em textos curtos).
_STATUS_PORTUGUESE_ACCENTED = frozenset("áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ")

#: Símbolos tipográficos não ASCII aceitos em textos longos.
_STATUS_TYPOGRAPHIC_CHARS = frozenset("ºª°§–—‘’“”…€«»\u00a0")


def _is_latin_letter(char: str) -> bool:
    """Indica se o caractere é uma letra latina (ASCII ou acentuada)."""
    return char.isalpha() and (char.isascii() or 0xC0 <= ord(char) <= 0x24F)


def _is_plausible_status_text(text: str) -> bool:
    """
    Indica se um texto decodificado de Base64 parece uma mensagem legível.

    Uma mensagem em texto puro formada só por caracteres do alfabeto Base64
    (por exemplo ``deadlock``, ``Pendente`` ou ``12345678``) também é Base64
    válido, mas os bytes decodificados viram lixo (``uæ\\x9d\\x96\\x87$``).
    Estas regras recusam esse lixo para que o texto original seja mantido:

    - ao menos 4 caracteres e uma letra;
    - apenas letras latinas, dígitos ASCII, espaços e quebras de linha,
      símbolos ASCII imprimíveis e alguns símbolos tipográficos (``º``,
      ``°``, ``§``, aspas curvas, ``€``...);
    - no máximo 30% de caracteres não ASCII, nunca três seguidos;
    - no máximo 35% de símbolos e 10% de símbolos fora da pontuação comum;
    - textos curtos (menos de 16 caracteres) devem ter uma única linha,
      apenas pontuação comum, apenas acentos do português junto de uma
      letra e nenhuma maiúscula logo após uma minúscula.

    Args:
        text: Texto decodificado

    Returns:
        True se o texto parecer uma mensagem legível
    """
    length = len(text)
    if length < 4 or not text.strip():
        return False

    short = length < _STATUS_SHORT_TEXT_LENGTH
    letters = symbols = uncommon_symbols = non_ascii = non_ascii_run = 0
    previous = ""
    for index, char in enumerate(text):
        if char.isascii():
            non_ascii_run = 0
        else:
            non_ascii += 1
            non_ascii_run += 1
            if non_ascii_run >= 3:
                return False

        if _is_latin_letter(char):
            letters += 1
            if short:
                if char.isupper() and previous.islower():
                    return False
                if not char.isascii():
                    following = text[index + 1 : index + 2]
                    if char not in _STATUS_PORTUGUESE_ACCENTED or not (
                        previous.isalpha() or following.isalpha()
                    ):
                        return False
        elif char.isascii() and char.isdigit():
            pass
        elif short:
            if char not in _STATUS_COMMON_PUNCTUATION:
                return False
            if char != " ":
                symbols += 1
        elif char in "\t\r\n ":
            pass
        elif (char.isascii() and char.isprintable()) or char in _STATUS_TYPOGRAPHIC_CHARS:
            symbols += 1
            if char not in _STATUS_COMMON_PUNCTUATION:
                uncommon_symbols += 1
        else:
            return False
        previous = char

    return (
        letters > 0
        and non_ascii * 10 <= length * 3
        and symbols * 100 <= length * 35
        and uncommon_symbols * 10 <= length
    )


def _decode_status_message(raw: str) -> Optional[str]:
    """
    Decodifica o conteúdo Base64 de ``<statusMessage>``.

    Porta de ``StatusMessage.ValueInternal`` (.NET), que sempre aplica
    ``FromBase64`` ao texto (ServiceResponse.cs:309). No CrispyWaffle,
    ``FromBase64`` usa ``Convert.FromBase64String`` e decodifica os bytes
    com ISO-8859-1. Aqui os bytes são lidos como UTF-8 estrito e, se não
    forem UTF-8 válido, como ISO-8859-1 (como no .NET). Quebras de linha
    (Base64 quebrado em linhas) são ignoradas.

    O .NET lança FormatException para conteúdo que não é Base64; aqui o
    conteúdo só é decodificado se for Base64 canônico (tamanho múltiplo de
    4, padding correto, bits finais zerados) e resultar em um texto legível
    (``_is_plausible_status_text``). Caso contrário retorna None e o texto
    original é mantido.

    Args:
        raw: Conteúdo do elemento ``<statusMessage>``

    Returns:
        Texto decodificado ou None se o conteúdo não for uma mensagem em Base64
    """
    compact = raw.strip().replace("\r", "").replace("\n", "")
    if not compact or len(compact) % 4 or not _BASE64_TEXT_PATTERN.match(compact):
        return None
    try:
        data = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        return None
    if base64.b64encode(data).decode("ascii") != compact:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("iso-8859-1")
    return text if _is_plausible_status_text(text) else None


class StatusMessage(BaseModel):
    """
    Mensagem de status retornada pelo serviço.

    O servidor envia o texto em Base64 (``<statusMessage><![CDATA[...]]>``);
    ``from_xml`` o decodifica, como ``StatusMessage.ValueInternal`` no .NET.
    """

    model_config = ConfigDict(frozen=False)

    value: str = ""
    is_encoded: bool = False

    @property
    def decoded_value(self) -> str:
        """Retorna o valor decodificado se necessário."""
        if self.is_encoded and self.value:
            return from_base64(self.value)
        return self.value

    @classmethod
    def from_encoded(cls, encoded_value: str) -> "StatusMessage":
        """Cria uma instância a partir de um valor codificado em Base64."""
        return cls(value=encoded_value, is_encoded=True)

    @classmethod
    def from_plain(cls, plain_value: str) -> "StatusMessage":
        """Cria uma instância a partir de um valor não codificado."""
        return cls(value=plain_value, is_encoded=False)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("statusMessage")
        if self.is_encoded:
            elem.set("encoded", "true")
        elem.text = self.value
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "StatusMessage":
        """
        Deserializa de elemento XML.

        Como no .NET (``ValueInternal`` aplica ``FromBase64``), o conteúdo é
        decodificado de Base64 mesmo sem atributo. Um conteúdo que não é
        uma mensagem em Base64 (texto puro) é mantido como está; com
        ``encoded="true"`` o valor é mantido codificado (``is_encoded``).
        """
        raw = get_element_text(element, "")
        if deserialize_bool(get_element_attr(element, "encoded", "")):
            return cls(value=raw, is_encoded=True)
        decoded = _decode_status_message(raw)
        return cls(value=raw if decoded is None else decoded, is_encoded=False)


class Metadata(BaseModel):
    """
    Metadados de campos e entidades.
    
    Contém informações sobre a estrutura de dados retornada.
    """

    model_config = ConfigDict(frozen=False)

    fields: List[Field] = PydanticField(default_factory=list)
    total_records: Optional[int] = None
    page_size: Optional[int] = None
    current_page: Optional[int] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("metadata")
        if self.total_records is not None:
            elem.set("totalRecords", str(self.total_records))
        if self.page_size is not None:
            elem.set("pageSize", str(self.page_size))
        if self.current_page is not None:
            elem.set("currentPage", str(self.current_page))

        if self.fields:
            fields_elem = etree.SubElement(elem, "fields")
            for field in self.fields:
                fields_elem.append(field.to_xml())

        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Metadata":
        """Deserializa de elemento XML."""
        fields = []
        fields_elem = element.find("fields")
        if fields_elem is not None:
            for field_elem in fields_elem:
                fields.append(Field.from_xml(field_elem))

        total_records = None
        page_size = None
        current_page = None

        if element.get("totalRecords"):
            try:
                total_records = int(element.get("totalRecords"))
            except (ValueError, TypeError):
                pass

        if element.get("pageSize"):
            try:
                page_size = int(element.get("pageSize"))
            except (ValueError, TypeError):
                pass

        if element.get("currentPage"):
            try:
                current_page = int(element.get("currentPage"))
            except (ValueError, TypeError):
                pass

        return cls(
            fields=fields,
            total_records=total_records,
            page_size=page_size,
            current_page=current_page,
        )


class Config(BaseModel):
    """
    Configurações de serviço.
    
    Define parâmetros de comportamento para operações CRUD e arquivos.
    """

    model_config = ConfigDict(frozen=False)

    include_presentation: bool = False
    return_fields: bool = True
    generate_records: bool = False
    validate_access: bool = True
    calculate_expressions: bool = False
    path: Optional[str] = None  # File path for file operations

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("config")
        elem.set("includePresentation", serialize_bool(self.include_presentation))
        elem.set("returnFields", serialize_bool(self.return_fields))
        elem.set("generateRecords", serialize_bool(self.generate_records))
        elem.set("validateAccess", serialize_bool(self.validate_access))
        elem.set("calculateExpressions", serialize_bool(self.calculate_expressions))
        if self.path:
            elem.set("path", self.path)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Config":
        """Deserializa de elemento XML."""
        return cls(
            include_presentation=deserialize_bool(
                get_element_attr(element, "includePresentation", "")
            ),
            return_fields=deserialize_bool(
                get_element_attr(element, "returnFields", ""), default=True
            ),
            generate_records=deserialize_bool(
                get_element_attr(element, "generateRecords", "")
            ),
            validate_access=deserialize_bool(
                get_element_attr(element, "validateAccess", ""), default=True
            ),
            calculate_expressions=deserialize_bool(
                get_element_attr(element, "calculateExpressions", "")
            ),
            path=get_element_attr(element, "path"),
        )


class Key(BaseModel):
    """
    Chave de entidade.
    
    Representa a chave primária ou única de um registro.

    O atributo ``valor`` de ``<chave>`` (``Key.Value`` no .NET) é exposto em
    ``value``; é a chave retornada por ``FileOpen`` (``OpenFile``).
    """

    model_config = ConfigDict(frozen=False)

    name: Optional[str] = None
    value: Optional[str] = None
    values: Dict[str, Any] = PydanticField(default_factory=dict)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("chave")
        if self.name:
            elem.set("nome", self.name)
        if self.value is not None:
            elem.set("valor", self.value)
        for key, value in self.values.items():
            create_xml_element(key, value, parent=elem)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Key":
        """Deserializa de elemento XML."""
        values: Dict[str, Any] = {}
        for child in element:
            values[child.tag] = get_element_text(child)

        return cls(
            name=get_element_attr(element, "nome"),
            value=get_element_attr(element, "valor"),
            values=values,
        )


class Session(BaseModel):
    """
    Informações de sessão do usuário.
    
    Contém dados de autenticação e contexto do usuário logado.

    Serializada como no .NET (``RequestBody.Session`` em
    ``[XmlElement("SESSION")]``, ``Session.Id`` em ``[XmlAttribute("ID")]``),
    por exemplo ``<SESSION ID="..."/>`` em ``SessionManagerSP.killSession``.
    """

    model_config = ConfigDict(frozen=False)

    jsession_id: Optional[str] = None
    user_id: Optional[int] = None
    user_code: Optional[str] = None
    user_name: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    call_id: Optional[str] = None
    transaction_id: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("SESSION")
        if self.jsession_id:
            elem.set("ID", self.jsession_id)
        if self.user_id is not None:
            elem.set("USERID", str(self.user_id))
        if self.user_code:
            elem.set("userCode", self.user_code)
        if self.user_name:
            elem.set("USERNAME", self.user_name)
        if self.company_id is not None:
            elem.set("companyId", str(self.company_id))
        if self.company_name:
            elem.set("companyName", self.company_name)
        if self.call_id:
            elem.set("callId", self.call_id)
        if self.transaction_id:
            elem.set("transactionId", self.transaction_id)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Session":
        """Deserializa de elemento XML (formato .NET ou legado)."""
        user_id = None
        company_id = None

        user_id_str = get_element_attr(element, "USERID") or get_element_attr(
            element, "userId"
        )
        if user_id_str:
            try:
                user_id = int(user_id_str)
            except ValueError:
                pass

        company_id_str = get_element_attr(element, "companyId")
        if company_id_str:
            try:
                company_id = int(company_id_str)
            except ValueError:
                pass

        return cls(
            jsession_id=get_element_attr(element, "ID")
            or get_element_attr(element, "jsessionid"),
            user_id=user_id,
            user_code=get_element_attr(element, "userCode"),
            user_name=get_element_attr(element, "USERNAME")
            or get_element_attr(element, "userName"),
            company_id=company_id,
            company_name=get_element_attr(element, "companyName"),
            call_id=get_element_attr(element, "callId"),
            transaction_id=get_element_attr(element, "transactionId"),
        )


class SingleNumber(BaseModel):
    """Número único retornado por operações de geração de sequência."""

    model_config = ConfigDict(frozen=False)

    name: Optional[str] = None
    value: Optional[int] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("singleNumber")
        if self.name:
            elem.set("name", self.name)
        if self.value is not None:
            elem.text = str(self.value)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SingleNumber":
        """Deserializa de elemento XML."""
        value = None
        text = get_element_text(element)
        if text:
            try:
                value = int(text)
            except ValueError:
                pass

        return cls(
            name=get_element_attr(element, "name"),
            value=value,
        )


class SingleNumbers(BaseModel):
    """Lista de números únicos."""

    model_config = ConfigDict(frozen=False)

    items: List[SingleNumber] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("singleNumbers")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "SingleNumbers":
        """Deserializa de elemento XML."""
        items = [
            SingleNumber.from_xml(child)
            for child in element.findall("singleNumber")
        ]
        return cls(items=items)


class Warning(BaseModel):
    """Aviso retornado pelo serviço."""

    model_config = ConfigDict(frozen=False)

    code: Optional[str] = None
    message: Optional[str] = None
    level: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("aviso")
        if self.code:
            elem.set("codigo", self.code)
        if self.level:
            elem.set("nivel", self.level)
        if self.message:
            elem.text = self.message
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Warning":
        """Deserializa de elemento XML."""
        return cls(
            code=get_element_attr(element, "codigo"),
            level=get_element_attr(element, "nivel"),
            message=get_element_text(element),
        )


class Warnings(BaseModel):
    """Lista de avisos."""

    model_config = ConfigDict(frozen=False)

    items: List[Warning] = PydanticField(default_factory=list)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("avisos")
        for item in self.items:
            elem.append(item.to_xml())
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Warnings":
        """Deserializa de elemento XML."""
        items = [Warning.from_xml(child) for child in element]
        return cls(items=items)


class Pager(BaseModel):
    """
    Informações de paginação.
    
    Usado em respostas paginadas para controlar o cursor.
    """

    model_config = ConfigDict(frozen=False)

    total_pages: Optional[int] = None
    total_records: Optional[int] = None
    pager_id: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("pager")
        if self.total_pages is not None:
            elem.set("totalPages", str(self.total_pages))
        if self.total_records is not None:
            elem.set("totalRecords", str(self.total_records))
        if self.pager_id:
            elem.set("pagerId", self.pager_id)
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Pager":
        """Deserializa de elemento XML."""
        return cls(
            total_pages=deserialize_optional_int(get_element_attr(element, "totalPages")),
            total_records=deserialize_optional_int(get_element_attr(element, "totalRecords")),
            pager_id=get_element_attr(element, "pagerId")
        )
