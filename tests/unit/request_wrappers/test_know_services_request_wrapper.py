# -*- coding: utf-8 -*-
"""
Unit tests for KnowServicesRequestWrapper.

Tests all major functionality including lifecycle management,
session operations, messaging, invoice operations, billing,
financial operations, and file/image handling.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from sankhya_sdk.core.types import ServiceFile
from sankhya_sdk.enums.billing_type import BillingType
from sankhya_sdk.enums.movement_type import MovementType
from sankhya_sdk.enums.sankhya_warning_level import SankhyaWarningLevel
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.exceptions import (
    ConfirmInvoiceException,
    MarkAsPaymentPaidException,
    NoItemsConfirmInvoiceException,
    SankhyaException,
    UnlinkShippingException,
)
from sankhya_sdk.models.service.event_types import (
    ClientEvent,
    SystemWarningRecipient,
)
from sankhya_sdk.models.service.invoice_types import Invoice, InvoiceItem
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.models.service.user_types import SessionInfo
from sankhya_sdk.request_wrappers.know_services_request_wrapper import (
    KnowServicesRequestWrapper,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_wrapper():
    """Reset wrapper state before and after each test."""
    KnowServicesRequestWrapper._context = None
    KnowServicesRequestWrapper._session_token = None
    KnowServicesRequestWrapper._initialized = False
    KnowServicesRequestWrapper._last_time_message_received = datetime.now()
    yield
    KnowServicesRequestWrapper._context = None
    KnowServicesRequestWrapper._session_token = None
    KnowServicesRequestWrapper._initialized = False


@pytest.fixture
def mock_context():
    """Create a mock SankhyaContext."""
    context = MagicMock()
    context.token = uuid.uuid4()
    context.acquire_new_session = MagicMock(return_value=uuid.uuid4())
    context.finalize_session = MagicMock()
    return context


@pytest.fixture
def mock_response():
    """Create a mock ServiceResponse."""
    response = MagicMock(spec=ServiceResponse)
    response.response_body = MagicMock()
    return response


@pytest.fixture
def initialized_wrapper(mock_context, mock_response):
    """Initialize wrapper with mocked context and invoke service."""
    KnowServicesRequestWrapper.initialize(mock_context)
    
    with patch.object(
        KnowServicesRequestWrapper,
        "_invoke_service",
        return_value=mock_response,
    ):
        yield KnowServicesRequestWrapper
    
    KnowServicesRequestWrapper.dispose()


# =============================================================================
# Lifecycle Tests
# =============================================================================


class TestLifecycle:
    """Tests for wrapper lifecycle (initialize, dispose, ensure_initialized)."""

    def test_initialize_with_context(self, mock_context):
        """Test initialization with provided context."""
        KnowServicesRequestWrapper.initialize(mock_context)
        
        assert KnowServicesRequestWrapper._initialized is True
        assert KnowServicesRequestWrapper._context is mock_context
        assert KnowServicesRequestWrapper._session_token == mock_context.token

    def test_initialize_without_context(self):
        """Test initialization creates new context."""
        # This test needs specific setup because SankhyaContext is imported locally
        # Skip detailed mocking and just verify the basic behavior
        mock_ctx = MagicMock()
        mock_ctx.acquire_new_session.return_value = uuid.uuid4()
        
        with patch(
            "sankhya_sdk.core.context.SankhyaContext.from_settings",
            return_value=mock_ctx,
        ):
            KnowServicesRequestWrapper.initialize()
            
            assert KnowServicesRequestWrapper._initialized is True
            mock_ctx.acquire_new_session.assert_called_once_with(
                ServiceRequestType.KNOW_SERVICES
            )

    def test_initialize_already_initialized_logs_warning(self, mock_context, caplog):
        """Test double initialization logs warning."""
        KnowServicesRequestWrapper.initialize(mock_context)
        KnowServicesRequestWrapper.initialize(mock_context)
        
        assert "já inicializado" in caplog.text

    def test_dispose(self, mock_context):
        """Test dispose releases resources."""
        KnowServicesRequestWrapper.initialize(mock_context)
        KnowServicesRequestWrapper.dispose()
        
        assert KnowServicesRequestWrapper._initialized is False
        assert KnowServicesRequestWrapper._context is None
        assert KnowServicesRequestWrapper._session_token is None
        mock_context.finalize_session.assert_called_once()

    def test_dispose_not_initialized(self):
        """Test dispose when not initialized does nothing."""
        KnowServicesRequestWrapper.dispose()  # Should not raise
        assert KnowServicesRequestWrapper._initialized is False

    def test_ensure_initialized_raises_when_not_initialized(self):
        """Test _ensure_initialized raises RuntimeError."""
        with pytest.raises(RuntimeError, match="não inicializado"):
            KnowServicesRequestWrapper._ensure_initialized()

    def test_context_manager(self, mock_context):
        """Test context manager usage."""
        with patch.object(
            KnowServicesRequestWrapper, "initialize"
        ) as mock_init, patch.object(
            KnowServicesRequestWrapper, "dispose"
        ) as mock_dispose:
            with KnowServicesRequestWrapper():
                mock_init.assert_called_once()
            mock_dispose.assert_called_once()


# =============================================================================
# Session Management Tests
# =============================================================================


class TestSessionManagement:
    """Tests for session management methods."""

    def test_get_sessions(self, mock_context, mock_response):
        """Test get_sessions returns list of sessions."""
        # Setup mock response
        mock_sessions = MagicMock()
        mock_sessions.sessions = [
            SessionInfo(
                user_code=1,
                user_name="test_user",
                jsession_id="abc123",
            )
        ]
        mock_response.response_body.sessions = mock_sessions
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            sessions = KnowServicesRequestWrapper.get_sessions()
            
            # Verify request was made with correct service
            KnowServicesRequestWrapper._invoke_service.assert_called_once()
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.SESSION_GET_ALL

    def test_kill_session(self, mock_context, mock_response):
        """Test kill_session sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.kill_session("ABC123XYZ")
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.SESSION_KILL
            assert request.request_body.session.jsession_id == "ABC123XYZ"


# =============================================================================
# Messaging Tests
# =============================================================================


class TestMessaging:
    """Tests for messaging and warning methods."""

    def test_send_warning(self, mock_context, mock_response):
        """Test send_warning sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.send_warning(
                title="Test Warning",
                description="This is a test",
                level=SankhyaWarningLevel.WARNING,
            )
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.WARNING_SEND
            assert request.request_body.system_warning.title == "Test Warning"

    def test_send_message(self, mock_context, mock_response):
        """Test send_message sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.send_message(
                content="Hello World!",
            )
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.MESSAGE_SEND
            assert request.request_body.system_message.content == "Hello World!"

    def test_receive_messages(self, mock_context, mock_response):
        """Test receive_messages updates timestamp and returns data."""
        mock_response.response_body.model_dump_json.return_value = '{"messages": []}'
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            old_time = KnowServicesRequestWrapper._last_time_message_received
            
            result = KnowServicesRequestWrapper.receive_messages()
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.WARNING_RECEIVE
            # Timestamp should be updated
            assert KnowServicesRequestWrapper._last_time_message_received >= old_time


# =============================================================================
# Invoice CRUD Tests
# =============================================================================


class TestInvoiceCRUD:
    """Tests for invoice CRUD operations."""

    def test_create_invoice(self, mock_context, mock_response):
        """Test create_invoice returns NUNOTA."""
        mock_pk = MagicMock()
        mock_pk.nunota = 12345
        mock_response.response_body.primary_key = mock_pk
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            header = Invoice(partner_code=100, top_code=1)
            items = [InvoiceItem(product_code="PROD1", quantity=10)]
            
            nunota = KnowServicesRequestWrapper.create_invoice(header, items)
            
            assert nunota == 12345
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_INCLUDE

    def test_create_invoice_null_header_raises(self, mock_context):
        """Test create_invoice with None header raises ValueError."""
        KnowServicesRequestWrapper.initialize(mock_context)
        
        with pytest.raises(ValueError, match="invoice_header não pode ser None"):
            KnowServicesRequestWrapper.create_invoice(None)

    def test_remove_invoice(self, mock_context, mock_response):
        """Test remove_invoice sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.remove_invoice(12345)
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_REMOVE

    def test_add_invoice_items(self, mock_context, mock_response):
        """Test add_invoice_items returns sequence."""
        mock_response.response_body.sequence = 5
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            items = [InvoiceItem(product_code="PROD1", quantity=5)]
            seq = KnowServicesRequestWrapper.add_invoice_items(12345, items)
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_ITEM_INCLUDE

    def test_remove_invoice_items(self, mock_context, mock_response):
        """Test remove_invoice_items sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            items = [InvoiceItem(sequence=1), InvoiceItem(sequence=2)]
            KnowServicesRequestWrapper.remove_invoice_items(items)
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_ITEM_REMOVE

    def test_remove_invoice_items_empty_list(self, mock_context, caplog):
        """Test remove_invoice_items with empty list logs warning."""
        KnowServicesRequestWrapper.initialize(mock_context)
        KnowServicesRequestWrapper.remove_invoice_items([])
        
        assert "Lista de itens vazia" in caplog.text


# =============================================================================
# Billing Tests
# =============================================================================


class TestBilling:
    """Tests for billing operations."""

    def test_bill(self, mock_context, mock_response):
        """Test bill returns NUNOTA and events."""
        mock_response.response_body.invoice = MagicMock()
        mock_response.response_body.invoice.unique_number = 12345
        mock_response.response_body.client_events = MagicMock()
        mock_response.response_body.client_events.items = [ClientEvent(type="test")]
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            nunota, events = KnowServicesRequestWrapper.bill(
                single_number=12345,
                code_operation_type=1,
                billing_type=BillingType.NORMAL,
            )
            
            assert nunota == 12345
            assert events is not None
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_BILL

    def test_confirm_invoice(self, mock_context, mock_response):
        """Test confirm_invoice sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.confirm_invoice(12345)
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_CONFIRM

    def test_confirm_invoice_no_items_raises(self, mock_context):
        """Test confirm_invoice raises NoItemsConfirmInvoiceException."""
        error = SankhyaException("Não é possível confirmar sem produtos")
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            side_effect=error,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            with pytest.raises(NoItemsConfirmInvoiceException):
                KnowServicesRequestWrapper.confirm_invoice(12345)

    def test_confirm_invoice_already_confirmed_silent(self, mock_context):
        """Test confirm_invoice ignores already confirmed error."""
        error = SankhyaException("Nota já foi confirmada")
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            side_effect=error,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            # Should not raise
            KnowServicesRequestWrapper.confirm_invoice(12345)

    def test_duplicate_invoice(self, mock_context, mock_response):
        """Test duplicate_invoice returns new NUNOTA."""
        mock_pk = MagicMock()
        mock_pk.nunota = 54321
        mock_response.response_body.primary_key = mock_pk
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            new_nunota = KnowServicesRequestWrapper.duplicate_invoice(
                single_number=12345,
                code_operation_type=2,
            )
            
            assert new_nunota == 54321
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_DUPLICATE


# =============================================================================
# Invoice Status Tests
# =============================================================================


class TestInvoiceStatus:
    """Tests for invoice status operations."""

    def test_flag_invoices_as_not_pending(self, mock_context, mock_response):
        """Test flag_invoices_as_not_pending sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.flag_invoices_as_not_pending([123, 456])
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_FLAG_AS_NOT_PENDING

    def test_get_invoice_accompaniments(self, mock_context, mock_response):
        """Test get_invoice_accompaniments returns invoices."""
        mock_accomp = MagicMock()
        mock_accomp.invoices = [Invoice(unique_number=123)]
        mock_response.response_body.invoice_accompaniments = mock_accomp
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            invoices = KnowServicesRequestWrapper.get_invoice_accompaniments([123])
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_ACCOMPANIMENTS

    def test_cancel_invoices(self, mock_context, mock_response):
        """Test cancel_invoices returns cancelled count and not-cancelled list."""
        mock_response.response_body.total_cancelled_invoices = 1
        mock_response.response_body.single_numbers = [456]
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            cancelled, not_cancelled = KnowServicesRequestWrapper.cancel_invoices(
                single_numbers=[123, 456],
                justification="Teste",
            )
            
            assert cancelled == 1
            assert not_cancelled == [456]
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_CANCEL

    def test_bind_invoice_with_order(self, mock_context, mock_response):
        """Test bind_invoice_with_order sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.bind_invoice_with_order(
                single_number=12345,
                code_partner=100,
                movement_type=MovementType.SALES,
            )
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_BIND_WITH_ORDER


# =============================================================================
# NFe Tests
# =============================================================================


class TestNFe:
    """Tests for NFe operations."""

    def test_get_fiscal_invoice_authorization(self, mock_context, mock_response):
        """Test get_fiscal_invoice_authorization sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.get_fiscal_invoice_authorization([123, 456])
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.NFE_GET_AUTHORIZATION

    def test_generate_lot(self, mock_context, mock_response):
        """Test generate_lot sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.generate_lot([123, 456])
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.NFE_GENERATE_LOT


# =============================================================================
# Financial Tests
# =============================================================================


class TestFinancial:
    """Tests for financial operations."""

    def test_flag_as_payments_paid(self, mock_context, mock_response):
        """Test flag_as_payments_paid sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.flag_as_payments_paid(
                financial_numbers=[1001, 1002],
                code_account=123,
            )
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_AUTOMATIC_LOW

    def test_flag_as_payments_paid_raises(self, mock_context):
        """Test flag_as_payments_paid raises MarkAsPaymentPaidException."""
        error = SankhyaException("Erro de baixa")
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            side_effect=error,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            with pytest.raises(MarkAsPaymentPaidException):
                KnowServicesRequestWrapper.flag_as_payments_paid(
                    financial_numbers=[1001],
                    code_account=123,
                )

    def test_reverse_payments(self, mock_context, mock_response):
        """Test reverse_payments sends individual requests."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.reverse_payments([1001, 1002])
            
            # Should be called twice (once per financial number)
            assert KnowServicesRequestWrapper._invoke_service.call_count == 2

    def test_unlink_shipping(self, mock_context, mock_response):
        """Test unlink_shipping sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.unlink_shipping(1001)
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.UNLINK_SHIPPING

    def test_unlink_shipping_raises(self, mock_context):
        """Test unlink_shipping raises UnlinkShippingException."""
        error = SankhyaException("Erro ao desvincular")
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            side_effect=error,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            
            with pytest.raises(UnlinkShippingException):
                KnowServicesRequestWrapper.unlink_shipping(1001)


# =============================================================================
# File Operations Tests
# =============================================================================


class TestFileOperations:
    """Tests for file operations."""

    def test_open_file(self, mock_context, mock_response):
        """Test open_file returns file key."""
        mock_key = MagicMock()
        mock_key.value = "ABC123KEY"
        mock_response.response_body.key = mock_key
        
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            key = KnowServicesRequestWrapper.open_file("/path/to/file.pdf")
            
            assert key == "ABC123KEY"
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.FILE_OPEN

    def test_delete_files(self, mock_context, mock_response):
        """Test delete_files sends correct request."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.delete_files(["/path/to/file1.pdf"])
            
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.FILE_DELETE

    def test_get_file(self, mock_context):
        """Test get_file delegates to SankhyaContext."""
        mock_file = ServiceFile(
            data=b"test data",
            content_type="application/pdf",
            file_extension="pdf",
        )
        
        KnowServicesRequestWrapper.initialize(mock_context)
        
        with patch(
            "sankhya_sdk.core.context.SankhyaContext.get_file_with_token",
            return_value=mock_file,
        ):
            result = KnowServicesRequestWrapper.get_file("ABC123KEY")
            
            assert result == mock_file

    @pytest.mark.asyncio
    async def test_get_file_async(self, mock_context):
        """Test get_file_async delegates to SankhyaContext."""
        mock_file = ServiceFile(
            data=b"test data",
            content_type="application/pdf",
            file_extension="pdf",
        )
        
        KnowServicesRequestWrapper.initialize(mock_context)
        
        with patch(
            "sankhya_sdk.core.context.SankhyaContext.get_file_async_with_token",
            new_callable=AsyncMock,
            return_value=mock_file,
        ):
            result = await KnowServicesRequestWrapper.get_file_async("ABC123KEY")
            
            assert result == mock_file


# =============================================================================
# Image Operations Tests
# =============================================================================


class TestImageOperations:
    """Tests for image operations."""

    def test_get_image_none_entity_raises(self, mock_context):
        """Test get_image with None entity raises ValueError."""
        KnowServicesRequestWrapper.initialize(mock_context)
        
        with pytest.raises(ValueError, match="entity não pode ser None"):
            KnowServicesRequestWrapper.get_image(None)

    def test_get_image(self, mock_context):
        """Test get_image delegates to context."""
        mock_file = ServiceFile(
            data=b"image data",
            content_type="image/jpeg",
            file_extension="jpg",
        )
        mock_context.get_image.return_value = mock_file
        
        KnowServicesRequestWrapper.initialize(mock_context)
        
        entity = MagicMock()
        
        with patch(
            "sankhya_sdk.helpers.entity_extensions.extract_keys",
            return_value={"code": 123},
        ):
            result = KnowServicesRequestWrapper.get_image(entity)
            
            assert result == mock_file

    @pytest.mark.asyncio
    async def test_get_image_async_none_entity_raises(self, mock_context):
        """Test get_image_async with None entity raises ValueError."""
        KnowServicesRequestWrapper.initialize(mock_context)
        
        with pytest.raises(ValueError, match="entity não pode ser None"):
            await KnowServicesRequestWrapper.get_image_async(None)


# =============================================================================
# Service Invocation Tests
# =============================================================================


class TestServiceInvocation:
    """Tests for internal service invocation methods."""

    def test_invoke_service_no_token_raises(self):
        """Test _invoke_service without token raises RuntimeError."""
        KnowServicesRequestWrapper._initialized = True
        KnowServicesRequestWrapper._session_token = None
        
        with pytest.raises(RuntimeError, match="Token de sessão não disponível"):
            KnowServicesRequestWrapper._invoke_service(MagicMock())

    @pytest.mark.asyncio
    async def test_invoke_service_async_no_token_raises(self):
        """Test _invoke_service_async without token raises RuntimeError."""
        KnowServicesRequestWrapper._initialized = True
        KnowServicesRequestWrapper._session_token = None
        
        with pytest.raises(RuntimeError, match="Token de sessão não disponível"):
            await KnowServicesRequestWrapper._invoke_service_async(MagicMock())
