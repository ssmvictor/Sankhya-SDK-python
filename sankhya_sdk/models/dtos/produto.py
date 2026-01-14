"""
Produto DTO for Sankhya JSON Gateway.

Lightweight DTO for Product (Produto) entity operations via JSON API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProdutoDTO(BaseModel):
    """
    DTO completo para Produto.
    
    Usado para leitura/escrita de dados de produtos via JSON Gateway.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
    
    # Identificação
    codigo: Optional[int] = Field(None, alias="CODPROD", description="Código do produto (PK)")
    descricao: str = Field(..., alias="DESCRPROD", max_length=200, description="Descrição do produto")
    referencia: Optional[str] = Field(None, alias="REFERENCIA", max_length=50, description="Referência/SKU")
    
    # Classificação
    ncm: Optional[str] = Field(None, alias="NCM", max_length=15, description="NCM fiscal")
    codigo_grupo: Optional[int] = Field(None, alias="CODGRUPOPROD", description="Código do grupo")
    codigo_marca: Optional[int] = Field(None, alias="CODMARCA", description="Código da marca")
    
    # Medidas
    unidade: Optional[str] = Field(None, alias="UNIDADE", max_length=5)
    peso_bruto: Optional[Decimal] = Field(None, alias="PESOBRUTO")
    peso_liquido: Optional[Decimal] = Field(None, alias="PESOLIQ")
    
    # Status
    ativo: str = Field("S", alias="ATIVO", pattern="^[SN]$")
    
    # Datas
    data_inclusao: Optional[datetime] = Field(None, alias="DTCAD")
    data_alteracao: Optional[datetime] = Field(None, alias="DTALTER")


class ProdutoListDTO(BaseModel):
    """
    DTO leve para listagem de Produtos.
    
    Contém apenas campos essenciais para exibição em listas.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    codigo: int = Field(..., alias="CODPROD")
    descricao: str = Field(..., alias="DESCRPROD")
    referencia: Optional[str] = Field(None, alias="REFERENCIA")
    ncm: Optional[str] = Field(None, alias="NCM")
    ativo: str = Field(..., alias="ATIVO")
