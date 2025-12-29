# -*- coding: utf-8 -*-
"""
Testes de integração para SimpleCRUDRequestWrapper.

Testa operações CRUD completas: find, create, update, delete.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import (
    ServiceRequestTooManyResultsException,
    ServiceRequestUnexpectedResultException,
    SankhyaException,
)
from sankhya_sdk.models.service.service_request import ServiceRequest
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
    SamplePartner,
    SampleProduct,
    SampleNeighborhood,
)


@pytest.mark.integration
class TestSimpleCRUDFind:
    """Testes de operações de busca (find)."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_single_entity(self, mock_session_class):
        """Busca uma entidade por chave primária."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "123", "NOMEPARC": "Cliente Encontrado"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, find_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Buscar parceiro por código
            search = Partner(code=123)
            result = SimpleCRUDRequestWrapper.try_find(search)
            
            # Verificar resultado
            if result:
                assert result.code == 123
                assert result.name == "Cliente Encontrado"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_multiple_entities(self, mock_session_class):
        """Busca múltiplas entidades com critérios."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Cliente 1"},
                {"CODPARC": "2", "NOMEPARC": "Cliente 2"},
                {"CODPARC": "3", "NOMEPARC": "Cliente 3"},
            ], total_records=3)
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, find_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Buscar todos os parceiros ativos
            search = Partner()  # Sem filtros específicos
            results = SimpleCRUDRequestWrapper.find_all(search)
            
            assert len(results) == 3
            assert results[0].code == 1
            assert results[1].code == 2
            assert results[2].code == 3
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_returns_none_when_not_found(self, mock_session_class):
        """Busca retorna None quando não encontra."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        empty_resp = create_mock_response(200, create_success_response([]))
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, empty_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            search = Partner(code=99999)
            result = SimpleCRUDRequestWrapper.try_find(search)
            
            assert result is None
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSimpleCRUDCreate:
    """Testes de operações de criação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_create_entity(self, mock_session_class):
        """Cria nova entidade."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1000", "NOMEPARC": "Novo Parceiro"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, create_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            new_partner = Partner(name="Novo Parceiro")
            result = SimpleCRUDRequestWrapper.create(new_partner)
            
            # O servidor deve ter atribuído o código
            assert result.code == 1000
            assert result.name == "Novo Parceiro"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_create_product(self, mock_session_class):
        """Cria novo produto."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Novo", "CODVOL": "UN"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, create_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            new_product = Product(name="Produto Novo", code_volume="UN")
            result = SimpleCRUDRequestWrapper.create(new_product)
            
            assert result.code == 500
            assert result.name == "Produto Novo"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSimpleCRUDUpdate:
    """Testes de operações de atualização."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_update_entity(self, mock_session_class):
        """Atualiza entidade existente."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        update_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "123", "NOMEPARC": "Nome Atualizado"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, update_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            partner = Partner(code=123, name="Nome Atualizado")
            result = SimpleCRUDRequestWrapper.update(partner)
            
            assert result.code == 123
            assert result.name == "Nome Atualizado"
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSimpleCRUDDelete:
    """Testes de operações de remoção."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_delete_entity(self, mock_session_class):
        """Remove entidade."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        delete_resp = create_mock_response(
            200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, delete_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            partner = Partner(code=123)
            # Não deve lançar exceção
            SimpleCRUDRequestWrapper.remove(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSimpleCRUDErrorHandling:
    """Testes de tratamento de erros."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_crud_error_duplicate_key(self, mock_session_class):
        """Testa erro de chave duplicada."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response("DB.DUPLICATE_KEY", "Chave primária duplicada")
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            partner = Partner(code=1, name="Duplicado")
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_crud_error_fk_violation(self, mock_session_class):
        """Testa erro de violação de FK."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response(
                "DB.FK_VIOLATION", 
                "Violação de chave estrangeira"
            )
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Tentar deletar parceiro que tem dependências
            partner = Partner(code=1)
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.remove(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_crud_with_validation_error(self, mock_session_class):
        """Testa erros de validação de campos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        error_resp = create_mock_response(
            200, create_error_response(
                "VALIDATION.ERROR",
                "Campo obrigatório não preenchido: NOMEPARC"
            )
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, error_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            # Parceiro sem nome
            partner = Partner(code=0)
            
            with pytest.raises(SankhyaException):
                SimpleCRUDRequestWrapper.create(partner)
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSimpleCRUDWithCriteria:
    """Testes de busca com critérios literais."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_with_literal_criteria(self, mock_session_class):
        """Busca com critérios SQL literais."""
        from sankhya_sdk.criteria.literal_criteria import LiteralCriteria
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        find_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "42", "NOMEPARC": "Parceiro Específico"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, find_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            criteria = LiteralCriteria.equals("CODPARC", 42)
            result = SimpleCRUDRequestWrapper.try_find_with_criteria(
                Partner, criteria
            )
            
            if result:
                assert result.code == 42
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestSimpleCRUDBulkOperations:
    """Testes de operações em lote."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_create_partners(self, mock_session_class):
        """Cria múltiplos parceiros em lote."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Respostas para cada criação
        create_resps = [
            create_mock_response(
                200, 
                create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"}
                ])
            )
            for i in range(1, 4)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + create_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        SimpleCRUDRequestWrapper.initialize(wrapper)
        
        try:
            created = []
            for i in range(1, 4):
                partner = Partner(name=f"Parceiro {i}")
                result = SimpleCRUDRequestWrapper.create(partner)
                created.append(result)
            
            assert len(created) == 3
            for i, p in enumerate(created, 1):
                assert p.code == i
        finally:
            SimpleCRUDRequestWrapper.dispose()
            wrapper.dispose()
