"""
Classes de entidade e dataset para serviços Sankhya.

Inclui tipos para entidades de consulta, datasets e containers CRUD.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from lxml import etree
from lxml.etree import Element
from pydantic import BaseModel, ConfigDict, Field as PydanticField

from sankhya_sdk.models.base import EntityBase
from .xml_serialization import (
    create_xml_element,
    get_element_attr,
    get_element_text,
    serialize_bool,
    deserialize_bool,
    deserialize_optional_int,
)
from .basic_types import (
    Field,
    Criteria,
    LiteralCriteria,
    LiteralCriteriaSql,
    DataRow,
    ReferenceFetch,
    FieldValue,
)
from .constants import SankhyaConstants
from .metadata_types import Metadata


def _dynamic_to_xml(tag: str, values: Dict[str, Any]) -> Element:
    """
    Serializa um dicionário dinâmico como elemento com um filho por chave.

    Equivale a ``DynamicSerialization.WriteXml`` (CrispyWaffle), usado pelo
    .NET em ``DataRow.LocalFields``/``DataRow.Keys`` e ``Entity.Ids``:
    ``<tag><CHAVE>valor</CHAVE>...</tag>``.

    Args:
        tag: Nome do elemento agrupador
        values: Valores por nome de campo

    Returns:
        Elemento XML
    """
    elem = etree.Element(tag)
    for key, value in values.items():
        child = etree.SubElement(elem, key)
        if value is None:
            continue
        if isinstance(value, bool):
            child.text = serialize_bool(value)
        else:
            child.text = str(value)
    return elem


def _dynamic_from_xml(element: Element) -> Dict[str, Any]:
    """
    Lê um elemento dinâmico (``<tag><CHAVE>valor</CHAVE>...</tag>``).

    Os valores são mantidos como texto bruto, como em
    ``DynamicSerialization.ReadXml`` (.NET).

    Args:
        element: Elemento XML agrupador

    Returns:
        Dicionário com os valores por nome de campo
    """
    return {child.tag: child.text for child in element}


def _fieldset_to_xml(fieldset: Field) -> Element:
    """
    Serializa o ``fieldset`` de uma entidade (``<fieldset list="..."/>``).

    No .NET (``Entity.Fieldset``, ``[XmlElement("fieldset")]``) apenas o
    atributo ``list`` é definido por ``ServiceRequestExtensions``; o nome
    vazio não é serializado.

    Args:
        fieldset: Campo com a lista de campos

    Returns:
        Elemento XML ``fieldset``
    """
    elem = fieldset.to_xml()
    elem.tag = "fieldset"
    if not fieldset.name:
        elem.attrib.pop("name", None)
    return elem


class DataSetRow(BaseModel):
    """
    Linha de dados (``<dataRow>``) de um DataSet do CRUDServiceProvider.

    Porta de ``Sankhya-SDK-dotnet/Src/Sankhya/Service/DataRow.cs``: contém os
    campos locais (``<localFields>``) e as chaves (``<key>``) do registro a
    salvar. Não confundir com ``basic_types.DataRow`` (``<row>``).
    """

    model_config = ConfigDict(frozen=False)

    local_fields: Optional[Dict[str, Any]] = None
    keys: Optional[Dict[str, Any]] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("dataRow")
        # Mesma ordem de declaração do .NET: LocalFields e depois Keys
        if self.local_fields is not None:
            elem.append(_dynamic_to_xml("localFields", self.local_fields))
        if self.keys is not None:
            elem.append(_dynamic_to_xml("key", self.keys))
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "DataSetRow":
        """Deserializa de elemento XML."""
        local_fields_elem = element.find("localFields")
        keys_elem = element.find("key")
        return cls(
            local_fields=(
                _dynamic_from_xml(local_fields_elem)
                if local_fields_elem is not None
                else None
            ),
            keys=_dynamic_from_xml(keys_elem) if keys_elem is not None else None,
        )


class Entity(BaseModel):
    """
    Entidade de consulta Sankhya.
    
    Define a estrutura de uma entidade para operações CRUD,
    incluindo campos, critérios e configurações de busca.

    Os campos seguem ``Sankhya-SDK-dotnet/Src/Sankhya/Service/Entity.cs``
    (``include_presentation_fields`` -> ``getPresentations``,
    ``rows_limit`` -> ``rowsLimit``, ``data_set_id`` -> ``datasetid``,
    ``campos`` -> ``<campo>``, ``fieldset`` -> ``<fieldset>``,
    ``criteria`` -> ``<criterio>``, ``references_fetch`` ->
    ``<referenceFetch>`` e ``ids`` -> ``<id>``).
    """

    model_config = ConfigDict(frozen=False)

    name: str = ""
    root_entity: Optional[str] = None
    include_presentation_fields: Optional[bool] = None
    rows_limit: Optional[int] = None
    path: Optional[str] = None
    data_set_id: Optional[str] = None
    fields: List[Field] = PydanticField(default_factory=list)
    field_values: List[FieldValue] = PydanticField(default_factory=list)
    campos: List[FieldValue] = PydanticField(default_factory=list)
    fieldset: Optional[Field] = None
    criteria: List[Criteria] = PydanticField(default_factory=list)
    literal_criteria: Optional[LiteralCriteria] = None
    literal_criteria_sql: Optional[LiteralCriteriaSql] = None
    reference_fetch: Optional[ReferenceFetch] = None
    references_fetch: Optional[List[ReferenceFetch]] = None
    ids: List[Dict[str, Any]] = PydanticField(default_factory=list)
    order_by_expression: Optional[str] = None
    include_deleted: bool = False

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("entity")
        # Como no .NET (ShouldSerializeName), o nome só é serializado quando
        # definido: entidades de dataSet e de remoção não possuem nome.
        if self.name or "name" in self.model_fields_set:
            elem.set("name", self.name)
        
        if self.root_entity:
            elem.set("rootEntity", self.root_entity)
        if self.include_presentation_fields is not None:
            elem.set(
                "getPresentations",
                serialize_bool(
                    self.include_presentation_fields,
                    SankhyaConstants.BOOL_FORMAT_TRUE_FALSE,
                ),
            )
        if self.rows_limit is not None:
            elem.set("rowsLimit", str(self.rows_limit))
        if self.path is not None:
            elem.set("path", self.path)
        if self.data_set_id is not None:
            elem.set("datasetid", self.data_set_id)
        if self.include_deleted:
            elem.set("includeDeleted", serialize_bool(self.include_deleted, SankhyaConstants.BOOL_FORMAT_S_N))
        if self.order_by_expression:
            elem.set("orderByExpression", self.order_by_expression)
        
        # Fields
        if self.fields:
            fields_elem = etree.SubElement(elem, "fields")
            for field in self.fields:
                fields_elem.append(field.to_xml())
        
        # Field values (para insert/update)
        for fv in self.field_values:
            fv_elem = etree.SubElement(elem, fv.name)
            if fv.value is not None:
                fv_elem.text = fv.value
        
        # Campos (crud.save / crud.remove): <campo nome="...">valor</campo>
        for campo in self.campos:
            elem.append(campo.to_xml())

        # Fieldset (CRUDServiceProvider): <fieldset list="..."/>
        if self.fieldset is not None:
            elem.append(_fieldset_to_xml(self.fieldset))

        # Criteria: elementos <criterio> diretos, sem agrupador
        # (.NET: [XmlElement(ElementName = "criterio")] em um array)
        for crit in self.criteria:
            elem.append(crit.to_xml())
        
        # Literal criteria
        if self.literal_criteria:
            elem.append(self.literal_criteria.to_xml())
        
        if self.literal_criteria_sql:
            elem.append(self.literal_criteria_sql.to_xml())
        
        # Reference fetch
        references = list(self.references_fetch or [])
        if self.reference_fetch and not any(
            ref is self.reference_fetch for ref in references
        ):
            elem.append(self.reference_fetch.to_xml())
        for ref in references:
            elem.append(ref.to_xml())

        # Ids (CRUDServiceProvider.removeRecord): <id><CHAVE>valor</CHAVE></id>
        for entity_id in self.ids:
            elem.append(_dynamic_to_xml("id", entity_id))
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Entity":
        """Deserializa de elemento XML."""
        fields: List[Field] = []
        field_values: List[FieldValue] = []
        campos: List[FieldValue] = []
        fieldset: Optional[Field] = None
        criteria: List[Criteria] = []
        literal_criteria: Optional[LiteralCriteria] = None
        literal_criteria_sql: Optional[LiteralCriteriaSql] = None
        references_fetch: List[ReferenceFetch] = []
        ids: List[Dict[str, Any]] = []
        
        fields_elem = element.find("fields")
        if fields_elem is not None:
            for child in fields_elem:
                fields.append(Field.from_xml(child))
        
        for campo_elem in element.findall("campo"):
            campos.append(FieldValue.from_xml(campo_elem))

        fieldset_elem = element.find("fieldset")
        if fieldset_elem is not None:
            fieldset = Field.from_xml(fieldset_elem)

        for criterio_elem in element.findall("criterio"):
            criteria.append(Criteria.from_xml(criterio_elem))

        # Formato legado: <criteria><criterio/></criteria>
        criteria_elem = element.find("criteria")
        if criteria_elem is not None:
            for child in criteria_elem:
                criteria.append(Criteria.from_xml(child))
        
        lit_crit_elem = element.find("literalCriteria")
        if lit_crit_elem is not None:
            literal_criteria = LiteralCriteria.from_xml(lit_crit_elem)
        
        lit_crit_sql_elem = element.find("criterioLiteral")
        if lit_crit_sql_elem is not None:
            literal_criteria_sql = LiteralCriteriaSql.from_xml(lit_crit_sql_elem)
        
        for ref_fetch_elem in element.findall("referenceFetch"):
            references_fetch.append(ReferenceFetch.from_xml(ref_fetch_elem))

        for id_elem in element.findall("id"):
            ids.append(_dynamic_from_xml(id_elem))
        
        # Parse field values from direct child elements
        known_elements = {
            "fields", "criteria", "literalCriteria", 
            "criterioLiteral", "referenceFetch",
            "campo", "fieldset", "criterio", "id",
        }
        for child in element:
            if child.tag not in known_elements:
                field_values.append(FieldValue(
                    name=child.tag,
                    value=get_element_text(child) or None,
                ))
        
        include_presentation_fields_attr = get_element_attr(element, "getPresentations")
        name_attr = get_element_attr(element, "name")

        kwargs: Dict[str, Any] = {}
        if name_attr is not None:
            kwargs["name"] = name_attr

        return cls(
            **kwargs,
            root_entity=get_element_attr(element, "rootEntity"),
            include_presentation_fields=(
                deserialize_bool(include_presentation_fields_attr)
                if include_presentation_fields_attr is not None
                else None
            ),
            rows_limit=deserialize_optional_int(
                get_element_attr(element, "rowsLimit")
            ),
            path=get_element_attr(element, "path"),
            data_set_id=get_element_attr(element, "datasetid"),
            fields=fields,
            field_values=field_values,
            campos=campos,
            fieldset=fieldset,
            criteria=criteria,
            literal_criteria=literal_criteria,
            literal_criteria_sql=literal_criteria_sql,
            # O primeiro referenceFetch também fica em reference_fetch
            # (campo legado); a serialização não o duplica.
            reference_fetch=references_fetch[0] if references_fetch else None,
            references_fetch=references_fetch or None,
            ids=ids,
            order_by_expression=get_element_attr(element, "orderByExpression"),
            include_deleted=deserialize_bool(
                get_element_attr(element, "includeDeleted", "")
            ),
        )


class DataSet(BaseModel):
    """
    Conjunto de dados para consultas paginadas.
    
    Encapsula a entidade de consulta com configurações de paginação.

    Os campos seguem ``Sankhya-SDK-dotnet/Src/Sankhya/Service/DataSet.cs``
    (``include_presentation_fields`` -> ``includePresentationFields``,
    ``parallel_loader`` -> ``parallelLoader``, ``page_number`` ->
    ``pageNumber``, ``pager_id`` -> ``pagerID``, ``data_set_id`` ->
    ``datasetid``, ``data_rows`` -> ``<dataRow>``, ``literal_criteria`` ->
    ``<criteria>`` e ``entities`` -> ``<entity>``). ``entity`` é mantido
    por compatibilidade e é serializado como um ``<entity>`` adicional.
    """

    model_config = ConfigDict(frozen=False)

    root_entity: Optional[str] = None
    include_presentation: bool = False
    include_presentation_fields: Optional[bool] = None
    parallel_loader: bool = False
    database_fetch_size: Optional[int] = None
    rows_limit: Optional[int] = None
    page_number: Optional[int] = None
    pager_id: Optional[str] = None
    data_set_id: Optional[str] = None
    data_source: Optional[str] = None
    entity: Optional[Entity] = None
    entities: List[Entity] = PydanticField(default_factory=list)
    data_rows: List[DataSetRow] = PydanticField(default_factory=list)
    rows: List[DataRow] = PydanticField(default_factory=list)
    literal_criteria: Optional[LiteralCriteria] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("dataSet")
        
        if self.root_entity:
            elem.set("rootEntity", self.root_entity)
        if self.include_presentation:
            elem.set("includePresentation", serialize_bool(self.include_presentation, SankhyaConstants.BOOL_FORMAT_S_N))
        if self.include_presentation_fields is not None:
            # .NET: IncludePresentationFieldsInternal => ToString("S", "N")
            elem.set(
                "includePresentationFields",
                serialize_bool(
                    self.include_presentation_fields,
                    SankhyaConstants.BOOL_FORMAT_S_N,
                ),
            )
        if self.parallel_loader or "parallel_loader" in self.model_fields_set:
            # .NET: ParallelLoaderInternal => ToString("true", "false")
            elem.set(
                "parallelLoader",
                serialize_bool(
                    self.parallel_loader, SankhyaConstants.BOOL_FORMAT_TRUE_FALSE
                ),
            )
        if self.database_fetch_size is not None:
            elem.set("databaseFetchSize", str(self.database_fetch_size))
        if self.rows_limit is not None:
            elem.set("rowsLimit", str(self.rows_limit))
        if self.page_number is not None:
            elem.set("pageNumber", str(self.page_number))
        if self.pager_id is not None:
            elem.set(SankhyaConstants.PAGER_ID, self.pager_id)
        if self.data_set_id is not None:
            elem.set("datasetid", self.data_set_id)
        if self.data_source:
            elem.set("dataSource", self.data_source)
        
        # Mesma ordem de declaração do .NET: dataRow, criteria, entity
        for data_row in self.data_rows:
            elem.append(data_row.to_xml())

        if self.literal_criteria:
            # .NET: [XmlElement("criteria")] public LiteralCriteria LiteralCriteria
            criteria_elem = self.literal_criteria.to_xml()
            criteria_elem.tag = "criteria"
            elem.append(criteria_elem)

        if self.entity and not any(e is self.entity for e in self.entities):
            elem.append(self.entity.to_xml())

        for entity in self.entities:
            elem.append(entity.to_xml())
        
        if self.rows:
            for row in self.rows:
                elem.append(row.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "DataSet":
        """Deserializa de elemento XML."""
        entities: List[Entity] = []
        data_rows: List[DataSetRow] = []
        rows: List[DataRow] = []
        literal_criteria: Optional[LiteralCriteria] = None
        
        for entity_elem in element.findall("entity"):
            entities.append(Entity.from_xml(entity_elem))

        for data_row_elem in element.findall("dataRow"):
            data_rows.append(DataSetRow.from_xml(data_row_elem))
        
        for row_elem in element.findall("row"):
            rows.append(DataRow.from_xml(row_elem))
        
        # Formato .NET (<criteria>) e formato legado (<literalCriteria>)
        lit_crit_elem = element.find("criteria")
        if lit_crit_elem is None:
            lit_crit_elem = element.find("literalCriteria")
        if lit_crit_elem is not None:
            literal_criteria = LiteralCriteria.from_xml(lit_crit_elem)
        
        db_fetch_size = deserialize_optional_int(
            get_element_attr(element, "databaseFetchSize")
        )
        rows_limit = deserialize_optional_int(
            get_element_attr(element, "rowsLimit")
        )
        page_number = deserialize_optional_int(
            get_element_attr(element, "pageNumber")
        )
        include_presentation_fields_attr = get_element_attr(
            element, "includePresentationFields"
        )
        parallel_loader_attr = get_element_attr(element, "parallelLoader")

        kwargs: Dict[str, Any] = {}
        if parallel_loader_attr is not None:
            kwargs["parallel_loader"] = deserialize_bool(parallel_loader_attr)
        
        return cls(
            **kwargs,
            root_entity=get_element_attr(element, "rootEntity"),
            include_presentation=deserialize_bool(
                get_element_attr(element, "includePresentation", "")
            ),
            include_presentation_fields=(
                deserialize_bool(include_presentation_fields_attr)
                if include_presentation_fields_attr is not None
                else None
            ),
            database_fetch_size=db_fetch_size,
            rows_limit=rows_limit,
            page_number=page_number,
            pager_id=get_element_attr(element, SankhyaConstants.PAGER_ID),
            data_set_id=get_element_attr(element, "datasetid"),
            data_source=get_element_attr(element, "dataSource"),
            # A primeira entidade também fica em entity (campo legado);
            # a serialização não a duplica.
            entity=entities[0] if entities else None,
            entities=entities,
            data_rows=data_rows,
            rows=rows,
            literal_criteria=literal_criteria,
        )


class EntityDynamic(BaseModel):
    """
    Entidade com serialização dinâmica.
    
    Usa dicionário para campos quando a estrutura é desconhecida.
    """

    model_config = ConfigDict(frozen=False, extra="allow")

    name: str = ""
    fields: Dict[str, Any] = PydanticField(default_factory=dict)
    metadata: Dict[str, Any] = PydanticField(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Acesso a campos por chave."""
        return self.fields.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Define valor de campo."""
        self.fields[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de campo com default."""
        return self.fields.get(key, default)

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element(self.name or "entity")
        
        for key, value in self.fields.items():
            child = etree.SubElement(elem, key)
            if value is not None:
                if isinstance(value, bool):
                    child.text = serialize_bool(value)
                else:
                    child.text = str(value)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "EntityDynamic":
        """Deserializa de elemento XML."""
        fields: Dict[str, Any] = {}
        metadata: Dict[str, Any] = dict(element.attrib)
        
        for child in element:
            text = get_element_text(child)
            if text:
                # Tenta converter para tipos primitivos
                if text.lower() in ("true", "false"):
                    fields[child.tag] = text.lower() == "true"
                else:
                    try:
                        fields[child.tag] = int(text)
                    except ValueError:
                        try:
                            fields[child.tag] = float(text)
                        except ValueError:
                            fields[child.tag] = text
            else:
                fields[child.tag] = None
        
        return cls(
            name=element.tag,
            fields=fields,
            metadata=metadata,
        )


class CrudServiceEntities(BaseModel):
    """
    Container para entidades CRUD (em português).
    
    Usado em respostas de serviços de CRUD com nomenclatura PT-BR.
    """

    model_config = ConfigDict(frozen=False)

    entities: List[EntityDynamic] = PydanticField(default_factory=list)
    total: Optional[int] = None
    total_pages: Optional[int] = None
    pager_id: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element(SankhyaConstants.ENTITIES_PT_BR)
        
        if self.total is not None:
            elem.set(SankhyaConstants.TOTAL, str(self.total))
        if self.total_pages is not None:
            elem.set(SankhyaConstants.TOTAL_PAGES, str(self.total_pages))
        if self.pager_id:
            elem.set(SankhyaConstants.PAGER_ID, self.pager_id)
        
        for entity in self.entities:
            entity_elem = entity.to_xml()
            entity_elem.tag = SankhyaConstants.ENTITY_PT_BR
            elem.append(entity_elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "CrudServiceEntities":
        """Deserializa de elemento XML."""
        entities: List[EntityDynamic] = []
        
        # Procura por elementos 'entidade'
        for child in element.findall(SankhyaConstants.ENTITY_PT_BR):
            entities.append(EntityDynamic.from_xml(child))
        
        total = deserialize_optional_int(
            get_element_attr(element, SankhyaConstants.TOTAL)
        )
        total_pages = deserialize_optional_int(
            get_element_attr(element, SankhyaConstants.TOTAL_PAGES)
        )
        
        return cls(
            entities=entities,
            total=total,
            total_pages=total_pages,
            pager_id=get_element_attr(element, SankhyaConstants.PAGER_ID),
        )


class CrudServiceProviderEntities(BaseModel):
    """
    Container para entidades CRUD (em inglês).
    
    Usado em respostas de serviços de CRUD com nomenclatura EN.
    """

    model_config = ConfigDict(frozen=False)

    entities: List[EntityDynamic] = PydanticField(default_factory=list)
    total: Optional[int] = None
    total_pages: Optional[int] = None
    pager_id: Optional[str] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element(SankhyaConstants.ENTITIES_EN)
        
        if self.total is not None:
            elem.set(SankhyaConstants.TOTAL, str(self.total))
        if self.total_pages is not None:
            elem.set(SankhyaConstants.TOTAL_PAGES, str(self.total_pages))
        if self.pager_id:
            elem.set(SankhyaConstants.PAGER_ID, self.pager_id)
        
        for entity in self.entities:
            entity_elem = entity.to_xml()
            entity_elem.tag = SankhyaConstants.ENTITY_EN
            elem.append(entity_elem)
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "CrudServiceProviderEntities":
        """Deserializa de elemento XML."""
        entities: List[EntityDynamic] = []
        
        # Procura por elementos 'entity'
        for child in element.findall(SankhyaConstants.ENTITY_EN):
            entities.append(EntityDynamic.from_xml(child))
        
        total = deserialize_optional_int(
            get_element_attr(element, SankhyaConstants.TOTAL)
        )
        total_pages = deserialize_optional_int(
            get_element_attr(element, SankhyaConstants.TOTAL_PAGES)
        )
        
        return cls(
            entities=entities,
            total=total,
            total_pages=total_pages,
            pager_id=get_element_attr(element, SankhyaConstants.PAGER_ID),
        )
