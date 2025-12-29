# -*- coding: utf-8 -*-
"""
Wrapper principal para comunicação com a API Sankhya.

Este módulo fornece a classe SankhyaWrapper que gerencia toda a
comunicação HTTP com a API Sankhya, incluindo autenticação,
retry automático e tratamento de exceções.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Transport/SankhyaWrapper.cs
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, ClassVar, Dict, List, Optional

import requests

from sankhya_sdk.config import SankhyaSettings
from sankhya_sdk.enums.service_category import ServiceCategory
from sankhya_sdk.enums.service_environment import ServiceEnvironment
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.enums.service_response_status import ServiceResponseStatus
from sankhya_sdk.enums.service_type import ServiceType
from sankhya_sdk.exceptions import (
    ServiceRequestCanceledQueryException,
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestInaccessibleException,
    ServiceRequestInvalidAuthorizationException,
    ServiceRequestPropertyValueException,
    ServiceRequestTimeoutException,
    ServiceRequestUnavailableException,
)
from sankhya_sdk.helpers.status_message_helper import StatusMessageHelper
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.request_helpers import RequestRetryData, RequestRetryDelay

from .constants import (
    CONTENT_TYPE_FORM,
    DEFAULT_TIMEOUT,
    DWR_CONTROLLER_PATH,
    FILE_VIEWER_PATH,
    IMAGE_PATH_TEMPLATE,
    MAX_RETRY_COUNT,
    MIME_TYPES_TO_EXTENSIONS,
    SYSVERSION_PATTERN,
)
from .lock_manager import LockManager
from .low_level_wrapper import LowLevelSankhyaWrapper
from .types import ServiceAttribute, ServiceFile, SessionInfo


logger = logging.getLogger(__name__)


class SankhyaWrapper(LowLevelSankhyaWrapper):
    """
    Wrapper principal para comunicação com a API Sankhya.

    Gerencia autenticação, sessão, retry automático e tratamento
    de exceções para todas as chamadas de serviço.

    Esta classe é thread-safe e pode ser usada em aplicações
    concorrentes com múltiplas threads.

    Attributes:
        environment: Ambiente de serviço (Production, Sandbox, Training)
        database_name: Nome do banco de dados
        user_code: Código do usuário autenticado
        is_authenticated: Se há uma sessão ativa

    Example:
        >>> wrapper = SankhyaWrapper.from_settings()
        >>> request = ServiceRequest(service=ServiceName.CRUD_FIND)
        >>> response = wrapper.service_invoker(request)
        >>> wrapper.dispose()

    Context Manager:
        Use SankhyaContext para gerenciamento automático:

        >>> with SankhyaContext.from_settings() as wrapper:
        ...     response = wrapper.service_invoker(request)
    """

    # Lista de session IDs invalidados (class-level para compartilhar entre instâncias)
    _invalid_session_ids: ClassVar[List[str]] = []
    _invalid_session_ids_lock: ClassVar = None

    def __init__(
        self,
        host: str,
        port: int,
        request_type: ServiceRequestType = ServiceRequestType.DEFAULT,
        environment: Optional[ServiceEnvironment] = None,
        database_name: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRY_COUNT,
    ) -> None:
        """
        Inicializa o wrapper Sankhya.

        Args:
            host: Host do servidor Sankhya (sem porta)
            port: Porta do servidor
            request_type: Tipo de requisição (XML ou JSON)
            environment: Ambiente de serviço. Se None, determina pela porta
            database_name: Nome do banco de dados. Se None, usa padrão do ambiente
            timeout: Timeout para requisições HTTP em segundos
            max_retries: Número máximo de tentativas em caso de erro

        Example:
            >>> wrapper = SankhyaWrapper(
            ...     host="http://sankhya.example.com",
            ...     port=8180
            ... )
        """
        super().__init__(
            host=host,
            port=port,
            request_type=request_type,
            environment=environment,
            database_name=database_name,
            timeout=timeout,
        )

        self._session_info: Optional[SessionInfo] = None
        self._request_count: int = 0
        self._disposed: bool = False
        self._max_retries = max_retries
        self._sankhya_version: Optional[str] = None

        # Inicializa lock para invalid_session_ids se necessário
        if SankhyaWrapper._invalid_session_ids_lock is None:
            import threading
            SankhyaWrapper._invalid_session_ids_lock = threading.Lock()

        logger.debug(f"SankhyaWrapper inicializado: {self.base_url}")

    def __del__(self) -> None:
        """Destrutor - chama dispose() para limpeza."""
        if not self._disposed:
            try:
                self.dispose()
            except Exception:
                pass

    # ==========================================================================
    # Propriedades
    # ==========================================================================

    @property
    def is_authenticated(self) -> bool:
        """Verifica se há uma sessão autenticada ativa."""
        return self._session_info is not None

    @property
    def session_id(self) -> Optional[str]:
        """Retorna o ID da sessão atual."""
        return self._session_info.session_id if self._session_info else None

    @property
    def sankhya_version(self) -> Optional[str]:
        """Retorna a versão do Sankhya (se disponível)."""
        return self._sankhya_version

    @property
    def request_count(self) -> int:
        """Retorna o número de requisições realizadas."""
        return self._request_count

    # ==========================================================================
    # Autenticação
    # ==========================================================================

    def authenticate(self, username: str, password: str) -> None:
        """
        Autentica no servidor Sankhya.

        Realiza login e armazena a sessão para uso subsequente.
        Se já houver uma sessão ativa, faz logout primeiro.

        Args:
            username: Nome de usuário
            password: Senha do usuário

        Raises:
            ServiceRequestInvalidCredentialsException: Credenciais inválidas
            ServiceRequestInvalidAuthorizationException: Usuário não autorizado
            requests.RequestException: Erro de rede

        Example:
            >>> wrapper.authenticate("admin", "senha123")
        """
        if self._disposed:
            raise RuntimeError("Wrapper já foi descartado")

        # Se já está autenticado, invalida a sessão atual
        if self._session_info:
            self._invalidate()

        logger.info(f"Autenticando usuário: {username}")

        # Cria request de login
        # Comment 1: Use request.no_auth flag (on ServiceRequest) instead of request_body.no_auth
        request = ServiceRequest(service=ServiceName.LOGIN)
        request.no_auth = True

        # Comment 2: Use request_body.username and password (plain, no base64)
        # to match the .NET contract - credentials go directly in RequestBody, not in params
        request.request_body.username = username
        request.request_body.password = password

        # Faz a requisição de login (sem retry)
        response = self._service_invoker_internal(
            request=request,
            service_name=ServiceName.LOGIN,
            request_count=0,
        )

        # Processa resposta
        if response.is_error:
            StatusMessageHelper.process_status_message(
                ServiceName.LOGIN, request, response
            )
            raise ServiceRequestInvalidAuthorizationException()

        # Extrai dados da sessão
        session_id = self._extract_session_id(response)
        user_code = self._extract_user_code(response)

        if not session_id:
            raise ServiceRequestInvalidAuthorizationException()

        # Armazena informações da sessão
        self._session_info = SessionInfo(
            session_id=session_id,
            user_code=user_code,
            username=username,
            password=password,
        )
        self._user_code = user_code

        # Adiciona cookie de sessão
        self._add_session_cookie(session_id)

        # Tenta registrar user agent e obter versão
        try:
            self._register_user_agent(username, password)
        except Exception as e:
            logger.warning(f"Falha ao registrar user agent: {e}")

        logger.info(f"Autenticação bem-sucedida: user_code={user_code}")

    def _extract_session_id(self, response: ServiceResponse) -> Optional[str]:
        """
        Extrai o session ID da resposta de login.

        Args:
            response: Resposta do serviço de login

        Returns:
            Session ID ou None se não encontrado
        """
        if response.response_body and response.response_body.jsession_id:
            return response.response_body.jsession_id

        # Fallback: procura no cookie da resposta HTTP
        return None

    def _extract_user_code(self, response: ServiceResponse) -> int:
        """
        Extrai o código do usuário da resposta de login.

        Args:
            response: Resposta do serviço de login

        Returns:
            Código do usuário (0 se não encontrado)
        """
        if response.response_body and response.response_body.user_code:
            return response.response_body.user_code

        return 0

    def _invalidate(self) -> None:
        """
        Invalida a sessão atual.

        Faz logout no servidor e limpa os dados da sessão local.
        """
        if not self._session_info:
            return

        session_id = self._session_info.session_id

        try:
            # Faz logout
            request = ServiceRequest(service=ServiceName.LOGOUT)
            self._service_invoker_internal(
                request=request,
                service_name=ServiceName.LOGOUT,
                request_count=0,
            )
        except Exception as e:
            logger.warning(f"Erro ao fazer logout: {e}")
        finally:
            # Adiciona à lista de sessões inválidas
            with SankhyaWrapper._invalid_session_ids_lock:
                if session_id not in SankhyaWrapper._invalid_session_ids:
                    SankhyaWrapper._invalid_session_ids.append(session_id)

            # Limpa dados locais
            self._session_info = None
            self._user_code = 0

            logger.debug(f"Sessão invalidada: {session_id}")

    def _register_user_agent(self, username: str, password: str) -> None:
        """
        Registra o user agent via DWR e extrai a versão do Sankhya.

        Args:
            username: Nome de usuário
            password: Senha
        """
        url = self._build_generic_url(DWR_CONTROLLER_PATH)

        # Payload DWR
        payload = (
            "callCount=1\n"
            "c0-scriptName=DWRController\n"
            "c0-methodName=execute\n"
            "c0-id=0\n"
            f"c0-param0=string:{username}\n"
            f"c0-param1=string:{password}\n"
            "c0-param2=string:web\n"
            "c0-param3=string:br.com.sankhya.actionbutton.IosUserAgentAB\n"
            "c0-param4=string:registerUserAgent\n"
            "c0-param5=array:[]\n"
            "batchId=1\n"
        )

        try:
            response = self._make_request(
                method="POST",
                url=url,
                data=payload,
                content_type=CONTENT_TYPE_FORM,
            )

            if response.ok:
                # Tenta extrair versão do HTML
                self._sankhya_version = self._extract_version_from_html(response.text)
                logger.debug(f"Versão do Sankhya: {self._sankhya_version}")

        except Exception as e:
            logger.warning(f"Falha no registro de user agent: {e}")

    def _extract_version_from_html(self, html: str) -> Optional[str]:
        """
        Extrai a versão do Sankhya do HTML.

        Args:
            html: HTML retornado pelo DWR

        Returns:
            Versão do Sankhya ou None se não encontrada
        """
        match = re.search(SYSVERSION_PATTERN, html)
        if match:
            return match.group(1)
        return None

    # ==========================================================================
    # Service Invoker
    # ==========================================================================

    def service_invoker(self, request: ServiceRequest) -> ServiceResponse:
        """
        Invoca um serviço no Sankhya.

        Ponto de entrada principal para chamadas de serviço.
        Gerencia retry automático e tratamento de exceções.

        Args:
            request: Requisição de serviço

        Returns:
            Resposta do serviço

        Raises:
            ServiceRequestInvalidAuthorizationException: Sessão inválida
            ServiceRequestException: Erro na chamada do serviço
            RuntimeError: Wrapper não autenticado ou descartado

        Example:
            >>> request = ServiceRequest(service=ServiceName.CRUD_FIND)
            >>> response = wrapper.service_invoker(request)
        """
        if self._disposed:
            raise RuntimeError("Wrapper já foi descartado")

        service_name = request.service

        # Cria dados de retry
        retry_data = RequestRetryData(
            lock_key=self.session_id or "no_session",
            retry_count=0,
            retry_delay=0,
        )

        return self._service_invoker_with_retry(request, service_name, retry_data)

    async def service_invoker_async(self, request: ServiceRequest) -> ServiceResponse:
        """
        Invoca um serviço no Sankhya de forma assíncrona.

        Versão assíncrona do service_invoker usando asyncio.to_thread.

        Args:
            request: Requisição de serviço

        Returns:
            Resposta do serviço

        Example:
            >>> response = await wrapper.service_invoker_async(request)
        """
        return await asyncio.to_thread(self.service_invoker, request)

    def _service_invoker_with_retry(
        self,
        request: ServiceRequest,
        service_name: ServiceName,
        retry_data: RequestRetryData,
    ) -> ServiceResponse:
        """
        Invoca serviço com lógica de retry.

        Args:
            request: Requisição de serviço
            service_name: Nome do serviço
            retry_data: Dados de retry

        Returns:
            Resposta do serviço
        """
        lock = LockManager.get_lock(retry_data.lock_key)

        with lock:
            while True:
                try:
                    # Incrementa contador de requisições
                    self._request_count += 1
                    current_request = self._request_count

                    # Executa requisição
                    response = self._service_invoker_internal(
                        request=request,
                        service_name=service_name,
                        request_count=current_request,
                    )

                    return response

                except Exception as e:
                    # Obtém atributos do serviço
                    service_attr = self._get_service_attribute(service_name)

                    # Tenta tratar a exceção
                    should_retry = self._handle_exception(
                        exception=e,
                        service_name=service_name,
                        service_attr=service_attr,
                        request=request,
                        retry_data=retry_data,
                    )

                    if not should_retry:
                        raise

                    # Incrementa contador de retry
                    retry_data.retry_count += 1

                    # Aplica delay se especificado
                    if retry_data.retry_delay > 0:
                        logger.debug(f"Aguardando {retry_data.retry_delay}s antes do retry")
                        time.sleep(retry_data.retry_delay)

    def _service_invoker_internal(
        self,
        request: ServiceRequest,
        service_name: ServiceName,
        request_count: int,
    ) -> ServiceResponse:
        """
        Executa a requisição HTTP real.

        Args:
            request: Requisição de serviço
            service_name: Nome do serviço
            request_count: Número da requisição

        Returns:
            Resposta deserializada
        """
        # Verifica autenticação (exceto para login)
        # Comment 1: Check request.no_auth flag (with safe default False)
        if service_name != ServiceName.LOGIN and not getattr(request, "no_auth", False):
            if not self._session_info:
                raise ServiceRequestInvalidAuthorizationException()

        # Constrói URL
        url = self._build_service_url(service_name)

        # Serializa request para XML
        xml_data = request.to_xml_string()

        logger.debug(f"Request #{request_count} para {service_name.name}")

        # Faz requisição HTTP
        http_response = self._make_request(
            method="POST",
            url=url,
            data=xml_data,
        )

        # Verifica status HTTP
        http_response.raise_for_status()

        # Deserializa response
        response = ServiceResponse.from_xml_bytes(http_response.content)

        # Processa mensagem de status se houver erro
        if response.is_error:
            StatusMessageHelper.process_status_message(
                service_name, request, response
            )

        return response

    def _get_service_attribute(self, service_name: ServiceName) -> ServiceAttribute:
        """
        Obtém os atributos de um serviço.

        Args:
            service_name: Nome do serviço

        Returns:
            Atributos do serviço
        """
        is_transactional = service_name.service_type == ServiceType.TRANSACTIONAL
        is_retriable = True

        return ServiceAttribute(
            is_transactional=is_transactional,
            is_retriable=is_retriable,
        )

    # ==========================================================================
    # Exception Handling
    # ==========================================================================

    def _handle_exception(
        self,
        exception: Exception,
        service_name: ServiceName,
        service_attr: ServiceAttribute,
        request: ServiceRequest,
        retry_data: RequestRetryData,
    ) -> bool:
        """
        Trata exceções e decide se deve fazer retry.

        Args:
            exception: Exceção ocorrida
            service_name: Nome do serviço
            service_attr: Atributos do serviço
            request: Requisição original
            retry_data: Dados de retry

        Returns:
            True se deve fazer retry, False caso contrário
        """
        # Verifica se atingiu máximo de retries
        if retry_data.retry_count >= self._max_retries:
            logger.warning(f"Máximo de retries atingido ({self._max_retries})")
            return False

        # Verifica se é serviço transacional com exceção não-retriable
        if service_attr.is_transactional:
            non_retriable_exceptions = (
                ServiceRequestCompetitionException,
                ServiceRequestDeadlockException,
                ServiceRequestTimeoutException,
            )
            if isinstance(exception, non_retriable_exceptions):
                return False

        # Delega para handler interno
        return self._handle_exception_internal(
            exception=exception,
            service_name=service_name,
            category=service_name.service_category,
            request=request,
            retry_data=retry_data,
        )

    def _handle_exception_internal(
        self,
        exception: Exception,
        service_name: ServiceName,
        category: ServiceCategory,
        request: ServiceRequest,
        retry_data: RequestRetryData,
    ) -> bool:
        """
        Handler interno de exceções.

        Args:
            exception: Exceção ocorrida
            service_name: Nome do serviço
            category: Categoria do serviço
            request: Requisição original
            retry_data: Dados de retry

        Returns:
            True se deve fazer retry, False caso contrário
        """
        # ServiceRequestInvalidAuthorizationException
        if isinstance(exception, ServiceRequestInvalidAuthorizationException):
            session_id = self.session_id

            # Verifica se já foi invalidada
            with SankhyaWrapper._invalid_session_ids_lock:
                if session_id and session_id in SankhyaWrapper._invalid_session_ids:
                    return False

            # Reautentica
            if self._session_info:
                username = self._session_info.username
                password = self._session_info.password
                self._invalidate()
                self.authenticate(username, password)
                return True

            return False

        # ServiceRequestPropertyValueException
        if isinstance(exception, ServiceRequestPropertyValueException):
            property_name = exception.property_name if hasattr(exception, "property_name") else ""
            xml_str = request.to_xml_string()

            # Se property_name não está no XML, pode ser erro transitório
            if property_name and property_name not in xml_str:
                retry_data.retry_delay = RequestRetryDelay.STABLE
                return True

            return False

        # ServiceRequestCompetitionException
        if isinstance(exception, ServiceRequestCompetitionException):
            if self._session_info:
                username = self._session_info.username
                password = self._session_info.password
                self._invalidate()
                self.authenticate(username, password)
            return True

        # ServiceRequestDeadlockException
        if isinstance(exception, ServiceRequestDeadlockException):
            retry_data.retry_delay = RequestRetryDelay.STABLE
            return True

        # ServiceRequestTimeoutException
        if isinstance(exception, ServiceRequestTimeoutException):
            retry_data.retry_delay = RequestRetryDelay.FREE
            return True

        # ServiceRequestInaccessibleException
        if isinstance(exception, ServiceRequestInaccessibleException):
            if category != ServiceCategory.AUTHORIZATION:
                if self._session_info:
                    username = self._session_info.username
                    password = self._session_info.password
                    self._invalidate()
                    self.authenticate(username, password)

            retry_data.retry_delay = RequestRetryDelay.BREAKDOWN
            return True

        # ServiceRequestUnavailableException
        if isinstance(exception, ServiceRequestUnavailableException):
            retry_data.retry_delay = RequestRetryDelay.UNSTABLE
            return True

        # ServiceRequestCanceledQueryException
        if isinstance(exception, ServiceRequestCanceledQueryException):
            retry_data.retry_delay = RequestRetryDelay.STABLE
            return True

        # requests.RequestException (erros de rede)
        if isinstance(exception, requests.RequestException):
            retry_data.retry_delay = RequestRetryDelay.UNSTABLE
            return True

        # Exceção não tratada - não faz retry
        return False

    # ==========================================================================
    # File/Image Operations
    # ==========================================================================

    def get_file(self, key: str) -> ServiceFile:
        """
        Baixa um arquivo do repositório Sankhya.

        Args:
            key: Chave do arquivo no repositório

        Returns:
            ServiceFile com os dados do arquivo

        Raises:
            ServiceRequestFileNotFoundException: Arquivo não encontrado
            RuntimeError: Erro ao processar arquivo

        Example:
            >>> file = wrapper.get_file("ABC123")
            >>> with open(file.filename, "wb") as f:
            ...     f.write(file.data)
        """
        if self._disposed:
            raise RuntimeError("Wrapper já foi descartado")

        url = self._build_generic_url(
            FILE_VIEWER_PATH,
            {"chaveArquivo": key}
        )

        response = self._make_request("GET", url)
        response.raise_for_status()

        return self._process_file_response(response, key)

    async def get_file_async(self, key: str) -> ServiceFile:
        """
        Versão assíncrona de get_file.

        Args:
            key: Chave do arquivo no repositório

        Returns:
            ServiceFile com os dados do arquivo
        """
        return await asyncio.to_thread(self.get_file, key)

    def get_image(
        self,
        entity: str,
        keys: Dict[str, Any],
    ) -> Optional[ServiceFile]:
        """
        Baixa uma imagem associada a uma entidade.

        Args:
            entity: Nome da entidade (ex: "Parceiro")
            keys: Chaves primárias da entidade

        Returns:
            ServiceFile com os dados da imagem, ou None se não existir

        Example:
            >>> image = wrapper.get_image("Parceiro", {"CODPARC": 1})
            >>> if image:
            ...     with open(f"parceiro.{image.file_extension}", "wb") as f:
            ...         f.write(image.data)
        """
        if self._disposed:
            raise RuntimeError("Wrapper já foi descartado")

        # Constrói chaves no formato @key=value@key2=value2
        keys_str = "".join(f"@{k}={v}" for k, v in keys.items())

        path = IMAGE_PATH_TEMPLATE.format(entity=entity, keys=keys_str)
        url = self._build_generic_url(path)

        try:
            response = self._make_request("GET", url)

            if response.status_code == 404:
                return None

            response.raise_for_status()

            # Extrai content type e extension
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            extension = MIME_TYPES_TO_EXTENSIONS.get(
                content_type.split(";")[0].strip(),
                "bin"
            )

            return ServiceFile(
                data=response.content,
                content_type=content_type,
                file_extension=extension,
                filename=None,
            )

        except requests.RequestException:
            return None

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
        return await asyncio.to_thread(self.get_image, entity, keys)

    def _process_file_response(
        self,
        response: requests.Response,
        key: str,
    ) -> ServiceFile:
        """
        Processa a resposta de download de arquivo.

        Args:
            response: Resposta HTTP
            key: Chave do arquivo

        Returns:
            ServiceFile com os dados processados

        Raises:
            RuntimeError: Se a resposta é HTML de erro
        """
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        content = response.content

        # Verifica se é HTML de erro
        if "text/html" in content_type:
            html_text = content.decode("utf-8", errors="ignore")
            if "erro" in html_text.lower() or "error" in html_text.lower():
                from sankhya_sdk.exceptions import ServiceRequestFileNotFoundException
                raise ServiceRequestFileNotFoundException(request=None)

        # Extrai filename do Content-Disposition
        filename = None
        content_disposition = response.headers.get("Content-Disposition", "")
        if "filename=" in content_disposition:
            import re
            match = re.search(r'filename[^;=\n]*=(["\']?)([^"\';]+)\1', content_disposition)
            if match:
                filename = match.group(2)

        # Determina extensão
        extension = MIME_TYPES_TO_EXTENSIONS.get(
            content_type.split(";")[0].strip(),
            "bin"
        )

        return ServiceFile(
            data=content,
            content_type=content_type,
            file_extension=extension,
            filename=filename,
        )

    # ==========================================================================
    # Lifecycle
    # ==========================================================================

    def dispose(self) -> None:
        """
        Libera recursos do wrapper.

        Faz logout, limpa sessão e fecha conexão HTTP.
        Deve ser chamado quando o wrapper não for mais necessário.

        Example:
            >>> wrapper.dispose()
        """
        if self._disposed:
            return

        logger.debug("Descartando SankhyaWrapper")

        try:
            self._invalidate()
        except Exception as e:
            logger.warning(f"Erro ao invalidar sessão durante dispose: {e}")

        try:
            self.close()
        except Exception as e:
            logger.warning(f"Erro ao fechar sessão HTTP durante dispose: {e}")

        # Limpa lock do gerenciador
        if self.session_id:
            try:
                LockManager.release_lock(self.session_id)
            except Exception:
                pass

        self._disposed = True
        logger.debug("SankhyaWrapper descartado")

    # ==========================================================================
    # Factory Methods
    # ==========================================================================

    @classmethod
    def from_settings(
        cls,
        settings: Optional[SankhyaSettings] = None,
    ) -> "SankhyaWrapper":
        """
        Cria um wrapper a partir das configurações.

        Factory method que cria e autentica um wrapper usando
        as configurações fornecidas ou as configurações globais.

        Args:
            settings: Configurações Sankhya. Se None, usa configurações globais

        Returns:
            Wrapper autenticado

        Raises:
            ServiceRequestInvalidCredentialsException: Credenciais inválidas

        Example:
            >>> wrapper = SankhyaWrapper.from_settings()
            >>> # ou
            >>> settings = SankhyaSettings(...)
            >>> wrapper = SankhyaWrapper.from_settings(settings)
        """
        if settings is None:
            from sankhya_sdk.config import settings as global_settings
            settings = global_settings

        # Extrai host e porta da URL
        from urllib.parse import urlparse
        parsed = urlparse(settings.url)

        host = f"{parsed.scheme}://{parsed.hostname}" if parsed.scheme else settings.url
        port = settings.port

        # Cria wrapper
        wrapper = cls(
            host=host,
            port=port,
            timeout=settings.timeout,
            max_retries=settings.max_retries,
        )

        # Autentica
        wrapper.authenticate(settings.username, settings.password)

        return wrapper

    def __repr__(self) -> str:
        """Representação string do objeto."""
        return (
            f"SankhyaWrapper("
            f"host={self._host}, "
            f"port={self._port}, "
            f"environment={self._environment.name}, "
            f"authenticated={self.is_authenticated})"
        )
