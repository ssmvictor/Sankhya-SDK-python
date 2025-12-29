import pytest
from sankhya_sdk.enums import ProductSourceType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ProductSourceType.NONE, "None", "None"),
        (ProductSourceType.GROUP, "G", "Group of product"),
        (ProductSourceType.PRODUCT, "P", "Product"),
    ],
)
def test_product_source_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
