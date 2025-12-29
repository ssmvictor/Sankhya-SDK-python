import pytest
from sankhya_sdk.enums import ServiceModule


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ServiceModule.NONE, "none", "Test"),
        (ServiceModule.MGE, "mge", "MGE"),
        (ServiceModule.MGECOM, "mgecom", "MGECOM"),
        (ServiceModule.MGEFIN, "mgefin", "MGEFIN"),
    ],
)
def test_service_module_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal