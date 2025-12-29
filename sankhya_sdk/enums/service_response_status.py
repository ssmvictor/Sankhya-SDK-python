from enum import IntEnum


class ServiceResponseStatus(IntEnum):
    """Representa o status de uma resposta de serviço."""

    ERROR = 0
    OK = 1
    INFO = 2
    TIMEOUT = 3
    SERVICE_CANCELED = 4
