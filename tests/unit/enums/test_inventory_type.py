import pytest
from sankhya_sdk.enums import InventoryType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (InventoryType.OWN, "P", "Próprio"),
        (InventoryType.THIRD, "T", "Terceiro"),
    ],
)
def test_inventory_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
