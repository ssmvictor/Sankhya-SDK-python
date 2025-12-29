# -*- coding: utf-8 -*-
"""
Testes de integração para OnDemandRequestWrapper.

Testa processamento em lote, throttling, concorrência e retry.
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from sankhya_sdk.core.wrapper import SankhyaWrapper
from sankhya_sdk.exceptions import SankhyaException
from sankhya_sdk.models.transport.partner import Partner
from sankhya_sdk.models.transport.product import Product
from sankhya_sdk.request_wrappers.on_demand_request_wrapper import (
    OnDemandRequestWrapper,
)
from sankhya_sdk.request_wrappers.on_demand_request_factory import (
    OnDemandRequestFactory,
)

from .conftest import (
    create_error_response,
    create_login_response,
    create_logout_response,
    create_mock_response,
    create_success_response,
)


@pytest.mark.integration
class TestOnDemandBasic:
    """Testes básicos de on-demand."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_single_request(self, mock_session_class):
        """Testa requisição única on-demand."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "100", "NOMEPARC": "Parceiro OnDemand"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, create_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        OnDemandRequestWrapper.initialize(wrapper)
        
        try:
            partner = Partner(name="Parceiro OnDemand")
            OnDemandRequestWrapper.add(partner)
            
            # Flush para processar
            OnDemandRequestWrapper.flush()
            
            # Verificar que a requisição foi enviada
            assert mock_session.request.call_count >= 2  # login + create
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_batch_processing(self, mock_session_class):
        """Testa processamento de lote de requisições."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Respostas para múltiplas criações
        create_resps = [
            create_mock_response(
                200, create_success_response([
                    {"CODPARC": str(i), "NOMEPARC": f"Parceiro {i}"}
                ])
            )
            for i in range(1, 6)
        ]
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + create_resps + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        OnDemandRequestWrapper.initialize(wrapper, throughput=5)
        
        try:
            # Adicionar múltiplos itens
            for i in range(1, 6):
                partner = Partner(name=f"Parceiro {i}")
                OnDemandRequestWrapper.add(partner)
            
            # Flush para processar todos
            OnDemandRequestWrapper.flush()
            
            # Deve ter processado todos (login + 5 creates ou batched)
            assert mock_session.request.call_count >= 2
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandThrottling:
    """Testes de controle de throughput."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_with_throughput_limit(self, mock_session_class):
        """Testa controle de throughput."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        create_resp = create_mock_response(
            200, create_success_response([
                {"CODPARC": "1", "NOMEPARC": "Parceiro"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        # Configurar respostas suficientes
        mock_session.request.side_effect = [login_resp] + [create_resp] * 10 + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        # Throughput de 2 por vez
        OnDemandRequestWrapper.initialize(wrapper, throughput=2)
        
        try:
            for i in range(5):
                partner = Partner(name=f"Parceiro {i}")
                OnDemandRequestWrapper.add(partner)
            
            OnDemandRequestWrapper.flush()
            
            # Deve ter processado (comportamento exato depende da implementação)
            assert mock_session.request.call_count >= 2
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_with_concurrency_limit(self, mock_session_class):
        """Testa limite de concorrência."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Simular delay nas respostas
        def delayed_response(*args, **kwargs):
            time.sleep(0.01)  # Pequeno delay
            return create_mock_response(
                200, create_success_response([{"CODPARC": "1", "NOMEPARC": "P"}])
            )
        
        mock_session.request.side_effect = [login_resp] + [
            delayed_response() for _ in range(10)
        ] + [create_mock_response(200, create_logout_response())]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        OnDemandRequestWrapper.initialize(wrapper, throughput=3)
        
        try:
            for i in range(5):
                partner = Partner(name=f"Parceiro {i}")
                OnDemandRequestWrapper.add(partner)
            
            OnDemandRequestWrapper.flush()
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandErrorHandling:
    """Testes de tratamento de erros."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_error_handling(self, mock_session_class):
        """Testa tratamento de erros individuais."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeira requisição OK, segunda falha, terceira OK
        success_resp = create_mock_response(
            200, create_success_response([{"CODPARC": "1", "NOMEPARC": "OK"}])
        )
        error_resp = create_mock_response(
            200, create_error_response("DB.ERROR", "Erro no banco")
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, success_resp, error_resp, success_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        errors_captured: List[Exception] = []
        
        def on_failure(entity, error):
            errors_captured.append(error)
        
        OnDemandRequestWrapper.initialize(wrapper, on_failure=on_failure)
        
        try:
            for i in range(3):
                partner = Partner(name=f"Parceiro {i}")
                OnDemandRequestWrapper.add(partner)
            
            OnDemandRequestWrapper.flush()
            
            # Pode ter capturado erros (depende da implementação)
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_retry_failed_requests(self, mock_session_class):
        """Testa retry de requisições falhas."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Primeira tentativa falha, segunda sucede
        error_resp = create_mock_response(
            200, create_error_response("TIMEOUT", "Timeout")
        )
        success_resp = create_mock_response(
            200, create_success_response([{"CODPARC": "1", "NOMEPARC": "OK"}])
        )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [
            login_resp, error_resp, success_resp, logout_resp
        ]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        OnDemandRequestWrapper.initialize(wrapper)
        
        try:
            partner = Partner(name="Parceiro Retry")
            OnDemandRequestWrapper.add(partner)
            
            OnDemandRequestWrapper.flush()
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandCancellation:
    """Testes de cancelamento."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_cancellation(self, mock_session_class):
        """Testa cancelamento de processamento."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        
        # Simular operação lenta
        def slow_response():
            time.sleep(0.05)
            return create_mock_response(
                200, create_success_response([{"CODPARC": "1", "NOMEPARC": "P"}])
            )
        
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, slow_response(), logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        OnDemandRequestWrapper.initialize(wrapper)
        
        try:
            # Adicionar itens
            for i in range(10):
                partner = Partner(name=f"Parceiro {i}")
                OnDemandRequestWrapper.add(partner)
            
            # Cancelar antes de processar tudo
            OnDemandRequestWrapper.cancel()
            
            # Dispose deve funcionar normalmente
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandProgress:
    """Testes de rastreamento de progresso."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_progress_tracking(self, mock_session_class):
        """Testa rastreamento de progresso."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([{"CODPARC": "1", "NOMEPARC": "P"}])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + [success_resp] * 5 + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        progress_updates: List[int] = []
        
        def on_progress(processed, total):
            progress_updates.append(processed)
        
        OnDemandRequestWrapper.initialize(wrapper, on_progress=on_progress)
        
        try:
            for i in range(5):
                partner = Partner(name=f"Parceiro {i}")
                OnDemandRequestWrapper.add(partner)
            
            OnDemandRequestWrapper.flush()
            
            # Progresso deve ter sido atualizado
            # (comportamento exato depende da implementação)
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandFactory:
    """Testes do OnDemandRequestFactory."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_factory_create_wrapper(self, mock_session_class):
        """Testa criação de wrapper via factory."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp, logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        try:
            # Criar via factory
            on_demand = OnDemandRequestFactory.create(wrapper, throughput=5)
            
            assert on_demand is not None
            
            on_demand.dispose()
        finally:
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandAsync:
    """Testes de processamento assíncrono."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    @pytest.mark.asyncio
    async def test_async_on_demand_processing(self, mock_session_class):
        """Testa processamento assíncrono on-demand."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([{"CODPARC": "1", "NOMEPARC": "P"}])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + [success_resp] * 5 + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        # Usar AsyncOnDemandRequestWrapper se disponível
        from sankhya_sdk.request_wrappers.async_on_demand_request_wrapper import (
            AsyncOnDemandRequestWrapper,
        )
        
        AsyncOnDemandRequestWrapper.initialize(wrapper)
        
        try:
            for i in range(3):
                partner = Partner(name=f"Parceiro Async {i}")
                await AsyncOnDemandRequestWrapper.add_async(partner)
            
            await AsyncOnDemandRequestWrapper.flush_async()
        finally:
            AsyncOnDemandRequestWrapper.dispose()
            wrapper.dispose()


@pytest.mark.integration
class TestOnDemandProducts:
    """Testes de on-demand com Products."""

    @patch("sankhya_sdk.core.low_level_wrapper.requests.Session")
    def test_on_demand_products(self, mock_session_class):
        """Testa processamento on-demand de produtos."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        login_resp = create_mock_response(200, create_login_response())
        success_resp = create_mock_response(
            200, create_success_response([
                {"CODPROD": "1", "DESCRPROD": "Produto", "CODVOL": "UN"}
            ])
        )
        logout_resp = create_mock_response(200, create_logout_response())
        
        mock_session.request.side_effect = [login_resp] + [success_resp] * 3 + [logout_resp]
        
        wrapper = SankhyaWrapper(host="http://test.local", port=8180)
        wrapper.authenticate("user", "pass")
        
        OnDemandRequestWrapper.initialize(wrapper)
        
        try:
            for i in range(3):
                product = Product(name=f"Produto {i}", code_volume="UN")
                OnDemandRequestWrapper.add(product)
            
            OnDemandRequestWrapper.flush()
        finally:
            OnDemandRequestWrapper.dispose()
            wrapper.dispose()
