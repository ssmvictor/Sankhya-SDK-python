from sankhya_sdk.enums import ServiceCategory


def test_service_category_values():
    assert ServiceCategory.NONE.value == 0
    assert ServiceCategory.CRUD.value == 3
    assert ServiceCategory.AUTHORIZATION.value == 1
