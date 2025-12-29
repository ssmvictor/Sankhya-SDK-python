# -*- coding: utf-8 -*-
"""
Context manager para sessões do Sankhya com suporte a múltiplas sessões.

Este módulo fornece a classe SankhyaContext que gerencia o ciclo
de vida de múltiplos SankhyaWrappers de forma thread-safe.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/GoodPractices/SankhyaContext.cs
"""

from __future__ import annotations

import logging
import threading
import uuid
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Set

if TYPE_CHECKING:
    from types import TracebackType
    from sankhya_sdk.config import SankhyaSettings

from sankhya_sdk.enums.service_environment import ServiceEnvironment
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse

from .types import ServiceFile
from .wrapper import SankhyaWrapper


logger = logging.getLogger(__name__)


class SankhyaContext:
    """
    Context manager para gerenciamento de múltiplas sessões Sankhya.

    Gerencia múltiplos wrappers de forma thread-safe, permitindo criar
    e finalizar sessões individuais identificadas por tokens UUID.

    Garante que todas as sessões sejam fechadas corretamente mesmo em
    caso de exceções, liberando recursos automaticamente.

    Attributes:
        token: Token UUID da sessão principal
        user_name: Nome do usuário autenticado
        user_code: Código do usuário autenticado
        environment: Ambiente de serviço
        database_name: Nome do banco de dados
        wrapper: Wrapper principal da sessão

    Class Attributes:
        _wrappers: Dicionário thread-safe de wrappers por token UUID
        _wrappers_lock: Lock para acesso thread-safe ao dicionário

    Example:
        Uso básico com sessão única:
        >>> with SankhyaContext.from_settings() as wrapper:
        ...     request = ServiceRequest(service=ServiceName.CRUD_FIND)
        ...     response = wrapper.service_invoker(request)

        Uso com múltiplas sessões:
        >>> ctx = SankhyaContext.from_settings()
        >>> with ctx:
        ...     token2 = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
        ...     response = SankhyaContext.service_invoker_with_token(request, token2)
        ...     ctx.finalize_session(token2)

    Async Usage:
        >>> async with SankhyaContext.from_settings() as wrapper:
        ...     response = await wrapper.service_invoker_async(request)
    """

    # Class-level attributes for shared wrapper management
    _wrappers: ClassVar[Dict[uuid.UUID, SankhyaWrapper]] = {}
    _wrappers_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        wrapper: Optional[SankhyaWrapper] = None,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Inicializa o context manager com um wrapper existente ou credenciais.

        Pode ser inicializado de duas formas:
        1. Com um wrapper existente (já autenticado ou não)
        2. Com parâmetros de conexão (host, port, username, password)

        Args:
            wrapper: Instância de SankhyaWrapper existente (prioridade)
            host: Host do servidor Sankhya (sem porta)
            port: Porta do servidor
            username: Nome de usuário para autenticação
            password: Senha do usuário

        Example:
            Com wrapper existente:
            >>> wrapper = SankhyaWrapper(host="http://example.com", port=8180)
            >>> wrapper.authenticate("user", "pass")
            >>> ctx = SankhyaContext(wrapper)

            Com parâmetros diretos:
            >>> ctx = SankhyaContext(
            ...     host="http://example.com",
            ...     port=8180,
            ...     username="user",
            ...     password="pass"
            ... )
        """
        self._disposed: bool = False
        self._on_demand_tokens: Set[uuid.UUID] = set()

        # Armazena credenciais para criação de novas sessões
        self._host: Optional[str] = host
        self._port: Optional[int] = port
        self._username: Optional[str] = username
        self._password: Optional[str] = password

        if wrapper is not None:
            # Usa wrapper existente
            self._wrapper = wrapper
            # Extrai credenciais do wrapper se disponíveis
            if hasattr(wrapper, "_session_info") and wrapper._session_info:
                self._username = wrapper._session_info.username
                self._password = wrapper._session_info.password
            if hasattr(wrapper, "_host"):
                self._host = wrapper._host
            if hasattr(wrapper, "_port"):
                self._port = wrapper._port
        elif host and port and username and password:
            # Cria novo wrapper e autentica
            self._wrapper = SankhyaWrapper(host=host, port=port)
            self._wrapper.authenticate(username, password)
        else:
            raise ValueError(
                "SankhyaContext requer um wrapper ou parâmetros de conexão "
                "(host, port, username, password)"
            )

        # Gera token UUID para sessão principal
        self._token: uuid.UUID = uuid.uuid4()

        # Registra no dicionário global com lock
        with SankhyaContext._wrappers_lock:
            SankhyaContext._wrappers[self._token] = self._wrapper

        logger.debug(
            f"SankhyaContext inicializado: token={self._token}, "
            f"user_code={self.user_code}"
        )

    def __del__(self) -> None:
        """
        Destrutor - garante limpeza de recursos.

        Chama dispose() se ainda não foi descartado.
        Equivalente ao finalizer C# ~SankhyaContext().
        """
        if not self._disposed:
            try:
                self.dispose()
            except Exception:
                # Silencia exceções no destrutor
                pass

    # ==========================================================================
    # Properties
    # ==========================================================================

    @property
    def token(self) -> uuid.UUID:
        """
        Retorna o token UUID da sessão principal.

        Returns:
            UUID identificador da sessão principal

        Example:
            >>> ctx = SankhyaContext.from_settings()
            >>> print(f"Token: {ctx.token}")
        """
        return self._token

    @property
    def wrapper(self) -> SankhyaWrapper:
        """
        Retorna a instância do wrapper principal.

        Returns:
            SankhyaWrapper da sessão principal
        """
        return self._wrapper

    @property
    def user_name(self) -> str:
        """
        Retorna o nome do usuário autenticado.

        Returns:
            Nome do usuário ou string vazia se não autenticado
        """
        if (
            hasattr(self._wrapper, "_session_info")
            and self._wrapper._session_info
        ):
            return self._wrapper._session_info.username
        return self._username or ""

    @property
    def user_code(self) -> int:
        """
        Retorna o código do usuário autenticado.

        Returns:
            Código do usuário (0 se não autenticado)
        """
        return getattr(self._wrapper, "_user_code", 0)

    @property
    def environment(self) -> ServiceEnvironment:
        """
        Retorna o ambiente de serviço configurado.

        Returns:
            ServiceEnvironment (Production, Sandbox, Training)
        """
        return self._wrapper._environment

    @property
    def database_name(self) -> str:
        """
        Retorna o nome do banco de dados.

        Returns:
            Nome do banco de dados
        """
        return self._wrapper._database_name

    # ==========================================================================
    # Static Wrapper Access
    # ==========================================================================

    @staticmethod
    def _get_wrapper(token: uuid.UUID) -> Optional[SankhyaWrapper]:
        """
        Obtém um wrapper pelo seu token UUID.

        Método interno thread-safe para buscar wrappers registrados.

        Args:
            token: Token UUID do wrapper

        Returns:
            SankhyaWrapper correspondente ou None se não encontrado

        Note:
            Thread-safe via lock global.
        """
        with SankhyaContext._wrappers_lock:
            wrapper = SankhyaContext._wrappers.get(token)

        if wrapper is None:
            logger.warning(f"Wrapper não encontrado para token: {token}")

        return wrapper

    # ==========================================================================
    # Session Management
    # ==========================================================================

    def acquire_new_session(
        self,
        request_type: ServiceRequestType = ServiceRequestType.DEFAULT,
    ) -> uuid.UUID:
        """
        Cria uma nova sessão autenticada e retorna seu token.

        Cria um novo SankhyaWrapper com as mesmas credenciais da
        sessão principal, autentica e retorna um token UUID para
        identificar a nova sessão.

        Args:
            request_type: Tipo de requisição para a nova sessão.
                Se ON_DEMAND_CRUD, a sessão será rastreada para
                limpeza automática via detach_on_demand_request_wrapper.

        Returns:
            UUID token identificador da nova sessão

        Raises:
            RuntimeError: Se o contexto foi descartado ou credenciais indisponíveis
            ServiceRequestInvalidCredentialsException: Credenciais inválidas

        Example:
            >>> with SankhyaContext.from_settings() as ctx:
            ...     token = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
            ...     # Usar token para operações
            ...     ctx.finalize_session(token)
        """
        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        if not self._host or not self._port:
            raise RuntimeError(
                "Não foi possível obter host/port para criar nova sessão"
            )

        if not self._username or not self._password:
            raise RuntimeError(
                "Não foi possível obter credenciais para criar nova sessão"
            )

        # Cria novo wrapper
        new_wrapper = SankhyaWrapper(
            host=self._host,
            port=self._port,
            request_type=request_type,
        )

        # Autentica
        new_wrapper.authenticate(self._username, self._password)

        # Gera token
        new_token = uuid.uuid4()

        # Registra no dicionário global
        with SankhyaContext._wrappers_lock:
            SankhyaContext._wrappers[new_token] = new_wrapper

        # Rastreia se for on-demand (thread-safe)
        if request_type == ServiceRequestType.ON_DEMAND_CRUD:
            with SankhyaContext._wrappers_lock:
                self._on_demand_tokens.add(new_token)

        logger.info(
            f"Nova sessão criada: token={new_token}, "
            f"request_type={request_type.name}"
        )

        return new_token

    def finalize_session(self, token: uuid.UUID) -> None:
        """
        Finaliza uma sessão específica pelo seu token.

        Remove o wrapper do dicionário global e chama dispose()
        para liberar recursos. Não permite finalizar a sessão principal.

        Args:
            token: Token UUID da sessão a finalizar

        Note:
            - Não finaliza a sessão principal (self._token)
            - Silencia exceções durante dispose
            - Thread-safe via lock global

        Example:
            >>> token = ctx.acquire_new_session()
            >>> # ... usar sessão ...
            >>> ctx.finalize_session(token)
        """
        # Não permite finalizar sessão principal
        if token == self._token:
            logger.warning(
                "Tentativa de finalizar sessão principal ignorada. "
                "Use dispose() para finalizar o contexto."
            )
            return

        wrapper: Optional[SankhyaWrapper] = None

        # Remove do dicionário com lock
        with SankhyaContext._wrappers_lock:
            wrapper = SankhyaContext._wrappers.pop(token, None)

        if wrapper is None:
            logger.debug(f"Sessão não encontrada para finalização: {token}")
            return

        # Remove de on-demand tokens se presente (thread-safe)
        with SankhyaContext._wrappers_lock:
            self._on_demand_tokens.discard(token)

        # Dispose no wrapper
        try:
            wrapper.dispose()
            logger.debug(f"Sessão finalizada: {token}")
        except Exception as e:
            logger.warning(f"Erro ao finalizar sessão {token}: {e}")

    def detach_on_demand_request_wrapper(self, token: uuid.UUID) -> None:
        """
        Desanexa um wrapper de requisição on-demand.

        Finaliza a sessão e remove do rastreamento de on-demand.
        Usado pelo OnDemandRequestFactory para limpeza.

        Args:
            token: Token UUID do wrapper on-demand

        Example:
            >>> token = ctx.acquire_new_session(ServiceRequestType.ON_DEMAND_CRUD)
            >>> # ... usar wrapper on-demand ...
            >>> ctx.detach_on_demand_request_wrapper(token)
        """
        self.finalize_session(token)
        # finalize_session já remove de _on_demand_tokens

    # ==========================================================================
    # Service Invoker - Instance Methods
    # ==========================================================================

    def service_invoker(self, request: ServiceRequest) -> ServiceResponse:
        """
        Invoca um serviço usando a sessão principal.

        Args:
            request: Requisição de serviço

        Returns:
            Resposta do serviço

        Raises:
            ValueError: Se request é None
            RuntimeError: Se contexto foi descartado
            ServiceRequestException: Erro na chamada do serviço

        Example:
            >>> request = ServiceRequest(service=ServiceName.CRUD_FIND)
            >>> response = ctx.service_invoker(request)
        """
        if request is None:
            raise ValueError("request não pode ser None")

        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        return self._wrapper.service_invoker(request)

    async def service_invoker_async(
        self, request: ServiceRequest
    ) -> ServiceResponse:
        """
        Invoca um serviço de forma assíncrona usando a sessão principal.

        Args:
            request: Requisição de serviço

        Returns:
            Resposta do serviço

        Example:
            >>> response = await ctx.service_invoker_async(request)
        """
        if request is None:
            raise ValueError("request não pode ser None")

        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        return await self._wrapper.service_invoker_async(request)

    # ==========================================================================
    # Service Invoker - Static Methods with Token
    # ==========================================================================

    @staticmethod
    def service_invoker_with_token(
        request: ServiceRequest,
        token: uuid.UUID,
    ) -> ServiceResponse:
        """
        Invoca um serviço usando uma sessão específica por token.

        Args:
            request: Requisição de serviço
            token: Token UUID da sessão a usar

        Returns:
            Resposta do serviço

        Raises:
            ValueError: Se request é None ou token não encontrado
            ServiceRequestException: Erro na chamada do serviço

        Example:
            >>> token = ctx.acquire_new_session()
            >>> response = SankhyaContext.service_invoker_with_token(request, token)
        """
        if request is None:
            raise ValueError("request não pode ser None")

        wrapper = SankhyaContext._get_wrapper(token)
        if wrapper is None:
            raise ValueError(f"Wrapper não encontrado para token: {token}")

        return wrapper.service_invoker(request)

    @staticmethod
    async def service_invoker_async_with_token(
        request: ServiceRequest,
        token: uuid.UUID,
    ) -> ServiceResponse:
        """
        Invoca um serviço de forma assíncrona usando uma sessão específica.

        Args:
            request: Requisição de serviço
            token: Token UUID da sessão a usar

        Returns:
            Resposta do serviço

        Raises:
            ValueError: Se request é None ou token não encontrado

        Example:
            >>> response = await SankhyaContext.service_invoker_async_with_token(
            ...     request, token
            ... )
        """
        if request is None:
            raise ValueError("request não pode ser None")

        wrapper = SankhyaContext._get_wrapper(token)
        if wrapper is None:
            raise ValueError(f"Wrapper não encontrado para token: {token}")

        return await wrapper.service_invoker_async(request)

    # ==========================================================================
    # File/Image Operations - Instance Methods
    # ==========================================================================

    def get_file(self, key: str) -> ServiceFile:
        """
        Baixa um arquivo do repositório Sankhya usando sessão principal.

        Args:
            key: Chave do arquivo no repositório

        Returns:
            ServiceFile com os dados do arquivo

        Raises:
            ServiceRequestFileNotFoundException: Arquivo não encontrado
            RuntimeError: Contexto descartado

        Example:
            >>> file = ctx.get_file("ABC123")
        """
        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        return self._wrapper.get_file(key)

    async def get_file_async(self, key: str) -> ServiceFile:
        """
        Versão assíncrona de get_file.

        Args:
            key: Chave do arquivo no repositório

        Returns:
            ServiceFile com os dados do arquivo
        """
        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        return await self._wrapper.get_file_async(key)

    def get_image(
        self,
        entity: str,
        keys: Dict[str, Any],
    ) -> Optional[ServiceFile]:
        """
        Baixa uma imagem associada a uma entidade usando sessão principal.

        Args:
            entity: Nome da entidade (ex: "Parceiro")
            keys: Chaves primárias da entidade

        Returns:
            ServiceFile com os dados da imagem, ou None se não existir

        Example:
            >>> image = ctx.get_image("Parceiro", {"CODPARC": 1})
        """
        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        return self._wrapper.get_image(entity, keys)

    async def get_image_async(
        self,
        entity: str,
        keys: Dict[str, Any],
    ) -> Optional[ServiceFile]:
        """
        Versão assíncrona de get_image.

        Args:
            entity: Nome da entidade
            keys: Chaves primárias da entidade

        Returns:
            ServiceFile com os dados da imagem, ou None se não existir
        """
        if self._disposed:
            raise RuntimeError("SankhyaContext já foi descartado")

        return await self._wrapper.get_image_async(entity, keys)

    # ==========================================================================
    # File/Image Operations - Static Methods with Token
    # ==========================================================================

    @staticmethod
    def get_file_with_token(key: str, token: uuid.UUID) -> ServiceFile:
        """
        Baixa um arquivo usando uma sessão específica por token.

        Args:
            key: Chave do arquivo no repositório
            token: Token UUID da sessão a usar

        Returns:
            ServiceFile com os dados do arquivo

        Raises:
            ValueError: Se token não encontrado

        Example:
            >>> file = SankhyaContext.get_file_with_token("ABC123", token)
        """
        wrapper = SankhyaContext._get_wrapper(token)
        if wrapper is None:
            raise ValueError(f"Wrapper não encontrado para token: {token}")

        return wrapper.get_file(key)

    @staticmethod
    async def get_file_async_with_token(
        key: str, token: uuid.UUID
    ) -> ServiceFile:
        """
        Versão assíncrona de get_file_with_token.

        Args:
            key: Chave do arquivo no repositório
            token: Token UUID da sessão a usar

        Returns:
            ServiceFile com os dados do arquivo
        """
        wrapper = SankhyaContext._get_wrapper(token)
        if wrapper is None:
            raise ValueError(f"Wrapper não encontrado para token: {token}")

        return await wrapper.get_file_async(key)

    @staticmethod
    def get_image_with_token(
        entity: str,
        keys: Dict[str, Any],
        token: uuid.UUID,
    ) -> Optional[ServiceFile]:
        """
        Baixa uma imagem usando uma sessão específica por token.

        Args:
            entity: Nome da entidade
            keys: Chaves primárias da entidade
            token: Token UUID da sessão a usar

        Returns:
            ServiceFile com os dados da imagem, ou None se não existir

        Raises:
            ValueError: Se token não encontrado

        Example:
            >>> image = SankhyaContext.get_image_with_token(
            ...     "Parceiro", {"CODPARC": 1}, token
            ... )
        """
        wrapper = SankhyaContext._get_wrapper(token)
        if wrapper is None:
            raise ValueError(f"Wrapper não encontrado para token: {token}")

        return wrapper.get_image(entity, keys)

    @staticmethod
    async def get_image_async_with_token(
        entity: str,
        keys: Dict[str, Any],
        token: uuid.UUID,
    ) -> Optional[ServiceFile]:
        """
        Versão assíncrona de get_image_with_token.

        Args:
            entity: Nome da entidade
            keys: Chaves primárias da entidade
            token: Token UUID da sessão a usar

        Returns:
            ServiceFile com os dados da imagem, ou None se não existir
        """
        wrapper = SankhyaContext._get_wrapper(token)
        if wrapper is None:
            raise ValueError(f"Wrapper não encontrado para token: {token}")

        return await wrapper.get_image_async(entity, keys)

    # ==========================================================================
    # Lifecycle Management
    # ==========================================================================

    def dispose(self) -> None:
        """
        Libera todos os recursos do contexto.

        Finaliza todas as sessões (on-demand e regulares), remove todos
        os wrappers registrados e faz dispose em cada um.

        Note:
            - Idempotente: múltiplas chamadas não causam erro
            - Thread-safe via lock global
            - Silencia exceções de dispose individuais
            - Dispõe TODOS os wrappers, não apenas on-demand

        Example:
            >>> ctx.dispose()
        """
        if self._disposed:
            return

        logger.debug("Descartando SankhyaContext")

        # Snapshot de tokens on-demand para finalização (thread-safe)
        with SankhyaContext._wrappers_lock:
            on_demand_tokens_snapshot = list(self._on_demand_tokens)
            self._on_demand_tokens.clear()

        # Finaliza sessões on-demand primeiro
        for token in on_demand_tokens_snapshot:
            try:
                self.finalize_session(token)
            except Exception as e:
                logger.warning(f"Erro ao finalizar sessão on-demand {token}: {e}")

        # Snapshot de todos os wrappers restantes (thread-safe)
        with SankhyaContext._wrappers_lock:
            wrappers_snapshot = list(SankhyaContext._wrappers.items())

        # Dispõe todos os wrappers restantes (exceto main que será tratado por último)
        for token, wrapper in wrappers_snapshot:
            if token == self._token:
                continue  # Main wrapper será tratado por último
            try:
                with SankhyaContext._wrappers_lock:
                    SankhyaContext._wrappers.pop(token, None)
                wrapper.dispose()
                logger.debug(f"Sessão adicional finalizada: {token}")
            except Exception as e:
                logger.warning(f"Erro ao descartar wrapper {token}: {e}")

        # Remove wrapper principal do dicionário
        with SankhyaContext._wrappers_lock:
            SankhyaContext._wrappers.pop(self._token, None)

        # Dispose no wrapper principal
        if self._wrapper:
            try:
                self._wrapper.dispose()
            except Exception as e:
                logger.warning(f"Erro ao descartar wrapper principal: {e}")

        self._disposed = True
        logger.debug(f"SankhyaContext descartado: token={self._token}")

    # ==========================================================================
    # Context Manager Protocol
    # ==========================================================================

    def __enter__(self) -> SankhyaWrapper:
        """
        Entra no contexto.

        Returns:
            Instância do SankhyaWrapper principal
        """
        return self._wrapper

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Sai do contexto, liberando todos os recursos.

        Args:
            exc_type: Tipo da exceção (se houver)
            exc_val: Valor da exceção (se houver)
            exc_tb: Traceback da exceção (se houver)

        Note:
            Chama dispose() para limpar todas as sessões.
            Não suprime exceções (retorna None/False).
        """
        self.dispose()

    async def __aenter__(self) -> SankhyaWrapper:
        """
        Entra no contexto de forma assíncrona.

        Returns:
            Instância do SankhyaWrapper principal
        """
        return self._wrapper

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Sai do contexto assíncrono, liberando todos os recursos.

        Note:
            O dispose() é síncrono, mas chamado em contexto async.
        """
        self.dispose()

    # ==========================================================================
    # Factory Methods
    # ==========================================================================

    @classmethod
    def from_settings(
        cls,
        settings: Optional["SankhyaSettings"] = None,
    ) -> "SankhyaContext":
        """
        Cria um context manager a partir das configurações.

        Factory method que cria e autentica um wrapper usando
        as configurações fornecidas ou as configurações globais,
        e o encapsula em um context manager.

        Args:
            settings: Configurações Sankhya. Se None, usa configurações globais

        Returns:
            SankhyaContext com wrapper autenticado

        Raises:
            ServiceRequestInvalidCredentialsException: Credenciais inválidas

        Example:
            >>> with SankhyaContext.from_settings() as wrapper:
            ...     # usar wrapper
            ...     pass

            >>> # Ou com configurações específicas
            >>> settings = SankhyaSettings(
            ...     url="http://server.example.com",
            ...     port=8180,
            ...     username="admin",
            ...     password="secret"
            ... )
            >>> with SankhyaContext.from_settings(settings) as wrapper:
            ...     pass
        """
        wrapper = SankhyaWrapper.from_settings(settings)
        return cls(wrapper)

    def __repr__(self) -> str:
        """Representação string do objeto."""
        return (
            f"SankhyaContext("
            f"token={self._token}, "
            f"user_code={self.user_code}, "
            f"disposed={self._disposed})"
        )
