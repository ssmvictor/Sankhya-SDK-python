import pytest
from sankhya_sdk.enums import ServiceRequestType


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human",
    [
        (ServiceRequestType.DEFAULT, "Default", "Default"),
        (ServiceRequestType.SIMPLE_CRUD, "SimpleCrud", "Simple CRUD"),
        (ServiceRequestType.PAGED_CRUD, "PagedCrud", "Paged CRUD (retrieve)"),
        (ServiceRequestType.QUERYABLE_CRUD, "QueryableCrud", "Queryable CRUD"),
        (ServiceRequestType.ON_DEMAND_CRUD, "OnDemandCrud", "On demand CRUD (Create, Update, Delete)"),
        (ServiceRequestType.KNOW_SERVICES, "KnowServices", "Know services"),
    ],
)
def test_service_request_type_metadata(enum_member, expected_internal, expected_human):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert str(enum_member) == expected_internal
