"""
Movimento DTO for Sankhya JSON Gateway.

DTO for financial movement (Movimento) operations.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TipoTitulo(str, Enum):
    """Tipo de título financeiro."""
    RECEBER = "R"
    PAGAR = "P"


class StatusFinanceiro(str, Enum):
    """Status do movimento financeiro."""
    ABERTO = "A"
    BAIXADO = "B"
    PARCIAL = "P"
    CANCELADO = "C"


class MovimentoDTO(BaseModel):
    """
    DTO para Movimento Financeiro.
    
    Representa um título a pagar ou receber no Sankhya.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
    
    # Identificação
    numero_unico: Optional[int] = Field(None, alias="NUFIN", description="Número único (PK)")
    numero_titulo: Optional[str] = Field(None, alias="NUMNOTA", max_length=20)
    parcela: Optional[str] = Field(None, alias="DESDOBESSION", max_length=10)
    
    # Tipo
    tipo_titulo: TipoTitulo = Field(..., alias="RECDESP")
    
    # Relacionamentos
    codigo_parceiro: int = Field(..., alias="CODPARC")
    codigo_empresa: int = Field(..., alias="CODEMP")
    codigo_natureza: Optional[int] = Field(None, alias="CODNAT")
    codigo_centro_resultado: Optional[int] = Field(None, alias="CODCENCUS")
    codigo_tipo_titulo: Optional[int] = Field(None, alias="CODTIPTIT")
    numero_unico_nota: Optional[int] = Field(None, alias="NUNOTA")
    
    # Datas
    data_negociacao: date = Field(..., alias="DTNEG")
    data_vencimento: date = Field(..., alias="DTVENC")
    data_pagamento: Optional[date] = Field(None, alias="DHBAIXA")
    data_previsao: Optional[date] = Field(None, alias="DTPREV")
    
    # Valores
    valor_desdobramento: Decimal = Field(..., alias="VLRDESDOB")
    valor_baixado: Optional[Decimal] = Field(None, alias="VLRBAIXA")
    valor_desconto: Optional[Decimal] = Field(None, alias="VLRDESC")
    valor_juros: Optional[Decimal] = Field(None, alias="VLRJURO")
    valor_multa: Optional[Decimal] = Field(None, alias="VLRMULTA")
    
    # Status
    provisorio: str = Field("N", alias="PROVISORIO", pattern="^[SN]$")
    baixado: str = Field("N", alias="BAIXADO", pattern="^[SN]$")
    
    # Observações
    historico: Optional[str] = Field(None, alias="HISTORICO", max_length=4000)
    
    @property
    def status(self) -> StatusFinanceiro:
        """Determina status baseado nos valores."""
        if self.baixado == "S":
            return StatusFinanceiro.BAIXADO
        if self.valor_baixado and self.valor_baixado > 0:
            return StatusFinanceiro.PARCIAL
        return StatusFinanceiro.ABERTO
    
    @property
    def valor_em_aberto(self) -> Decimal:
        """Calcula valor em aberto (desdobramento - baixado)."""
        baixado = self.valor_baixado or Decimal("0")
        return self.valor_desdobramento - baixado
    
    @property
    def esta_vencido(self) -> bool:
        """Verifica se o título está vencido."""
        if self.baixado == "S":
            return False
        return self.data_vencimento < date.today()
