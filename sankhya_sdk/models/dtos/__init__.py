"""
DTOs for Sankhya JSON Gateway API.

These are lightweight Pydantic models optimized for the JSON Gateway API,
with field aliases matching Sankhya's naming conventions.
"""

from .parceiro import ParceiroDTO, ParceiroCreateDTO, ParceiroListDTO
from .nota import NotaDTO, NotaCabecalhoDTO, NotaItemDTO
from .movimento import MovimentoDTO
from .produto import ProdutoDTO, ProdutoListDTO

__all__ = [
    "ParceiroDTO",
    "ParceiroCreateDTO",
    "ParceiroListDTO",
    "NotaDTO",
    "NotaCabecalhoDTO",
    "NotaItemDTO",
    "MovimentoDTO",
    "ProdutoDTO",
    "ProdutoListDTO",
]
