from pydantic import Field, BaseModel
from sankhya_sdk.value_objects.parse_property_model import ParsePropertyModel
from sankhya_sdk.attributes.metadata import EntityCustomDataMetadata
from sankhya_sdk.attributes.decorators import (
    entity_element,
    entity_key,
    entity_reference,
    entity_ignore,
    entity_custom_data,
)


def test_parse_property_model_defaults():
    model = ParsePropertyModel()
    assert model.is_criteria is True
    assert model.is_ignored is False
    assert model.is_entity_key is False
    assert model.is_entity_reference is False


def test_parse_property_model_all_fields():
    custom_data = EntityCustomDataMetadata(max_length=100)
    model = ParsePropertyModel(
        is_ignored=True,
        is_criteria=False,
        is_entity_key=True,
        is_entity_reference=True,
        is_entity_reference_inline=True,
        ignore_entity_reference_inline=True,
        property_name="test_prop",
        custom_relation_name="rel_name",
        custom_data=custom_data,
    )
    assert model.is_ignored is True
    assert model.is_criteria is False
    assert model.is_entity_key is True
    assert model.is_entity_reference is True
    assert model.is_entity_reference_inline is True
    assert model.ignore_entity_reference_inline is True
    assert model.property_name == "test_prop"
    assert model.custom_relation_name == "rel_name"
    assert model.custom_data == custom_data


def test_parse_property_model_from_field_info():
    class TestEntity(BaseModel):
        id: int = entity_key(entity_element("ID"))
        name: str = entity_element("NOME")
        ref_id: int = entity_reference("CustomRel", entity_element("REFID"))
        ignored: str = entity_ignore()
        with_custom_data: str = entity_custom_data(max_length=50)

    # Test ID
    id_model = ParsePropertyModel.from_field_info("id", TestEntity.model_fields["id"])
    assert id_model.property_name == "ID"
    assert id_model.is_entity_key is True
    assert id_model.is_ignored is False

    # Test Name
    name_model = ParsePropertyModel.from_field_info(
        "name", TestEntity.model_fields["name"]
    )
    assert name_model.property_name == "NOME"
    assert name_model.is_entity_key is False

    # Test Ref
    ref_model = ParsePropertyModel.from_field_info(
        "ref_id", TestEntity.model_fields["ref_id"]
    )
    assert ref_model.property_name == "REFID"
    assert ref_model.is_entity_reference is True
    assert ref_model.is_entity_reference_inline is True
    assert ref_model.ignore_entity_reference_inline is False
    assert ref_model.custom_relation_name == "CustomRel"

    # Test Ref with ignore inline
    class TestEntityIgnoreInline(BaseModel):
        ref_id: int = entity_reference(
            "CustomRel", entity_element("REFID", ignore_inline_reference=True)
        )

    ref_ignore_model = ParsePropertyModel.from_field_info(
        "ref_id", TestEntityIgnoreInline.model_fields["ref_id"]
    )
    assert ref_ignore_model.is_entity_reference is True
    assert ref_ignore_model.is_entity_reference_inline is False
    assert ref_ignore_model.ignore_entity_reference_inline is True

    # Test Ignored
    ignored_model = ParsePropertyModel.from_field_info(
        "ignored", TestEntity.model_fields["ignored"]
    )
    assert ignored_model.is_ignored is True

    # Test Custom Data
    cd_model = ParsePropertyModel.from_field_info(
        "with_custom_data", TestEntity.model_fields["with_custom_data"]
    )
    assert cd_model.custom_data is not None
    assert cd_model.custom_data.max_length == 50
