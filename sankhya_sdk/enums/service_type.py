from enum import IntEnum


class ServiceType(IntEnum):
    """Representa o tipo de serviço."""

    NONE = 0
    RETRIEVE = 1
    NON_TRANSACTIONAL = 2
    TRANSACTIONAL = 3
