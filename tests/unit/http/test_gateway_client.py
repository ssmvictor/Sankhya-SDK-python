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
            "CRUDServiceProvider.test", {"data": "test"}, module=GatewayModule.MGECOM
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


class TestGatewayClientSaveRecordDatasetUpdate:
    """Tests for save_record with pk (DatasetSP.save)."""

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        response = Mock()
        response.json.return_value = {"status": "1", "responseBody": {}}
        response.raise_for_status = Mock()
        session.post.return_value = response
        return session

    @pytest.fixture
    def client(self, mock_session):
        return GatewayClient(mock_session)

    def test_save_record_with_pk_uses_dataset_sp(self, client, mock_session):
        """Update with pk should use DatasetSP.save."""
        client.save_record("Parceiro", {"NOMEPARC": "Teste"}, pk={"CODPARC": "4454"})

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert payload["serviceName"] == "DatasetSP.save"
        assert payload["requestBody"]["entityName"] == "Parceiro"
        assert payload["requestBody"]["records"][0]["pk"]["CODPARC"] == "4454"

    def test_save_record_with_pk_builds_correct_fields_order(self, client, mock_session):
        """Fields should have PK first, then value fields."""
        client.save_record(
            "Parceiro", {"NOMEPARC": "Teste", "EMAIL": "x@y.com"}, pk={"CODPARC": "4454"}
        )

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        fields = payload["requestBody"]["fields"]

        # PK first, then value fields
        assert fields[0] == "CODPARC"
        assert "NOMEPARC" in fields
        assert "EMAIL" in fields

    def test_save_record_with_pk_values_indexed_correctly(self, client, mock_session):
        """Values should be indexed by position, excluding PK."""
        client.save_record("Parceiro", {"NOMEPARC": "Teste"}, pk={"CODPARC": "4454"})

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]
        values = payload["requestBody"]["records"][0]["values"]

        # CODPARC is index 0 (PK), NOMEPARC is index 1
        # values should NOT contain "0" (it's PK)
        assert "0" not in values
        assert values["1"] == "Teste"

    def test_save_record_with_pk_composite_key(self, client, mock_session):
        """Composite PK should work correctly."""
        client.save_record(
            "CabecalhoNota", {"VLRNOTA": "1000.50"}, pk={"NUNOTA": "100", "SEQUENCIA": "1"}
        )

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        pk = payload["requestBody"]["records"][0]["pk"]
        assert pk["NUNOTA"] == "100"
        assert pk["SEQUENCIA"] == "1"
        # VLRNOTA should be at index 2 (after the 2 PK fields)
        assert payload["requestBody"]["records"][0]["values"]["2"] == "1000.50"

    def test_save_record_without_pk_uses_crud_provider(self, client, mock_session):
        """Without pk, should use CRUDServiceProvider.saveRecord."""
        client.save_record("Parceiro", {"NOMEPARC": "Teste", "ATIVO": "S"})

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert payload["serviceName"] == "CRUDServiceProvider.saveRecord"

    def test_save_record_with_pk_but_use_dataset_false(self, client, mock_session):
        """With pk but use_dataset_for_update=False, should use CRUDService."""
        client.save_record(
            "Parceiro", {"NOMEPARC": "Teste"}, pk={"CODPARC": "4454"}, use_dataset_for_update=False
        )

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert payload["serviceName"] == "CRUDServiceProvider.saveRecord"

    def test_save_record_with_stand_alone(self, client, mock_session):
        """standAlone flag should be passed correctly."""
        client.save_record(
            "Parceiro", {"NOMEPARC": "Teste"}, pk={"CODPARC": "4454"}, stand_alone=True
        )

        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert payload["requestBody"]["standAlone"] is True
