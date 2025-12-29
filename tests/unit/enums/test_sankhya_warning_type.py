import pytest
from sankhya_sdk.enums import SankhyaWarningType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (SankhyaWarningType.NONE, "0", "Nenhum"),
        (SankhyaWarningType.USER, "usuario", "Usuário"),
        (SankhyaWarningType.GROUP, "grupo", "Grupo"),
    ],
)
def test_sankhya_warning_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
