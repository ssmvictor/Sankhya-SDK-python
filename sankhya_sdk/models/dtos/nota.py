"""
Nota Fiscal DTOs for Sankhya JSON Gateway.

DTOs for invoice (Nota) operations via MGECOM module.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TipoOperacao(str, Enum):
    """Tipo de operação da nota."""
    ENTRADA = "E"
    SAIDA = "S"


class TipoNota(str, Enum):
    """Tipo de nota fiscal."""
    NFE = "1"
    NFCE = "2"
    SAT = "3"
    MANUAL = "4"


class NotaCabecalhoDTO(BaseModel):
    """
    DTO para cabeçalho de Nota Fiscal.
    
    Representa os dados principais da nota (CabecalhoNota).
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
    
    # Identificação
    numero_unico: Optional[int] = Field(None, alias="NUNOTA", description="Número único (PK)")
    numero_nota: Optional[int] = Field(None, alias="NUMNOTA")
    serie: Optional[str] = Field(None, alias="SERIENOTA", max_length=5)
    
    # Tipo/Operação
    tipo_operacao: TipoOperacao = Field(TipoOperacao.SAIDA, alias="TIPMOV")
    codigo_tipo_operacao: Optional[int] = Field(None, alias="CODTIPOPER")
    
    # Parceiros
    codigo_parceiro: int = Field(..., alias="CODPARC")
    codigo_empresa: int = Field(..., alias="CODEMP")
    
    # Datas
    data_negociacao: date = Field(..., alias="DTNEG")
    data_movimento: Optional[date] = Field(None, alias="DTMOV")
    data_faturamento: Optional[date] = Field(None, alias="DTFATUR")
    data_previsao: Optional[date] = Field(None, alias="DTPREVENT")
    
    # Valores
    valor_nota: Optional[Decimal] = Field(None, alias="VLRNOTA")
    valor_desconto: Optional[Decimal] = Field(None, alias="VLRDESC")
    valor_frete: Optional[Decimal] = Field(None, alias="VLRFRETE")
    valor_ipi: Optional[Decimal] = Field(None, alias="VLRIPI")
    valor_icms: Optional[Decimal] = Field(None, alias="VLRICMS")
    
    # Situação
    status_nota: Optional[str] = Field(None, alias="STATUSNOTA")
    pendente: str = Field("S", alias="PENDENTE", pattern="^[SN]$")
    
    # Observações
    observacao: Optional[str] = Field(None, alias="OBSERVACAO", max_length=4000)


class NotaItemDTO(BaseModel):
    """
    DTO para Item de Nota Fiscal.
    
    Representa um item/produto da nota (ItemNota).
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
    
    # Identificação
    numero_unico: int = Field(..., alias="NUNOTA", description="Número único da nota")
    sequencia: Optional[int] = Field(None, alias="SEQUENCIA")
    
    # Produto
    codigo_produto: int = Field(..., alias="CODPROD")
    codigo_local: Optional[int] = Field(None, alias="CODLOCALORIG")
    
    # Quantidades
    quantidade: Decimal = Field(..., alias="QTDNEG")
    quantidade_entregue: Optional[Decimal] = Field(None, alias="QTDENTREGUE")
    
    # Valores unitários
    valor_unitario: Decimal = Field(..., alias="VLRUNIT")
    valor_desconto: Optional[Decimal] = Field(None, alias="VLRDESC")
    
    # Valores totais
    valor_total: Optional[Decimal] = Field(None, alias="VLRTOT")
    valor_icms: Optional[Decimal] = Field(None, alias="VLRICMS")
    valor_ipi: Optional[Decimal] = Field(None, alias="VLRIPI")
    
    # NCM/CFOP
    cfop: Optional[str] = Field(None, alias="CODCFO", max_length=10)
    
    # Controle
    usoprod: Optional[str] = Field(None, alias="USOPROD")


class NotaDTO(BaseModel):
    """
    DTO completo para Nota Fiscal.
    
    Combina cabeçalho e itens para operações completas.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    cabecalho: NotaCabecalhoDTO
    itens: List[NotaItemDTO] = Field(default_factory=list)
    
    @property
    def valor_total_itens(self) -> Decimal:
        """Calcula valor total dos itens."""
        return sum(
            item.valor_total or Decimal("0")
            for item in self.itens
        )
    
    @property
    def quantidade_itens(self) -> int:
        """Retorna quantidade de itens na nota."""
        return len(self.itens)
