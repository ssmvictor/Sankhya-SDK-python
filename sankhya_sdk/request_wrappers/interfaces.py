# -*- coding: utf-8 -*-
"""
Interfaces para Request Wrappers.

Define protocolos e contratos para wrappers de requisição on-demand.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from sankhya_sdk.models.base import EntityBase


# Type variable for entity types
TEntity = TypeVar("TEntity", bound=EntityBase)


@runtime_checkable
class IOnDemandRequestWrapper(Protocol[TEntity]):
    """
    Protocolo para wrappers de requisição on-demand.
    
    Define a interface para processamento em lote assíncrono com controle de throughput.
    Implementações devem suportar uso como context manager.
    
    Exemplo de uso:
        >>> with OnDemandRequestWrapper[Partner](service, cancel_token) as wrapper:
        ...     for partner in partners:
        ...         wrapper.add(partner)
        ...     wrapper.flush()
    """

    @property
    def request_count(self) -> int:
        """Retorna o número de requisições feitas."""
        ...

    @property
    def entities_sent(self) -> int:
        """Retorna o número total de entidades enviadas."""
        ...

    @property
    def entities_sent_successfully(self) -> int:
        """Retorna o número de entidades enviadas com sucesso."""
        ...

    @property
    def is_disposed(self) -> bool:
        """Indica se o wrapper foi descartado."""
        ...

    def add(self, entity: TEntity) -> None:
        """
        Adiciona uma entidade à fila de processamento.
        
        Args:
            entity: Entidade a ser processada.
            
        Raises:
            ValueError: Se o wrapper já foi descartado.
        """
        ...

    def flush(self) -> None:
        """
        Força o processamento imediato de todas as entidades na fila.
        
        Bloqueia até que todas as entidades pendentes sejam processadas.
        """
        ...

    def dispose(self) -> None:
        """
        Finaliza o wrapper e libera recursos.
        
        Aguarda a conclusão do processamento em andamento antes de encerrar.
        """
        ...

    def __enter__(self) -> IOnDemandRequestWrapper[TEntity]:
        """Suporta uso como context manager."""
        ...

    def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object | None) -> None:
        """Finaliza o context manager chamando dispose()."""
        ...


@runtime_checkable
class IAsyncOnDemandRequestWrapper(Protocol[TEntity]):
    """
    Protocolo para wrappers de requisição on-demand assíncronos.
    
    Versão assíncrona do IOnDemandRequestWrapper para uso com asyncio.
    
    Exemplo de uso:
        >>> async with AsyncOnDemandRequestWrapper[Partner](service, cancel_token) as wrapper:
        ...     for partner in partners:
        ...         await wrapper.add(partner)
        ...     await wrapper.flush()
    """

    @property
    def request_count(self) -> int:
        """Retorna o número de requisições feitas."""
        ...

    @property
    def entities_sent(self) -> int:
        """Retorna o número total de entidades enviadas."""
        ...

    @property
    def entities_sent_successfully(self) -> int:
        """Retorna o número de entidades enviadas com sucesso."""
        ...

    @property
    def is_disposed(self) -> bool:
        """Indica se o wrapper foi descartado."""
        ...

    async def add(self, entity: TEntity) -> None:
        """
        Adiciona uma entidade à fila de processamento.
        
        Args:
            entity: Entidade a ser processada.
            
        Raises:
            ValueError: Se o wrapper já foi descartado.
        """
        ...

    async def flush(self) -> None:
        """
        Força o processamento imediato de todas as entidades na fila.
        
        Aguarda até que todas as entidades pendentes sejam processadas.
        """
        ...

    async def dispose(self) -> None:
        """
        Finaliza o wrapper e libera recursos.
        
        Aguarda a conclusão do processamento em andamento antes de encerrar.
        """
        ...

    async def __aenter__(self) -> IAsyncOnDemandRequestWrapper[TEntity]:
        """Suporta uso como async context manager."""
        ...

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object | None) -> None:
        """Finaliza o async context manager chamando dispose()."""
        ...


__all__ = [
    "TEntity",
    "IOnDemandRequestWrapper",
    "IAsyncOnDemandRequestWrapper",
]
