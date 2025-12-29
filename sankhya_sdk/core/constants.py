# -*- coding: utf-8 -*-
"""
Constantes específicas do wrapper Sankhya.

Este módulo contém constantes utilizadas pelo SankhyaWrapper para
comunicação HTTP com a API Sankhya.
"""

from typing import Dict, Final

from sankhya_sdk.enums.service_environment import ServiceEnvironment


# Timeout padrão para requisições HTTP (segundos)
DEFAULT_TIMEOUT: Final[int] = 30

# Template do User-Agent para requisições
USER_AGENT_TEMPLATE: Final[str] = "SankhyaSDK-Python/{version} ({os_info})"

# Mapeamento de MIME types para extensões de arquivo
MIME_TYPES_TO_EXTENSIONS: Final[Dict[str, str]] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
    "application/pdf": "pdf",
    "application/xml": "xml",
    "text/xml": "xml",
    "application/json": "json",
    "text/plain": "txt",
    "application/octet-stream": "bin",
}

# Mapeamento de ambientes para nomes de banco de dados padrão
# Alinhado com os valores originais do .NET SDK
DATABASE_NAMES: Final[Dict[ServiceEnvironment, str]] = {
    ServiceEnvironment.PRODUCTION: "SANKHYA_PRODUCAO",
    ServiceEnvironment.SANDBOX: "SANKHYA_HOMOLOGACAO",
    ServiceEnvironment.TRAINING: "SANKHYA_TREINAMENTO",
    ServiceEnvironment.NONE: "",
}

# Mapeamento de portas para ambientes
PORT_TO_ENVIRONMENT: Final[Dict[int, ServiceEnvironment]] = {
    8180: ServiceEnvironment.PRODUCTION,
    8280: ServiceEnvironment.SANDBOX,
    8380: ServiceEnvironment.TRAINING,
}

# Constantes de retry
MAX_RETRY_COUNT: Final[int] = 3

# URLs e paths
DWR_CONTROLLER_PATH: Final[str] = "/mge/dwr/exec/DWRController.execute.dwr"
FILE_VIEWER_PATH: Final[str] = "/mge/visualizadorArquivos.mge"
IMAGE_PATH_TEMPLATE: Final[str] = "/mge/{entity}@IMAGEM{keys}.dbimage"

# Headers HTTP
CONTENT_TYPE_XML: Final[str] = "text/xml; charset=utf-8"
CONTENT_TYPE_FORM: Final[str] = "application/x-www-form-urlencoded"
ACCEPT_ANY: Final[str] = "*/*"

# Cookie names
SESSION_COOKIE_NAME: Final[str] = "JSESSIONID"

# Regex patterns
SYSVERSION_PATTERN: Final[str] = r'SYSVERSION\s*=\s*["\']([^"\']+)["\']'
