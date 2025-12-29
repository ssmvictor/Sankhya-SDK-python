import pytest
from sankhya_sdk.enums import ServiceType


@pytest.mark.parametrize(
    "enum_member, expected_value",
    [
        (ServiceType.NONE, 0),
        (ServiceType.RETRIEVE, 1),
        (ServiceType.NON_TRANSACTIONAL, 2),
        (ServiceType.TRANSACTIONAL, 3),
    ],
)
def test_service_type_values(enum_member, expected_value):
    assert enum_member.value == expected_value