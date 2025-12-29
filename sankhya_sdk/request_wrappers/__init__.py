# -*- coding: utf-8 -*-
"""
Request Wrappers para o Sankhya SDK.

Fornece wrappers de alto nível para operações CRUD e outras
operações de serviço no Sankhya.
"""

from .interfaces import (
    TEntity,
    IOnDemandRequestWrapper,
    IAsyncOnDemandRequestWrapper,
)
from .simple_crud_request_wrapper import SimpleCRUDRequestWrapper
from .paged_request_wrapper import PagedRequestWrapper, PagedRequestException
from .on_demand_request_wrapper import OnDemandRequestWrapper
from .async_on_demand_request_wrapper import AsyncOnDemandRequestWrapper
from .on_demand_request_factory import OnDemandRequestFactory
from .async_on_demand_request_factory import AsyncOnDemandRequestFactory
from .know_services_request_wrapper import KnowServicesRequestWrapper


__all__ = [
    # Interfaces
    "TEntity",
    "IOnDemandRequestWrapper",
    "IAsyncOnDemandRequestWrapper",
    # Simple CRUD
    "SimpleCRUDRequestWrapper",
    # Paged
    "PagedRequestWrapper",
    "PagedRequestException",
    # On-Demand
    "OnDemandRequestWrapper",
    "AsyncOnDemandRequestWrapper",
    "OnDemandRequestFactory",
    "AsyncOnDemandRequestFactory",
    # Know Services
    "KnowServicesRequestWrapper",
]
