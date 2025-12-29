# -*- coding: utf-8 -*-
"""
Opções de configuração para queries de entidades.

Define EntityQueryOptions, uma dataclass que encapsula opções
de configuração para consultas de entidades no Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/EntityQueryOptions.cs
"""

from datetime import timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityQueryOptions(BaseModel):
    """
    Opções de configuração para queries de entidades.
    
    Encapsula configurações como número máximo de resultados,
    inclusão de referências, profundidade de referências, etc.
    
    Attributes:
        max_results: Número máximo de resultados a retornar
        include_references: Se deve incluir entidades referenciadas
        max_reference_depth: Profundidade máxima de referências aninhadas
        include_presentation_fields: Se deve incluir campos de apresentação
        use_wildcard_fields: Se deve usar wildcard (*) para campos
        timeout: Tempo limite para a query (default: 30 minutos)
    
    Example:
        >>> options = EntityQueryOptions(max_results=100, include_references=True)
        >>> options.timeout
        datetime.timedelta(seconds=1800)
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )

    max_results: Optional[int] = Field(
        default=None,
        description="Número máximo de resultados a retornar",
        ge=1,
    )
    include_references: Optional[bool] = Field(
        default=None,
        description="Se deve incluir entidades referenciadas",
    )
    max_reference_depth: Optional[int] = Field(
        default=None,
        description="Profundidade máxima de referências (0-6)",
        ge=0,
        le=6,
    )
    include_presentation_fields: Optional[bool] = Field(
        default=None,
        description="Se deve incluir campos de apresentação",
    )
    use_wildcard_fields: Optional[bool] = Field(
        default=None,
        description="Se deve usar wildcard (*) para campos",
    )
    timeout: timedelta = Field(
        default_factory=lambda: timedelta(minutes=30),
        description="Tempo limite para a query",
    )

    @field_validator("timeout", mode="before")
    @classmethod
    def validate_timeout(cls, v):
        """Garante que timeout é sempre um timedelta válido."""
        if v is None:
            return timedelta(minutes=30)
        if isinstance(v, (int, float)):
            return timedelta(seconds=v)
        return v

    def get_timeout_seconds(self) -> float:
        """
        Retorna o timeout em segundos.
        
        Returns:
            Valor do timeout em segundos como float
        """
        return self.timeout.total_seconds()

    def with_max_results(self, max_results: int) -> "EntityQueryOptions":
        """
        Retorna uma nova instância com max_results atualizado.
        
        Args:
            max_results: Novo valor para max_results
            
        Returns:
            Nova instância de EntityQueryOptions
        """
        return self.model_copy(update={"max_results": max_results})

    def with_references(
        self, 
        include: bool = True, 
        max_depth: Optional[int] = None
    ) -> "EntityQueryOptions":
        """
        Retorna uma nova instância com configurações de referências.
        
        Args:
            include: Se deve incluir referências
            max_depth: Profundidade máxima de referências
            
        Returns:
            Nova instância de EntityQueryOptions
        """
        updates = {"include_references": include}
        if max_depth is not None:
            updates["max_reference_depth"] = max_depth
        return self.model_copy(update=updates)

    def with_timeout(self, timeout: timedelta) -> "EntityQueryOptions":
        """
        Retorna uma nova instância com timeout atualizado.
        
        Args:
            timeout: Novo valor para timeout
            
        Returns:
            Nova instância de EntityQueryOptions
        """
        return self.model_copy(update={"timeout": timeout})
