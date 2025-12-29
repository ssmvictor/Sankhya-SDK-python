import pytest
from sankhya_sdk.enums import OrderHistoryEvent


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (OrderHistoryEvent.NONE, "", "Nenhum"),
        (OrderHistoryEvent.CHANGE, "A", "Alteração"),
        (OrderHistoryEvent.CONFIRMATION, "C", "Confirmação"),
        (OrderHistoryEvent.EXCLUSION, "E", "Exclusão"),
        (OrderHistoryEvent.INCLUSION, "I", "Inclusão"),
    ],
)
def test_order_history_event_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
