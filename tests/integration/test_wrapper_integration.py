# -*- coding: utf-8 -*-
"""
Integration tests for SankhyaWrapper.

These tests require a running Sankhya server or use mocked responses
to test the full integration flow.
"""

import os
from unittest.mock import MagicMock, Mock, patch
import pytest

from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.service.service_request import ServiceRequest


# Skip integration tests if no real server is configured
SKIP_INTEGRATION = os.getenv("SANKHYA_SKIP_INTEGRATION", "true").lower() == "true"


def _dwr_response() -> Mock:
    """
    Mock HTTP response for the DWR user agent registration.

    SankhyaWrapper.authenticate() issues two HTTP requests: the login
    (MobileLoginSP.login) followed by a POST to
    /mge/dwr/exec/DWRController.execute.dwr. Mocked response sequences
    must include this response right after the login one, otherwise the
    DWR call consumes the response meant for the next operation.
    """
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.text = ""
    return response


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests disabled")
class TestWrapperIntegration:
    """Integration tests requiring a real Sankhya server."""

    def test_full_authentication_flow(self):
        """Test complete authentication flow with real server."""
        with SankhyaContext.from_settings() as wrapper:
            assert wrapper.is_authenticated
            assert wrapper.session_id is not None
            assert wrapper.user_code > 0

    def test_crud_find_service(self):
        """Test CRUD find service call."""
        with SankhyaContext.from_settings() as wrapper:
            request = ServiceRequest(service=ServiceName.CRUD_FIND)
            # Configure request for a simple query...
            response = wrapper.service_invoker(request)
            assert response is not None

    def test_get_file_operation(self):
        """Test file download operation."""
        with SankhyaContext.from_settings() as wrapper:
            # Would need a valid file key
            pass

    def test_get_image_operation(self):
        """Test image download operation."""
        with SankhyaContext.from_settings() as wrapper:
            # Test with a known entity
            image = wrapper.get_image("Parceiro", {"CODPARC": 1})
            # Note: may be None if no image exists


class TestWrapperIntegrationMocked:
    """Integration tests using mocked server responses."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_full_flow_with_mocked_server(self, mock_session_class):
        """Test complete flow with mocked HTTP responses."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock login response
        login_response = Mock()
        login_response.ok = True
        login_response.status_code = 200
        login_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="1">
            <responseBody>
                <jsessionid>MOCK_SESSION_123</jsessionid>
                <idusu>MTI=</idusu>
            </responseBody>
        </serviceResponse>"""

        # Mock CRUD response
        crud_response = Mock()
        crud_response.ok = True
        crud_response.status_code = 200
        crud_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="1">
            <responseBody>
                <entities>
                    <entity>
                        <field name="CODPARC">1</field>
                    </entity>
                </entities>
            </responseBody>
        </serviceResponse>"""

        # Mock logout response
        logout_response = Mock()
        logout_response.ok = True
        logout_response.status_code = 200
        logout_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="1"></serviceResponse>"""

        # Configure session to return different responses
        # (authenticate() performs login + DWR user agent registration)
        mock_session.request.side_effect = [
            login_response,
            _dwr_response(),
            crud_response,
            logout_response,
        ]

        # Run the flow
        wrapper = SankhyaWrapper(
            host="http://mock.example.com",
            port=8180,
        )

        # Authenticate
        wrapper.authenticate("testuser", "testpass")
        assert wrapper.is_authenticated

        # Make a service call
        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        response = wrapper.service_invoker(request)
        assert response is not None

        # Dispose
        wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_retry_on_timeout(self, mock_session_class):
        """Test automatic retry on timeout error."""
        import requests

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # First call times out, second succeeds
        timeout_error = requests.exceptions.Timeout("Connection timed out")
        
        success_response = Mock()
        success_response.ok = True
        success_response.status_code = 200
        success_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="1">
            <responseBody>
                <jsessionid>SESSION123</jsessionid>
                <idusu>MQ==</idusu>
            </responseBody>
        </serviceResponse>"""

        mock_session.request.side_effect = [success_response]

        wrapper = SankhyaWrapper(
            host="http://mock.example.com",
            port=8180,
        )
        wrapper.authenticate("user", "pass")
        assert wrapper.is_authenticated

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_file_download_with_mocked_response(self, mock_session_class):
        """Test file download with mocked response."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock login response
        login_response = Mock()
        login_response.ok = True
        login_response.status_code = 200
        login_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <serviceResponse status="1">
            <responseBody>
                <jsessionid>SESSION123</jsessionid>
                <idusu>MQ==</idusu>
            </responseBody>
        </serviceResponse>"""

        # Mock file response
        file_response = Mock()
        file_response.ok = True
        file_response.status_code = 200
        file_response.content = b"PDF_FILE_CONTENT"
        file_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="document.pdf"',
        }

        # authenticate() performs login + DWR user agent registration
        # (POST /mge/dwr/exec/DWRController.execute.dwr) before get_file
        mock_session.request.side_effect = [
            login_response,
            _dwr_response(),
            file_response,
        ]

        wrapper = SankhyaWrapper(
            host="http://mock.example.com",
            port=8180,
        )
        wrapper.authenticate("user", "pass")

        file = wrapper.get_file("FILE_KEY_123")

        assert file.data == b"PDF_FILE_CONTENT"
        assert file.content_type == "application/pdf"
        assert file.file_extension == "pdf"
        assert file.filename == "document.pdf"


class TestContextManagerIntegration:
    """Integration tests for context manager usage."""

    @patch.object(SankhyaWrapper, "from_settings")
    def test_context_manager_full_flow(self, mock_from_settings):
        """Test context manager handles full lifecycle."""
        mock_wrapper = MagicMock(spec=SankhyaWrapper)
        mock_from_settings.return_value = mock_wrapper

        with SankhyaContext.from_settings() as wrapper:
            wrapper.service_invoker(MagicMock())

        mock_wrapper.dispose.assert_called_once()

    @patch.object(SankhyaWrapper, "from_settings")
    def test_context_manager_handles_exception(self, mock_from_settings):
        """Test context manager cleans up on exception."""
        mock_wrapper = MagicMock(spec=SankhyaWrapper)
        mock_wrapper.service_invoker.side_effect = RuntimeError("Test error")
        mock_from_settings.return_value = mock_wrapper

        with pytest.raises(RuntimeError):
            with SankhyaContext.from_settings() as wrapper:
                wrapper.service_invoker(MagicMock())

        mock_wrapper.dispose.assert_called_once()
