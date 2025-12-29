import pytest
from sankhya_sdk.enums import ProductSuggestionType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ProductSuggestionType.NONE, "None", "Nenhum"),
        (ProductSuggestionType.ACCESSORY, "A", "Acessório"),
        (ProductSuggestionType.SUGGESTION, "S", "Sugestão"),
        (ProductSuggestionType.BUY_TOGETHER, "C", "Compre Junto"),
    ],
)
def test_product_suggestion_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
