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


class Entity(BaseModel):
    """
    Entidade de consulta Sankhya.
    
    Define a estrutura de uma entidade para operações CRUD,
    incluindo campos, critérios e configurações de busca.
    """

    model_config = ConfigDict(frozen=False)

    name: str = ""
    root_entity: Optional[str] = None
    path: Optional[str] = None
    fields: List[Field] = PydanticField(default_factory=list)
    field_values: List[FieldValue] = PydanticField(default_factory=list)
    criteria: List[Criteria] = PydanticField(default_factory=list)
    literal_criteria: Optional[LiteralCriteria] = None
    literal_criteria_sql: Optional[LiteralCriteriaSql] = None
    reference_fetch: Optional[ReferenceFetch] = None
    order_by_expression: Optional[str] = None
    include_deleted: bool = False

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("entity")
        elem.set("name", self.name)
        
        if self.root_entity:
            elem.set("rootEntity", self.root_entity)
        if self.path:
            elem.set("path", self.path)
        if self.include_deleted:
            elem.set("includeDeleted", serialize_bool(self.include_deleted))
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
        
        # Criteria
        if self.criteria:
            criteria_elem = etree.SubElement(elem, "criteria")
            for crit in self.criteria:
                criteria_elem.append(crit.to_xml())
        
        # Literal criteria
        if self.literal_criteria:
            elem.append(self.literal_criteria.to_xml())
        
        if self.literal_criteria_sql:
            elem.append(self.literal_criteria_sql.to_xml())
        
        # Reference fetch
        if self.reference_fetch:
            elem.append(self.reference_fetch.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "Entity":
        """Deserializa de elemento XML."""
        fields: List[Field] = []
        field_values: List[FieldValue] = []
        criteria: List[Criteria] = []
        literal_criteria: Optional[LiteralCriteria] = None
        literal_criteria_sql: Optional[LiteralCriteriaSql] = None
        reference_fetch: Optional[ReferenceFetch] = None
        
        fields_elem = element.find("fields")
        if fields_elem is not None:
            for child in fields_elem:
                fields.append(Field.from_xml(child))
        
        criteria_elem = element.find("criteria")
        if criteria_elem is not None:
            for child in criteria_elem:
                criteria.append(Criteria.from_xml(child))
        
        lit_crit_elem = element.find("literalCriteria")
        if lit_crit_elem is not None:
            literal_criteria = LiteralCriteria.from_xml(lit_crit_elem)
        
        lit_crit_sql_elem = element.find("criterioLiteralSql")
        if lit_crit_sql_elem is not None:
            literal_criteria_sql = LiteralCriteriaSql.from_xml(lit_crit_sql_elem)
        
        ref_fetch_elem = element.find("referenceFetch")
        if ref_fetch_elem is not None:
            reference_fetch = ReferenceFetch.from_xml(ref_fetch_elem)
        
        # Parse field values from direct child elements
        known_elements = {
            "fields", "criteria", "literalCriteria", 
            "criterioLiteralSql", "referenceFetch"
        }
        for child in element:
            if child.tag not in known_elements:
                field_values.append(FieldValue(
                    name=child.tag,
                    value=get_element_text(child) or None,
                ))
        
        return cls(
            name=get_element_attr(element, "name", ""),
            root_entity=get_element_attr(element, "rootEntity"),
            path=get_element_attr(element, "path"),
            fields=fields,
            field_values=field_values,
            criteria=criteria,
            literal_criteria=literal_criteria,
            literal_criteria_sql=literal_criteria_sql,
            reference_fetch=reference_fetch,
            order_by_expression=get_element_attr(element, "orderByExpression"),
            include_deleted=deserialize_bool(
                get_element_attr(element, "includeDeleted", "")
            ),
        )


class DataSet(BaseModel):
    """
    Conjunto de dados para consultas paginadas.
    
    Encapsula a entidade de consulta com configurações de paginação.
    """

    model_config = ConfigDict(frozen=False)

    root_entity: Optional[str] = None
    include_presentation: bool = False
    parallel_loader: bool = False
    database_fetch_size: Optional[int] = None
    rows_limit: Optional[int] = None
    data_source: Optional[str] = None
    entity: Optional[Entity] = None
    rows: List[DataRow] = PydanticField(default_factory=list)
    literal_criteria: Optional[LiteralCriteria] = None

    def to_xml(self) -> Element:
        """Serializa para elemento XML."""
        elem = etree.Element("dataSet")
        
        if self.root_entity:
            elem.set("rootEntity", self.root_entity)
        if self.include_presentation:
            elem.set("includePresentation", serialize_bool(self.include_presentation))
        if self.parallel_loader:
            elem.set("parallelLoader", serialize_bool(self.parallel_loader))
        if self.database_fetch_size is not None:
            elem.set("databaseFetchSize", str(self.database_fetch_size))
        if self.rows_limit is not None:
            elem.set("rowsLimit", str(self.rows_limit))
        if self.data_source:
            elem.set("dataSource", self.data_source)
        
        if self.entity:
            elem.append(self.entity.to_xml())
        
        if self.rows:
            for row in self.rows:
                elem.append(row.to_xml())
        
        if self.literal_criteria:
            elem.append(self.literal_criteria.to_xml())
        
        return elem

    @classmethod
    def from_xml(cls, element: Element) -> "DataSet":
        """Deserializa de elemento XML."""
        entity: Optional[Entity] = None
        rows: List[DataRow] = []
        literal_criteria: Optional[LiteralCriteria] = None
        
        entity_elem = element.find("entity")
        if entity_elem is not None:
            entity = Entity.from_xml(entity_elem)
        
        for row_elem in element.findall("row"):
            rows.append(DataRow.from_xml(row_elem))
        
        lit_crit_elem = element.find("literalCriteria")
        if lit_crit_elem is not None:
            literal_criteria = LiteralCriteria.from_xml(lit_crit_elem)
        
        db_fetch_size = deserialize_optional_int(
            get_element_attr(element, "databaseFetchSize")
        )
        rows_limit = deserialize_optional_int(
            get_element_attr(element, "rowsLimit")
        )
        
        return cls(
            root_entity=get_element_attr(element, "rootEntity"),
            include_presentation=deserialize_bool(
                get_element_attr(element, "includePresentation", "")
            ),
            parallel_loader=deserialize_bool(
                get_element_attr(element, "parallelLoader", "")
            ),
            database_fetch_size=db_fetch_size,
            rows_limit=rows_limit,
            data_source=get_element_attr(element, "dataSource"),
            entity=entity,
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
