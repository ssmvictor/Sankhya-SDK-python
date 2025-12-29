import pytest
from sankhya_sdk.enums import TradingSubType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (TradingSubType.NONE, "0", "Nenhum"),
        (TradingSubType.IN_CASH, "1", "A vista"),
        (TradingSubType.DEFERRED, "2", "A prazo"),
        (TradingSubType.PARCELED_OUT, "3", "Parcelada"),
        (TradingSubType.POSTDATED_CHECK, "4", "Cheque pré-datado"),
        (TradingSubType.INSTALLMENT_CREDIT, "5", "Crediário"),
        (TradingSubType.FINANCIAL, "6", "Financeira"),
        (TradingSubType.CREDIT_CARD, "7", "Cartão de crédito"),
        (TradingSubType.DEBIT_CARD, "8", "Cartão de débito"),
    ],
)
def test_trading_sub_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
