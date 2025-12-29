# -*- coding: utf-8 -*-
"""
Core module for Sankhya SDK.

This module provides the main components for communicating with the Sankhya API,
including session management, authentication, and HTTP transport.
"""

from .constants import (
    CONTENT_TYPE_FORM,
    CONTENT_TYPE_XML,
    DATABASE_NAMES,
    DEFAULT_TIMEOUT,
    DWR_CONTROLLER_PATH,
    FILE_VIEWER_PATH,
    IMAGE_PATH_TEMPLATE,
    MAX_RETRY_COUNT,
    MIME_TYPES_TO_EXTENSIONS,
    PORT_TO_ENVIRONMENT,
    SESSION_COOKIE_NAME,
    SYSVERSION_PATTERN,
    USER_AGENT_TEMPLATE,
)
from .context import SankhyaContext
from .lock_manager import LockManager
from .low_level_wrapper import LowLevelSankhyaWrapper
from .types import ServiceAttribute, ServiceFile, SessionInfo
from .wrapper import SankhyaWrapper

__all__ = [
    # Main classes
    "SankhyaWrapper",
    "SankhyaContext",
    "LowLevelSankhyaWrapper",
    "LockManager",
    # Types
    "SessionInfo",
    "ServiceFile",
    "ServiceAttribute",
    # Constants
    "DEFAULT_TIMEOUT",
    "USER_AGENT_TEMPLATE",
    "MIME_TYPES_TO_EXTENSIONS",
    "DATABASE_NAMES",
    "PORT_TO_ENVIRONMENT",
    "MAX_RETRY_COUNT",
    "DWR_CONTROLLER_PATH",
    "FILE_VIEWER_PATH",
    "IMAGE_PATH_TEMPLATE",
    "CONTENT_TYPE_XML",
    "CONTENT_TYPE_FORM",
    "SESSION_COOKIE_NAME",
    "SYSVERSION_PATTERN",
]
