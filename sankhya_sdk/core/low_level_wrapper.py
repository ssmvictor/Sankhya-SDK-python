# -*- coding: utf-8 -*-
"""
Wrapper de baixo nível para comunicação HTTP com o Sankhya.

Este módulo fornece a classe base LowLevelSankhyaWrapper com
métodos fundamentais para requisições HTTP.
"""

from __future__ import annotations

import logging
import platform
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse

import requests

from sankhya_sdk.enums.service_environment import ServiceEnvironment
from sankhya_sdk.enums.service_module import ServiceModule
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType

from .constants import (
    ACCEPT_ANY,
    CONTENT_TYPE_XML,
    DEFAULT_TIMEOUT,
    PORT_TO_ENVIRONMENT,
    SESSION_COOKIE_NAME,
    USER_AGENT_TEMPLATE,
)


logger = logging.getLogger(__name__)


class LowLevelSankhyaWrapper:
    """
    Classe base para comunicação HTTP de baixo nível com o Sankhya.

    Fornece métodos fundamentais para construção de URLs,
    configuração de sessão HTTP e execução de requisições.

    Esta classe não deve ser instanciada diretamente. Use
    SankhyaWrapper que herda desta classe.

    Attributes:
        environment: Ambiente de serviço (Production, Sandbox, Training)
        database_name: Nome do banco de dados
        user_code: Código do usuário autenticado

    Example:
        Esta classe é usada como base para SankhyaWrapper:

        >>> class SankhyaWrapper(LowLevelSankhyaWrapper):
        ...     pass
    """

    def __init__(
        self,
        host: str,
        port: int,
        request_type: ServiceRequestType = ServiceRequestType.DEFAULT,
        environment: Optional[ServiceEnvironment] = None,
        database_name: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Inicializa o wrapper de baixo nível.

        Args:
            host: Host do servidor Sankhya (sem porta)
            port: Porta do servidor
            request_type: Tipo de requisição (XML ou JSON)
            environment: Ambiente de serviço. Se None, determina pela porta
            database_name: Nome do banco de dados. Se None, usa padrão do ambiente
            timeout: Timeout para requisições HTTP em segundos

        Example:
            >>> wrapper = LowLevelSankhyaWrapper(
            ...     host="http://sankhya.example.com",
            ...     port=8180
            ... )
        """
        self._host = self._normalize_host(host)
        self._port = port
        self._request_type = request_type
        self._timeout = timeout
        self._user_code: int = 0

        # Determina ambiente pela porta se não especificado
        if environment is None:
            self._environment = PORT_TO_ENVIRONMENT.get(port, ServiceEnvironment.PRODUCTION)
        else:
            self._environment = environment

        # Define nome do banco de dados
        if database_name:
            self._database_name = database_name
        else:
            from .constants import DATABASE_NAMES
            self._database_name = DATABASE_NAMES.get(self._environment, "")

        # Cria sessão HTTP
        self._http_session = self._create_http_session()

        logger.debug(
            f"LowLevelSankhyaWrapper inicializado: host={self._host}, "
            f"port={self._port}, environment={self._environment.name}"
        )

    @staticmethod
    def _normalize_host(host: str) -> str:
        """
        Normaliza o host removendo porta e trailing slash.

        Args:
            host: Host a ser normalizado

        Returns:
            Host normalizado
        """
        parsed = urlparse(host)
        if parsed.scheme:
            return f"{parsed.scheme}://{parsed.hostname}"
        return f"http://{host.split(':')[0].rstrip('/')}"

    def _create_http_session(self) -> requests.Session:
        """
        Cria e configura uma sessão HTTP.

        Configura headers padrão, keep-alive e timeout.

        Returns:
            Sessão HTTP configurada
        """
        session = requests.Session()

        # User-Agent personalizado
        version = "1.0.0"  # TODO: Obter da versão do pacote
        os_info = f"{platform.system()} {platform.release()}"
        user_agent = USER_AGENT_TEMPLATE.format(version=version, os_info=os_info)

        session.headers.update({
            "User-Agent": user_agent,
            "Accept": ACCEPT_ANY,
            "Connection": "keep-alive",
        })

        return session

    def _build_service_url(
        self,
        service: ServiceName,
        module: Optional[ServiceModule] = None,
    ) -> str:
        """
        Constrói a URL completa para um serviço.

        Args:
            service: Nome do serviço
            module: Módulo do serviço. Se None, usa o módulo do serviço

        Returns:
            URL completa para o serviço

        Example:
            >>> url = wrapper._build_service_url(ServiceName.LOGIN)
            >>> print(url)
            http://server:8180/mge/service.sbr?serviceName=MobileLoginSP.login
        """
        if module is None:
            module = service.service_module

        # Obtém o internal_value do módulo para o path
        module_path = module.internal_value if module != ServiceModule.NONE else "mge"
        service_internal = service.internal_value

        base_url = f"{self._host}:{self._port}/{module_path}/service.sbr"
        params = urlencode({"serviceName": service_internal, "outputType": "xml"})

        return f"{base_url}?{params}"

    def _build_generic_url(
        self,
        path: str,
        query_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Constrói uma URL genérica.

        Args:
            path: Caminho relativo (ex: /mge/visualizadorArquivos.mge)
            query_params: Parâmetros de query string

        Returns:
            URL completa

        Example:
            >>> url = wrapper._build_generic_url(
            ...     "/mge/arquivo.mge",
            ...     {"chave": "123"}
            ... )
        """
        url = f"{self._host}:{self._port}{path}"

        if query_params:
            params = urlencode(query_params)
            url = f"{url}?{params}"

        return url

    def _add_session_cookie(
        self,
        session_id: str,
    ) -> None:
        """
        Adiciona o cookie de sessão à sessão HTTP.

        Args:
            session_id: ID da sessão (JSESSIONID)
        """
        self._http_session.cookies.set(
            SESSION_COOKIE_NAME,
            session_id,
            domain=urlparse(self._host).hostname,
        )

    def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> requests.Response:
        """
        Executa uma requisição HTTP.

        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL completa
            data: Dados do corpo da requisição
            headers: Headers adicionais
            content_type: Content-Type da requisição

        Returns:
            Response da requisição

        Raises:
            requests.RequestException: Em caso de erro de rede
        """
        request_headers = dict(headers) if headers else {}

        if content_type:
            request_headers["Content-Type"] = content_type
        elif data:
            request_headers["Content-Type"] = CONTENT_TYPE_XML

        logger.debug(f"Requisição {method} para {url}")

        response = self._http_session.request(
            method=method,
            url=url,
            data=data.encode("utf-8") if isinstance(data, str) else data,
            headers=request_headers,
            timeout=self._timeout,
        )

        logger.debug(f"Response status: {response.status_code}")

        return response

    @property
    def environment(self) -> ServiceEnvironment:
        """Retorna o ambiente de serviço."""
        return self._environment

    @property
    def database_name(self) -> str:
        """Retorna o nome do banco de dados."""
        return self._database_name

    @property
    def user_code(self) -> int:
        """Retorna o código do usuário autenticado."""
        return self._user_code

    @property
    def host(self) -> str:
        """Retorna o host do servidor."""
        return self._host

    @property
    def port(self) -> int:
        """Retorna a porta do servidor."""
        return self._port

    @property
    def base_url(self) -> str:
        """Retorna a URL base do servidor."""
        return f"{self._host}:{self._port}"

    def close(self) -> None:
        """
        Fecha a sessão HTTP.

        Libera recursos da sessão HTTP. Chamado automaticamente
        pelo dispose() do SankhyaWrapper.
        """
        if self._http_session:
            self._http_session.close()
            logger.debug("Sessão HTTP fechada")
