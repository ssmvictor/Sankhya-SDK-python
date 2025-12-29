import pytest
from sankhya_sdk.enums import (
    BillingType,
    FiscalClassification,
    FiscalPersonType,
    InvoiceStatus,
    MovementType,
    ServiceRequestType,
)


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (FiscalPersonType.INDIVIDUAL, "F", "Pessoa física"),
        (FiscalPersonType.CORPORATION, "J", "Pessoa jurídica"),
        (BillingType.NORMAL, "FaturamentoNormal", "Faturamento normal"),
        (InvoiceStatus.RELEASED, "L", "Liberada"),
        (MovementType.SALES, "V", "Venda"),
        (ServiceRequestType.PAGED_CRUD, "PagedCrud", "Paged CRUD (retrieve)"),
    ],
)
def test_basic_enums_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
