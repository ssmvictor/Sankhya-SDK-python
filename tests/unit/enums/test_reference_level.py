import pytest
from sankhya_sdk.enums import ReferenceLevel


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ReferenceLevel.NONE, "None", "None"),
        (ReferenceLevel.FIRST, "First", "First"),
        (ReferenceLevel.SECOND, "Second", "Second"),
        (ReferenceLevel.THIRD, "Third", "Third"),
        (ReferenceLevel.FOURTH, "Fourth", "Fourth"),
        (ReferenceLevel.FIFTH, "Fifth", "Fifth"),
        (ReferenceLevel.SIXTH, "Sixth", "Sixth"),
    ],
)
def test_reference_level_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
