# -*- coding: utf-8 -*-
"""
Paged Request Wrapper.

Fornece operações de requisição paginada para entidades do Sankhya,
com suporte a operações síncronas e assíncronas, callbacks de progresso,
e processamento on-demand.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/PagedRequestWrapper.cs
"""

from __future__ import annotations

import asyncio
import logging
import queue
import threading
import time
import uuid
from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    AsyncGenerator,
    Awaitable,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

if TYPE_CHECKING:
    from sankhya_sdk.core.context import SankhyaContext

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.helpers.entity_dynamic_serialization import EntityDynamicSerialization
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.value_objects.paged_request_event_args import PagedRequestEventArgs


logger = logging.getLogger(__name__)

# TypeVar para entidades genéricas
T = TypeVar("T", bound=EntityBase)

# Type aliases para callbacks
PageLoadedCallback = Callable[[PagedRequestEventArgs], None]
PageProcessedCallback = Callable[[PagedRequestEventArgs], None]
PageErrorCallback = Callable[[PagedRequestEventArgs], None]
ProcessDataCallback = Callable[[List[T]], None]
ProcessDataCallbackAsync = Callable[[List[T]], Awaitable[None]]


class PagedRequestException(Exception):
    """Exceção específica para erros de requisição paginada."""
    
    def __init__(
        self,
        message: str,
        page: int = 0,
        inner_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.page = page
        self.inner_exception = inner_exception


class PagedRequestWrapper:
    """
    Wrapper para operações de requisição paginada em entidades do Sankhya.
    
    Gerencia o carregamento de grandes conjuntos de dados através de
    paginação automática, com suporte a callbacks de progresso,
    processamento on-demand e timeout configurável.
    
    Suporta tanto operações síncronas quanto assíncronas:
    - `get_paged_results`: Generator síncrono com yield
    - `get_paged_results_async`: Async generator com async for
    
    Attributes:
        _context: Contexto Sankhya para gerenciamento de sessão
        _token: Token UUID da sessão
        _entity_type: Tipo da entidade sendo carregada
        _request: Requisição de serviço base
        _max_results: Limite máximo de resultados (-1 = ilimitado)
    
    Example:
        Uso básico síncrono:
        
        >>> SimpleCRUDRequestWrapper.initialize()
        >>> request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        >>> for partner in PagedRequestWrapper.get_paged_results(
        ...     request, Partner, timeout=timedelta(minutes=5)
        ... ):
        ...     print(partner.name)
        
        Com callbacks de progresso:
        
        >>> def on_page(args):
        ...     print(f"Página {args.current_page}: {args.quantity_loaded} itens")
        ...
        >>> for item in PagedRequestWrapper.get_paged_results(
        ...     request, Partner, on_page_loaded=on_page
        ... ):
        ...     process(item)
        
        Versão assíncrona:
        
        >>> async for partner in PagedRequestWrapper.get_paged_results_async(
        ...     request, Partner
        ... ):
        ...     await process_async(partner)
    """
    
    # Cache simples em memória para evitar carregamentos duplicados
    _cache: ClassVar[Dict[str, Tuple[int, float]]] = {}
    _cache_lock: ClassVar[threading.Lock] = threading.Lock()
    
    # Tamanhos de página padrão do Sankhya
    PAGE_SIZE_SMALL = 150
    PAGE_SIZE_LARGE = 300
    
    def __init__(
        self,
        request: ServiceRequest,
        entity_type: Type[T],
        token: uuid.UUID,
        max_results: int = -1,
    ):
        """
        Inicializa o wrapper de requisição paginada.
        
        Args:
            request: Requisição de serviço base
            entity_type: Tipo da entidade a carregar
            token: Token UUID da sessão
            max_results: Limite máximo de resultados (-1 = ilimitado)
        """
        self._request = request
        self._entity_type = entity_type
        self._token = token
        self._max_results = max_results
        
        # Estado interno
        self._results_loaded = 0
        self._items: queue.Queue[EntityDynamicSerialization] = queue.Queue()
        self._all_pages_loaded = threading.Event()
        self._load_error: Optional[Exception] = None
        self._results_lock = threading.Lock()
        
        # Callbacks
        self._on_page_loaded: List[PageLoadedCallback] = []
        self._on_page_error: List[PageErrorCallback] = []
        self._on_page_processed: List[PageProcessedCallback] = []
        
        # Estado de paginação
        self._pager_id: Optional[str] = None
        self._total_pages: Optional[int] = None
        self._total_records: Optional[int] = None
    
    # =========================================================================
    # Callback Registration
    # =========================================================================
    
    def on_page_loaded(self, callback: PageLoadedCallback) -> "PagedRequestWrapper":
        """
        Registra callback para quando uma página é carregada com sucesso.
        
        Args:
            callback: Função a ser chamada com PagedRequestEventArgs
            
        Returns:
            Self para encadeamento
        """
        self._on_page_loaded.append(callback)
        return self
    
    def on_page_error(self, callback: PageErrorCallback) -> "PagedRequestWrapper":
        """
        Registra callback para quando ocorre erro no carregamento.
        
        Args:
            callback: Função a ser chamada com PagedRequestEventArgs
            
        Returns:
            Self para encadeamento
        """
        self._on_page_error.append(callback)
        return self
    
    def on_page_processed(self, callback: PageProcessedCallback) -> "PagedRequestWrapper":
        """
        Registra callback para quando uma página é processada.
        
        Args:
            callback: Função a ser chamada com PagedRequestEventArgs
            
        Returns:
            Self para encadeamento
        """
        self._on_page_processed.append(callback)
        return self
    
    # =========================================================================
    # Private Methods - Callback Dispatching
    # =========================================================================
    
    def _dispatch_page_loaded(
        self,
        page: int,
        quantity: int,
        total_pages: Optional[int] = None,
    ) -> None:
        """Dispara callbacks de página carregada."""
        args = PagedRequestEventArgs(
            entity_type=self._entity_type,
            current_page=page,
            total_loaded=self._results_loaded,
            quantity_loaded=quantity,
            total_pages=total_pages,
        )
        
        for callback in self._on_page_loaded:
            try:
                callback(args)
            except Exception as e:
                logger.warning(f"Erro em callback on_page_loaded: {e}")
    
    def _dispatch_page_error(
        self,
        page: int,
        exception: Exception,
    ) -> None:
        """Dispara callbacks de erro."""
        args = PagedRequestEventArgs(
            entity_type=self._entity_type,
            current_page=page,
            total_loaded=self._results_loaded,
            exception=exception,
        )
        
        for callback in self._on_page_error:
            try:
                callback(args)
            except Exception as e:
                logger.warning(f"Erro em callback on_page_error: {e}")
    
    def _dispatch_page_processed(
        self,
        page: int,
        quantity: int,
        total_pages: Optional[int] = None,
    ) -> None:
        """Dispara callbacks de página processada."""
        # Use provided total_pages or fallback to instance value
        pages = total_pages if total_pages is not None else self._total_pages
        args = PagedRequestEventArgs(
            entity_type=self._entity_type,
            current_page=page,
            total_loaded=self._results_loaded,
            quantity_loaded=quantity,
            total_pages=pages,
        )
        
        for callback in self._on_page_processed:
            try:
                callback(args)
            except Exception as e:
                logger.warning(f"Erro em callback on_page_processed: {e}")
    
    # =========================================================================
    # Private Methods - Page Loading (Sync)
    # =========================================================================
    
    def _load_page(self, page: int) -> Tuple[bool, int, Optional[int]]:
        """
        Carrega uma página específica de resultados.
        
        Args:
            page: Número da página (1-indexed)
            
        Returns:
            Tuple de (sucesso, quantidade_carregada, total_páginas)
        """
        from sankhya_sdk.core.context import SankhyaContext
        
        # Atualiza número da página na requisição
        if self._request.request_body and self._request.request_body.data_set:
            self._request.request_body.data_set.page_number = page
            
            # Adiciona pager_id se disponível
            if self._pager_id:
                self._request.request_body.data_set.pager_id = self._pager_id
        
        try:
            # Invoca serviço
            response = SankhyaContext.service_invoker_with_token(
                self._request, self._token
            )
            
            # Extrai informações de paginação
            entities = self._extract_entities_from_response(response)
            quantity_loaded = len(entities)
            
            # Atualiza pager_id e total_pages se disponíveis
            if response.response_body:
                pager = response.response_body.pager
                if pager:
                    if pager.pager_id:
                        self._pager_id = pager.pager_id
                    if pager.total_pages is not None:
                        self._total_pages = pager.total_pages
                    if pager.total_records is not None:
                        self._total_records = pager.total_records
            
            # Adiciona entidades à fila
            for entity in entities:
                self._items.put(entity)
            
            # Atualiza contador (thread-safe)
            with self._results_lock:
                self._results_loaded += quantity_loaded
            
            # Dispara callback de sucesso
            self._dispatch_page_loaded(page, quantity_loaded, self._total_pages)
            
            logger.debug(
                f"Página {page} carregada: {quantity_loaded} itens, "
                f"total: {self._results_loaded}"
            )
            
            return (True, quantity_loaded, self._total_pages)
            
        except Exception as e:
            logger.error(f"Erro ao carregar página {page}: {e}")
            # Comment 2: Set _load_error when _load_page catches an exception
            self._load_error = PagedRequestException(
                f"Erro ao carregar página {page}: {e}",
                page=page,
                inner_exception=e,
            )
            self._dispatch_page_error(page, e)
            return (False, 0, None)
    
    def _load_all_pages(self, cancel_event: threading.Event) -> None:
        """
        Carrega todas as páginas em uma thread separada.
        
        Args:
            cancel_event: Evento para sinalizar cancelamento
        """
        current_page = 1
        
        try:
            while not cancel_event.is_set():
                # Carrega página atual
                success, quantity, total_pages = self._load_page(current_page)
                
                if not success:
                    # Comment 2: Ensure _load_error is set when success is False
                    if not self._load_error:
                        self._load_error = PagedRequestException(
                            f"Falha ao carregar página {current_page}",
                            page=current_page,
                        )
                    break
                
                # Comment 3: Invoke _dispatch_page_processed after page items are enqueued
                self._dispatch_page_processed(current_page, quantity, total_pages)
                
                # Verifica se atingiu max_results
                if self._max_results > 0 and self._results_loaded >= self._max_results:
                    logger.debug(
                        f"Max results ({self._max_results}) atingido: "
                        f"{self._results_loaded}"
                    )
                    break
                
                # Verifica se há mais páginas
                # Sankhya retorna 150 ou 300 itens por página quando há mais
                if quantity not in (self.PAGE_SIZE_SMALL, self.PAGE_SIZE_LARGE):
                    logger.debug(
                        f"Última página detectada: {quantity} itens "
                        f"(esperado {self.PAGE_SIZE_SMALL} ou {self.PAGE_SIZE_LARGE})"
                    )
                    break
                
                # Verifica total_pages se disponível
                if total_pages is not None and current_page >= total_pages:
                    logger.debug(f"Todas as {total_pages} páginas carregadas")
                    break
                
                current_page += 1
                
        except Exception as e:
            logger.error(f"Erro durante carregamento de páginas: {e}")
            self._load_error = e
            
        finally:
            self._all_pages_loaded.set()
            logger.debug(
                f"Carregamento finalizado: {self._results_loaded} itens em "
                f"{current_page} páginas"
            )
    
    # =========================================================================
    # Private Methods - Response Processing
    # =========================================================================
    
    def _extract_entities_from_response(
        self, response: ServiceResponse
    ) -> List[EntityDynamicSerialization]:
        """
        Extrai entidades da resposta do serviço.
        
        Args:
            response: Resposta do serviço
            
        Returns:
            Lista de EntityDynamicSerialization
        """
        entities: List[EntityDynamicSerialization] = []
        
        if not response.response_body:
            return entities
        
        # Processa resposta baseada na estrutura
        body = response.response_body
        
        # Verifica se há entities diretas
        if hasattr(body, "entities") and body.entities:
            for entity_data in body.entities:
                if isinstance(entity_data, dict):
                    entities.append(EntityDynamicSerialization(entity_data))
                elif isinstance(entity_data, EntityDynamicSerialization):
                    entities.append(entity_data)
        
        # Verifica se há data_set com rows
        elif hasattr(body, "data_set") and body.data_set:
            data_set = body.data_set
            if hasattr(data_set, "rows") and data_set.rows:
                for row in data_set.rows:
                    if isinstance(row, dict):
                        entities.append(EntityDynamicSerialization(row))
        
        # Verifica se há result com data
        elif hasattr(body, "result") and body.result:
            result = body.result
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        entities.append(EntityDynamicSerialization(item))
        
        return entities
    
    # =========================================================================
    # Public Methods - Sync Generator
    # =========================================================================
    
    @classmethod
    def get_paged_results(
        cls,
        request: ServiceRequest,
        entity_type: Type[T],
        token: uuid.UUID,
        timeout: timedelta = timedelta(minutes=5),
        process_data: Optional[ProcessDataCallback[T]] = None,
        max_results: int = -1,
        on_page_loaded: Optional[PageLoadedCallback] = None,
        on_page_error: Optional[PageErrorCallback] = None,
        on_page_processed: Optional[PageProcessedCallback] = None,
    ) -> Generator[T, None, None]:
        """
        Obtém resultados paginados como um generator síncrono.
        
        Carrega páginas de resultados em uma thread separada enquanto
        retorna itens incrementalmente via yield. Suporta callbacks
        de progresso e processamento on-demand.
        
        Args:
            request: Requisição de serviço configurada
            entity_type: Tipo da entidade a retornar
            token: Token UUID da sessão Sankhya
            timeout: Timeout para a operação completa
            process_data: Callback opcional para processar lotes de dados
            max_results: Limite máximo de resultados (-1 = ilimitado)
            on_page_loaded: Callback quando página é carregada
            on_page_error: Callback quando ocorre erro
            on_page_processed: Callback quando página é processada
            
        Yields:
            Entidades tipadas do tipo especificado
            
        Raises:
            PagedRequestException: Erro durante carregamento
            TimeoutError: Timeout excedido
            
        Example:
            >>> for partner in PagedRequestWrapper.get_paged_results(
            ...     request, Partner, token,
            ...     timeout=timedelta(minutes=10),
            ...     max_results=1000
            ... ):
            ...     print(partner.name)
        """
        # Cria instância do wrapper
        wrapper = cls(
            request=request,
            entity_type=entity_type,
            token=token,
            max_results=max_results,
        )
        
        # Registra callbacks
        if on_page_loaded:
            wrapper.on_page_loaded(on_page_loaded)
        if on_page_error:
            wrapper.on_page_error(on_page_error)
        if on_page_processed:
            wrapper.on_page_processed(on_page_processed)
        
        # Evento de cancelamento
        cancel_event = threading.Event()
        
        # Inicia thread de carregamento
        loader_thread = threading.Thread(
            target=wrapper._load_all_pages,
            args=(cancel_event,),
            daemon=True,
        )
        loader_thread.start()
        
        # Comment 1: Track start time for timeout handling
        timeout_seconds = timeout.total_seconds()
        start_time = time.time()
        
        items_yielded = 0
        batch: List[T] = []
        batch_size = 50  # Tamanho do lote para process_data
        
        try:
            while True:
                try:
                    # Tenta obter item da fila com timeout curto
                    item = wrapper._items.get(timeout=0.1)
                    
                    # Converte para tipo de entidade
                    entity = item.convert_to_type(entity_type)
                    
                    # Adiciona ao lote se process_data fornecido
                    if process_data:
                        batch.append(entity)
                        if len(batch) >= batch_size:
                            process_data(batch)
                            batch = []
                    
                    yield entity
                    items_yielded += 1
                    
                    # Verifica max_results
                    if max_results > 0 and items_yielded >= max_results:
                        # Comment 4: Process pending batch before breaking due to max_results
                        if process_data and batch:
                            process_data(batch)
                            batch = []
                        cancel_event.set()
                        break
                        
                except queue.Empty:
                    # Comment 1: Check elapsed time against timeout
                    elapsed = time.time() - start_time
                    if elapsed >= timeout_seconds:
                        # Timeout exceeded - signal cancellation and stop loader
                        cancel_event.set()
                        wrapper._all_pages_loaded.set()  # Signal to break consumers
                        # Process any pending batch before raising
                        if process_data and batch:
                            process_data(batch)
                        raise TimeoutError(
                            f"Paged request timeout exceeded: {elapsed:.1f}s > {timeout_seconds}s"
                        )
                    
                    # Fila vazia - verifica se carregamento finalizou
                    if wrapper._all_pages_loaded.is_set():
                        # Comment 2: Check for load error and raise if present
                        if wrapper._load_error:
                            raise PagedRequestException(
                                f"Erro durante carregamento: {wrapper._load_error}",
                                inner_exception=wrapper._load_error,
                            )
                        # Processa último lote se houver
                        if process_data and batch:
                            process_data(batch)
                        break
                    
                    # Verifica se thread morreu
                    if not loader_thread.is_alive():
                        # Thread morreu - verifica erro
                        if wrapper._load_error:
                            raise PagedRequestException(
                                f"Erro durante carregamento: {wrapper._load_error}",
                                inner_exception=wrapper._load_error,
                            )
                        break
                        
        except GeneratorExit:
            # Generator foi fechado prematuramente
            cancel_event.set()
            raise
            
        finally:
            # Garante que thread é finalizada
            cancel_event.set()
            loader_thread.join(timeout=5.0)
            
            # Propaga erro se houver
            if wrapper._load_error:
                raise PagedRequestException(
                    f"Erro durante carregamento: {wrapper._load_error}",
                    inner_exception=wrapper._load_error,
                )
        
        logger.info(f"Paginação completa: {items_yielded} itens retornados")
    
    # =========================================================================
    # Private Methods - Page Loading (Async)
    # =========================================================================
    
    async def _load_page_async(self, page: int) -> Tuple[bool, int, Optional[int]]:
        """
        Carrega uma página específica de forma assíncrona.
        
        Args:
            page: Número da página (1-indexed)
            
        Returns:
            Tuple de (sucesso, quantidade_carregada, total_páginas)
        """
        from sankhya_sdk.core.context import SankhyaContext
        
        # Atualiza número da página na requisição
        if self._request.request_body and self._request.request_body.data_set:
            self._request.request_body.data_set.page_number = page
            
            if self._pager_id:
                self._request.request_body.data_set.pager_id = self._pager_id
        
        try:
            # Invoca serviço de forma assíncrona
            response = await SankhyaContext.service_invoker_async_with_token(
                self._request, self._token
            )
            
            # Extrai entidades
            entities = self._extract_entities_from_response(response)
            quantity_loaded = len(entities)
            
            # Atualiza paginação
            if response.response_body:
                pager = response.response_body.pager
                if pager:
                    if pager.pager_id:
                        self._pager_id = pager.pager_id
                    if pager.total_pages is not None:
                        self._total_pages = pager.total_pages
                    if pager.total_records is not None:
                        self._total_records = pager.total_records
            
            # Atualiza contador
            self._results_loaded += quantity_loaded
            
            # Dispara callback
            self._dispatch_page_loaded(page, quantity_loaded, self._total_pages)
            
            logger.debug(
                f"Página {page} carregada (async): {quantity_loaded} itens"
            )
            
            return (True, quantity_loaded, self._total_pages, entities)
            
        except Exception as e:
            logger.error(f"Erro ao carregar página {page} (async): {e}")
            # Comment 2: Set _load_error when _load_page_async catches an exception
            self._load_error = PagedRequestException(
                f"Erro ao carregar página {page} (async): {e}",
                page=page,
                inner_exception=e,
            )
            self._dispatch_page_error(page, e)
            return (False, 0, None, [])
    
    async def _load_all_pages_async(
        self,
        cancel_event: asyncio.Event,
        items_queue: asyncio.Queue,
    ) -> None:
        """
        Carrega todas as páginas de forma assíncrona.
        
        Args:
            cancel_event: Evento para sinalizar cancelamento
            items_queue: Fila assíncrona para armazenar itens
        """
        current_page = 1
        
        try:
            while not cancel_event.is_set():
                result = await self._load_page_async(current_page)
                success, quantity, total_pages = result[:3]
                entities = result[3] if len(result) > 3 else []
                
                if not success:
                    # Comment 2: Ensure _load_error is set when success is False
                    if not self._load_error:
                        self._load_error = PagedRequestException(
                            f"Falha ao carregar página {current_page} (async)",
                            page=current_page,
                        )
                    break
                
                # Adiciona entidades à fila assíncrona
                for entity in entities:
                    await items_queue.put(entity)
                
                # Comment 3: Invoke _dispatch_page_processed after page items are enqueued
                self._dispatch_page_processed(current_page, quantity, total_pages)
                
                # Verifica max_results
                if self._max_results > 0 and self._results_loaded >= self._max_results:
                    break
                
                # Verifica se há mais páginas
                if quantity not in (self.PAGE_SIZE_SMALL, self.PAGE_SIZE_LARGE):
                    break
                
                if total_pages is not None and current_page >= total_pages:
                    break
                
                current_page += 1
                
        except Exception as e:
            logger.error(f"Erro durante carregamento async: {e}")
            self._load_error = e
            
        finally:
            # Sinaliza fim do carregamento
            await items_queue.put(None)  # Sentinel value
    
    # =========================================================================
    # Public Methods - Async Generator
    # =========================================================================
    
    @classmethod
    async def get_paged_results_async(
        cls,
        request: ServiceRequest,
        entity_type: Type[T],
        token: uuid.UUID,
        timeout: timedelta = timedelta(minutes=5),
        process_data: Optional[ProcessDataCallbackAsync[T]] = None,
        max_results: int = -1,
        on_page_loaded: Optional[PageLoadedCallback] = None,
        on_page_error: Optional[PageErrorCallback] = None,
        on_page_processed: Optional[PageProcessedCallback] = None,
    ) -> AsyncGenerator[T, None]:
        """
        Obtém resultados paginados como um async generator.
        
        Carrega páginas de resultados de forma assíncrona enquanto
        retorna itens incrementalmente via async yield.
        
        Args:
            request: Requisição de serviço configurada
            entity_type: Tipo da entidade a retornar
            token: Token UUID da sessão Sankhya
            timeout: Timeout para a operação completa
            process_data: Callback async opcional para processar lotes
            max_results: Limite máximo de resultados (-1 = ilimitado)
            on_page_loaded: Callback quando página é carregada
            on_page_error: Callback quando ocorre erro
            on_page_processed: Callback quando página é processada
            
        Yields:
            Entidades tipadas do tipo especificado
            
        Raises:
            PagedRequestException: Erro durante carregamento
            asyncio.TimeoutError: Timeout excedido
            
        Example:
            >>> async for partner in PagedRequestWrapper.get_paged_results_async(
            ...     request, Partner, token
            ... ):
            ...     await process_async(partner)
        """
        # Cria instância do wrapper
        wrapper = cls(
            request=request,
            entity_type=entity_type,
            token=token,
            max_results=max_results,
        )
        
        # Registra callbacks
        if on_page_loaded:
            wrapper.on_page_loaded(on_page_loaded)
        if on_page_error:
            wrapper.on_page_error(on_page_error)
        if on_page_processed:
            wrapper.on_page_processed(on_page_processed)
        
        # Fila assíncrona e evento de cancelamento
        items_queue: asyncio.Queue = asyncio.Queue()
        cancel_event = asyncio.Event()
        
        # Inicia task de carregamento
        loader_task = asyncio.create_task(
            wrapper._load_all_pages_async(cancel_event, items_queue)
        )
        
        # Comment 1: Track start time for timeout handling
        timeout_seconds = timeout.total_seconds()
        start_time = time.time()
        
        items_yielded = 0
        batch: List[T] = []
        batch_size = 50
        
        try:
            while True:
                try:
                    # Comment 1: Check elapsed time against timeout on each loop
                    elapsed = time.time() - start_time
                    if elapsed >= timeout_seconds:
                        # Timeout exceeded - signal cancellation and stop loader
                        cancel_event.set()
                        await items_queue.put(None)  # Signal sentinel to break consumers
                        # Process any pending batch before raising
                        if process_data and batch:
                            await process_data(batch)
                        raise TimeoutError(
                            f"Paged request timeout exceeded (async): {elapsed:.1f}s > {timeout_seconds}s"
                        )
                    
                    # Aguarda item com timeout parcial (máximo 10 segundos)
                    remaining = timeout_seconds - elapsed
                    wait_timeout = min(remaining, 10.0)
                    item = await asyncio.wait_for(
                        items_queue.get(),
                        timeout=wait_timeout,
                    )
                    
                    # Verifica sentinel (fim do carregamento)
                    if item is None:
                        # Comment 2: Check for load error and raise if present
                        if wrapper._load_error:
                            raise PagedRequestException(
                                f"Erro durante carregamento: {wrapper._load_error}",
                                inner_exception=wrapper._load_error,
                            )
                        # Processa último lote
                        if process_data and batch:
                            await process_data(batch)
                        break
                    
                    # Converte para tipo de entidade
                    entity = item.convert_to_type(entity_type)
                    
                    # Processa em lotes se callback fornecido
                    if process_data:
                        batch.append(entity)
                        if len(batch) >= batch_size:
                            await process_data(batch)
                            batch = []
                    
                    yield entity
                    items_yielded += 1
                    
                    # Verifica max_results
                    if max_results > 0 and items_yielded >= max_results:
                        # Comment 4: Process pending batch before breaking due to max_results
                        if process_data and batch:
                            await process_data(batch)
                            batch = []
                        cancel_event.set()
                        break
                        
                except asyncio.TimeoutError:
                    # Verifica se loader ainda está rodando
                    if loader_task.done():
                        # Verifica erro
                        if wrapper._load_error:
                            raise PagedRequestException(
                                f"Erro durante carregamento: {wrapper._load_error}",
                                inner_exception=wrapper._load_error,
                            )
                        # Processa último lote se houver
                        if process_data and batch:
                            await process_data(batch)
                        break
                    # Continua aguardando (timeout parcial expirou)
                    continue
                    
        except GeneratorExit:
            cancel_event.set()
            raise
            
        finally:
            # Cancela task se ainda estiver rodando
            cancel_event.set()
            if not loader_task.done():
                loader_task.cancel()
                try:
                    await loader_task
                except asyncio.CancelledError:
                    pass
            
            # Propaga erro se houver
            if wrapper._load_error:
                raise PagedRequestException(
                    f"Erro durante carregamento: {wrapper._load_error}",
                    inner_exception=wrapper._load_error,
                )
        
        logger.info(f"Paginação async completa: {items_yielded} itens")
    
    # =========================================================================
    # Cache Methods (Optional)
    # =========================================================================
    
    @classmethod
    def _get_cache_key(cls, entity_type: Type[T], user_code: int) -> str:
        """
        Gera chave de cache baseada na entidade e usuário.
        
        Args:
            entity_type: Tipo da entidade
            user_code: Código do usuário
            
        Returns:
            Chave de cache única
        """
        import os
        entity_name = entity_type.__name__
        process_id = os.getpid()
        return f"{entity_name}:{user_code}:{process_id}"
    
    @classmethod
    def _acquire_cache_lock(cls, key: str, timeout: float = 30.0) -> bool:
        """
        Tenta adquirir lock de cache.
        
        Args:
            key: Chave de cache
            timeout: Timeout em segundos
            
        Returns:
            True se lock adquirido
        """
        import time
        import os
        
        process_id = os.getpid()
        current_time = time.time()
        
        with cls._cache_lock:
            if key in cls._cache:
                cached_pid, cached_time = cls._cache[key]
                # Verifica se lock expirou
                if current_time - cached_time > timeout:
                    cls._cache[key] = (process_id, current_time)
                    return True
                return False
            
            cls._cache[key] = (process_id, current_time)
            return True
    
    @classmethod
    def _release_cache_lock(cls, key: str) -> None:
        """
        Libera lock de cache.
        
        Args:
            key: Chave de cache
        """
        with cls._cache_lock:
            cls._cache.pop(key, None)
