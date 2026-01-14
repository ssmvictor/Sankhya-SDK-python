"""
XML Adapter for backward compatibility with legacy integrations.

Provides conversion between XML and JSON formats to support existing
integrations that still use the old XML-based API.
"""

import json
import logging
import re
from typing import Any, Dict, Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class XmlAdapter:
    """
    Adapter for converting between XML and JSON formats.
    
    Provides backward compatibility for legacy integrations that expect
    XML request/response formats while using the modern JSON API Gateway.
    
    Example:
        >>> adapter = XmlAdapter()
        >>> json_payload = adapter.xml_to_json(xml_string)
        >>> xml_response = adapter.json_to_xml(json_dict)
    """

    def xml_to_json(self, xml_payload: str) -> Dict[str, Any]:
        """
        Convert XML payload to JSON format.
        
        Args:
            xml_payload: XML string to convert.
            
        Returns:
            Equivalent JSON dictionary.
            
        Raises:
            ValueError: If XML is malformed.
        """
        try:
            root = ET.fromstring(xml_payload)
            return self._element_to_dict(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            raise ValueError(f"Malformed XML: {e}") from e

    def json_to_xml(
        self, 
        json_data: Dict[str, Any], 
        root_name: str = "serviceRequest"
    ) -> str:
        """
        Convert JSON dictionary to XML format.
        
        Args:
            json_data: JSON dictionary to convert.
            root_name: Name for the root XML element.
            
        Returns:
            XML string representation.
        """
        root = self._dict_to_element(json_data, root_name)
        return ET.tostring(root, encoding="unicode")

    def wrap_legacy_request(
        self,
        service_name: str,
        request_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wrap a legacy-style request for the modern JSON API.
        
        Args:
            service_name: Full service name (e.g., "CRUDServiceProvider.loadRecords").
            request_body: Request payload.
            
        Returns:
            Properly formatted request for JSON API.
        """
        return {
            "serviceName": service_name,
            "requestBody": request_body
        }

    def extract_legacy_response(
        self, 
        json_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract data from JSON response in a legacy-compatible format.
        
        Transforms the modern JSON response structure to match what
        legacy integrations expect.
        
        Args:
            json_response: Response from JSON API Gateway.
            
        Returns:
            Transformed response for legacy compatibility.
        """
        # Handle common response structures
        if "responseBody" in json_response:
            return json_response["responseBody"]
        
        if "entities" in json_response:
            return {"entities": json_response["entities"]}
        
        return json_response

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Recursively convert XML element to dictionary."""
        result: Dict[str, Any] = {}
        
        # Add element attributes
        if element.attrib:
            result["@attributes"] = dict(element.attrib)
        
        # Handle text content
        if element.text and element.text.strip():
            text = element.text.strip()
            if len(element) == 0:  # No children
                return {"$": text} if result else text
            result["$"] = text
        
        # Process children
        children: Dict[str, Any] = {}
        for child in element:
            child_dict = self._element_to_dict(child)
            
            if child.tag in children:
                # Convert to list if multiple elements with same tag
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_dict)
            else:
                children[child.tag] = child_dict
        
        if children:
            result.update(children)
        
        return result if result else {}

    def _dict_to_element(
        self, 
        data: Any, 
        tag_name: str
    ) -> ET.Element:
        """Recursively convert dictionary to XML element."""
        element = ET.Element(tag_name)
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "@attributes":
                    for attr_name, attr_value in value.items():
                        element.set(attr_name, str(attr_value))
                elif key == "$":
                    element.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = self._dict_to_element(item, key)
                            element.append(child)
                    else:
                        child = self._dict_to_element(value, key)
                        element.append(child)
        elif isinstance(data, list):
            for item in data:
                child = self._dict_to_element(item, "item")
                element.append(child)
        else:
            element.text = str(data) if data is not None else ""
        
        return element

    def convert_field_format(
        self,
        fields: Dict[str, Any],
        to_sankhya: bool = True
    ) -> Dict[str, Any]:
        """
        Convert field format between legacy and modern styles.
        
        Sankhya API expects: {"FIELD": {"$": "value"}}
        Legacy style might use: {"FIELD": "value"}
        
        Args:
            fields: Dictionary of field values.
            to_sankhya: If True, convert to Sankhya format. Otherwise, flatten.
            
        Returns:
            Converted fields dictionary.
        """
        if to_sankhya:
            return {
                key: {"$": str(value)} if not isinstance(value, dict) else value
                for key, value in fields.items()
            }
        else:
            return {
                key: value.get("$") if isinstance(value, dict) and "$" in value else value
                for key, value in fields.items()
            }
