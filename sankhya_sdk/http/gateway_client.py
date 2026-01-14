"""
Gateway Client for Sankhya API Gateway.

Provides high-level interface for executing services via the Sankhya Gateway
with automatic module selection (MGE/MGECOM) and JSON output.
"""

import logging
from typing import Any, Dict, Optional, List
from enum import Enum

from sankhya_sdk.http.session import SankhyaSession

logger = logging.getLogger(__name__)


class GatewayModule(Enum):
    """Sankhya Gateway modules."""

    MGE = "mge"
    MGECOM = "mgecom"


# Service prefixes mapped to their respective modules
MODULE_SERVICE_MAP: Dict[str, GatewayModule] = {
    # MGE - Cadastros gerais
    "CRUDServiceProvider": GatewayModule.MGE,
    "DatasetSP": GatewayModule.MGE,
    # MGECOM - Movimentações comerciais
    "CACSP": GatewayModule.MGECOM,
    "SelecaoDocumentoSP": GatewayModule.MGECOM,
}


class GatewayClient:
    """
    Client for executing services via Sankhya API Gateway.

    Automatically selects the correct module (MGE/MGECOM) based on service name
    and enforces JSON output format.

    Example:
        >>> client = GatewayClient(session)
        >>> response = client.execute_service(
        ...     "CRUDServiceProvider.loadRecords",
        ...     {"dataSet": {"rootEntity": "Parceiro"}}
        ... )
    """

    def __init__(self, session: SankhyaSession, default_module: GatewayModule = GatewayModule.MGE):
        """
        Initialize Gateway Client.

        Args:
            session: Authenticated SankhyaSession instance.
            default_module: Default module when service cannot be auto-detected.
        """
        self.session = session
        self.default_module = default_module

    def execute_service(
        self,
        service_name: str,
        request_body: Dict[str, Any],
        module: Optional[GatewayModule] = None,
    ) -> Dict[str, Any]:
        """
        Execute a service on Sankhya Gateway.

        Args:
            service_name: Full service name (e.g., "CRUDServiceProvider.loadRecords").
            request_body: Request payload dictionary.
            module: Optional module override. Auto-detected if not provided.

        Returns:
            Parsed JSON response from the Gateway.

        Raises:
            SankhyaClientError: On 4xx HTTP errors.
            SankhyaServerError: On 5xx HTTP errors.
        """
        resolved_module = module or self._resolve_module(service_name)
        url = self._build_url(resolved_module, service_name)

        payload = {"serviceName": service_name, "requestBody": request_body}

        logger.debug(f"Executing service {service_name} on module {resolved_module.value}")

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        return response.json()

    def load_records(
        self,
        entity: str,
        fields: List[str],
        criteria: Optional[str] = None,
        module: Optional[GatewayModule] = None,
        offset: int = 0,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Load records using CRUDServiceProvider.loadRecords.

        Args:
            entity: Root entity name (e.g., "Parceiro", "Produto").
            fields: List of field names to retrieve.
            criteria: Optional SQL-like criteria expression.
            module: Optional module override.
            offset: Page offset (0-based). Default 0.
            page_size: Number of records per page. Default 100.

        Returns:
            Parsed JSON response with records.
        """
        request_body = {
            "dataSet": {
                "rootEntity": entity,
                "includePresentationFields": "S",
                "offsetPage": str(offset),
                "pageSize": str(page_size),
                "entity": {"fieldset": {"list": ",".join(fields)}},
            }
        }

        if criteria:
            request_body["dataSet"]["criteria"] = {"expression": {"$": criteria}}

        return self.execute_service(
            "CRUDServiceProvider.loadRecords", request_body, module or GatewayModule.MGE
        )

    def save_record(
        self,
        entity: str,
        fields: Dict[str, Any],
        field_list: Optional[List[str]] = None,
        module: Optional[GatewayModule] = None,
    ) -> Dict[str, Any]:
        """
        Save (insert/update) a record using CRUDServiceProvider.saveRecord.

        The operation (INSERT or UPDATE) is determined by whether the primary key
        exists in the database.

        Args:
            entity: Root entity name.
            fields: Dictionary of field values.
            field_list: Optional list of fields to return. Defaults to fields keys.
            module: Optional module override.

        Returns:
            Parsed JSON response with saved record.
        """
        local_fields = {key: {"$": str(value)} for key, value in fields.items()}

        request_body = {
            "dataSet": {
                "rootEntity": entity,
                "includePresentationFields": "S",
                "dataRow": {"localFields": local_fields},
                "entity": {"fieldset": {"list": ",".join(field_list or list(fields.keys()))}},
            }
        }

        return self.execute_service(
            "CRUDServiceProvider.saveRecord", request_body, module or GatewayModule.MGE
        )

    def _resolve_module(self, service_name: str) -> GatewayModule:
        """Resolve module from service name prefix."""
        service_prefix = service_name.split(".")[0]

        if service_prefix in MODULE_SERVICE_MAP:
            return MODULE_SERVICE_MAP[service_prefix]

        logger.warning(
            f"Unknown service prefix '{service_prefix}', using default module {self.default_module.value}"
        )
        return self.default_module

    def _build_url(self, module: GatewayModule, service_name: str) -> str:
        """Build Gateway URL with required parameters."""
        return f"/gateway/v1/{module.value}/service.sbr?serviceName={service_name}&outputType=json"

    @staticmethod
    def extract_records(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize records from Gateway response.

        The Sankhya Gateway returns data in a compact format where field values
        are indexed (f0, f1, f2...) and must be mapped to actual field names
        using the metadata.

        Example response structure:
            {
                "responseBody": {
                    "entities": {
                        "metadata": {
                            "fields": {"field": [{"name": "CODPARC"}, {"name": "NOMEPARC"}]}
                        },
                        "entity": [
                            {"f0": {"$": "1"}, "f1": {"$": "EMPRESA TESTE"}}
                        ]
                    }
                }
            }

        Args:
            response: Raw response from execute_service or load_records.

        Returns:
            List of dictionaries with field names as keys and values extracted.
        """
        response_body = response.get("responseBody", {})
        entities_data = response_body.get("entities", {})

        # Extract metadata field names
        metadata = entities_data.get("metadata", {})
        fields_container = metadata.get("fields", {})
        field_list = fields_container.get("field", [])

        # Handle single field (dict) vs multiple fields (list)
        if isinstance(field_list, dict):
            field_list = [field_list]

        field_names = [f.get("name", f"unknown_{i}") for i, f in enumerate(field_list)]

        # Extract entities
        raw_entities = entities_data.get("entity", [])

        # Handle single entity (dict) vs multiple entities (list)
        if isinstance(raw_entities, dict):
            raw_entities = [raw_entities]
        elif not isinstance(raw_entities, list):
            raw_entities = []

        # Map indexed fields (f0, f1, ...) to actual field names
        result = []
        for entity in raw_entities:
            record = {}
            for i, field_name in enumerate(field_names):
                key = f"f{i}"
                if key in entity:
                    value = entity[key]
                    # Handle Sankhya's {"$": "value"} format
                    if isinstance(value, dict) and "$" in value:
                        record[field_name] = value["$"]
                    elif isinstance(value, dict):
                        # Some fields may have nested structure
                        record[field_name] = value
                    else:
                        record[field_name] = value
                else:
                    record[field_name] = None
            result.append(record)

        return result

    @staticmethod
    def is_success(response: Dict[str, Any]) -> bool:
        """
        Check if a Gateway response indicates success.

        Args:
            response: Raw response from execute_service.

        Returns:
            True if status is "1" or 1, False otherwise.
        """
        status = response.get("status")
        if status is None:
            status = response.get("responseBody", {}).get("status")
        return status in ("1", 1, True)

    @staticmethod
    def get_error_message(response: Dict[str, Any]) -> Optional[str]:
        """
        Extract error message from a Gateway response.

        Args:
            response: Raw response from execute_service.

        Returns:
            Error message string or None if successful.
        """
        if GatewayClient.is_success(response):
            return None

        msg = response.get("statusMessage")
        if msg is None:
            msg = response.get("responseBody", {}).get("statusMessage")
        return msg or "Unknown error"
