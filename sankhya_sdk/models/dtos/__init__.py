"""
DTOs for Sankhya JSON Gateway API.

These are lightweight Pydantic models optimized for the JSON Gateway API,
with field aliases matching Sankhya's naming conventions.
"""

from .movimento import MovimentoDTO
from .nota import NotaCabecalhoDTO, NotaDTO, NotaItemDTO
from .parceiro import ParceiroCreateDTO, ParceiroDTO, ParceiroListDTO
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
