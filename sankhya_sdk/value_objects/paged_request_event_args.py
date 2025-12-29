# -*- coding: utf-8 -*-
"""
Event arguments para requisições paginadas.

Fornece classes de dados para representar eventos durante
o carregamento de páginas de resultados.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/PagedRequestWrapper.cs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from sankhya_sdk.models.base import EntityBase


@dataclass
class PagedRequestEventArgs:
    """
    Argumentos de evento para operações de requisição paginada.
    
    Representa informações sobre o estado atual do carregamento
    de páginas, incluindo progresso, quantidade de itens e erros.
    
    Attributes:
        entity_type: Tipo da entidade sendo carregada
        current_page: Número da página atual (1-indexed)
        total_loaded: Total de itens carregados até o momento
        quantity_loaded: Quantidade de itens carregados na página atual
        total_pages: Total de páginas estimado (se disponível)
        exception: Exceção ocorrida durante o carregamento (se houver)
    
    Example:
        >>> args = PagedRequestEventArgs(
        ...     entity_type=Partner,
        ...     current_page=1,
        ...     total_loaded=150,
        ...     quantity_loaded=150,
        ...     total_pages=10
        ... )
        >>> print(f"Página {args.current_page}/{args.total_pages}")
        Página 1/10
    """
    
    entity_type: Type["EntityBase"]
    current_page: int
    total_loaded: int
    quantity_loaded: Optional[int] = None
    total_pages: Optional[int] = None
    exception: Optional[Exception] = None
    
    @property
    def has_error(self) -> bool:
        """Verifica se há um erro associado ao evento."""
        return self.exception is not None
    
    @property
    def is_complete(self) -> bool:
        """
        Verifica se o carregamento está completo.
        
        Returns:
            True se total_pages está definido e current_page >= total_pages
        """
        if self.total_pages is None:
            return False
        return self.current_page >= self.total_pages
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """
        Calcula o percentual de progresso.
        
        Returns:
            Percentual de progresso (0-100) ou None se total_pages não definido
        """
        if self.total_pages is None or self.total_pages == 0:
            return None
        return (self.current_page / self.total_pages) * 100
    
    def __str__(self) -> str:
        """Representação string do evento."""
        entity_name = (
            self.entity_type.__name__ 
            if self.entity_type else "Unknown"
        )
        
        if self.exception:
            return (
                f"PagedRequestEventArgs(entity={entity_name}, "
                f"page={self.current_page}, error={self.exception})"
            )
        
        pages_info = f"/{self.total_pages}" if self.total_pages else ""
        return (
            f"PagedRequestEventArgs(entity={entity_name}, "
            f"page={self.current_page}{pages_info}, "
            f"loaded={self.total_loaded})"
        )
