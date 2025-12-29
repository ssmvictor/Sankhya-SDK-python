import pytest
from sankhya_sdk.enums import SystemParameterType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (SystemParameterType.NONE, "", "Nenhum"),
        (SystemParameterType.TEXT, "T", "Texto"),
        (SystemParameterType.DATE, "D", "Data"),
        (SystemParameterType.DECIMAL, "F", "Número Decimal"),
        (SystemParameterType.LOGICAL, "L", "Lógico"),
        (SystemParameterType.LIST, "C", "List"),
        (SystemParameterType.INTEGER, "I", "Número Inteiro"),
    ],
)
def test_system_parameter_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
