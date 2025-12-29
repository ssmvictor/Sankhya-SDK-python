import pytest
from sankhya_sdk.enums import SankhyaWarningLevel


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (SankhyaWarningLevel.URGENT, "0", "Urgente"),
        (SankhyaWarningLevel.ERROR, "1", "Erro"),
        (SankhyaWarningLevel.WARNING, "2", "Alerta"),
        (SankhyaWarningLevel.INFORMATION, "3", "Informação"),
    ],
)
def test_sankhya_warning_level_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
