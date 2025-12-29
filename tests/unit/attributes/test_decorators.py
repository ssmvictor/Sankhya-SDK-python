import pytest
from pydantic import BaseModel
from sankhya_sdk.attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_reference,
    entity_ignore,
    entity_custom_data,
)
from sankhya_sdk.attributes.metadata import (
    EntityMetadata,
    EntityElementMetadata,
    EntityReferenceMetadata,
    EntityCustomDataMetadata,
)


def test_entity_decorator():
    @entity("Partner")
    class Partner(BaseModel):
        pass

    assert hasattr(Partner, "__entity_metadata__")
    assert isinstance(Partner.__entity_metadata__, EntityMetadata)
    assert Partner.__entity_metadata__.name == "Partner"


def test_entity_key_decorator():
    class TestModel(BaseModel):
        id: int = entity_key()

    field_info = TestModel.model_fields["id"]
    assert field_info.json_schema_extra["is_key"] is True


def test_entity_element_decorator():
    class TestModel(BaseModel):
        name: str = entity_element("NOMEPARC")

    field_info = TestModel.model_fields["name"]
    element_metadata = field_info.json_schema_extra["element"]
    assert isinstance(element_metadata, EntityElementMetadata)
    assert element_metadata.element_name == "NOMEPARC"


def test_chained_decorators():
    class TestModel(BaseModel):
        id: int = entity_key(entity_element("CODPARC"))

    field_info = TestModel.model_fields["id"]
    assert field_info.json_schema_extra["is_key"] is True
    assert field_info.json_schema_extra["element"].element_name == "CODPARC"


def test_entity_ignore_decorator():
    class TestModel(BaseModel):
        internal: str = entity_ignore()

    field_info = TestModel.model_fields["internal"]
    assert field_info.exclude is True
    assert field_info.json_schema_extra["is_ignored"] is True


def test_entity_custom_data_decorator():
    class TestModel(BaseModel):
        code: str = entity_custom_data(max_length=10)

    field_info = TestModel.model_fields["code"]
    custom_data = field_info.json_schema_extra["custom_data"]
    assert isinstance(custom_data, EntityCustomDataMetadata)
    assert custom_data.max_length == 10
