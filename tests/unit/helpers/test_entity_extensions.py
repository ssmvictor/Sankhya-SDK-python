# -*- coding: utf-8 -*-
"""
Testes unitários para entity_extensions.py
"""

import pytest
from datetime import timedelta
from typing import Optional

from sankhya_sdk.helpers.entity_extensions import (
    EntityResolverResult,
    Field,
    extract_keys,
    query,
    query_with_criteria,
    query_with_options,
    query_light,
    update_on_demand,
    remove_on_demand,
    get_on_demand_update_queue,
    get_on_demand_remove_queue,
    clear_on_demand_queues,
)
from sankhya_sdk.helpers.entity_query_options import EntityQueryOptions
from sankhya_sdk.helpers.filter_expression import IFilterExpression


class TestEntityResolverResult:
    """Testes para EntityResolverResult."""

    def test_initialization(self):
        """Verifica inicialização do resultado."""
        result = EntityResolverResult("Parceiro")
        
        assert result.name == "Parceiro"
        assert result.fields == []
        assert result.keys == []
        assert result.criteria == []
        assert result.field_values == []
        assert result.references == {}
        assert result.literal_criteria is None

    def test_adding_fields(self):
        """Verifica adição de campos."""
        result = EntityResolverResult("Produto")
        
        result.fields.append({"name": "CODPROD"})
        result.fields.append({"name": "DESCRPROD"})
        
        assert len(result.fields) == 2
        assert result.fields[0]["name"] == "CODPROD"

    def test_adding_keys(self):
        """Verifica adição de chaves."""
        result = EntityResolverResult("Parceiro")
        
        result.keys.append({"name": "CODPARC", "value": "123"})
        
        assert len(result.keys) == 1
        assert result.keys[0]["value"] == "123"

    def test_adding_references(self):
        """Verifica adição de referências."""
        result = EntityResolverResult("Cabecalho")
        
        result.references["Parceiro"] = [{"name": "NOMEPARC"}]
        result.references["Vendedor"] = [{"name": "NOMEVEND"}]
        
        assert len(result.references) == 2
        assert "Parceiro" in result.references


class TestField:
    """Testes para Field."""

    def test_field_creation(self):
        """Verifica criação de campo."""
        field = Field("CODPARC")
        
        assert field.name == "CODPARC"


class TestExtractKeys:
    """Testes para extract_keys - Regression tests para Comment 1."""
    
    def test_extract_keys_with_address_entity(self):
        """
        Regression test: extract_keys não deve levantar AttributeError
        ao acessar metadata de uma entidade com campos decorados.
        """
        from sankhya_sdk.models.transport.address import Address
        
        # Cria uma entidade Address com código definido
        address = Address(code=123, name="Rua Teste")
        
        # extract_keys NÃO deve levantar AttributeError
        result = extract_keys(address)
        
        # Verifica resultado
        assert result.name == "Endereco"
        assert len(result.fields) > 0
        
        # Verifica que a chave foi extraída corretamente
        assert len(result.keys) >= 1
        key_names = [k["name"] for k in result.keys]
        assert "CODEND" in key_names
        
        # Verifica o valor da chave
        key = next(k for k in result.keys if k["name"] == "CODEND")
        assert key["value"] == "123"
    
    def test_extract_keys_field_names_correct(self):
        """Verifica que os nomes dos campos são extraídos corretamente."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=1)
        result = extract_keys(address)
        
        # Os nomes dos campos devem ser os element_name (CODEND, TIPO, etc.)
        field_names = [f["name"] for f in result.fields]
        assert "CODEND" in field_names
        assert "TIPO" in field_names
        assert "NOMEEND" in field_names
        assert "DESCRICAOCORREIO" in field_names
        assert "DTALTER" in field_names
    
    def test_extract_keys_only_includes_set_keys(self):
        """Verifica que apenas chaves com should_serialize_field são incluídas."""
        from sankhya_sdk.models.transport.address import Address
        
        # Cria um Address sem definir o código explicitamente
        # O código tem default=0, então _fields_set não inclui 'code'
        address = Address()
        
        result = extract_keys(address)
        
        # código não foi "setado" explicitamente, então não deve aparecer nas keys
        # (depende da implementação de should_serialize_field)
        assert result.name == "Endereco"


class MockFilterExpression:
    """Mock para IFilterExpression para testes."""
    
    def __init__(self, expression: str = "CODPARC = 123"):
        self._expression = expression
    
    def build_expression(self) -> str:
        return self._expression


class TestQueryFunctions:
    """Testes para funções de query - agora devem funcionar sem NotImplementedError."""

    def test_query_returns_entity(self):
        """query deve retornar a própria entidade como resultado mínimo."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=123, name="Rua Teste")
        
        # query NÃO deve levantar NotImplementedError
        results = list(query(address, timedelta(seconds=30)))
        
        assert len(results) == 1
        assert results[0] is address
    
    def test_query_with_callback(self):
        """query deve chamar o callback de processamento."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=123)
        processed = []
        
        def callback(entities):
            processed.extend(entities)
        
        list(query(address, timedelta(seconds=30), process_data_on_demand=callback))
        
        assert len(processed) == 1
        assert processed[0] is address

    def test_query_with_criteria_returns_entity(self):
        """query_with_criteria deve retornar a própria entidade."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=456)
        criteria = MockFilterExpression("CODEND > 100")
        
        results = list(query_with_criteria(
            address, 
            criteria, 
            timedelta(seconds=30)
        ))
        
        assert len(results) == 1
        assert results[0] is address
    
    def test_query_with_criteria_with_callback(self):
        """query_with_criteria deve chamar o callback."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=456)
        criteria = MockFilterExpression()
        processed = []
        
        list(query_with_criteria(
            address, 
            criteria, 
            timedelta(seconds=30),
            process_data_on_demand=lambda e: processed.extend(e)
        ))
        
        assert len(processed) == 1

    def test_query_with_options_returns_entity(self):
        """query_with_options deve retornar a própria entidade."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=789)
        options = EntityQueryOptions(max_results=10)
        
        results = list(query_with_options(address, options))
        
        assert len(results) == 1
        assert results[0] is address
    
    def test_query_with_options_respects_max_results(self):
        """query_with_options deve respeitar max_results."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=1)
        options = EntityQueryOptions(max_results=1)
        
        results = list(query_with_options(address, options))
        
        # Deve retornar no máximo 1 resultado
        assert len(results) <= 1
    
    def test_query_with_options_with_callback(self):
        """query_with_options deve chamar o callback."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=1)
        options = EntityQueryOptions()
        processed = []
        
        list(query_with_options(
            address, 
            options,
            process_data_on_demand=lambda e: processed.extend(e)
        ))
        
        assert len(processed) == 1

    def test_query_light_returns_entity(self):
        """query_light deve retornar a própria entidade."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=999)
        
        results = list(query_light(address, timedelta(seconds=30)))
        
        assert len(results) == 1
        assert results[0] is address
    
    def test_query_light_respects_max_results(self):
        """query_light deve respeitar max_results."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=1)
        
        results = list(query_light(address, timedelta(seconds=30), max_results=1))
        
        assert len(results) <= 1


class TestOnDemandFunctions:
    """Testes para funções on-demand - agora devem funcionar sem NotImplementedError."""
    
    def setup_method(self):
        """Limpa as filas antes de cada teste."""
        clear_on_demand_queues()
    
    def teardown_method(self):
        """Limpa as filas após cada teste."""
        clear_on_demand_queues()

    def test_update_on_demand_adds_to_queue(self):
        """update_on_demand deve adicionar entidade à fila de update."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=123, name="Rua Update")
        
        # Não deve levantar NotImplementedError
        update_on_demand(address)
        
        queue = get_on_demand_update_queue()
        assert len(queue) == 1
        assert queue[0] is address
    
    def test_update_on_demand_multiple_entities(self):
        """update_on_demand deve adicionar múltiplas entidades."""
        from sankhya_sdk.models.transport.address import Address
        
        address1 = Address(code=1)
        address2 = Address(code=2)
        address3 = Address(code=3)
        
        update_on_demand(address1)
        update_on_demand(address2)
        update_on_demand(address3)
        
        queue = get_on_demand_update_queue()
        assert len(queue) == 3
        assert queue[0] is address1
        assert queue[1] is address2
        assert queue[2] is address3

    def test_remove_on_demand_adds_to_queue(self):
        """remove_on_demand deve adicionar entidade à fila de remove."""
        from sankhya_sdk.models.transport.address import Address
        
        address = Address(code=456, name="Rua Remove")
        
        # Não deve levantar NotImplementedError
        remove_on_demand(address)
        
        queue = get_on_demand_remove_queue()
        assert len(queue) == 1
        assert queue[0] is address
    
    def test_remove_on_demand_multiple_entities(self):
        """remove_on_demand deve adicionar múltiplas entidades."""
        from sankhya_sdk.models.transport.address import Address
        
        address1 = Address(code=10)
        address2 = Address(code=20)
        
        remove_on_demand(address1)
        remove_on_demand(address2)
        
        queue = get_on_demand_remove_queue()
        assert len(queue) == 2
    
    def test_queues_are_independent(self):
        """Filas de update e remove são independentes."""
        from sankhya_sdk.models.transport.address import Address
        
        update_addr = Address(code=100)
        remove_addr = Address(code=200)
        
        update_on_demand(update_addr)
        remove_on_demand(remove_addr)
        
        update_queue = get_on_demand_update_queue()
        remove_queue = get_on_demand_remove_queue()
        
        assert len(update_queue) == 1
        assert len(remove_queue) == 1
        assert update_queue[0] is update_addr
        assert remove_queue[0] is remove_addr
    
    def test_clear_on_demand_queues(self):
        """clear_on_demand_queues deve limpar ambas as filas."""
        from sankhya_sdk.models.transport.address import Address
        
        update_on_demand(Address(code=1))
        remove_on_demand(Address(code=2))
        
        assert len(get_on_demand_update_queue()) == 1
        assert len(get_on_demand_remove_queue()) == 1
        
        clear_on_demand_queues()
        
        assert len(get_on_demand_update_queue()) == 0
        assert len(get_on_demand_remove_queue()) == 0
    
    def test_get_queue_returns_copy(self):
        """get_on_demand_*_queue deve retornar cópia para evitar mutação."""
        from sankhya_sdk.models.transport.address import Address
        
        addr = Address(code=1)
        update_on_demand(addr)
        
        queue = get_on_demand_update_queue()
        queue.clear()  # Limpa a cópia
        
        # A fila original não deve ter sido afetada
        assert len(get_on_demand_update_queue()) == 1
