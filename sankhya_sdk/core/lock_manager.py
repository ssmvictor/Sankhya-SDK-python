# -*- coding: utf-8 -*-
"""
Gerenciador de locks thread-safe para o Sankhya SDK.

Este módulo fornece um gerenciador centralizado de locks
para garantir thread-safety em operações concorrentes.
"""

from __future__ import annotations

import threading
from typing import Dict


class LockManager:
    """
    Gerenciador de locks thread-safe.

    Fornece um mecanismo centralizado para obter e liberar locks
    baseados em chaves únicas (tipicamente session_id).

    Esta classe usa um padrão de singleton para garantir que
    o mesmo conjunto de locks seja compartilhado entre todas
    as instâncias do wrapper.

    Thread Safety:
        Todos os métodos são thread-safe e podem ser chamados
        de múltiplas threads simultaneamente.

    Example:
        >>> lock = LockManager.get_lock("session_123")
        >>> with lock:
        ...     # operação protegida
        ...     pass
    """

    _locks: Dict[str, threading.Lock] = {}
    _locks_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_lock(cls, key: str) -> threading.Lock:
        """
        Obtém um lock para a chave especificada.

        Se o lock não existir, cria um novo. Retorna sempre
        o mesmo lock para a mesma chave.

        Args:
            key: Chave única para identificar o lock

        Returns:
            Lock associado à chave

        Example:
            >>> lock = LockManager.get_lock("my_session")
            >>> lock.acquire()
            >>> # ... operação crítica ...
            >>> lock.release()
        """
        with cls._locks_lock:
            if key not in cls._locks:
                cls._locks[key] = threading.Lock()
            return cls._locks[key]

    @classmethod
    def release_lock(cls, key: str) -> None:
        """
        Remove um lock do gerenciador.

        Remove o lock associado à chave, liberando recursos.
        Chamado tipicamente quando uma sessão é encerrada.

        Args:
            key: Chave do lock a ser removido

        Note:
            Este método não libera o lock se ele estiver adquirido,
            apenas remove a referência do gerenciador.

        Example:
            >>> LockManager.release_lock("session_123")
        """
        with cls._locks_lock:
            if key in cls._locks:
                del cls._locks[key]

    @classmethod
    def clear_all(cls) -> None:
        """
        Remove todos os locks do gerenciador.

        Útil para cleanup durante testes ou shutdown da aplicação.

        Warning:
            Use com cuidado em produção, pois pode causar
            condições de corrida se houver operações em andamento.
        """
        with cls._locks_lock:
            cls._locks.clear()

    @classmethod
    def count(cls) -> int:
        """
        Retorna o número de locks registrados.

        Returns:
            Número de locks ativos no gerenciador
        """
        with cls._locks_lock:
            return len(cls._locks)
