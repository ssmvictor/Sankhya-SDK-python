import pytest
from sankhya_sdk.enums import ParameterType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ParameterType.STRING, "S", "String"),
        (ParameterType.INTEGER, "I", "Integer"),
        (ParameterType.DATETIME, "D", "Datetime"),
    ],
)
def test_parameter_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
