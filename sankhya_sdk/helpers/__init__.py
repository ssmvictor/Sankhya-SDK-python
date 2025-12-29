# -*- coding: utf-8 -*-
"""
Módulo de helpers para o Sankhya SDK.

Fornece interfaces, dataclasses, extensões e utilitários
para manipulação de entidades e requisições de serviço.
"""

# Interfaces e Protocolos
from .filter_expression import IFilterExpression, ILiteralCriteria, LiteralCriteria

# Dataclasses e Modelos
from .entity_query_options import EntityQueryOptions

# Helpers de Status
from .status_message_helper import (
    StatusMessageHelper,
    PROPERTY_VALUE_ERROR_PATTERN,
    PROPERTY_NAME_ERROR_PATTERN,
    REFERENCE_FIELDS_FIRST_LEVEL_PATTERN,
    REFERENCE_FIELDS_SECOND_LEVEL_PATTERN,
)

# Extensões de Entidade
from .entity_extensions import (
    EntityResolverResult,
    Field,
    get_entity_name,
    get_entity_custom_data,
    get_service_attribute,
    extract_keys,
    query,
    query_with_criteria,
    query_with_options,
    query_light,
    update_on_demand,
    remove_on_demand,
    get_on_demand_update_queue,
    get_on_demand_remove_queue,
    clear_on_demand_queues,
)

# Extensões de ServiceRequest
from .service_request_extensions import (
    ServiceRequestExtensions,
    ParsePropertyModel,
    resolve,
)

# Serialização
from .generic_service_entity import GenericServiceEntity
from .entity_dynamic_serialization import (
    EntityDynamicSerialization,
    Metadata,
)


__all__ = [
    # Interfaces
    "IFilterExpression",
    "ILiteralCriteria",
    "LiteralCriteria",
    # Dataclasses
    "EntityQueryOptions",
    # Status Helper
    "StatusMessageHelper",
    "PROPERTY_VALUE_ERROR_PATTERN",
    "PROPERTY_NAME_ERROR_PATTERN",
    "REFERENCE_FIELDS_FIRST_LEVEL_PATTERN",
    "REFERENCE_FIELDS_SECOND_LEVEL_PATTERN",
    # Entity Extensions
    "EntityResolverResult",
    "Field",
    "get_entity_name",
    "get_entity_custom_data",
    "get_service_attribute",
    "extract_keys",
    "query",
    "query_with_criteria",
    "query_with_options",
    "query_light",
    "update_on_demand",
    "remove_on_demand",
    "get_on_demand_update_queue",
    "get_on_demand_remove_queue",
    "clear_on_demand_queues",
    # ServiceRequest Extensions
    "ServiceRequestExtensions",
    "ParsePropertyModel",
    "resolve",
    # Serialization
    "GenericServiceEntity",
    "EntityDynamicSerialization",
    "Metadata",
]
