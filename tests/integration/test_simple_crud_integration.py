# -*- coding: utf-8 -*-
"""
Testes de integração para SimpleCRUDRequestWrapper.

Testa operações CRUD completas: find, create, update, delete.

Criação e atualização usam ``SimpleCRUDRequestWrapper.update``, que invoca
``CRUDServiceProvider.saveRecord`` (Create/Update): sem chave primária o
servidor cria o registro e devolve a chave gerada, como no SDK .NET
(``SimpleCrudRequestWrapper.Update``), que não possui método ``Create``.

``SimpleCRUDRequestWrapper.initialize(context)`` adquire uma sessão dedicada
(novo login), como ``Context.AcquireNewSession(ServiceRequestType.SimpleCrud)``
no .NET (SimpleCRUDRequestWrapper.cs:17-21). Por isso o transporte HTTP é
simulado pelo ``FakeSankhyaServer``, que responde login/logout/DWR de
qualquer sessão e entrega as respostas da fila apenas às chamadas de serviço.

O XML enviado segue ``ServiceRequestExtensions.HandleService`` do .NET:
loadRecords com ``dataSet rootEntity`` e ``criteria``; saveRecord com
``dataRow`` (``key`` + ``localFields``); removeRecord com ``entity
rootEntity`` e ``id``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
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


FIND = ServiceName.CRUD_SERVICE_FIND
SAVE = ServiceName.CRUD_SERVICE_SAVE
REMOVE = ServiceName.CRUD_SERVICE_REMOVE


def _install(mock_session_class, server: FakeSankhyaServer) -> None:
    """Instala o servidor simulado no transporte HTTP do SDK."""
    mock_session_class.return_value.request.side_effect = server


def _data_set_root_entity(body: str) -> str:
    """Entidade raiz (``dataSet/@rootEntity``) de loadRecords/saveRecord."""
    return request_xml(body).find("requestBody/dataSet").get("rootEntity")


@pytest.mark.integration
class TestSimpleCRUDFind:
    """Testes de operações de busca (find)."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_single_entity(self, mock_session_class):
        """Busca uma entidade por chave primária."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "123", "NOMEPARC": "Cliente Encontrado"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Sessão principal + sessão dedicada do SimpleCRUD
            assert server.logins == 2
            
            # Buscar parceiro por código
            search = Partner(code=123)
            result = SimpleCRUDRequestWrapper.try_find(search)
        
        # Verificar resultado (o servidor retornou exatamente um registro)
        assert result is not None
        assert result.code == 123
        assert result.name == "Cliente Encontrado"
        
        # loadRecords na entidade Parceiro com o critério da chave preenchida
        assert server.calls == [FIND.internal_value]
        (body,) = server.bodies(FIND)
        assert _data_set_root_entity(body) == "Parceiro"
        assert find_criteria(body) == "CODPARC = 123"
        
        # As duas sessões são encerradas no dispose
        assert server.logouts == 2

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_multiple_entities(self, mock_session_class):
        """Busca múltiplas entidades com critérios."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Cliente 1"},
                {"CODPARC": "2", "NOMEPARC": "Cliente 2"},
                {"CODPARC": "3", "NOMEPARC": "Cliente 3"},
            ], total_records=3)),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Buscar todos os parceiros ativos
            search = Partner()  # Sem filtros específicos
            results = SimpleCRUDRequestWrapper.find_all(search)
        
        assert len(results) == 3
        assert results[0].code == 1
        assert results[1].code == 2
        assert results[2].code == 3
        
        # Sem campos preenchidos o critério vai vazio (<criteria/>), como no
        # .NET (EntityResolverResult.LiteralCriteria sempre instanciado)
        (body,) = server.bodies(FIND)
        assert _data_set_root_entity(body) == "Parceiro"
        assert request_xml(body).find("requestBody/dataSet/criteria") is not None
        assert find_criteria(body) is None

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_returns_none_when_not_found(self, mock_session_class):
        """Busca retorna None quando não encontra."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            search = Partner(code=99999)
            result = SimpleCRUDRequestWrapper.try_find(search)
        
        assert result is None
        (body,) = server.bodies(FIND)
        assert find_criteria(body) == "CODPARC = 99999"


@pytest.mark.integration
class TestSimpleCRUDCreate:
    """Testes de operações de criação."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_create_entity(self, mock_session_class):
        """Cria nova entidade."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "1000", "NOMEPARC": "Novo Parceiro"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Sem chave primária: saveRecord cria o registro
            new_partner = Partner(name="Novo Parceiro")
            result = SimpleCRUDRequestWrapper.update(new_partner)
        
        # O servidor deve ter atribuído o código
        assert result.code == 1000
        assert result.name == "Novo Parceiro"
        
        # saveRecord sem chave, com o nome nos campos locais
        assert server.calls == [SAVE.internal_value]
        (body,) = server.bodies(SAVE)
        assert _data_set_root_entity(body) == "Parceiro"
        keys, local_fields = save_data_row(body)
        assert keys == {}
        assert local_fields == {"NOMEPARC": "Novo Parceiro"}

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_create_product(self, mock_session_class):
        """Cria novo produto."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPROD": "500", "DESCRPROD": "Produto Novo", "CODVOL": "UN"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            new_product = Product(name="Produto Novo", code_volume="UN")
            result = SimpleCRUDRequestWrapper.update(new_product)
        
        assert result.code == 500
        assert result.name == "Produto Novo"
        
        (body,) = server.bodies(SAVE)
        assert _data_set_root_entity(body) == "Produto"
        keys, local_fields = save_data_row(body)
        assert keys == {}
        assert local_fields == {"DESCRPROD": "Produto Novo", "CODVOL": "UN"}


@pytest.mark.integration
class TestSimpleCRUDUpdate:
    """Testes de operações de atualização."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_update_entity(self, mock_session_class):
        """Atualiza entidade existente."""
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "123", "NOMEPARC": "Nome Atualizado"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            partner = Partner(code=123, name="Nome Atualizado")
            result = SimpleCRUDRequestWrapper.update(partner)
        
        assert result.code == 123
        assert result.name == "Nome Atualizado"
        
        # A chave vai em dataRow/key e os demais campos em localFields
        (body,) = server.bodies(SAVE)
        assert _data_set_root_entity(body) == "Parceiro"
        keys, local_fields = save_data_row(body)
        assert keys == {"CODPARC": "123"}
        assert local_fields == {"NOMEPARC": "Nome Atualizado"}


@pytest.mark.integration
class TestSimpleCRUDDelete:
    """Testes de operações de remoção."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_delete_entity(self, mock_session_class):
        """Remove entidade."""
        server = FakeSankhyaServer([
            http_response(
                200, b'<?xml version="1.0"?><serviceResponse status="1"></serviceResponse>'
            ),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            partner = Partner(code=123)
            # Não deve lançar exceção
            SimpleCRUDRequestWrapper.remove(partner)
        
        # removeRecord: <entity rootEntity="Parceiro"><id><CODPARC>123</CODPARC></id>
        assert server.calls == [REMOVE.internal_value]
        (body,) = server.bodies(REMOVE)
        entity = request_xml(body).find("requestBody/entity")
        assert entity.get("rootEntity") == "Parceiro"
        ids = entity.findall("id")
        assert len(ids) == 1
        assert {child.tag: child.text for child in ids[0]} == {"CODPARC": "123"}


@pytest.mark.integration
class TestSimpleCRUDErrorHandling:
    """Testes de tratamento de erros."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_crud_error_duplicate_key(self, mock_session_class):
        """Testa erro de chave duplicada."""
        server = FakeSankhyaServer([
            http_response(
                200, create_error_response("DB.DUPLICATE_KEY", "Chave primária duplicada")
            ),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            partner = Partner(code=1, name="Duplicado")
            
            with pytest.raises(SankhyaException) as exc_info:
                SimpleCRUDRequestWrapper.update(partner)
        
        assert "Chave primária duplicada" in str(exc_info.value)
        assert server.calls_to(SAVE) == 1

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_crud_error_fk_violation(self, mock_session_class):
        """Testa erro de violação de FK."""
        server = FakeSankhyaServer([
            http_response(
                200, create_error_response(
                    "DB.FK_VIOLATION",
                    "Violação de chave estrangeira"
                )
            ),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Tentar deletar parceiro que tem dependências
            partner = Partner(code=1)
            
            with pytest.raises(SankhyaException) as exc_info:
                SimpleCRUDRequestWrapper.remove(partner)
        
        assert "Violação de chave estrangeira" in str(exc_info.value)
        assert server.calls_to(REMOVE) == 1

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_crud_with_validation_error(self, mock_session_class):
        """Testa erros de validação de campos."""
        server = FakeSankhyaServer([
            http_response(
                200, create_error_response(
                    "VALIDATION.ERROR",
                    "Campo obrigatório não preenchido: NOMEPARC"
                )
            ),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            # Parceiro sem nome
            partner = Partner(code=0)
            
            with pytest.raises(SankhyaException) as exc_info:
                SimpleCRUDRequestWrapper.update(partner)
        
        assert "NOMEPARC" in str(exc_info.value)
        assert server.calls_to(SAVE) == 1


@pytest.mark.integration
class TestSimpleCRUDWithCriteria:
    """Testes de busca com critérios literais."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_find_with_literal_criteria(self, mock_session_class):
        """Busca com critérios SQL literais."""
        from sankhya_sdk.helpers.filter_expression import LiteralCriteria
        
        server = FakeSankhyaServer([
            http_response(200, create_success_response([
                {"CODPARC": "42", "NOMEPARC": "Parceiro Específico"}
            ])),
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            criteria = LiteralCriteria.equals("CODPARC", 42)
            result = SimpleCRUDRequestWrapper.try_find_with_criteria(
                Partner, criteria
            )
        
        assert result is not None
        assert result.code == 42
        
        # O critério literal vai em dataSet/criteria (Resolve<T>(ILiteralCriteria))
        (body,) = server.bodies(FIND)
        assert _data_set_root_entity(body) == "Parceiro"
        assert find_criteria(body) == "CODPARC = 42"


@pytest.mark.integration
class TestSimpleCRUDBulkOperations:
    """Testes de operações em lote."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_bulk_create_partners(self, mock_session_class):
        """Cria múltiplos parceiros em lote."""
        # Respostas para cada criação
        server = FakeSankhyaServer([
            http_response(
                200,
                create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"}
                ])
            )
            for i in range(1, 4)
        ])
        _install(mock_session_class, server)
        
        with simple_crud_session():
            created = []
            for i in range(1, 4):
                partner = Partner(name=f"Parceiro {i}")
                result = SimpleCRUDRequestWrapper.update(partner)
                created.append(result)
        
        assert len(created) == 3
        for i, p in enumerate(created, 1):
            assert p.code == i
        
        # Um saveRecord por parceiro, cada um com o seu nome
        bodies = server.bodies(SAVE)
        assert [save_data_row(body)[1] for body in bodies] == [
            {"NOMEPARC": f"Parceiro {i}"} for i in range(1, 4)
        ]


@pytest.mark.integration
class TestSimpleCRUDResponseParsing:
    """Testes de extração de entidades de respostas desserializadas do XML."""

    @pytest.mark.parametrize(
        "entities_xml",
        [
            # CRUDServiceProvider.loadRecords: <entities>/<entity>
            '<entities total="1"><entity>'
            "<CODPARC>123</CODPARC><NOMEPARC>Cliente Encontrado</NOMEPARC>"
            "</entity></entities>",
            # crud.find: <entidades>/<entidade>
            '<entidades nome="Parceiro"><entidade>'
            "<CODPARC>123</CODPARC><NOMEPARC>Cliente Encontrado</NOMEPARC>"
            "</entidade></entidades>",
        ],
        ids=["crud_service_provider_entities", "crud_service_entities"],
    )
    def test_find_response_entities_from_parsed_xml(self, entities_xml):
        """
        Converte a entidade de uma ServiceResponse real (não mockada).
        
        Equivale a ``ServiceResponse.Entities`` no SDK .NET, que lê
        ``CrudServiceEntities`` ou ``CrudServiceProviderEntities``.
        """
        response = ServiceResponse.from_xml_bytes(
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<serviceResponse status="1"><responseBody>'
                f"{entities_xml}"
                "</responseBody></serviceResponse>"
            ).encode("utf-8")
        )
        
        result = SimpleCRUDRequestWrapper._process_find_response(
            response, Partner, optional=True
        )
        
        assert result is not None
        assert result.code == 123
        assert result.name == "Cliente Encontrado"
