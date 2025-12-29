# -*- coding: utf-8 -*-
"""
Tipos auxiliares para o wrapper Sankhya.

Este módulo contém dataclasses e tipos utilizados internamente
pelo SankhyaWrapper.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionInfo:
    """
    Informações da sessão autenticada no Sankhya.

    Armazena os dados necessários para manter uma sessão ativa,
    incluindo credenciais para reautenticação automática.

    Attributes:
        session_id: ID da sessão (JSESSIONID) retornado pelo login
        user_code: Código do usuário autenticado (IDUSU)
        username: Nome de usuário para reautenticação
        password: Senha para reautenticação

    Example:
        >>> session = SessionInfo(
        ...     session_id="ABC123",
        ...     user_code=1,
        ...     username="admin",
        ...     password="secret"
        ... )
        >>> print(session.session_id)
        ABC123
    """

    session_id: str
    user_code: int
    username: str
    password: str


@dataclass
class ServiceFile:
    """
    Arquivo retornado por operações de download.

    Encapsula os dados de um arquivo baixado do Sankhya,
    incluindo o conteúdo em bytes e metadados.

    Attributes:
        data: Conteúdo do arquivo em bytes
        content_type: Tipo MIME do arquivo (ex: image/jpeg)
        file_extension: Extensão do arquivo sem ponto (ex: jpg)
        filename: Nome original do arquivo (opcional)

    Example:
        >>> file = ServiceFile(
        ...     data=b"...",
        ...     content_type="image/jpeg",
        ...     file_extension="jpg",
        ...     filename="foto.jpg"
        ... )
    """

    data: bytes
    content_type: str
    file_extension: str
    filename: Optional[str] = None


@dataclass
class ServiceAttribute:
    """
    Atributos de um serviço do Sankhya.

    Encapsula metadados sobre um serviço, incluindo
    informações de categoria e tipo.

    Attributes:
        is_transactional: Se o serviço é transacional
        is_retriable: Se o serviço pode ser retentado em caso de erro

    Example:
        >>> attr = ServiceAttribute(is_transactional=True, is_retriable=False)
    """

    is_transactional: bool = False
    is_retriable: bool = True
