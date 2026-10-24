"""
Testes unitários para entity_types (Entity, DataSet, DataSetRow).

Os formatos XML esperados seguem os contratos de serialização do SDK .NET
(Sankhya-SDK-dotnet/Src/Sankhya/Service/DataSet.cs, Entity.cs e DataRow.cs).
"""

from lxml import etree

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.service.basic_types import (
    Criteria,
    Field,
    FieldValue,
    LiteralCriteria,
)
from sankhya_sdk.models.service.entity_types import DataSet, DataSetRow, Entity
from sankhya_sdk.models.service.service_request import ServiceRequest


def _request_body(request: ServiceRequest) -> etree._Element:
    """Serializa a requisição e retorna o elemento requestBody."""
    root = etree.fromstring(request.to_xml_bytes())
    body = root.find("requestBody")
    assert body is not None
    return body


class TestDataSetPagerId:
    """DataSet.pager_id (.NET DataSet.cs: [XmlAttribute("pagerID")])."""

    def test_pager_id_serialized_as_attribute(self):
        data_set = DataSet(root_entity="Parceiro", pager_id="PAGER-42")

        xml = data_set.to_xml()

        assert xml.get("pagerID") == "PAGER-42"

    def test_pager_id_not_serialized_when_unset(self):
        xml = DataSet(root_entity="Parceiro").to_xml()

        assert "pagerID" not in xml.attrib

    def test_pager_id_assignment(self):
        """O wrapper paginado atribui o pagerID depois de criar o DataSet."""
        data_set = DataSet(root_entity="Parceiro")
        data_set.pager_id = "PAGER-1"

        assert data_set.to_xml().get("pagerID") == "PAGER-1"

    def test_pager_id_from_xml(self):
        element = etree.fromstring('<dataSet rootEntity="Parceiro" pagerID="ABC"/>')

        assert DataSet.from_xml(element).pager_id == "ABC"


class TestDataSetCriteria:
    """DataSet.literal_criteria (.NET DataSet.cs: [XmlElement("criteria")])."""

    def test_literal_criteria_serialized_as_criteria_element(self):
        data_set = DataSet(
            root_entity="Parceiro",
            literal_criteria=LiteralCriteria(expression="CODPARC = 1"),
        )

        xml = data_set.to_xml()

        assert xml.find("literalCriteria") is None
        criteria = xml.find("criteria")
        assert criteria is not None
        assert criteria.findtext("expression") == "CODPARC = 1"

    def test_literal_criteria_from_criteria_element(self):
        element = etree.fromstring(
            "<dataSet><criteria><expression>CODPARC = 2</expression></criteria></dataSet>"
        )

        parsed = DataSet.from_xml(element)

        assert parsed.literal_criteria is not None
        assert parsed.literal_criteria.expression == "CODPARC = 2"

    def test_literal_criteria_from_legacy_element(self):
        element = etree.fromstring(
            "<dataSet><literalCriteria><expression>CODPARC = 3</expression>"
            "</literalCriteria></dataSet>"
        )

        parsed = DataSet.from_xml(element)

        assert parsed.literal_criteria is not None
        assert parsed.literal_criteria.expression == "CODPARC = 3"


class TestDataSetCrudServiceProviderShape:
    """Formato do dataSet montado por ServiceRequestExtensions.HandleService (.NET)."""

    def test_find_data_set_attributes_and_entities(self):
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body.data_set = DataSet(
            root_entity="Parceiro",
            include_presentation_fields=False,
            parallel_loader=True,
            data_set_id="1700000000_1",
            entities=[
                Entity(path="", fieldset=Field(name="", list="CODPARC,NOMEPARC")),
                Entity(path="Cidade", fieldset=Field(name="", list="NOMECID")),
            ],
        )

        data_set = _request_body(request).find("dataSet")

        assert data_set is not None
        assert data_set.get("rootEntity") == "Parceiro"
        # IncludePresentationFieldsInternal => "S"/"N"
        assert data_set.get("includePresentationFields") == "N"
        # ParallelLoaderInternal => "true"/"false"
        assert data_set.get("parallelLoader") == "true"
        assert data_set.get("datasetid") == "1700000000_1"
        entities = data_set.findall("entity")
        assert [e.get("path") for e in entities] == ["", "Cidade"]
        # Entidades do dataSet não possuem nome
        assert all("name" not in e.attrib for e in entities)
        fieldsets = [e.find("fieldset") for e in entities]
        assert [f.get("list") for f in fieldsets] == ["CODPARC,NOMEPARC", "NOMECID"]
        assert all("name" not in f.attrib for f in fieldsets)

    def test_parallel_loader_false_serialized_when_explicitly_set(self):
        assert DataSet(parallel_loader=False).to_xml().get("parallelLoader") == "false"
        assert "parallelLoader" not in DataSet().to_xml().attrib

    def test_save_data_set_data_rows(self):
        data_set = DataSet(
            root_entity="Parceiro",
            data_rows=[
                DataSetRow(
                    keys={"CODPARC": "1"},
                    local_fields={"NOMEPARC": "Cliente", "CGC_CPF": "01234567890"},
                )
            ],
        )

        xml = data_set.to_xml()

        data_row = xml.find("dataRow")
        assert data_row is not None
        # Ordem do .NET (DataRow.cs): localFields e depois key
        assert [child.tag for child in data_row] == ["localFields", "key"]
        assert data_row.findtext("localFields/NOMEPARC") == "Cliente"
        assert data_row.findtext("localFields/CGC_CPF") == "01234567890"
        assert data_row.findtext("key/CODPARC") == "1"

    def test_data_row_with_empty_keys(self):
        """Inclusão sem chave: o .NET envia Keys = new() (elemento vazio)."""
        xml = DataSetRow(keys={}, local_fields={"NOMEPARC": "Novo"}).to_xml()

        key = xml.find("key")
        assert key is not None
        assert len(key) == 0

    def test_element_order(self):
        """Ordem dos elementos conforme a declaração em DataSet.cs."""
        data_set = DataSet(
            data_rows=[DataSetRow(keys={}, local_fields={})],
            literal_criteria=LiteralCriteria(expression="1 = 1"),
            entities=[Entity(path="")],
        )

        assert [child.tag for child in data_set.to_xml()] == [
            "dataRow",
            "criteria",
            "entity",
        ]

    def test_round_trip(self):
        data_set = DataSet(
            root_entity="Parceiro",
            include_presentation_fields=False,
            parallel_loader=True,
            page_number=2,
            pager_id="P1",
            data_set_id="1_1",
            entities=[Entity(path="", fieldset=Field(name="", list="CODPARC"))],
            data_rows=[DataSetRow(keys={"CODPARC": "1"}, local_fields={"NOMEPARC": "X"})],
            literal_criteria=LiteralCriteria(expression="CODPARC = 1"),
        )
        original = etree.tostring(data_set.to_xml())

        parsed = DataSet.from_xml(data_set.to_xml())

        assert etree.tostring(parsed.to_xml()) == original
        assert parsed.pager_id == "P1"
        assert parsed.data_set_id == "1_1"
        assert parsed.include_presentation_fields is False
        assert parsed.parallel_loader is True
        assert parsed.data_rows[0].keys == {"CODPARC": "1"}
        assert parsed.data_rows[0].local_fields == {"NOMEPARC": "X"}
        # Campo legado continua apontando para a primeira entidade
        assert parsed.entity is parsed.entities[0]

    def test_legacy_entity_still_serialized(self):
        data_set = DataSet(
            root_entity="Produto",
            entity=Entity(name="Produto", fields=[Field(name="CODPROD")]),
        )

        entities = data_set.to_xml().findall("entity")

        assert len(entities) == 1
        assert entities[0].get("name") == "Produto"


class TestEntityCriteria:
    """Entity.criteria (.NET Entity.cs: [XmlElement(ElementName = "criterio")])."""

    def test_criteria_serialized_as_flat_criterio_elements(self):
        entity = Entity(
            name="Parceiro",
            criteria=[
                Criteria(name="CODPARC", value="1"),
                Criteria(name="NOMEPARC", value="X"),
            ],
        )

        xml = entity.to_xml()

        assert xml.find("criteria") is None
        criterios = xml.findall("criterio")
        assert [c.get("nome") for c in criterios] == ["CODPARC", "NOMEPARC"]

    def test_criteria_from_flat_and_legacy_elements(self):
        flat = etree.fromstring(
            '<entity name="Parceiro"><criterio nome="CODPARC">1</criterio></entity>'
        )
        legacy = etree.fromstring(
            '<entity name="Parceiro"><criteria><criterio nome="CODPARC">1</criterio>'
            "</criteria></entity>"
        )

        for element in (flat, legacy):
            parsed = Entity.from_xml(element)
            assert [c.name for c in parsed.criteria] == ["CODPARC"]
            assert parsed.field_values == []


class TestEntityCrudFields:
    """Campos de Entity usados por ServiceRequestExtensions (.NET Entity.cs)."""

    def test_remove_entity_shape(self):
        """CrudServiceRemove: <entity rootEntity datasetid><id><CHAVE/></id></entity>."""
        entity = Entity(
            root_entity="Parceiro",
            data_set_id="1700000000_2",
            ids=[{"CODPARC": "1"}, {"CODPARC": "2"}],
        )

        xml = entity.to_xml()

        assert "name" not in xml.attrib
        assert xml.get("rootEntity") == "Parceiro"
        assert xml.get("datasetid") == "1700000000_2"
        assert [i.findtext("CODPARC") for i in xml.findall("id")] == ["1", "2"]

    def test_find_entity_attributes(self):
        entity = Entity(
            name="Parceiro",
            include_presentation_fields=False,
            rows_limit=10,
            fields=[Field(name="CODPARC")],
        )

        xml = entity.to_xml()

        assert xml.get("name") == "Parceiro"
        # bool em [XmlAttribute] é serializado como "true"/"false"
        assert xml.get("getPresentations") == "false"
        assert xml.get("rowsLimit") == "10"
        assert xml.find("fields/field").get("name") == "CODPARC"

    def test_attributes_assignable_after_creation(self):
        """ServiceRequestExtensions._apply_options_to_request altera esses campos."""
        entity = Entity(name="Parceiro")
        entity.include_presentation_fields = True
        entity.rows_limit = 5
        entity.references_fetch = None

        xml = entity.to_xml()

        assert xml.get("getPresentations") == "true"
        assert xml.get("rowsLimit") == "5"

    def test_campos(self):
        entity = Entity(
            name="Parceiro",
            campos=[FieldValue(name="CODPARC", value="1"), FieldValue(name="NOMEPARC", value="X")],
        )

        xml = entity.to_xml()

        campos = xml.findall("campo")
        assert [(c.get("nome"), c.text) for c in campos] == [("CODPARC", "1"), ("NOMEPARC", "X")]

    def test_explicit_empty_name_is_serialized(self):
        assert Entity(name="").to_xml().get("name") == ""
        assert "name" not in Entity().to_xml().attrib

    def test_round_trip(self):
        entity = Entity(
            root_entity="Parceiro",
            data_set_id="1_2",
            include_presentation_fields=False,
            rows_limit=3,
            campos=[FieldValue(name="CODPARC", value="1")],
            fieldset=Field(name="", list="*"),
            criteria=[Criteria(name="CODPARC", value="1")],
            ids=[{"CODPARC": "1"}],
        )
        original = etree.tostring(entity.to_xml())

        parsed = Entity.from_xml(entity.to_xml())

        assert etree.tostring(parsed.to_xml()) == original
        assert parsed.ids == [{"CODPARC": "1"}]
        assert parsed.data_set_id == "1_2"
        assert parsed.include_presentation_fields is False
        assert parsed.rows_limit == 3
        assert parsed.fieldset is not None and parsed.fieldset.list == "*"
        assert parsed.field_values == []
