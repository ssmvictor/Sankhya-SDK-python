import pytest
from typing import Optional
from pydantic import BaseModel, Field
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


def test_chained_decorator_kwargs_are_kept_by_pydantic():
    # kwargs applied to an existing field (field=...) must survive the model build
    class TestModel(BaseModel):
        document: Optional[str] = entity_custom_data(
            max_length=14, field=entity_element("CGC_CPF"), default=None
        )

    field_info = TestModel.model_fields["document"]
    assert field_info.is_required() is False
    assert field_info.default is None
    assert field_info.json_schema_extra["element"].element_name == "CGC_CPF"
    assert field_info.json_schema_extra["custom_data"].max_length == 14
    assert TestModel().document is None


def test_decorator_on_plain_field_keeps_metadata():
    # json_schema_extra created by the decorator on a plain Field must not be lost
    class TestModel(BaseModel):
        id: int = entity_key(Field(default=0))

    field_info = TestModel.model_fields["id"]
    assert field_info.json_schema_extra["is_key"] is True


def test_entity_ignore_on_chained_field_excludes_from_dump():
    class TestModel(BaseModel):
        code: int = entity_element("CODIGO", default=1)
        internal: Optional[str] = entity_ignore(entity_element("INTERNO", default=None))

    field_info = TestModel.model_fields["internal"]
    assert field_info.exclude is True
    assert field_info.json_schema_extra["is_ignored"] is True
    assert field_info.json_schema_extra["element"].element_name == "INTERNO"
    assert TestModel(internal="x").model_dump() == {"code": 1}
