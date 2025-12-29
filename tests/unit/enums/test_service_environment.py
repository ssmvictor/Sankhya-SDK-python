import pytest
from sankhya_sdk.enums import ServiceEnvironment


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ServiceEnvironment.NONE, "0", "Nenhum"),
        (ServiceEnvironment.PRODUCTION, "8180", "Produção"),
        (ServiceEnvironment.SANDBOX, "8280", "Sandbox"),
        (ServiceEnvironment.TRAINING, "8380", "Treinamento"),
    ],
)
def test_service_environment_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
