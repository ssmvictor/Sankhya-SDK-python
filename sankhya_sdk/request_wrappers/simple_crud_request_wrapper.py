# -*- coding: utf-8 -*-
"""
SimpleCRUD Request Wrapper.

Fornece operações CRUD simplificadas (Find, Update, Remove) para entidades
do Sankhya, com suporte a operações síncronas e assíncronas.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/SimpleCRUDRequestWrapper.cs
"""

from __future__ import annotations

import logging
import threading
import uuid
from typing import (
    TYPE_CHECKING,
    ClassVar,
    List,
    Optional,
    Type,
    TypeVar,
)

if TYPE_CHECKING:
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.helpers.entity_query_options import EntityQueryOptions

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.exceptions import (
    ServiceRequestTooManyResultsException,
    ServiceRequestUnexpectedResultException,
)
from sankhya_sdk.helpers.entity_dynamic_serialization import EntityDynamicSerialization
from sankhya_sdk.helpers.filter_expression import ILiteralCriteria
from sankhya_sdk.helpers.service_request_extensions import ServiceRequestExtensions
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service.entity_types import EntityDynamic
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse

logger = logging.getLogger(__name__)

# TypeVar para entidades genéricas
T = TypeVar("T", bound=EntityBase)


class SimpleCRUDRequestWrapper:
    """
    Wrapper para operações CRUD simplificadas em entidades do Sankhya.
    
    Gerencia uma sessão autenticada e fornece métodos para buscar,
    atualizar e remover entidades, com suporte a operações síncronas
    e assíncronas.
    
    Esta classe utiliza atributos de classe para manter uma sessão
    compartilhada, similar ao padrão de métodos de extensão do C#.
    
    Attributes:
        _context: Contexto Sankhya para gerenciamento de sessão
        _session_token: Token UUID da sessão ativa
        _owns_context: Indica se o contexto foi criado pelo próprio wrapper
            (initialize() sem contexto) e, portanto, deve ter sua sessão
            principal encerrada em dispose()
        _initialized: Flag indicando se o wrapper foi inicializado
        _lock: Lock que serializa initialize() e dispose() entre threads
    
    Example:
        Inicialização e uso básico:
        
        >>> SimpleCRUDRequestWrapper.initialize()
        >>> partner = Partner(code=123)
        >>> result = SimpleCRUDRequestWrapper.try_find(partner)
        >>> if result:
        ...     print(result.name)
        >>> SimpleCRUDRequestWrapper.dispose()
        
        Com context manager:
        
        >>> with SimpleCRUDRequestWrapper():
        ...     partner = SimpleCRUDRequestWrapper.find(Partner(code=123))
        ...     print(partner.name)
    """

    _context: ClassVar[Optional["SankhyaContext"]] = None
    _session_token: ClassVar[Optional[uuid.UUID]] = None
    _owns_context: ClassVar[bool] = False
    _initialized: ClassVar[bool] = False
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        """
        Inicializa o wrapper como context manager.
        
        Quando usado como context manager, inicializa automaticamente
        a sessão ao entrar no contexto.
        """
        self._managed = False

    def __enter__(self) -> "SimpleCRUDRequestWrapper":
        """Entra no contexto e inicializa a sessão."""
        if not SimpleCRUDRequestWrapper._initialized:
            SimpleCRUDRequestWrapper.initialize()
        self._managed = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sai do contexto e libera recursos."""
        if self._managed:
            SimpleCRUDRequestWrapper.dispose()

    async def __aenter__(self) -> "SimpleCRUDRequestWrapper":
        """Entra no contexto assíncrono."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sai do contexto assíncrono."""
        self.__exit__(exc_type, exc_val, exc_tb)

    # =========================================================================
    # Initialization & Lifecycle
    # =========================================================================

    @classmethod
    def initialize(
        cls,
        context: Optional["SankhyaContext"] = None,
    ) -> None:
        """
        Inicializa o wrapper com um contexto Sankhya.
        
        Se nenhum contexto for fornecido, cria um novo usando
        as configurações padrão (SankhyaSettings). Em ambos os casos
        uma sessão dedicada (ServiceRequestType.SIMPLE_CRUD) é adquirida
        do contexto e finalizada em dispose().
        
        O contexto criado internamente pertence ao wrapper: sua sessão
        principal também é encerrada em dispose(). Um contexto informado
        pertence a quem o criou, que deve descartá-lo.
        
        Thread-safe e idempotente: chamadas concorrentes adquirem uma única
        sessão, como o inicializador estático do .NET
        (SimpleCRUDRequestWrapper.cs:17-21), executado uma única vez.
        
        Args:
            context: Contexto Sankhya existente (opcional)
            
        Raises:
            RuntimeError: Se já foi inicializado
            
        Example:
            >>> SimpleCRUDRequestWrapper.initialize()
            >>> # ou com contexto existente
            >>> ctx = SankhyaContext.from_settings()
            >>> SimpleCRUDRequestWrapper.initialize(ctx)
        """
        with cls._lock:
            if cls._initialized:
                logger.warning("SimpleCRUDRequestWrapper já inicializado")
                return

            if context is not None:
                # Como no .NET (Context.AcquireNewSession(ServiceRequestType.SimpleCrud)),
                # o wrapper usa uma sessão dedicada e não a sessão principal do contexto.
                cls._context = context
                cls._session_token = context.acquire_new_session(
                    ServiceRequestType.SIMPLE_CRUD
                )
                cls._owns_context = False
            else:
                # Import local para evitar circular
                from sankhya_sdk.core.context import SankhyaContext
                owned_context = SankhyaContext.from_settings()
                try:
                    session_token = owned_context.acquire_new_session(
                        ServiceRequestType.SIMPLE_CRUD
                    )
                except Exception:
                    # Ninguém mais referencia o contexto criado aqui
                    cls._release_owned_context(owned_context)
                    raise
                cls._context = owned_context
                cls._session_token = session_token
                cls._owns_context = True

            cls._initialized = True
            logger.info(
                f"SimpleCRUDRequestWrapper inicializado: token={cls._session_token}"
            )

    @classmethod
    def dispose(cls) -> None:
        """
        Libera os recursos do wrapper.
        
        Finaliza a sessão dedicada e limpa os atributos de classe. Se o
        contexto foi criado pelo próprio wrapper (initialize() sem
        contexto), encerra também a sessão principal desse contexto.
        Pode ser chamado múltiplas vezes sem efeito.
        
        Example:
            >>> SimpleCRUDRequestWrapper.dispose()
        """
        with cls._lock:
            if not cls._initialized:
                return

            context = cls._context
            session_token = cls._session_token
            owns_context = cls._owns_context
            cls._context = None
            cls._session_token = None
            cls._owns_context = False
            cls._initialized = False

        if context and session_token:
            try:
                context.finalize_session(session_token)
            except Exception as e:
                logger.warning(f"Erro ao finalizar sessão: {e}")

        if owns_context and context:
            cls._release_owned_context(context)

        logger.info("SimpleCRUDRequestWrapper descartado")

    @staticmethod
    def _release_owned_context(context: "SankhyaContext") -> None:
        """
        Encerra a sessão principal de um contexto criado pelo wrapper.
        
        No .NET o contexto vem do ServiceLocator e pertence à aplicação,
        que o descarta (SimpleCRUDRequestWrapper.cs:17); o wrapper nunca
        cria um. Aqui, sem contexto informado, o contexto criado em
        initialize() só é referenciado pelo wrapper, e
        ``SankhyaContext.__del__`` não encerra sessões
        (``~SankhyaContext() => Dispose(false)``): sem esta liberação a
        sessão principal ficaria autenticada no registro de classe.
        
        ``SankhyaContext.dispose()`` não é usado porque descarta TODOS os
        wrappers do registro de classe, inclusive sessões de outros
        contextos ainda em uso. Apenas a sessão principal deste contexto é
        removida do registro e encerrada (logout).
        
        Args:
            context: Contexto criado pelo próprio wrapper
        """
        from sankhya_sdk.core.context import SankhyaContext

        with SankhyaContext._wrappers_lock:
            SankhyaContext._wrappers.pop(context.token, None)
        try:
            context.wrapper.dispose()
        except Exception as e:
            logger.warning(f"Erro ao encerrar a sessão principal do contexto: {e}")
        finally:
            context._disposed = True

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Garante que o wrapper está inicializado."""
        if not cls._initialized:
            raise RuntimeError(
                "SimpleCRUDRequestWrapper não inicializado. "
                "Chame SimpleCRUDRequestWrapper.initialize() primeiro."
            )

    # =========================================================================
    # Find Operations (Sync)
    # =========================================================================

    @classmethod
    def try_find(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"] = None,
    ) -> Optional[T]:
        """
        Busca uma entidade por suas chaves primárias.
        
        Retorna None se a entidade não for encontrada. Lança exceção
        se múltiplos resultados forem retornados.
        
        Args:
            entity: Entidade com chaves primárias preenchidas
            options: Opções de query (opcional)
            
        Returns:
            Entidade encontrada ou None se não existir
            
        Raises:
            ServiceRequestTooManyResultsException: Se múltiplos resultados
            RuntimeError: Se wrapper não inicializado
            
        Example:
            >>> partner = Partner(code=123)
            >>> result = SimpleCRUDRequestWrapper.try_find(partner)
            >>> if result:
            ...     print(f"Encontrado: {result.name}")
            ... else:
            ...     print("Não encontrado")
        """
        cls._ensure_initialized()
        return cls._can_find_internal(entity, options)

    @classmethod
    def try_find_with_criteria(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"] = None,
    ) -> Optional[T]:
        """
        Busca uma entidade usando critérios literais.
        
        Args:
            entity_type: Tipo da entidade a buscar
            criteria: Critério de busca
            options: Opções de query (opcional)
            
        Returns:
            Entidade encontrada ou None se não existir
            
        Raises:
            ServiceRequestTooManyResultsException: Se múltiplos resultados
            
        Example:
            >>> criteria = LiteralCriteria.equals("CODPARC", 123)
            >>> result = SimpleCRUDRequestWrapper.try_find_with_criteria(
            ...     Partner, criteria
            ... )
        """
        cls._ensure_initialized()
        return cls._can_find_with_criteria_internal(entity_type, criteria, options)

    @classmethod
    def find(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"] = None,
    ) -> T:
        """
        Busca uma entidade por suas chaves primárias (obrigatório encontrar).
        
        Lança exceção se a entidade não for encontrada.
        
        Args:
            entity: Entidade com chaves primárias preenchidas
            options: Opções de query (opcional)
            
        Returns:
            Entidade encontrada
            
        Raises:
            ServiceRequestUnexpectedResultException: Se não encontrada
            ServiceRequestTooManyResultsException: Se múltiplos resultados
            
        Example:
            >>> partner = SimpleCRUDRequestWrapper.find(Partner(code=123))
        """
        cls._ensure_initialized()
        return cls._must_find_internal(entity, options)

    @classmethod
    def find_with_criteria(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"] = None,
    ) -> T:
        """
        Busca uma entidade usando critérios (obrigatório encontrar).
        
        Args:
            entity_type: Tipo da entidade a buscar
            criteria: Critério de busca
            options: Opções de query (opcional)
            
        Returns:
            Entidade encontrada
            
        Raises:
            ServiceRequestUnexpectedResultException: Se não encontrada
            ServiceRequestTooManyResultsException: Se múltiplos resultados
        """
        cls._ensure_initialized()
        return cls._must_find_with_criteria_internal(entity_type, criteria, options)

    @classmethod
    def find_all(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"] = None,
    ) -> List[T]:
        """
        Busca todas as entidades que correspondem aos critérios.
        
        Args:
            entity: Entidade com critérios de busca
            options: Opções de query (opcional)
            
        Returns:
            Lista de entidades encontradas (pode estar vazia)
            
        Example:
            >>> partner = Partner(active="S")
            >>> results = SimpleCRUDRequestWrapper.find_all(partner)
            >>> for p in results:
            ...     print(p.name)
        """
        cls._ensure_initialized()
        return cls._find_all_internal(entity, options)

    # =========================================================================
    # Find Operations (Async)
    # =========================================================================

    @classmethod
    async def try_find_async(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"] = None,
    ) -> Optional[T]:
        """
        Versão assíncrona de try_find.
        
        Args:
            entity: Entidade com chaves primárias
            options: Opções de query
            
        Returns:
            Entidade encontrada ou None
        """
        cls._ensure_initialized()
        return await cls._can_find_internal_async(entity, options)

    @classmethod
    async def try_find_async_with_criteria(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"] = None,
    ) -> Optional[T]:
        """
        Versão assíncrona de try_find_with_criteria.
        
        Args:
            entity_type: Tipo da entidade
            criteria: Critério de busca
            options: Opções de query
            
        Returns:
            Entidade encontrada ou None
        """
        cls._ensure_initialized()
        return await cls._can_find_with_criteria_internal_async(
            entity_type, criteria, options
        )

    @classmethod
    async def find_async(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"] = None,
    ) -> T:
        """
        Versão assíncrona de find.
        
        Args:
            entity: Entidade com chaves primárias
            options: Opções de query
            
        Returns:
            Entidade encontrada
            
        Raises:
            ServiceRequestUnexpectedResultException: Se não encontrada
        """
        cls._ensure_initialized()
        return await cls._must_find_internal_async(entity, options)

    @classmethod
    async def find_async_with_criteria(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"] = None,
    ) -> T:
        """
        Versão assíncrona de find_with_criteria.
        
        Args:
            entity_type: Tipo da entidade
            criteria: Critério de busca
            options: Opções de query
            
        Returns:
            Entidade encontrada
            
        Raises:
            ServiceRequestUnexpectedResultException: Se não encontrada
        """
        cls._ensure_initialized()
        return await cls._must_find_with_criteria_internal_async(
            entity_type, criteria, options
        )

    # =========================================================================
    # Update Operations
    # =========================================================================

    @classmethod
    def update(cls, entity: T) -> T:
        """
        Atualiza uma entidade no Sankhya.
        
        Args:
            entity: Entidade com valores atualizados
            
        Returns:
            Entidade atualizada com dados do servidor
            
        Raises:
            RuntimeError: Se wrapper não inicializado
            ServiceRequestException: Erro na atualização
            
        Example:
            >>> partner = SimpleCRUDRequestWrapper.find(Partner(code=123))
            >>> partner.name = "Novo Nome"
            >>> updated = SimpleCRUDRequestWrapper.update(partner)
        """
        cls._ensure_initialized()

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
        ServiceRequestExtensions.resolve_with_entity(request, entity)

        response = cls._invoke_service(request)
        return cls._process_single_response(response, type(entity), request=request)

    @classmethod
    async def update_async(cls, entity: T) -> T:
        """
        Versão assíncrona de update.
        
        Args:
            entity: Entidade com valores atualizados
            
        Returns:
            Entidade atualizada
        """
        cls._ensure_initialized()

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_SAVE)
        ServiceRequestExtensions.resolve_with_entity(request, entity)

        response = await cls._invoke_service_async(request)
        return cls._process_single_response(response, type(entity), request=request)

    # =========================================================================
    # Remove Operations
    # =========================================================================

    @classmethod
    def remove(cls, entity: T) -> None:
        """
        Remove uma entidade do Sankhya.
        
        Args:
            entity: Entidade com chaves primárias a remover
            
        Raises:
            RuntimeError: Se wrapper não inicializado
            ServiceRequestException: Erro na remoção
            
        Example:
            >>> partner = Partner(code=123)
            >>> SimpleCRUDRequestWrapper.remove(partner)
        """
        cls._ensure_initialized()

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_REMOVE)
        ServiceRequestExtensions.resolve_with_entity(request, entity)

        cls._invoke_service(request)
        logger.debug(f"Entidade removida: {type(entity).__name__}")

    @classmethod
    async def remove_async(cls, entity: T) -> None:
        """
        Versão assíncrona de remove.
        
        Args:
            entity: Entidade com chaves primárias
        """
        cls._ensure_initialized()

        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_REMOVE)
        ServiceRequestExtensions.resolve_with_entity(request, entity)

        await cls._invoke_service_async(request)
        logger.debug(f"Entidade removida: {type(entity).__name__}")

    # =========================================================================
    # Internal Methods - Find Logic
    # =========================================================================

    @classmethod
    def _build_find_request(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"],
    ) -> ServiceRequest:
        """Monta a requisição de busca pelas chaves da entidade."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        if options:
            ServiceRequestExtensions.resolve_with_options(request, entity, options)
        else:
            ServiceRequestExtensions.resolve_with_entity(request, entity)

        return request

    @classmethod
    def _build_find_with_criteria_request(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"],
    ) -> ServiceRequest:
        """Monta a requisição de busca por critério literal."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        ServiceRequestExtensions.resolve_with_literal_criteria(
            request, entity_type, criteria
        )

        if options:
            ServiceRequestExtensions._apply_options_to_request(request, options)

        return request

    @classmethod
    def _can_find_internal(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"],
    ) -> Optional[T]:
        """Lógica core de busca opcional."""
        request = cls._build_find_request(entity, options)
        response = cls._invoke_service(request)
        return cls._process_find_response(
            response, type(entity), optional=True, request=request
        )

    @classmethod
    def _can_find_with_criteria_internal(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"],
    ) -> Optional[T]:
        """Lógica core de busca com critérios opcional."""
        request = cls._build_find_with_criteria_request(entity_type, criteria, options)
        response = cls._invoke_service(request)
        return cls._process_find_response(
            response, entity_type, optional=True, request=request
        )

    @classmethod
    def _must_find_internal(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"],
    ) -> T:
        """
        Lógica core de busca obrigatória.
        
        Como ``MustFindInternal`` (.NET, SimpleCRUDRequestWrapper.cs:122-151),
        sem entidade na resposta lança ServiceRequestUnexpectedResultException
        com a requisição enviada e a resposta recebida.
        """
        request = cls._build_find_request(entity, options)
        response = cls._invoke_service(request)
        return cls._process_find_response(
            response, type(entity), optional=False, request=request
        )

    @classmethod
    def _must_find_with_criteria_internal(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"],
    ) -> T:
        """
        Lógica core de busca com critérios obrigatória.
        
        Como ``MustFindInternal<T>(ILiteralCriteria)`` (.NET,
        SimpleCRUDRequestWrapper.cs:153-174).
        """
        request = cls._build_find_with_criteria_request(entity_type, criteria, options)
        response = cls._invoke_service(request)
        return cls._process_find_response(
            response, entity_type, optional=False, request=request
        )

    @classmethod
    def _find_all_internal(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"],
    ) -> List[T]:
        """Lógica core de busca de múltiplos resultados."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)

        if options:
            ServiceRequestExtensions.resolve_with_options(request, entity, options)
        else:
            ServiceRequestExtensions.resolve_with_entity(request, entity)

        response = cls._invoke_service(request)
        return cls._process_find_all_response(response, type(entity))

    # =========================================================================
    # Internal Methods - Async Find Logic
    # =========================================================================

    @classmethod
    async def _can_find_internal_async(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"],
    ) -> Optional[T]:
        """Versão assíncrona de _can_find_internal."""
        request = cls._build_find_request(entity, options)
        response = await cls._invoke_service_async(request)
        return cls._process_find_response(
            response, type(entity), optional=True, request=request
        )

    @classmethod
    async def _can_find_with_criteria_internal_async(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"],
    ) -> Optional[T]:
        """Versão assíncrona de _can_find_with_criteria_internal."""
        request = cls._build_find_with_criteria_request(entity_type, criteria, options)
        response = await cls._invoke_service_async(request)
        return cls._process_find_response(
            response, entity_type, optional=True, request=request
        )

    @classmethod
    async def _must_find_internal_async(
        cls,
        entity: T,
        options: Optional["EntityQueryOptions"],
    ) -> T:
        """
        Versão assíncrona de _must_find_internal.
        
        Como ``MustFindInternalAsync`` (.NET, SimpleCRUDRequestWrapper.cs:176-186):
        a exceção de não encontrada recebe a requisição e a resposta.
        """
        request = cls._build_find_request(entity, options)
        response = await cls._invoke_service_async(request)
        return cls._process_find_response(
            response, type(entity), optional=False, request=request
        )

    @classmethod
    async def _must_find_with_criteria_internal_async(
        cls,
        entity_type: Type[T],
        criteria: ILiteralCriteria,
        options: Optional["EntityQueryOptions"],
    ) -> T:
        """
        Versão assíncrona de _must_find_with_criteria_internal.
        
        Como ``MustFindInternalAsync<T>(ILiteralCriteria)`` (.NET,
        SimpleCRUDRequestWrapper.cs:188-198).
        """
        request = cls._build_find_with_criteria_request(entity_type, criteria, options)
        response = await cls._invoke_service_async(request)
        return cls._process_find_response(
            response, entity_type, optional=False, request=request
        )

    # =========================================================================
    # Internal Methods - Service Invocation
    # =========================================================================

    @classmethod
    def _invoke_service(cls, request: ServiceRequest) -> ServiceResponse:
        """Invoca o serviço de forma síncrona."""
        from sankhya_sdk.core.context import SankhyaContext

        if cls._session_token is None:
            raise RuntimeError("Token de sessão não disponível")

        return SankhyaContext.service_invoker_with_token(
            request, cls._session_token
        )

    @classmethod
    async def _invoke_service_async(cls, request: ServiceRequest) -> ServiceResponse:
        """Invoca o serviço de forma assíncrona."""
        from sankhya_sdk.core.context import SankhyaContext

        if cls._session_token is None:
            raise RuntimeError("Token de sessão não disponível")

        return await SankhyaContext.service_invoker_async_with_token(
            request, cls._session_token
        )

    # =========================================================================
    # Internal Methods - Response Processing
    # =========================================================================

    @classmethod
    def _process_find_response(
        cls,
        response: ServiceResponse,
        entity_type: Type[T],
        optional: bool = False,
        request: Optional[ServiceRequest] = None,
    ) -> Optional[T]:
        """
        Processa resposta de busca retornando uma única entidade.
        
        Como ``CanFindInternal``/``MustFindInternal`` (.NET), as exceções
        recebem a requisição e a resposta que as originaram.
        
        Args:
            response: Resposta do serviço
            entity_type: Tipo da entidade esperada
            optional: Se True, retorna None quando não encontrada
            request: Requisição que originou a resposta (opcional)
            
        Returns:
            Entidade convertida ou None
            
        Raises:
            ServiceRequestTooManyResultsException: Se múltiplos resultados
            ServiceRequestUnexpectedResultException: Se não encontrada (quando não optional)
        """
        entities = cls._extract_entities_from_response(response)

        if len(entities) == 0:
            if optional:
                return None
            raise ServiceRequestUnexpectedResultException(
                request=request,
                response=response,
            )

        if len(entities) > 1:
            raise ServiceRequestTooManyResultsException(
                result_length=len(entities),
                request=request,
                response=response,
            )

        return entities[0].convert_to_type(entity_type)

    @classmethod
    def _process_find_all_response(
        cls,
        response: ServiceResponse,
        entity_type: Type[T],
    ) -> List[T]:
        """
        Processa resposta de busca retornando múltiplas entidades.
        
        Args:
            response: Resposta do serviço
            entity_type: Tipo da entidade esperada
            
        Returns:
            Lista de entidades convertidas (pode estar vazia)
        """
        entities = cls._extract_entities_from_response(response)
        return [e.convert_to_type(entity_type) for e in entities]

    @classmethod
    def _process_single_response(
        cls,
        response: ServiceResponse,
        entity_type: Type[T],
        request: Optional[ServiceRequest] = None,
    ) -> T:
        """
        Processa resposta esperando exatamente uma entidade.
        
        Equivale a ``response.Entities.Single()`` em ``Update`` (.NET): a
        resposta deve conter exatamente uma entidade.
        
        Args:
            response: Resposta do serviço
            entity_type: Tipo da entidade esperada
            request: Requisição que originou a resposta (opcional)
            
        Returns:
            Entidade convertida
            
        Raises:
            ServiceRequestUnexpectedResultException: Se não houver entidade
            ServiceRequestTooManyResultsException: Se houver mais de uma
                entidade (``Single()`` falha no .NET)
        """
        entities = cls._extract_entities_from_response(response)

        if len(entities) == 0:
            raise ServiceRequestUnexpectedResultException(
                request=request,
                response=response,
            )

        if len(entities) > 1:
            raise ServiceRequestTooManyResultsException(
                result_length=len(entities),
                request=request,
                response=response,
            )

        return entities[0].convert_to_type(entity_type)

    @classmethod
    def _extract_entities_from_response(
        cls,
        response: ServiceResponse,
    ) -> List[EntityDynamicSerialization]:
        """
        Extrai entidades dinâmicas da resposta do serviço.
        
        Equivale a ``ServiceResponse.Entities`` (.NET, ServiceResponse.cs),
        usado pelo ``SimpleCrudRequestWrapper``: as entidades vêm de
        ``CrudServiceEntities`` (crud.find) ou de
        ``CrudServiceProviderEntities`` (CRUDServiceProvider), já com os
        nomes reais dos campos quando a resposta traz ``<metadata>``. Os
        valores permanecem como texto bruto; a conversão de tipos é feita
        por ``EntityDynamicSerialization.convert_to_type``.
        
        Args:
            response: Resposta do serviço
            
        Returns:
            Lista de EntityDynamicSerialization
        """
        result: List[EntityDynamicSerialization] = []

        if response is None or response.response_body is None:
            return result

        for entity_data in response.entities:
            if isinstance(entity_data, EntityDynamicSerialization):
                result.append(entity_data)
            elif isinstance(entity_data, dict):
                result.append(EntityDynamicSerialization(dict(entity_data)))
            elif isinstance(entity_data, EntityDynamic):
                result.append(EntityDynamicSerialization(dict(entity_data.fields)))
            else:
                logger.warning(
                    f"Entidade de tipo inesperado ignorada na resposta: "
                    f"{type(entity_data).__name__}"
                )

        return result

    @classmethod
    def _apply_options_to_request(
        cls,
        request: ServiceRequest,
        options: "EntityQueryOptions",
    ) -> None:
        """
        Aplica opções de query a uma requisição existente.
        
        Args:
            request: Requisição a modificar
            options: Opções a aplicar
        """
        if request.request_body is None:
            return

        body = request.request_body

        # Aplica max_results
        if options.max_results is not None:
            if body.entity:
                body.entity.max_results = options.max_results
            if body.data_set:
                body.data_set.max_results = options.max_results

        # Aplica include_presentation_fields
        if options.include_presentation_fields is not None:
            if body.entity:
                body.entity.include_presentation_fields = (
                    options.include_presentation_fields
                )
            if body.data_set:
                body.data_set.include_presentation_fields = (
                    options.include_presentation_fields
                )
