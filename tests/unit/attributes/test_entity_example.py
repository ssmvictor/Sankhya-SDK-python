import pytest
from typing import Optional
from pydantic import ValidationError
from sankhya_sdk.attributes.decorators import (
    entity,
    entity_key,
    entity_element,
    entity_custom_data,
    entity_ignore,
)
from sankhya_sdk.models.base import EntityBase


@entity("Parceiro")
class Partner(EntityBase):
    code: Optional[int] = entity_key(entity_element("CODPARC"))
    name: str = entity_element("NOMEPARC")
    document: Optional[str] = entity_custom_data(max_length=14, field=entity_element("CGC_CPF"), default=None)
    internal_notes: Optional[str] = entity_ignore(default=None)


def test_partner_entity_behavior():
    # Test initialization
    partner = Partner(code=1, name="Test Partner")
    assert partner.code == 1
    assert partner.name == "Test Partner"
    
    # Test dirty tracking
    assert "code" in partner._fields_set
    assert "name" in partner._fields_set
    assert "document" not in partner._fields_set
    
    partner.document = "12345678901"
    assert "document" in partner._fields_set
    
    # Test modified fields
    modified = partner.get_modified_fields()
    assert modified == {"code": 1, "name": "Test Partner", "document": "12345678901"}
    
    # Test should_serialize_field
    assert partner.should_serialize_field("code") is True
    assert partner.should_serialize_field("internal_notes") is False # Ignored
    
    # Test validation - max length
    with pytest.raises(ValueError, match="Value too long"):
        partner.document = "123456789012345" # 15 chars, max is 14
        
    # Test validation - key required
    with pytest.raises(ValueError, match="cannot be None"):
        Partner(code=None, name="Test") # type: ignore
