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
from sankhya_sdk.enums.sankhya_warning_type import SankhyaWarningType
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
    ClientEvents,
    SystemWarningRecipient,
)
from sankhya_sdk.models.service.invoice_types import Invoice, InvoiceItem, Invoices
from sankhya_sdk.models.service.response_body import ResponseBody
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
    KnowServicesRequestWrapper._owns_session = False
    KnowServicesRequestWrapper._initialized = False
    KnowServicesRequestWrapper._last_time_message_received = datetime.now()
    yield
    KnowServicesRequestWrapper._context = None
    KnowServicesRequestWrapper._session_token = None
    KnowServicesRequestWrapper._owns_session = False
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


def _sent_request_xml() -> str:
    """Retorna o XML da última requisição enviada a ``_invoke_service`` (mockado)."""
    request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
    return request.to_xml_string()


def _service_response(service_name: str, response_body_xml: str) -> ServiceResponse:
    """Cria um ServiceResponse real a partir do XML do ``<responseBody>``."""
    return ServiceResponse.from_xml_string(
        f'<serviceResponse serviceName="{service_name}" status="1">'
        f"<responseBody>{response_body_xml}</responseBody>"
        "</serviceResponse>"
    )


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
        """Test dispose releases resources without finalizing the context's main session."""
        KnowServicesRequestWrapper.initialize(mock_context)
        KnowServicesRequestWrapper.dispose()

        assert KnowServicesRequestWrapper._initialized is False
        assert KnowServicesRequestWrapper._context is None
        assert KnowServicesRequestWrapper._session_token is None
        # A sessão principal pertence ao contexto (o .NET nunca a finaliza a
        # partir do KnowServicesRequestWrapper); finalize_session(context.token)
        # seria apenas um no-op com aviso.
        mock_context.finalize_session.assert_not_called()

    def test_initialize_with_context_does_not_acquire_session(self, mock_context):
        """Test initialize(context) uses the context's main session (documented decision)."""
        KnowServicesRequestWrapper.initialize(mock_context)

        mock_context.acquire_new_session.assert_not_called()
        assert KnowServicesRequestWrapper._session_token == mock_context.token
        assert KnowServicesRequestWrapper._owns_session is False

    def test_dispose_finalizes_session_acquired_without_context(self):
        """Test dispose finalizes the dedicated KNOW_SERVICES session it acquired."""
        mock_ctx = MagicMock()
        acquired_token = uuid.uuid4()
        mock_ctx.acquire_new_session.return_value = acquired_token

        with patch(
            "sankhya_sdk.core.context.SankhyaContext.from_settings",
            return_value=mock_ctx,
        ):
            KnowServicesRequestWrapper.initialize()

        assert KnowServicesRequestWrapper._session_token == acquired_token
        assert KnowServicesRequestWrapper._owns_session is True

        KnowServicesRequestWrapper.dispose()

        mock_ctx.finalize_session.assert_called_once_with(acquired_token)
        assert KnowServicesRequestWrapper._owns_session is False
        assert KnowServicesRequestWrapper._session_token is None

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

    def test_get_sessions_parses_dotnet_sessions_xml(self, mock_context):
        """Test get_sessions returns the <SESSIONS><SESSION .../> entries (with host)."""
        # .NET: response.ResponseBody.Sessions.Sessions (SessionsResponse/Session.cs)
        response = _service_response(
            "SessionManagerSP.getCoreSessions",
            "<SESSIONS>"
            '<SESSION ID="ABC123" USERID="7" USERNAME="SUP" HOST="10.0.0.5" '
            'USERAGENT="Mozilla" AUTHENTICATED="S"/>'
            "</SESSIONS>",
        )

        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            sessions = KnowServicesRequestWrapper.get_sessions()

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="SessionManagerSP.getCoreSessions">'
                "<requestBody/>"
                "</serviceRequest>"
            )
        assert len(sessions) == 1
        assert sessions[0].session_id == "ABC123"
        assert sessions[0].user_id == 7
        assert sessions[0].user_name == "SUP"
        assert sessions[0].host == "10.0.0.5"
        assert sessions[0].is_authenticated is True

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

    def test_send_warning_request_xml_matches_dotnet(self, mock_context, mock_response):
        """Test send_warning sends <Dica>, importancia and recipients like .NET."""
        # .NET KnowServicesRequestWrapper.cs:54-74 (SystemWarning: importancia,
        # titulo, descricao, Dica, destinatario id/tipo)
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.send_warning(
                title="Manutencao",
                description="Sistema fora do ar",
                tip="Salve seu trabalho",
                level=SankhyaWarningLevel.WARNING,
                recipients=[
                    SystemWarningRecipient(user_id=1, type=SankhyaWarningType.USER),
                    SystemWarningRecipient(user_id=5, type=SankhyaWarningType.GROUP),
                ],
            )

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="AvisoSistemaSP.enviarAviso">'
                "<requestBody>"
                '<aviso importancia="2">'
                "<titulo>Manutencao</titulo>"
                "<descricao>Sistema fora do ar</descricao>"
                "<Dica>Salve seu trabalho</Dica>"
                '<destinatario id="1" tipo="usuario"/>'
                '<destinatario id="5" tipo="grupo"/>'
                "</aviso>"
                "</requestBody>"
                "</serviceRequest>"
            )

    @pytest.mark.parametrize("tip", [None, "", "   "])
    def test_send_warning_blank_tip_is_not_sent(self, mock_context, mock_response, tip):
        """Test send_warning omits <Dica> when tip is blank (.NET IsNullOrWhiteSpace)."""
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.send_warning(
                title="Aviso",
                description="Descricao",
                tip=tip,
                level=SankhyaWarningLevel.URGENT,
            )

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="AvisoSistemaSP.enviarAviso">'
                "<requestBody>"
                '<aviso importancia="0">'
                "<titulo>Aviso</titulo>"
                "<descricao>Descricao</descricao>"
                "</aviso>"
                "</requestBody>"
                "</serviceRequest>"
            )

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

    def test_create_invoice_returns_int_from_pk_response(self, mock_context):
        """Test create_invoice returns the <pk><NUNOTA> text as int (.NET ToInt32)."""
        # .NET KnowServicesRequestWrapper.cs:154-156:
        # response.ResponseBody.PrimaryKey.NUNOTA.ToString().ToInt32()
        response = _service_response(
            "CACSP.incluirNota", "<pk><NUNOTA>12345</NUNOTA></pk>"
        )

        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            nunota = KnowServicesRequestWrapper.create_invoice(
                Invoice(partner_code=100, top_code=1)
            )

        assert nunota == 12345
        assert type(nunota) is int

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

    def test_remove_invoice_request_xml_matches_dotnet(self, mock_context, mock_response):
        """Test remove_invoice sends <notas><nota NUNOTA="n"/></notas> like .NET."""
        # .NET KnowServicesRequestWrapper.cs:159-170:
        # Invoices = new() { Invoice = new() { SingleNumberDuplication = singleNumber } }
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.remove_invoice(12345)

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="CACSP.excluirNotas">'
                "<requestBody>"
                '<notas><nota NUNOTA="12345"/></notas>'
                "</requestBody>"
                "</serviceRequest>"
            )

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
        # Real ResponseBody: the billed invoice comes in <notas><nota>, i.e.
        # response_body.invoices.items[0] (.NET: ResponseBody.Invoices.Invoice)
        response_events = [ClientEvent(type="test")]
        mock_response.response_body = ResponseBody(
            invoices=Invoices(items=[Invoice(unique_number=12345)]),
            client_events=ClientEvents(items=response_events),
        )
        
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
            assert events == response_events
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

    def test_duplicate_invoice(self, mock_context):
        """Test duplicate_invoice returns new NUNOTA."""
        # Real primary-key response: <pk><NUNOTA>...</NUNOTA></pk> is
        # deserialized as Key(values={"NUNOTA": "54321"}) (XML text).
        response = ServiceResponse.from_xml_string(
            '<serviceResponse serviceName="CACSP.duplicarNota" status="1">'
            "<responseBody><pk><NUNOTA>54321</NUNOTA></pk></responseBody>"
            "</serviceResponse>"
        )

        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)

            new_nunota = KnowServicesRequestWrapper.duplicate_invoice(
                single_number=12345,
                code_operation_type=2,
            )

            assert new_nunota == 54321
            assert isinstance(new_nunota, int)
            request = KnowServicesRequestWrapper._invoke_service.call_args[0][0]
            assert request.service == ServiceName.INVOICE_DUPLICATE

    def test_duplicate_invoice_from_invoices_response(self, mock_context, mock_response):
        """Test duplicate_invoice reads destiny NUNOTA from invoices (.NET path)."""
        # .NET: response.ResponseBody.Invoices.Invoice.SingleNumberDuplicationDestiny
        mock_response.response_body = ResponseBody(
            invoices=Invoices(
                items=[
                    Invoice(
                        extra_data={"singleNumberDuplicationDestiny": "54321"}
                    )
                ]
            )
        )
        
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

    def test_get_invoice_accompaniments_request_xml_matches_dotnet(
        self, mock_context, mock_response
    ):
        """Test get_invoice_accompaniments sends <notas><nunota>...</notas> like .NET."""
        # .NET KnowServicesRequestWrapper.cs:375-389:
        # Invoices = new() { SingleNumbers = singleNumbersList }
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.get_invoice_accompaniments([123, 456])

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="ServicosNfeSP.getAcompanhamentosNota">'
                "<requestBody>"
                "<notas><nunota>123</nunota><nunota>456</nunota></notas>"
                "</requestBody>"
                "</serviceRequest>"
            )

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

    def test_get_fiscal_invoice_authorization_request_xml_matches_dotnet(
        self, mock_context, mock_response
    ):
        """Test get_fiscal_invoice_authorization sends <nunota> children like .NET."""
        # .NET KnowServicesRequestWrapper.cs:501-515:
        # Invoices = new() { SingleNumbers = singleNumbersLists }
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.get_fiscal_invoice_authorization([123, 456])

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="ServicosNfeSP.buscaProcessamentoLote">'
                "<requestBody>"
                "<notas><nunota>123</nunota><nunota>456</nunota></notas>"
                "</requestBody>"
                "</serviceRequest>"
            )

    def test_generate_lot_request_xml_matches_dotnet(self, mock_context, mock_response):
        """Test generate_lot sends retNotasReprovadas="N" and <nunota> children like .NET."""
        # .NET KnowServicesRequestWrapper.cs:517-538:
        # Invoices = new() { ReturnDisapprovedInvoices = false, SingleNumbers = ... }
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.generate_lot([123, 456])

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="ServicosNfeSP.gerarLote">'
                "<requestBody>"
                '<notas retNotasReprovadas="N">'
                "<nunota>123</nunota><nunota>456</nunota>"
                "</notas>"
                "</requestBody>"
                "</serviceRequest>"
            )


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

    def test_delete_files_request_xml_matches_dotnet(self, mock_context, mock_response):
        """Test delete_files sends the clientconfirm event and paths like .NET."""
        # .NET KnowServicesRequestWrapper.cs:641-655: Paths (<arquivos><path>)
        # e ClientEvent { Text = "br.com.sankhya.actionbutton.clientconfirm" }
        with patch.object(
            KnowServicesRequestWrapper,
            "_invoke_service",
            return_value=mock_response,
        ):
            KnowServicesRequestWrapper.initialize(mock_context)
            KnowServicesRequestWrapper.delete_files(
                ["/path/to/file1.pdf", "/path/to/file2.pdf"]
            )

            assert _sent_request_xml() == (
                '<serviceRequest serviceName="ImportacaoImagemSP.deletaArquivos">'
                "<requestBody>"
                "<clientEventList>"
                "<clientEvent>br.com.sankhya.actionbutton.clientconfirm</clientEvent>"
                "</clientEventList>"
                "<arquivos>"
                "<path>/path/to/file1.pdf</path>"
                "<path>/path/to/file2.pdf</path>"
                "</arquivos>"
                "</requestBody>"
                "</serviceRequest>"
            )

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
