# -*- coding: utf-8 -*-
from unittest.mock import MagicMock
import pytest
from sankhya_sdk.exceptions import (
    ConfirmInvoiceException,
    NoItemsConfirmInvoiceException,
    InvalidServiceQueryOptionsException,
    MissingSerializerHelperEntityException,
    OpenFileException,
)
from sankhya_sdk.enums.service_name import ServiceName

def test_confirm_invoice_exception() -> None:
    exc: ConfirmInvoiceException = ConfirmInvoiceException(123)
    assert "Unable to confirm invoice with single number: 123" in str(exc)

def test_no_items_confirm_invoice_exception() -> None:
    exc: NoItemsConfirmInvoiceException = NoItemsConfirmInvoiceException(456)
    assert "Invoice 456 has no items, cannot be confirmed" in str(exc)

def test_invalid_service_query_options_exception() -> None:
    exc: InvalidServiceQueryOptionsException = InvalidServiceQueryOptionsException(ServiceName.LOGIN)
    assert "Unable to use query options with service Login" in str(exc)

def test_missing_serializer_helper_entity_exception() -> None:
    exc: MissingSerializerHelperEntityException = MissingSerializerHelperEntityException("Items", "Invoice", "Sankhya.Models.Invoice")
    assert "The Items property of Invoice entity (Type: Sankhya.Models.Invoice) is missing the serializer helper method" in str(exc)

def test_open_file_exception() -> None:
    exc: OpenFileException = OpenFileException("file_key_123")
    assert "Unable to open the file with the key file_key_123 in the Sankhya file manager" in str(exc)
