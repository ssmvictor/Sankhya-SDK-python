from pydantic import BaseModel
from sankhya_sdk.attributes.decorators import entity, entity_key, entity_element
from sankhya_sdk.attributes.reflection import (
    get_entity_name,
    get_field_metadata,
    is_entity_key,
    extract_keys,
)
from sankhya_sdk.models.base import EntityBase


def test_get_entity_name():
    @entity("Partner")
    class Partner(BaseModel):
        pass

    assert get_entity_name(Partner) == "Partner"


def test_get_entity_name_no_decorator():
    class SimpleModel(BaseModel):
        pass

    assert get_entity_name(SimpleModel) == "SimpleModel"


def test_get_field_metadata():
    class TestModel(BaseModel):
        id: int = entity_key(entity_element("CODPARC"))

    field_info = TestModel.model_fields["id"]
    metadata = get_field_metadata(field_info)
    assert metadata.is_key is True
    assert metadata.element.element_name == "CODPARC"


def test_extract_keys():
    @entity("Partner")
    class Partner(EntityBase):
        id: int = entity_key(entity_element("CODPARC"))
        name: str = entity_element("NOMEPARC")

    partner = Partner(id=1, name="Test")
    result = extract_keys(partner)

    assert result.entity_name == "Partner"
    assert len(result.keys) == 1
    assert result.keys[0].name == "CODPARC"
    assert result.keys[0].value == "1"
    assert any(f.name == "NOMEPARC" for f in result.fields)
