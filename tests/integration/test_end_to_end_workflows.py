# -*- coding: utf-8 -*-
"""
Testes de integração end-to-end para workflows completos.

Testa fluxos completos de criação, busca, atualização e deleção.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.models.transport.neighborhood import Neighborhood
from sankhya_sdk.request_wrappers.simple_crud_request_wrapper import (
    SimpleCRUDRequestWrapper,
)

from .conftest import (
    create_error_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_success_response,
)


@pytest.mark.integration
class TestPartnerWorkflow:
    """Testes de workflow completo de Partner."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_complete_partner_workflow(self, mock_session_class):
        """Criar, buscar, atualizar, deletar Partner."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # 1. Criar partner
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Novo Parceiro", "EMAIL": "email@test.com"}
            ])
        )
        
        # 2. Buscar partner criado
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Novo Parceiro", "EMAIL": "email@test.com"}
            ])
        )
        
        # 3. Atualizar partner
        update_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Parceiro Atualizado", "EMAIL": "novo@test.com"}
            ])
        )
        
        # 4. Buscar partner atualizado
        find_updated_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1001", "NOMEPARC": "Parceiro Atualizado", "EMAIL": "novo@test.com"}
            ])
        )
        
        # 5. Deletar partner
        delete_resp = create_mock_response(
            200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
        )
        
        # 6. Verificar deleção (não deve encontrar)
        find_deleted_resp = create_mock_response(200, create_success_response([]))
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp,
            create_resp,
            find_resp,
            update_resp,
            find_updated_resp,
            delete_resp,
            find_deleted_resp,
            logout_resp,
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # 1. Criar
            new_partner = Partner(name="Novo Parceiro", email_address="email@test.com")
            created = SimpleCRUDRequestWrapper.create(new_partner)
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
            
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestProductWorkflow:
    """Testes de workflow completo de Product."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_complete_product_workflow(self, mock_session_class):
        """Criar, buscar, atualizar, deletar Product."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # 1. Criar produto
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Teste", "CODVOL": "UN"}
            ])
        )
        
        # 2. Buscar produto
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Teste", "CODVOL": "UN"}
            ])
        )
        
        # 3. Atualizar produto
        update_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Atualizado", "CODVOL": "KG"}
            ])
        )
        
        # 4. Deletar produto
        delete_resp = create_mock_response(
            200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp,
            create_resp,
            find_resp,
            update_resp,
            delete_resp,
            logout_resp,
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # 1. Criar
            new_product = Product(name="Produto Teste", code_volume="UN")
            created = SimpleCRUDRequestWrapper.create(new_product)
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
            
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestBulkImport:
    """Testes de importação em lote."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_partner_import(self, mock_session_class):
        """Importar múltiplos parceiros em lote."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Respostas para 10 criações
        create_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro Importado {i}"}
                ])
            )
            for i in range(1, 11)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + create_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            imported = []
            for i in range(1, 11):
                partner = Partner(name=f"Parceiro Importado {i}")
                result = SimpleCRUDRequestWrapper.create(partner)
                imported.append(result)
            
            assert len(imported) == 10
            for i, p in enumerate(imported, 1):
                assert p.code == i
                assert f"Parceiro Importado {i}" in p.name
                
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_product_update(self, mock_session_class):
        """Atualizar múltiplos produtos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Respostas para 5 atualizações
        update_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPROD": str(i), "DESCRPROD": f"Produto Atualizado {i}", "CODVOL": "UN"}
                ])
            )
            for i in range(1, 6)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + update_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            updated = []
            for i in range(1, 6):
                product = Product(code=i, name=f"Produto Atualizado {i}")
                result = SimpleCRUDRequestWrapper.update(product)
                updated.append(result)
            
            assert len(updated) == 5
            for i, p in enumerate(updated, 1):
                assert "Atualizado" in p.name
                
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestComplexQueries:
    """Testes de queries complexas."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_complex_query_multiple_entities(self, mock_session_class):
        """Query que retorna múltiplas entidades relacionadas."""
        from sankhya_sdk.criteria.literal_criteria import LiteralCriteria
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Buscar parceiros com cidade específica
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro 1", "CODCID": "100"},
                {"CODPARC": "2", "NOMEPARC": "Parceiro 2", "CODCID": "100"},
                {"CODPARC": "3", "NOMEPARC": "Parceiro 3", "CODCID": "100"},
            ], total_records=3)
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, find_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            criteria = LiteralCriteria.equals("CODCID", 100)
            results = SimpleCRUDRequestWrapper.find_all_with_criteria(Partner, criteria)
            
            assert len(results) == 3
            for p in results:
                assert p.code_city == 100
                
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestTransactionRollback:
    """Testes de rollback de transação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_transaction_rollback_on_error(self, mock_session_class):
        """Testa rollback de transação em erro."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeira criação OK
        create1_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro 1"}
            ])
        )
        
        # Segunda criação falha
        create2_error = create_mock_response(
            200, create_error_response("DB.ERROR", "Erro de banco")
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create1_resp, create2_error, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Primeira criação deve funcionar
            p1 = SimpleCRUDRequestWrapper.create(Partner(name="Parceiro 1"))
            assert p1.code == 1
            
            # Segunda criação deve falhar
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(Partner(name="Parceiro 2"))
                
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestNeighborhoodWorkflow:
    """Testes de workflow de Neighborhood."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_neighborhood_crud(self, mock_session_class):
        """CRUD completo de bairros."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODBAI": "100", "NOMEBAI": "Centro"}
            ])
        )
        
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODBAI": "100", "NOMEBAI": "Centro"}
            ])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, create_resp, find_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Criar
            neighborhood = Neighborhood(name="Centro")
            created = SimpleCRUDRequestWrapper.create(neighborhood)
            assert created.code == 100
            
            # Buscar
            found = SimpleCRUDRequestWrapper.try_find(Neighborhood(code=100))
            assert found is not None
            assert found.name == "Centro"
            
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestMixedEntityOperations:
    """Testes com múltiplos tipos de entidades."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_create_partner_and_product(self, mock_session_class):
        """Criar parceiro e produto na mesma sessão."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        partner_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Fornecedor"}
            ])
        )
        
        product_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "1", "DESCRPROD": "Produto do Fornecedor", "CODVOL": "UN"}
            ])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, partner_resp, product_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Criar parceiro
            partner = SimpleCRUDRequestWrapper.create(Partner(name="Fornecedor"))
            assert partner.code == 1
            
            # Criar produto
            product = SimpleCRUDRequestWrapper.create(
                Product(name="Produto do Fornecedor", code_volume="UN")
            )
            assert product.code == 1
            
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()
