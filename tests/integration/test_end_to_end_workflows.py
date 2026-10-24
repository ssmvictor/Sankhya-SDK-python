# -*- coding: utf-8 -*-
"""
Testes de integração end-to-end para workflows completos.

Testa fluxos completos de criação, busca, atualização e deleção.

Criação usa ``SimpleCRUDRequestWrapper.update``, que invoca
``CRUDServiceProvider.saveRecord`` (Create/Update), como no SDK .NET.

O SimpleCRUDRequestWrapper usa uma sessão dedicada (novo login), como
``Context.AcquireNewSession(SimpleCrud)`` no .NET; o ``FakeSankhyaServer``
responde login/logout/DWR e entrega a fila de respostas, em ordem, apenas
às chamadas de serviço, registrando o XML enviado em cada uma.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.models.transport.neighborhood import Neighborhood
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    FakeSankhyaServer,
    create_error_response,
    create_success_response,
    find_criteria,
    http_response,
    request_xml,
    save_data_row,
    simple_crud_session,
)


FIND = ServiceName.CRUD_SERVICE_FIND.internal_value
SAVE = ServiceName.CRUD_SERVICE_SAVE.internal_value
REMOVE = ServiceName.CRUD_SERVICE_REMOVE.internal_value

DELETE_OK = b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'


def _install(mock_session_class, server: FakeSankhyaServer) -> None:
    """Instala o servidor simulado no transporte HTTP do SDK."""
    mock_session_class.return_value.request.side_effect = server


def _root_entity(body: str) -> str:
    """Entidade raiz da requisição (dataSet ou entity de removeRecord)."""
    request_body = request_xml(body).find("requestBody")
    element = request_body.find("dataSet")
    if element is None:
        element = request_body.find("entity")
    return element.get("rootEntity")


@pytest.mark.integration
class TestPartnerWorkflow:
    """Testes de workflow completo de Partner."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_complete_partner_workflow(self, mock_session_class):
        """Criar, buscar, atualizar, deletar Partner."""
        server = FakeSankhyaServer([
            # 1. Criar partner
            http_response(200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Novo Parceiro", "EMAIL": "email@test.com"}
            ])),
            # 2. Buscar partner criado
            http_response(200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Novo Parceiro", "EMAIL": "email@test.com"}
            ])),
            # 3. Atualizar partner
            http_response(200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Parceiro Atualizado", "EMAIL": "novo@test.com"}
            ])),
            # 4. Buscar partner atualizado
            http_response(200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Parceiro Atualizado", "EMAIL": "novo@test.com"}
            ])),
            # 5. Deletar partner
            http_response(200, DELETE_OK),
            # 6. Verificar deleção (não deve encontrar)
            http_response(200, create_success_response([])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # 1. Criar
            new_partner = Partner(name="Novo Parceiro", email_address="email@test.com")
            created = SimpleCRUDRequestWrapper.update(new_partner)
            assert created.code == 1001
            assert created.name == "Novo Parceiro"
            
            # 2. Buscar
            search = Partner(code=1001)
            found = SimpleCRUDRequestWrapper.try_find(search)
            assert found is not None
            assert found.code == 1001
            
            # 3. Atualizar
            found.name = "Parceiro Atualizado"
            found.email_address = "novo@test.com"
            updated = SimpleCRUDRequestWrapper.update(found)
            assert updated.name == "Parceiro Atualizado"
            
            # 4. Verificar atualização
            search = Partner(code=1001)
            found_updated = SimpleCRUDRequestWrapper.try_find(search)
            assert found_updated is not None
            assert found_updated.name == "Parceiro Atualizado"
            
            # 5. Deletar
            SimpleCRUDRequestWrapper.remove(Partner(code=1001))
            
            # 6. Verificar deleção
            deleted = SimpleCRUDRequestWrapper.try_find(Partner(code=1001))
            assert deleted is None
        
        # Sequência de serviços enviada ao servidor
        assert server.calls == [SAVE, FIND, SAVE, FIND, REMOVE, FIND]
        assert all(_root_entity(body) == "Parceiro" for _, body in server.requests)
        
        saves = [save_data_row(body) for service, body in server.requests if service == SAVE]
        assert saves[0] == ({}, {"NOMEPARC": "Novo Parceiro", "EMAIL": "email@test.com"})
        # Atualização: a chave vai em key e os campos alterados em localFields
        keys, local_fields = saves[1]
        assert keys == {"CODPARC": "1001"}
        assert local_fields["NOMEPARC"] == "Parceiro Atualizado"
        assert local_fields["EMAIL"] == "novo@test.com"
        
        finds = [find_criteria(body) for service, body in server.requests if service == FIND]
        assert finds == ["CODPARC = 1001"] * 3


@pytest.mark.integration
class TestProductWorkflow:
    """Testes de workflow completo de Product."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_complete_product_workflow(self, mock_session_class):
        """Criar, buscar, atualizar, deletar Product."""
        server = FakeSankhyaServer([
            # 1. Criar produto
            http_response(200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Teste", "CODVOL": "UN"}
            ])),
            # 2. Buscar produto
            http_response(200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Teste", "CODVOL": "UN"}
            ])),
            # 3. Atualizar produto
            http_response(200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Atualizado", "CODVOL": "KG"}
            ])),
            # 4. Deletar produto
            http_response(200, DELETE_OK),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # 1. Criar
            new_product = Product(name="Produto Teste", code_volume="UN")
            created = SimpleCRUDRequestWrapper.update(new_product)
            assert created.code == 500
            
            # 2. Buscar
            found = SimpleCRUDRequestWrapper.try_find(Product(code=500))
            assert found is not None
            
            # 3. Atualizar
            found.name = "Produto Atualizado"
            found.code_volume = "KG"
            updated = SimpleCRUDRequestWrapper.update(found)
            assert updated.name == "Produto Atualizado"
            
            # 4. Deletar
            SimpleCRUDRequestWrapper.remove(Product(code=500))
        
        assert server.calls == [SAVE, FIND, SAVE, REMOVE]
        assert all(_root_entity(body) == "Produto" for _, body in server.requests)
        keys, local_fields = save_data_row(server.requests[2][1])
        assert keys == {"CODPROD": "500"}
        assert local_fields["DESCRPROD"] == "Produto Atualizado"
        assert local_fields["CODVOL"] == "KG"


@pytest.mark.integration
class TestBulkImport:
    """Testes de importação em lote."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_partner_import(self, mock_session_class):
        """Importar múltiplos parceiros em lote."""
        # Respostas para 10 criações
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": str(i), "NOMEPARC": f"Parceiro Importado {i}"}
            ]))
            for i in range(1, 11)
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            imported = []
            for i in range(1, 11):
                partner = Partner(name=f"Parceiro Importado {i}")
                result = SimpleCRUDRequestWrapper.update(partner)
                imported.append(result)
        
        assert len(imported) == 10
        for i, p in enumerate(imported, 1):
            assert p.code == i
            assert f"Parceiro Importado {i}" in p.name
        
        assert [save_data_row(body)[1] for body in server.bodies(ServiceName.CRUD_SERVICE_SAVE)] == [
            {"NOMEPARC": f"Parceiro Importado {i}"} for i in range(1, 11)
        ]

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_product_update(self, mock_session_class):
        """Atualizar múltiplos produtos."""
        # Respostas para 5 atualizações
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPROD": str(i), "DESCRPROD": f"Produto Atualizado {i}", "CODVOL": "UN"}
            ]))
            for i in range(1, 6)
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            updated = []
            for i in range(1, 6):
                product = Product(code=i, name=f"Produto Atualizado {i}")
                result = SimpleCRUDRequestWrapper.update(product)
                updated.append(result)
        
        assert len(updated) == 5
        for i, p in enumerate(updated, 1):
            assert "Atualizado" in p.name
        
        assert [save_data_row(body) for body in server.bodies(ServiceName.CRUD_SERVICE_SAVE)] == [
            ({"CODPROD": str(i)}, {"DESCRPROD": f"Produto Atualizado {i}"})
            for i in range(1, 6)
        ]


@pytest.mark.integration
class TestComplexQueries:
    """Testes de queries complexas."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_complex_query_multiple_entities(self, mock_session_class):
        """Query que retorna múltiplas entidades relacionadas."""
        # Buscar parceiros com cidade específica
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro 1", "CODCID": "100"},
                {"CODPARC": "2", "NOMEPARC": "Parceiro 2", "CODCID": "100"},
                {"CODPARC": "3", "NOMEPARC": "Parceiro 3", "CODCID": "100"},
            ], total_records=3)),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Critério CODCID = 100 a partir dos campos preenchidos da entidade
            results = SimpleCRUDRequestWrapper.find_all(Partner(code_city=100))
        
        assert len(results) == 3
        for p in results:
            assert p.code_city == 100
        
        (body,) = server.bodies(ServiceName.CRUD_SERVICE_FIND)
        assert find_criteria(body) == "CODCID = 100"


@pytest.mark.integration
class TestTransactionRollback:
    """Testes de rollback de transação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_transaction_rollback_on_error(self, mock_session_class):
        """Testa rollback de transação em erro."""
        server = FakeSankhyaServer([
            # Primeira criação OK
            http_response(200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro 1"}
            ])),
            # Segunda criação falha
            http_response(200, create_error_response("DB.ERROR", "Erro de banco")),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Primeira criação deve funcionar
            p1 = SimpleCRUDRequestWrapper.update(Partner(name="Parceiro 1"))
            assert p1.code == 1
            
            # Segunda criação deve falhar
            with pytest.raises(SankhyaException) as exc_info:
                SimpleCRUDRequestWrapper.update(Partner(name="Parceiro 2"))
        
        assert "Erro de banco" in str(exc_info.value)
        # Mensagem sem tratamento específico não é retentada
        # (StatusMessageHelper.cs:261, ServiceRequestUnexpectedResultException)
        assert server.calls == [SAVE, SAVE]


@pytest.mark.integration
class TestNeighborhoodWorkflow:
    """Testes de workflow de Neighborhood."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_neighborhood_crud(self, mock_session_class):
        """CRUD completo de bairros."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODBAI": "100", "NOMEBAI": "Centro"}
            ])),
            http_response(200, create_success_response([
                {"CODBAI": "100", "NOMEBAI": "Centro"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Criar
            neighborhood = Neighborhood(name="Centro")
            created = SimpleCRUDRequestWrapper.update(neighborhood)
            assert created.code == 100
            
            # Buscar
            found = SimpleCRUDRequestWrapper.try_find(Neighborhood(code=100))
            assert found is not None
            assert found.name == "Centro"
        
        assert server.calls == [SAVE, FIND]
        assert all(_root_entity(body) == "Bairro" for _, body in server.requests)
        assert save_data_row(server.requests[0][1]) == ({}, {"NOMEBAI": "Centro"})
        assert find_criteria(server.requests[1][1]) == "CODBAI = 100"


@pytest.mark.integration
class TestMixedEntityOperations:
    """Testes com múltiplos tipos de entidades."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_create_partner_and_product(self, mock_session_class):
        """Criar parceiro e produto na mesma sessão."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Fornecedor"}
            ])),
            http_response(200, create_success_response([
                {"CODPROD": "1", "DESCRPROD": "Produto do Fornecedor", "CODVOL": "UN"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Criar parceiro
            partner = SimpleCRUDRequestWrapper.update(Partner(name="Fornecedor"))
            assert partner.code == 1
            
            # Criar produto
            product = SimpleCRUDRequestWrapper.update(
                Product(name="Produto do Fornecedor", code_volume="UN")
            )
            assert product.code == 1
        
        assert [_root_entity(body) for _, body in server.requests] == ["Parceiro", "Produto"]
