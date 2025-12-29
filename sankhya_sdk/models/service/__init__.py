"""
Módulo de tipos para comunicação com serviços Sankhya (camada Service Layer).

Este módulo contém todas as classes necessárias para serialização/deserialização
XML de requisições e respostas da API Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Service/
"""

# Constantes XML
from .constants import SankhyaConstants

# Helpers de serialização
from .xml_serialization import (
    XmlSerializable,
    XmlSerializableBase,
    to_base64,
    from_base64,
    serialize_bool,
    deserialize_bool,
    create_xml_element,
    parse_xml_element,
    get_element_text,
    get_element_attr,
)

# Tipos básicos
from .basic_types import (
    FieldValue,
    Field,
    Criteria,
    Parameter,
    LiteralCriteria,
    LiteralCriteriaSql,
    DataRow,
    ReferenceFetch,
    Prop,
    Path,
    Paths,
)

# Tipos de metadados e configuração
from .metadata_types import (
    StatusMessage,
    Metadata,
    Config,
    Key,
    Session,
    SingleNumber,
    SingleNumbers,
    Warning,
    Warnings,
)

# Tipos de entidade e dataset
from .entity_types import (
    Entity,
    DataSet,
    EntityDynamic,
    CrudServiceEntities,
    CrudServiceProviderEntities,
)

# Tipos de query e parâmetros
from .query_types import (
    ILiteralCriteria,
    Param,
    Params,
    QueryCriteria,
    QueryBuilder,
)

# Tipos de invoice
from .invoice_types import (
    Invoice,
    Invoices,
    InvoiceItem,
    InvoiceItems,
    Accompaniment,
    InvoiceAccompaniments,
    InvoicesWithCurrency,
    CancelledInvoice,
    CancelledInvoices,
    CancellationResult,
)

# Tipos de eventos e mensagens
from .event_types import (
    ClientEvent,
    ClientEvents,
    ClientEventInvoiceItem,
    Event,
    Message,
    Messages,
    SystemMessage,
    SystemWarning,
    SystemWarningRecipient,
    NotificationElem,
)

# Tipos de usuários e sessões
from .user_types import (
    User,
    Users,
    SessionInfo,
    SessionsResponse,
    Release,
    Releases,
    MessageUnlinkShipping,
    LowData,
)

# Classes principais de request/response
from .request_body import RequestBody
from .response_body import ResponseBody
from .service_request import ServiceRequest
from .service_response import ServiceResponse


__all__ = [
    # Constantes
    "SankhyaConstants",
    # Serialização
    "XmlSerializable",
    "XmlSerializableBase",
    "to_base64",
    "from_base64",
    "serialize_bool",
    "deserialize_bool",
    "create_xml_element",
    "parse_xml_element",
    "get_element_text",
    "get_element_attr",
    # Tipos básicos
    "FieldValue",
    "Field",
    "Criteria",
    "Parameter",
    "LiteralCriteria",
    "LiteralCriteriaSql",
    "DataRow",
    "ReferenceFetch",
    "Prop",
    "Path",
    "Paths",
    # Metadados
    "StatusMessage",
    "Metadata",
    "Config",
    "Key",
    "Session",
    "SingleNumber",
    "SingleNumbers",
    "Warning",
    "Warnings",
    # Entidades
    "Entity",
    "DataSet",
    "EntityDynamic",
    "CrudServiceEntities",
    "CrudServiceProviderEntities",
    # Query
    "ILiteralCriteria",
    "Param",
    "Params",
    "QueryCriteria",
    "QueryBuilder",
    # Invoice
    "Invoice",
    "Invoices",
    "InvoiceItem",
    "InvoiceItems",
    "Accompaniment",
    "InvoiceAccompaniments",
    "InvoicesWithCurrency",
    "CancelledInvoice",
    "CancelledInvoices",
    "CancellationResult",
    # Eventos
    "ClientEvent",
    "ClientEvents",
    "ClientEventInvoiceItem",
    "Event",
    "Message",
    "Messages",
    "SystemMessage",
    "SystemWarning",
    "SystemWarningRecipient",
    "NotificationElem",
    # Usuários
    "User",
    "Users",
    "SessionInfo",
    "SessionsResponse",
    "Release",
    "Releases",
    "MessageUnlinkShipping",
    "LowData",
    # Request/Response
    "RequestBody",
    "ResponseBody",
    "ServiceRequest",
    "ServiceResponse",
]
