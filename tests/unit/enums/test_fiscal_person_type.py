import pytest
from sankhya_sdk.enums import FiscalPersonType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (FiscalPersonType.INDIVIDUAL, "F", "Pessoa física"),
        (FiscalPersonType.CORPORATION, "J", "Pessoa jurídica"),
    ],
)
def test_fiscal_person_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
