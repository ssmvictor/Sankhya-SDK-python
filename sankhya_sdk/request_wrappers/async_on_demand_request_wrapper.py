# -*- coding: utf-8 -*-
"""
AsyncOnDemandRequestWrapper para processamento assíncrono em lote.

Versão assíncrona do OnDemandRequestWrapper usando asyncio para
operações de criação/atualização de entidades.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/OnDemandRequestWrapper.cs
"""

from __future__ import annotations

import asyncio
import logging
from typing import (
    TYPE_CHECKING,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)
from uuid import UUID

if TYPE_CHECKING:
    from sankhya_sdk.core.context import SankhyaContext

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.events import EventBus, OnDemandRequestFailureEvent
from sankhya_sdk.exceptions import (
    CanceledOnDemandRequestWrapperException,
    SankhyaException,
    ServiceRequestDeadlockException,
    ServiceRequestTimeoutException,
)
from sankhya_sdk.helpers.service_request_extensions import ServiceRequestExtensions
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service.service_request import ServiceRequest


def _is_update_operation(entity: EntityBase) -> bool:
    """Verifica se a operação é de atualização baseado nas chaves."""
    from sankhya_sdk.attributes.reflection import get_field_metadata
    for field_name, field_info in entity.model_fields.items():
        try:
            metadata = get_field_metadata(field_info)
            if metadata.is_key:
                value = getattr(entity, field_name, None)
                if value is None:
                    return False
        except Exception:
            continue
    return True


logger = logging.getLogger(__name__)

# TypeVar para entidades genéricas
TEntity = TypeVar("TEntity", bound=EntityBase)


# Constantes
_WAIT_TIMEOUT_SECONDS = 60.0
_MAX_RETRY_COUNT = 3


class AsyncOnDemandRequestWrapper(Generic[TEntity]):
    """
    Wrapper assíncrono para processamento em lote de entidades.
    
    Implementa processamento em background com controle de throughput,
    filas asyncio e retry automático para erros transientes.
    
    Usa uma task asyncio dedicada que processa entidades em lotes
    quando o throughput é atingido ou quando flush() é chamado.
    
    Attributes:
        request_count: Número de requisições feitas
        entities_sent: Número total de entidades enviadas
        entities_sent_successfully: Número de entidades enviadas com sucesso
        is_disposed: Indica se o wrapper foi descartado
    
    Example:
        >>> async with AsyncOnDemandRequestWrapper[Partner](
        ...     ServiceName.CRUD_SERVICE_SAVE,
        ...     cancel_event
        ... ) as wrapper:
        ...     for partner in partners:
        ...         await wrapper.add(partner)
        ...     await wrapper.flush()
    """

    def __init__(
        self,
        service: ServiceName,
        cancel_event: asyncio.Event,
        throughput: int = 10,
        allow_above_throughput: bool = True,
        context: Optional["SankhyaContext"] = None,
        session_token: Optional[UUID] = None,
    ) -> None:
        """
        Inicializa o wrapper assíncrono.
        
        Args:
            service: Nome do serviço a usar (ex: CRUD_SERVICE_SAVE)
            cancel_event: Evento asyncio para sinalizar cancelamento
            throughput: Quantidade de entidades na fila que dispara o envio
                de um lote (abaixo disso só há envio em flush, cancelamento
                ou dispose)
            allow_above_throughput: Se True, o lote leva todas as entidades
                disponíveis na fila; se False, no máximo ``throughput``
            context: Contexto Sankhya (opcional)
            session_token: Token de sessão existente (opcional)
        """
        self._service = service
        self._throughput = throughput
        self._allow_above_throughput = allow_above_throughput
        self._cancel_event = cancel_event
        
        # Filas e eventos de sincronização
        self._queue: asyncio.Queue[TEntity] = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._flush_event = asyncio.Event()
        self._work_available = asyncio.Event()
        self._flush_complete = asyncio.Event()
        
        # Sessão e contexto
        self._context = context
        self._session_token = session_token
        self._owns_session = False
        
        # Estatísticas
        self._request_count = 0
        self._entities_sent = 0
        self._entities_sent_successfully = 0
        
        # Estado
        self._disposed = False
        self._lock = asyncio.Lock()
        
        # Task worker (será iniciada no __aenter__)
        self._worker_task: Optional[asyncio.Task] = None
        
        logger.debug(
            f"AsyncOnDemandRequestWrapper criado: service={service.name}, "
            f"throughput={throughput}"
        )

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def request_count(self) -> int:
        """Retorna o número de requisições feitas."""
        return self._request_count

    @property
    def entities_sent(self) -> int:
        """Retorna o número total de entidades enviadas."""
        return self._entities_sent

    @property
    def entities_sent_successfully(self) -> int:
        """Retorna o número de entidades enviadas com sucesso."""
        return self._entities_sent_successfully

    @property
    def is_disposed(self) -> bool:
        """Indica se o wrapper foi descartado."""
        return self._disposed

    @property
    def queue_size(self) -> int:
        """Retorna o número de entidades na fila."""
        return self._queue.qsize()

    # =========================================================================
    # Public Methods
    # =========================================================================

    async def start(self) -> None:
        """Inicia a task worker."""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(
                self._process(),
                name=f"AsyncOnDemandWorker-{id(self)}",
            )
            logger.debug("Worker task iniciada")

    async def add(self, entity: TEntity) -> None:
        """
        Adiciona uma entidade à fila de processamento.
        
        Args:
            entity: Entidade a ser processada
            
        Raises:
            ValueError: Se o wrapper já foi descartado
            CanceledOnDemandRequestWrapperException: Se o cancelamento já
                foi solicitado (.NET OnDemandRequestWrapper.cs:105-108)
        """
        if self._disposed:
            raise ValueError("AsyncOnDemandRequestWrapper já foi descartado")
        
        if self._cancel_event.is_set():
            raise CanceledOnDemandRequestWrapperException()
        
        await self._queue.put(entity)
        self._work_available.set()
        
        logger.debug(f"Entidade adicionada à fila: {type(entity).__name__}")

    async def flush(self) -> None:
        """
        Força o processamento imediato de todas as entidades na fila.
        
        Aguarda até que todas as entidades pendentes sejam processadas.
        """
        if self._disposed:
            return
        
        if self._queue.empty():
            return
        
        # Sem task worker ativa ninguém processaria a fila nem sinalizaria
        # a conclusão do flush
        if not self._is_worker_running():
            await self.start()
        
        self._flush_complete.clear()
        self._flush_event.set()
        self._work_available.set()
        
        # Aguarda conclusão do flush
        await self._flush_complete.wait()
        
        logger.debug("Flush concluído")

    async def dispose(self) -> None:
        """
        Finaliza o wrapper e libera recursos.
        
        Aguarda a conclusão do processamento em andamento.
        """
        if self._disposed:
            return
        
        async with self._lock:
            if self._disposed:
                return
            self._disposed = True
        
        # Sinaliza parada
        self._stop_event.set()
        self._work_available.set()
        
        # Como no .NET, o dispose envia as entidades pendentes: sem task
        # worker ativa, ela é iniciada para drenar a fila
        if not self._is_worker_running() and not self._queue.empty():
            await self.start()
        
        # Aguarda task worker
        if self._worker_task and not self._worker_task.done():
            try:
                await asyncio.wait_for(self._worker_task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Worker task não finalizou no tempo esperado")
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
        
        # Finaliza sessão se for proprietário
        if self._owns_session and self._session_token and self._context:
            try:
                self._context.detach_on_demand_request_wrapper(self._session_token)
            except Exception as e:
                logger.warning(f"Erro ao finalizar sessão: {e}")
        
        logger.info(
            f"AsyncOnDemandRequestWrapper finalizado: "
            f"requests={self._request_count}, "
            f"sent={self._entities_sent}, "
            f"successful={self._entities_sent_successfully}"
        )

    # =========================================================================
    # Async Context Manager
    # =========================================================================

    async def __aenter__(self) -> "AsyncOnDemandRequestWrapper[TEntity]":
        """Entra no contexto assíncrono e inicia worker."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: object,
    ) -> None:
        """Sai do contexto assíncrono e libera recursos."""
        await self.flush()
        await self.dispose()

    # =========================================================================
    # Worker Task
    # =========================================================================

    def _is_worker_running(self) -> bool:
        """Indica se a task worker está ativa."""
        return self._worker_task is not None and not self._worker_task.done()

    async def _process(self) -> None:
        """
        Loop principal da task worker.
        
        Equivalente a ``Process`` do .NET (OnDemandRequestWrapper.cs:144-165):
        processa até que cancelamento ou dispose encontrem a fila vazia.
        """
        try:
            while True:
                try:
                    if await self._process_internal():
                        break
                except Exception as e:
                    logger.error(f"Erro na worker task: {e}", exc_info=True)
        finally:
            # Sinaliza conclusão de qualquer flush pendente
            self._flush_complete.set()
            logger.debug("Worker task finalizada")

    async def _wait_for_work(self) -> None:
        """
        Aguarda sinal de trabalho, cancelamento ou timeout.
        
        Equivalente a ``WaitHandle.WaitAny(new[] { _event, _token.WaitHandle },
        1 min)`` do .NET.
        """
        if self._work_available.is_set() or self._cancel_event.is_set():
            return
        
        waiters = [
            asyncio.ensure_future(self._work_available.wait()),
            asyncio.ensure_future(self._cancel_event.wait()),
        ]
        try:
            await asyncio.wait(
                waiters,
                timeout=_WAIT_TIMEOUT_SECONDS,
                return_when=asyncio.FIRST_COMPLETED,
            )
        finally:
            for waiter in waiters:
                waiter.cancel()
            await asyncio.gather(*waiters, return_exceptions=True)

    async def _process_internal(self) -> bool:
        """
        Executa uma iteração da task worker.
        
        Equivalente a ``ProcessInternal`` do .NET
        (OnDemandRequestWrapper.cs:167-240): com menos de ``throughput``
        entidades na fila nada é enviado, exceto em flush, cancelamento ou
        dispose. Com ``allow_above_throughput`` (ou envio forçado) o lote leva
        todas as entidades disponíveis; caso contrário, no máximo
        ``throughput``.
        
        Returns:
            True se deve parar, False para continuar.
        """
        await self._wait_for_work()
        
        # Consome o sinal antes de inspecionar o estado: um add() posterior
        # sinaliza de novo, então nenhum aviso se perde
        self._work_available.clear()
        
        is_flushing = self._flush_event.is_set()
        if is_flushing:
            self._flush_event.clear()
        
        try:
            is_cancelling = self._cancel_event.is_set()
            is_disposing = self._stop_event.is_set()
            
            if self._queue.empty() and (is_cancelling or is_disposing):
                return True
            
            force_request = is_cancelling or is_disposing or is_flushing
            
            if self._queue.qsize() < self._throughput and not force_request:
                return False
            
            # Coleta itens da fila
            items: List[TEntity] = []
            while (
                len(items) < self._throughput
                or force_request
                or self._allow_above_throughput
            ):
                try:
                    items.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            
            if not items:
                return False
            
            try:
                await self._process_batch(items)
            finally:
                # Como no .NET (que não reseta o evento após enviar um lote),
                # a fila é reavaliada sem esperar novo add(): se ainda houver
                # throughput, o próximo lote é enviado em seguida
                self._work_available.set()
            
            return False
        finally:
            # O flush é sinalizado mesmo se o processamento falhar, para que
            # flush() não fique bloqueado para sempre
            if is_flushing:
                self._flush_complete.set()

    async def _process_batch(self, items: List[TEntity]) -> None:
        """
        Processa um lote de entidades.
        
        Equivalente ao final de ``ProcessInternal`` do .NET
        (OnDemandRequestWrapper.cs:222-237): ``request.Resolve(items)`` monta
        a requisição em lote e, se o lote falhar, as entidades são reenviadas
        individualmente.
        
        Args:
            items: Lista de entidades a processar
        """
        if not items:
            return
        
        self._entities_sent += len(items)
        
        # Cria requisição (Resolve<T>(ICollection<T>) no .NET)
        try:
            request = ServiceRequest(service=self._service)
            ServiceRequestExtensions.resolve_with_collection(request, items)
        except Exception as e:
            # Não descarta o lote: cada entidade é montada e enviada sozinha,
            # e as que falharem geram OnDemandRequestFailureEvent
            logger.error(f"Erro ao montar requisição em lote: {e}", exc_info=True)
            await self._process_items_separately(items)
            return
        
        # Tenta processar em lote
        success, exception = await self._process_request(request)
        
        if success:
            self._entities_sent_successfully += len(items)
            logger.debug(f"Lote processado: {len(items)} entidades")
        else:
            # Fallback: processa individualmente
            logger.warning(
                f"Falha no lote, processando {len(items)} entidades individualmente"
            )
            await self._process_items_separately(items)

    async def _process_request(
        self,
        request: ServiceRequest,
        retry: bool = False,
    ) -> Tuple[bool, Optional[Exception]]:
        """
        Executa uma requisição com retry para erros transientes.
        
        Args:
            request: Requisição a executar
            retry: Se True, é uma tentativa de retry
            
        Returns:
            Tuple (sucesso, exceção_se_falhou)
        """
        try:
            self._request_count += 1
            await self._invoke_service_async(request)
            return True, None
            
        except (ServiceRequestTimeoutException, ServiceRequestDeadlockException) as e:
            # .NET (OnDemandRequestWrapper.cs:259-280): timeout e deadlock são
            # tentados novamente uma única vez, de imediato
            if retry:
                logger.warning(f"Retry falhou: {e}")
                return False, e
            
            return await self._process_request(request, retry=True)
            
        except SankhyaException as e:
            logger.error(f"Erro na requisição: {e}")
            return False, e
            
        except Exception as e:
            logger.error(f"Erro inesperado: {e}", exc_info=True)
            return False, e

    async def _process_items_separately(self, items: List[TEntity]) -> None:
        """
        Processa itens individualmente após falha em lote.
        
        Args:
            items: Lista de entidades a processar individualmente
        """
        for item in items:
            # Resolve<T>(T) no .NET
            try:
                request = ServiceRequest(service=self._service)
                ServiceRequestExtensions.resolve_with_entity(request, item)
            except Exception as e:
                logger.error(f"Erro ao montar requisição: {e}", exc_info=True)
                self._publish_failure(item, e)
                continue
            
            success, exception = await self._process_request(request)
            
            if success:
                self._entities_sent_successfully += 1
            elif exception:
                self._publish_failure(item, exception)

    def _publish_failure(self, item: TEntity, exception: BaseException) -> None:
        """
        Dispara o OnDemandRequestFailureEvent de uma entidade que falhou.
        
        Args:
            item: Entidade que falhou
            exception: Exceção que causou a falha
        """
        is_update = _is_update_operation(item)
        failure_event = OnDemandRequestFailureEvent(
            entity=item,
            is_update=is_update,
            exception=exception,
        )
        EventBus.publish(failure_event)
        logger.warning(
            f"Entidade falhou: {type(item).__name__}, "
            f"is_update={is_update}"
        )

    async def _invoke_service_async(self, request: ServiceRequest) -> None:
        """
        Invoca o serviço de forma assíncrona.
        
        Args:
            request: Requisição a executar
        """
        from sankhya_sdk.core.context import SankhyaContext
        
        if self._session_token:
            await SankhyaContext.service_invoker_async_with_token(
                request, self._session_token
            )
        elif self._context:
            await self._context.service_invoker_async(request)
        else:
            raise RuntimeError(
                "Nenhum contexto ou token de sessão disponível para invocação"
            )


__all__ = ["AsyncOnDemandRequestWrapper"]
