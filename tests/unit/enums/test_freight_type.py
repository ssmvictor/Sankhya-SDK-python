import pytest
from sankhya_sdk.enums import FreightType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (FreightType.COST_INSURANCE_FREIGHT, "C", "CIF"),
        (FreightType.FREE_ON_BOARD, "F", "FOB"),
        (FreightType.NO_FREIGHT, "S", "Sem Frete"),
        (FreightType.THIRD, "T", "Terceiros"),
    ],
)
def test_freight_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
