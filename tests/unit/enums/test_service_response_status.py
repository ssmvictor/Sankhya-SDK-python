import pytest
from sankhya_sdk.enums import ServiceResponseStatus


@pytest.mark.parametrize(
    "enum_member, expected_value",
    [
        (ServiceResponseStatus.ERROR, 0),
        (ServiceResponseStatus.OK, 1),
        (ServiceResponseStatus.INFO, 2),
        (ServiceResponseStatus.TIMEOUT, 3),
        (ServiceResponseStatus.SERVICE_CANCELED, 4),
    ],
)
def test_service_response_status_values(enum_member, expected_value):
    assert enum_member.value == expected_value
