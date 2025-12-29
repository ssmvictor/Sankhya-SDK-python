"""
Constantes XML para serialização de serviços Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/SankhyaConstants.cs
"""

from typing import Final


class SankhyaConstants:
    """Constantes utilizadas na comunicação com a API Sankhya."""

    # ============================================================
    # Cookies e Sessão
    # ============================================================
    SESSION_ID_COOKIE_NAME: Final[str] = "JSESSIONID"

    # ============================================================
    # Mensagens de Erro
    # ============================================================
    SESSION_MANAGER_NOT_STARTED: Final[str] = "Gerenciador de sessão não foi iniciado"
    FILE_NOT_FOUND_ON_SERVER: Final[str] = "O arquivo solicitado não existe no servidor"

    # ============================================================
    # Elementos XML - Requisição/Resposta
    # ============================================================
    SERVICE_RESPONSE: Final[str] = "serviceResponse"
    SERVICE_REQUEST: Final[str] = "serviceRequest"
    SERVICE_NAME: Final[str] = "serviceName"
    STATUS_MESSAGE: Final[str] = "statusMessage"
    RESPONSE_BODY: Final[str] = "responseBody"
    REQUEST_BODY: Final[str] = "requestBody"

    # ============================================================
    # Elementos XML - Metadados
    # ============================================================
    METADATA: Final[str] = "metadata"

    # ============================================================
    # Elementos XML - Entidades (Inglês)
    # ============================================================
    ENTITIES_EN: Final[str] = "entities"
    ENTITY_EN: Final[str] = "entity"

    # ============================================================
    # Elementos XML - Entidades (Português)
    # ============================================================
    ENTITIES_PT_BR: Final[str] = "entidades"
    ENTITY_PT_BR: Final[str] = "entidade"

    # ============================================================
    # Elementos XML - Notas Fiscais
    # ============================================================
    INVOICE_ACCOMPANIMENTS: Final[str] = "acompanhamentosNotas"
    INVOICES: Final[str] = "notas"
    CANCELLATION_RESULT: Final[str] = "resultadoCancelamento"

    # ============================================================
    # Elementos XML - Usuários e Sessões
    # ============================================================
    USERS: Final[str] = "usuarios"
    SESSIONS: Final[str] = "SESSIONS"
    CODE_USER: Final[str] = "idusu"
    CODE_USER_LOGGED_ID: Final[str] = "codUsuLogado"

    # ============================================================
    # Elementos XML - Mensagens e Avisos
    # ============================================================
    WARNINGS: Final[str] = "avisos"
    MESSAGES: Final[str] = "mensagens"
    RELEASES: Final[str] = "liberacoes"
    MESSAGE_UNLINK_SHIPPING: Final[str] = "msgDesvincularRemessa"

    # ============================================================
    # Elementos XML - Eventos
    # ============================================================
    CLIENT_EVENTS: Final[str] = "clientEvents"

    # ============================================================
    # Elementos XML - Chaves
    # ============================================================
    KEY: Final[str] = "chave"
    PRIMARY_KEY: Final[str] = "pk"
    PRIMARY_KEY_UPPER: Final[str] = "PK"

    # ============================================================
    # Elementos XML - Sessão/Identificadores
    # ============================================================
    JSESSION_ID: Final[str] = "jsessionid"
    CALL_ID: Final[str] = "callID"
    PAGER_ID: Final[str] = "pagerID"
    TRANSACTION_ID: Final[str] = "transactionId"

    # ============================================================
    # Elementos XML - Paginação
    # ============================================================
    TOTAL: Final[str] = "total"
    TOTAL_PAGES: Final[str] = "totalPages"

    # ============================================================
    # Elementos XML - Atributos Comuns
    # ============================================================
    NAME: Final[str] = "nome"
    STATUS: Final[str] = "status"
    RMD: Final[str] = "_rmd"
    PENDING_PRINTING: Final[str] = "pendingPrinting"
    ERROR_CODE: Final[str] = "errorCode"
    ERROR_LEVEL: Final[str] = "errorLevel"

    # ============================================================
    # Formatos de Serialização Booleana
    # ============================================================
    TRUE_OR_FALSE: Final[str] = "true|false"
    BOOL_FORMAT_TRUE_FALSE: Final[str] = "true|false"
    BOOL_FORMAT_S_N: Final[str] = "S|N"
    BOOL_FORMAT_1_0: Final[str] = "1|0"
    BOOL_FORMAT_SIM_NAO: Final[str] = "Sim|Não"

    # ============================================================
    # Valores Booleanos
    # ============================================================
    TRUE_VALUES: Final[tuple] = ("true", "True", "TRUE", "S", "s", "1", "Sim", "sim")
    FALSE_VALUES: Final[tuple] = ("false", "False", "FALSE", "N", "n", "0", "Não", "nao", "")
