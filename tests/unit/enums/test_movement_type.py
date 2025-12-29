import pytest
from sankhya_sdk.enums import MovementType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (MovementType.NONE, "", "Nenhum"),
        (MovementType.DEPOSIT, "1", "NF Depósito"),
        (MovementType.WARRANT, "2", "PD Devol. / Procuração / Warrant"),
        (MovementType.OUTPUT, "3", "Saídas"),
        (MovementType.BILLING, "4", "Faturamento"),
        (MovementType.RD8, "8", "RD8"),
        (MovementType.BANK_MOVEMENT, "B", "Movimento bancário"),
        (MovementType.PURCHASE, "C", "Compra"),
        (MovementType.SALES_RETURN, "D", "Devolução de venda"),
        (MovementType.PURCHASE_RETURN, "E", "Devolução de compra"),
        (MovementType.PRODUCTION, "F", "Produção"),
        (MovementType.PAYMENT, "G", "Pagamento"),
        (MovementType.FINANCIAL, "I", "Financeiro"),
        (MovementType.REQUEST_ORDER, "J", "Pedido de Requisição"),
        (MovementType.TRANSFER_ORDER, "K", "Pedido de Transferência"),
        (MovementType.REQUEST_RETURN, "L", "Devolução de Requisição"),
        (MovementType.TRANSFER_RETURN, "M", "Devolução de Transferência"),
        (MovementType.INPUT, "N", "Entradas"),
        (MovementType.PURCHASE_ORDER, "O", "Pedido de compra"),
        (MovementType.SALES_ORDER, "P", "Pedido de venda"),
        (MovementType.REQUEST, "Q", "Requisição"),
        (MovementType.RECEIPT, "R", "Recebimento"),
        (MovementType.TRANSFER, "T", "Transferência"),
        (MovementType.SALES, "V", "Venda"),
        (MovementType.MODEL, "Z", "Modelo"),
    ],
)
def test_movement_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
