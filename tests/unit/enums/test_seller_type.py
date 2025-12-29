import pytest
from sankhya_sdk.enums import SellerType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (SellerType.NONE, "0", "Nenhum"),
        (SellerType.BUYER, "C", "Comprador"),
        (SellerType.SELLER, "V", "Vendedor"),
        (SellerType.SUPERVISOR, "S", "Supervisor"),
        (SellerType.MANAGER, "G", "Gerente"),
        (SellerType.PERFORMER, "E", "Executante"),
        (SellerType.REPRESENTATIVE, "R", "Representante"),
        (SellerType.TECHNICIAN, "T", "Técnico"),
    ],
)
def test_seller_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
