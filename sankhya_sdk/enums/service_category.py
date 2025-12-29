from enum import IntEnum


class ServiceCategory(IntEnum):
    """Representa a categoria de um serviço."""

    NONE = 0
    AUTHORIZATION = 1
    COMMUNICATION = 2
    CRUD = 3
    FILE = 4
    FISCAL_INVOICE = 5
    INVOICE = 6
