"""Unit tests for GatewayClient."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sankhya_sdk.http.gateway_client import GatewayClient, GatewayModule, MODULE_SERVICE_MAP


class TestGatewayModule:
    """Tests for GatewayModule enum."""
    
    def test_mge_value(self):
        assert GatewayModule.MGE.value == "mge"
    
    def test_mgecom_value(self):
        assert GatewayModule.MGECOM.value == "mgecom"


class TestModuleServiceMap:
    """Tests for service to module mapping."""
    
    def test_crud_service_maps_to_mge(self):
        assert MODULE_SERVICE_MAP["CRUDServiceProvider"] == GatewayModule.MGE
    
    def test_dataset_sp_maps_to_mge(self):
        assert MODULE_SERVICE_MAP["DatasetSP"] == GatewayModule.MGE
    
    def test_cacsp_maps_to_mgecom(self):
        assert MODULE_SERVICE_MAP["CACSP"] == GatewayModule.MGECOM
    
    def test_selecao_documento_maps_to_mgecom(self):
        assert MODULE_SERVICE_MAP["SelecaoDocumentoSP"] == GatewayModule.MGECOM


class TestGatewayClient:
    """Tests for GatewayClient class."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SankhyaSession."""
        session = Mock()
        response = Mock()
        response.json.return_value = {"status": "success"}
        response.raise_for_status = Mock()
        session.post.return_value = response
        return session
    
    @pytest.fixture
    def client(self, mock_session):
        """Create a GatewayClient with mock session."""
        return GatewayClient(mock_session)
    
    def test_init_with_default_module(self, mock_session):
        client = GatewayClient(mock_session)
        assert client.default_module == GatewayModule.MGE
    
    def test_init_with_custom_module(self, mock_session):
        client = GatewayClient(mock_session, default_module=GatewayModule.MGECOM)
        assert client.default_module == GatewayModule.MGECOM
    
    def test_resolve_module_crud_service(self, client):
        module = client._resolve_module("CRUDServiceProvider.loadRecords")
        assert module == GatewayModule.MGE
    
    def test_resolve_module_cacsp(self, client):
        module = client._resolve_module("CACSP.IncluirNota")
        assert module == GatewayModule.MGECOM
    
    def test_resolve_module_unknown_uses_default(self, client):
        module = client._resolve_module("UnknownService.method")
        assert module == GatewayModule.MGE
    
    def test_build_url_mge(self, client):
        url = client._build_url(GatewayModule.MGE, "TestService")
        assert url == "/gateway/v1/mge/service.sbr?serviceName=TestService&outputType=json"
    
    def test_build_url_mgecom(self, client):
        url = client._build_url(GatewayModule.MGECOM, "TestService")
        assert url == "/gateway/v1/mgecom/service.sbr?serviceName=TestService&outputType=json"
    
    def test_execute_service_calls_post(self, client, mock_session):
        result = client.execute_service("CRUDServiceProvider.test", {"data": "test"})
        
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert "outputType=json" in call_args[0][0]
        assert result == {"status": "success"}
    
    def test_execute_service_with_module_override(self, client, mock_session):
        client.execute_service(
            "CRUDServiceProvider.test",
            {"data": "test"},
            module=GatewayModule.MGECOM
        )
        
        call_args = mock_session.post.call_args
        assert "/mgecom/" in call_args[0][0]


class TestGatewayClientLoadRecords:
    """Tests for load_records method."""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock()
        response = Mock()
        response.json.return_value = {"entities": []}
        response.raise_for_status = Mock()
        session.post.return_value = response
        return session
    
    @pytest.fixture
    def client(self, mock_session):
        return GatewayClient(mock_session)
    
    def test_load_records_builds_correct_payload(self, client, mock_session):
        client.load_records("Parceiro", ["CODPARC", "NOMEPARC"])
        
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        
        assert payload["serviceName"] == "CRUDServiceProvider.loadRecords"
        assert payload["requestBody"]["dataSet"]["rootEntity"] == "Parceiro"
        assert payload["requestBody"]["dataSet"]["entity"]["fieldset"]["list"] == "CODPARC,NOMEPARC"
    
    def test_load_records_with_criteria(self, client, mock_session):
        client.load_records("Parceiro", ["CODPARC"], criteria="CODPARC > 0")
        
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        
        assert "criteria" in payload["requestBody"]["dataSet"]
        assert payload["requestBody"]["dataSet"]["criteria"]["expression"]["$"] == "CODPARC > 0"


class TestGatewayClientSaveRecord:
    """Tests for save_record method."""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock()
        response = Mock()
        response.json.return_value = {"pk": {"CODPARC": {"$": "123"}}}
        response.raise_for_status = Mock()
        session.post.return_value = response
        return session
    
    @pytest.fixture
    def client(self, mock_session):
        return GatewayClient(mock_session)
    
    def test_save_record_builds_correct_payload(self, client, mock_session):
        client.save_record("Parceiro", {"NOMEPARC": "Teste", "ATIVO": "S"})
        
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        
        assert payload["serviceName"] == "CRUDServiceProvider.saveRecord"
        assert payload["requestBody"]["dataSet"]["rootEntity"] == "Parceiro"
        
        local_fields = payload["requestBody"]["dataSet"]["dataRow"]["localFields"]
        assert local_fields["NOMEPARC"]["$"] == "Teste"
        assert local_fields["ATIVO"]["$"] == "S"
