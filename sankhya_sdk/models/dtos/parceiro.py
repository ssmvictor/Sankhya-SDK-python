"""
Parceiro DTO for Sankhya JSON Gateway.

Lightweight DTO for Partner (Parceiro) entity operations via JSON API.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TipoPessoa(str, Enum):
    """Tipo de pessoa (física ou jurídica)."""
    FISICA = "F"
    JURIDICA = "J"


class ParceiroDTO(BaseModel):
    """
    DTO completo para Parceiro.
    
    Usado para leitura/escrita de dados de parceiros via JSON Gateway.
    Os aliases correspondem aos nomes dos campos no Sankhya.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
    
    # Identificação
    codigo: Optional[int] = Field(None, alias="CODPARC", description="Código do parceiro (PK)")
    nome: str = Field(..., alias="NOMEPARC", max_length=100, description="Nome/Razão Social")
    nome_fantasia: Optional[str] = Field(None, alias="NOMEFANTASIA", max_length=100)
    tipo_pessoa: TipoPessoa = Field(TipoPessoa.JURIDICA, alias="TIPPESSOA")
    
    # Documentos
    cnpj_cpf: Optional[str] = Field(None, alias="CGC_CPF", max_length=18)
    inscricao_estadual: Optional[str] = Field(None, alias="INSCESTADNAUF", max_length=20)
    inscricao_municipal: Optional[str] = Field(None, alias="INSCRICAOMUNICIPAL", max_length=20)
    
    # Endereço
    endereco: Optional[str] = Field(None, alias="NOMEEND", max_length=100)
    numero: Optional[str] = Field(None, alias="NUMEND", max_length=10)
    complemento: Optional[str] = Field(None, alias="COMPLEMENTO", max_length=50)
    bairro: Optional[str] = Field(None, alias="NOMEBAI", max_length=60)
    codigo_cidade: Optional[int] = Field(None, alias="CODCID")
    cep: Optional[str] = Field(None, alias="CEP", max_length=10)
    
    # Contato
    telefone: Optional[str] = Field(None, alias="TELEFONE", max_length=20)
    email: Optional[str] = Field(None, alias="EMAIL", max_length=100)
    
    # Status
    ativo: str = Field("S", alias="ATIVO", pattern="^[SN]$")
    cliente: str = Field("S", alias="CLIENTE", pattern="^[SN]$")
    fornecedor: str = Field("N", alias="FORNECEDOR", pattern="^[SN]$")
    
    # Financeiro
    limite_credito: Optional[Decimal] = Field(None, alias="LIMCRED")
    
    # Datas
    data_inclusao: Optional[datetime] = Field(None, alias="DTCAD")
    data_alteracao: Optional[datetime] = Field(None, alias="DTALTER")


class ParceiroCreateDTO(BaseModel):
    """
    DTO para criação de Parceiro.
    
    Contém apenas campos obrigatórios e comuns para criação.
    """
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)
    
    nome: str = Field(..., alias="NOMEPARC", max_length=100)
    tipo_pessoa: TipoPessoa = Field(TipoPessoa.JURIDICA, alias="TIPPESSOA")
    cnpj_cpf: Optional[str] = Field(None, alias="CGC_CPF", max_length=18)
    codigo_cidade: int = Field(..., alias="CODCID")
    ativo: str = Field("S", alias="ATIVO", pattern="^[SN]$")
    cliente: str = Field("S", alias="CLIENTE", pattern="^[SN]$")
    fornecedor: str = Field("N", alias="FORNECEDOR", pattern="^[SN]$")


class ParceiroListDTO(BaseModel):
    """
    DTO leve para listagem de Parceiros.
    
    Contém apenas campos essenciais para exibição em listas.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    codigo: int = Field(..., alias="CODPARC")
    nome: str = Field(..., alias="NOMEPARC")
    tipo_pessoa: TipoPessoa = Field(..., alias="TIPPESSOA")
    cnpj_cpf: Optional[str] = Field(None, alias="CGC_CPF")
    ativo: str = Field(..., alias="ATIVO")
