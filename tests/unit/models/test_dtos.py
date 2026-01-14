"""Unit tests for DTOs."""

import pytest
from datetime import date
from decimal import Decimal

from sankhya_sdk.models.dtos.parceiro import (
    ParceiroDTO,
    ParceiroCreateDTO,
    ParceiroListDTO,
    TipoPessoa
)
from sankhya_sdk.models.dtos.nota import (
    NotaCabecalhoDTO,
    NotaItemDTO,
    NotaDTO,
    TipoOperacao
)
from sankhya_sdk.models.dtos.movimento import (
    MovimentoDTO,
    TipoTitulo,
    StatusFinanceiro
)


class TestParceiroDTO:
    """Tests for ParceiroDTO."""
    
    def test_create_with_required_fields(self):
        parceiro = ParceiroDTO(nome="Test Partner")
        assert parceiro.nome == "Test Partner"
        assert parceiro.ativo == "S"
        assert parceiro.tipo_pessoa == TipoPessoa.JURIDICA
    
    def test_field_aliases(self):
        data = {"NOMEPARC": "Test", "TIPPESSOA": "F", "ATIVO": "S"}
        parceiro = ParceiroDTO.model_validate(data)
        assert parceiro.nome == "Test"
        assert parceiro.tipo_pessoa == TipoPessoa.FISICA
    
    def test_export_with_aliases(self):
        parceiro = ParceiroDTO(nome="Test", tipo_pessoa=TipoPessoa.FISICA)
        exported = parceiro.model_dump(by_alias=True, exclude_none=True)
        assert exported["NOMEPARC"] == "Test"
        assert exported["TIPPESSOA"] == "F"


class TestParceiroCreateDTO:
    """Tests for ParceiroCreateDTO."""
    
    def test_required_fields(self):
        with pytest.raises(ValueError):
            ParceiroCreateDTO()
    
    def test_valid_create(self):
        dto = ParceiroCreateDTO(nome="New Partner", codigo_cidade=10)
        assert dto.nome == "New Partner"
        assert dto.codigo_cidade == 10


class TestNotaCabecalhoDTO:
    """Tests for NotaCabecalhoDTO."""
    
    def test_create_with_required_fields(self):
        nota = NotaCabecalhoDTO(
            codigo_parceiro=1,
            codigo_empresa=1,
            data_negociacao=date.today()
        )
        assert nota.codigo_parceiro == 1
        assert nota.tipo_operacao == TipoOperacao.SAIDA
    
    def test_field_aliases(self):
        data = {
            "CODPARC": 123,
            "CODEMP": 1,
            "DTNEG": date.today(),
            "TIPMOV": "E"
        }
        nota = NotaCabecalhoDTO.model_validate(data)
        assert nota.codigo_parceiro == 123
        assert nota.tipo_operacao == TipoOperacao.ENTRADA


class TestNotaItemDTO:
    """Tests for NotaItemDTO."""
    
    def test_create_item(self):
        item = NotaItemDTO(
            numero_unico=1,
            codigo_produto=100,
            quantidade=Decimal("10"),
            valor_unitario=Decimal("5.50")
        )
        assert item.quantidade == Decimal("10")
        assert item.valor_unitario == Decimal("5.50")


class TestNotaDTO:
    """Tests for NotaDTO."""
    
    def test_nota_with_items(self):
        cabecalho = NotaCabecalhoDTO(
            codigo_parceiro=1,
            codigo_empresa=1,
            data_negociacao=date.today()
        )
        itens = [
            NotaItemDTO(
                numero_unico=1,
                codigo_produto=100,
                quantidade=Decimal("2"),
                valor_unitario=Decimal("10"),
                valor_total=Decimal("20")
            ),
            NotaItemDTO(
                numero_unico=1,
                codigo_produto=101,
                quantidade=Decimal("1"),
                valor_unitario=Decimal("30"),
                valor_total=Decimal("30")
            )
        ]
        nota = NotaDTO(cabecalho=cabecalho, itens=itens)
        
        assert nota.quantidade_itens == 2
        assert nota.valor_total_itens == Decimal("50")


class TestMovimentoDTO:
    """Tests for MovimentoDTO."""
    
    def test_create_movimento(self):
        mov = MovimentoDTO(
            tipo_titulo=TipoTitulo.RECEBER,
            codigo_parceiro=1,
            codigo_empresa=1,
            data_negociacao=date.today(),
            data_vencimento=date.today(),
            valor_desdobramento=Decimal("100")
        )
        assert mov.tipo_titulo == TipoTitulo.RECEBER
        assert mov.valor_desdobramento == Decimal("100")
    
    def test_status_aberto(self):
        mov = MovimentoDTO(
            tipo_titulo=TipoTitulo.PAGAR,
            codigo_parceiro=1,
            codigo_empresa=1,
            data_negociacao=date.today(),
            data_vencimento=date.today(),
            valor_desdobramento=Decimal("100"),
            baixado="N"
        )
        assert mov.status == StatusFinanceiro.ABERTO
    
    def test_status_baixado(self):
        mov = MovimentoDTO(
            tipo_titulo=TipoTitulo.PAGAR,
            codigo_parceiro=1,
            codigo_empresa=1,
            data_negociacao=date.today(),
            data_vencimento=date.today(),
            valor_desdobramento=Decimal("100"),
            baixado="S"
        )
        assert mov.status == StatusFinanceiro.BAIXADO
    
    def test_valor_em_aberto(self):
        mov = MovimentoDTO(
            tipo_titulo=TipoTitulo.RECEBER,
            codigo_parceiro=1,
            codigo_empresa=1,
            data_negociacao=date.today(),
            data_vencimento=date.today(),
            valor_desdobramento=Decimal("100"),
            valor_baixado=Decimal("40"),
            baixado="N"
        )
        assert mov.valor_em_aberto == Decimal("60")
        assert mov.status == StatusFinanceiro.PARCIAL
