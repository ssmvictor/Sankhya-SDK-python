# -*- coding: utf-8 -*-
"""
KnowServices Request Wrapper.

Fornece métodos de conveniência para serviços conhecidos da API Sankhya,
incluindo operações de sessão, mensagens, notas fiscais e arquivos.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/RequestWrappers/KnowServicesRequestWrapper.cs
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

if TYPE_CHECKING:
    from sankhya_sdk.core.context import SankhyaContext
    from sankhya_sdk.models.transport.base import TransportEntityBase

from sankhya_sdk.core.types import ServiceFile
from sankhya_sdk.enums.billing_type import BillingType
from sankhya_sdk.enums.movement_type import MovementType
from sankhya_sdk.enums.sankhya_warning_level import SankhyaWarningLevel
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.service_request_type import ServiceRequestType
from sankhya_sdk.exceptions import (
    ConfirmInvoiceException,
    InvalidServiceRequestOperationException,
    MarkAsPaymentPaidException,
    NoItemsConfirmInvoiceException,
    SankhyaException,
    UnlinkShippingException,
)
from sankhya_sdk.models.base import EntityBase
from sankhya_sdk.models.service.basic_types import Path, Paths
from sankhya_sdk.models.service.event_types import (
    ClientEvent,
    ClientEvents,
    NotificationElem,
    SystemMessage,
    SystemWarning,
    SystemWarningRecipient,
)
from sankhya_sdk.models.service.invoice_types import (
    Invoice,
    InvoiceItem,
    InvoiceItems,
    Invoices,
)
from sankhya_sdk.models.service.metadata_types import Config, Session
from sankhya_sdk.models.service.request_body import RequestBody
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.models.service.service_response import ServiceResponse
from sankhya_sdk.models.service.user_types import LowData, SessionInfo


logger = logging.getLogger(__name__)

# TypeVar para entidades genéricas
T = TypeVar("T", bound=EntityBase)


class KnowServicesRequestWrapper:
    """
    Wrapper para serviços conhecidos (known services) do Sankhya.
    
    Fornece métodos de conveniência para operações comuns como:
    - Gerenciamento de sessões (GetSessions, KillSession)
    - Mensagens e avisos (SendWarning, SendMessage, ReceiveMessages)
    - Operações de nota fiscal (CreateInvoice, RemoveInvoice, etc.)
    - Operações financeiras (FlagAsPaymentsPaid, ReversePayments)
    - Arquivos e imagens (GetFile, GetImage, OpenFile, DeleteFiles)
    
    Esta classe utiliza atributos de classe para manter uma sessão
    compartilhada, similar ao padrão de métodos de extensão do C#.
    
    Attributes:
        _context: Contexto Sankhya para gerenciamento de sessão
        _session_token: Token UUID da sessão ativa
        _initialized: Flag indicando se o wrapper foi inicializado
        _last_time_message_received: Timestamp da última mensagem recebida
    
    Example:
        Inicialização e uso básico:
        
        >>> KnowServicesRequestWrapper.initialize()
        >>> sessions = KnowServicesRequestWrapper.get_sessions()
        >>> print(f"Sessões ativas: {len(sessions)}")
        >>> KnowServicesRequestWrapper.dispose()
        
        Com context manager:
        
        >>> with KnowServicesRequestWrapper():
        ...     nunota = KnowServicesRequestWrapper.create_invoice(header, items)
        ...     print(f"Nota criada: {nunota}")
    """
    
    _context: ClassVar[Optional["SankhyaContext"]] = None
    _session_token: ClassVar[Optional[uuid.UUID]] = None
    _initialized: ClassVar[bool] = False
    _last_time_message_received: ClassVar[datetime] = datetime.now()
    
    def __init__(self) -> None:
        """
        Inicializa o wrapper como context manager.
        
        Quando usado como context manager, inicializa automaticamente
        a sessão ao entrar no contexto.
        """
        self._managed = False
    
    def __enter__(self) -> "KnowServicesRequestWrapper":
        """Entra no contexto e inicializa a sessão."""
        if not KnowServicesRequestWrapper._initialized:
            KnowServicesRequestWrapper.initialize()
        self._managed = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sai do contexto e libera recursos."""
        if self._managed:
            KnowServicesRequestWrapper.dispose()
    
    async def __aenter__(self) -> "KnowServicesRequestWrapper":
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
        as configurações padrão (SankhyaSettings).
        
        Args:
            context: Contexto Sankhya existente (opcional)
            
        Raises:
            RuntimeError: Se já foi inicializado
            
        Example:
            >>> KnowServicesRequestWrapper.initialize()
            >>> # ou com contexto existente
            >>> ctx = SankhyaContext.from_settings()
            >>> KnowServicesRequestWrapper.initialize(ctx)
        """
        if cls._initialized:
            logger.warning("KnowServicesRequestWrapper já inicializado")
            return
        
        if context is not None:
            cls._context = context
            cls._session_token = context.token
        else:
            # Import local para evitar circular
            from sankhya_sdk.core.context import SankhyaContext
            cls._context = SankhyaContext.from_settings()
            cls._session_token = cls._context.acquire_new_session(
                ServiceRequestType.KNOW_SERVICES
            )
        
        cls._last_time_message_received = datetime.now()
        cls._initialized = True
        logger.info(
            f"KnowServicesRequestWrapper inicializado: token={cls._session_token}"
        )
    
    @classmethod
    def dispose(cls) -> None:
        """
        Libera os recursos do wrapper.
        
        Finaliza a sessão e limpa os atributos de classe.
        Pode ser chamado múltiplas vezes sem efeito.
        
        Example:
            >>> KnowServicesRequestWrapper.dispose()
        """
        if not cls._initialized:
            return
        
        if cls._context and cls._session_token:
            try:
                cls._context.finalize_session(cls._session_token)
            except Exception as e:
                logger.warning(f"Erro ao finalizar sessão: {e}")
        
        cls._context = None
        cls._session_token = None
        cls._initialized = False
        cls._last_time_message_received = datetime.now()
        logger.info("KnowServicesRequestWrapper descartado")
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """Garante que o wrapper está inicializado."""
        if not cls._initialized:
            raise RuntimeError(
                "KnowServicesRequestWrapper não inicializado. "
                "Chame KnowServicesRequestWrapper.initialize() primeiro."
            )
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    @classmethod
    def get_sessions(cls) -> List[SessionInfo]:
        """
        Obtém a lista de sessões ativas no sistema.
        
        Returns:
            Lista de informações de sessões ativas
            
        Example:
            >>> sessions = KnowServicesRequestWrapper.get_sessions()
            >>> for session in sessions:
            ...     print(f"Usuário: {session.user_name}, IP: {session.ip_address}")
        """
        cls._ensure_initialized()
        logger.info("Obtendo lista de sessões ativas")
        
        request = ServiceRequest(service=ServiceName.SESSION_GET_ALL)
        response = cls._invoke_service(request)
        
        # Extrair sessões da resposta
        sessions: List[SessionInfo] = []
        if response.response_body and hasattr(response.response_body, "sessions"):
            body_sessions = response.response_body.sessions
            if body_sessions and hasattr(body_sessions, "sessions"):
                sessions = body_sessions.sessions
        
        logger.info(f"Sessões ativas encontradas: {len(sessions)}")
        return sessions
    
    @classmethod
    def kill_session(cls, session_id: str) -> None:
        """
        Finaliza uma sessão específica pelo seu ID.
        
        Args:
            session_id: ID da sessão a ser finalizada
            
        Example:
            >>> KnowServicesRequestWrapper.kill_session("ABC123XYZ")
        """
        cls._ensure_initialized()
        logger.info(f"Finalizando sessão: {session_id}")
        
        request = ServiceRequest(
            service=ServiceName.SESSION_KILL,
            request_body=RequestBody(
                session=Session(jsession_id=session_id)
            ),
        )
        cls._invoke_service(request)
        logger.debug(f"Sessão {session_id} finalizada com sucesso")
    
    # =========================================================================
    # Messaging & Warnings
    # =========================================================================
    
    @classmethod
    def send_warning(
        cls,
        title: str,
        description: str,
        tip: Optional[str] = None,
        level: SankhyaWarningLevel = SankhyaWarningLevel.INFORMATION,
        recipients: Optional[List[SystemWarningRecipient]] = None,
    ) -> None:
        """
        Envia um aviso do sistema para usuários.
        
        Args:
            title: Título do aviso
            description: Descrição detalhada do aviso
            tip: Dica opcional para o usuário
            level: Nível de severidade do aviso
            recipients: Lista de destinatários (None = todos)
            
        Example:
            >>> KnowServicesRequestWrapper.send_warning(
            ...     title="Manutenção Agendada",
            ...     description="Sistema ficará indisponível das 22h às 23h",
            ...     level=SankhyaWarningLevel.WARNING
            ... )
        """
        cls._ensure_initialized()
        
        recipient_count = len(recipients) if recipients else "todos"
        logger.info(
            f"Enviando aviso '{title}' (nível: {level.value}) "
            f"para {recipient_count} destinatário(s)"
        )
        
        warning = SystemWarning(
            title=title,
            content=description,
            type=tip,
            priority=level.internal_value if hasattr(level, "internal_value") else str(level.value),
            recipients=recipients or [],
        )
        
        request = ServiceRequest(
            service=ServiceName.WARNING_SEND,
            request_body=RequestBody(system_warning=warning),
        )
        cls._invoke_service(request)
        logger.debug("Aviso enviado com sucesso")
    
    @classmethod
    def send_message(
        cls,
        content: str,
        recipients: Optional[List[SystemWarningRecipient]] = None,
    ) -> None:
        """
        Envia uma mensagem do sistema para usuários.
        
        Args:
            content: Conteúdo da mensagem
            recipients: Lista de destinatários (None = todos)
            
        Example:
            >>> KnowServicesRequestWrapper.send_message(
            ...     content="Backup concluído com sucesso!",
            ...     recipients=[SystemWarningRecipient(user_id=1)]
            ... )
        """
        cls._ensure_initialized()
        
        recipient_count = len(recipients) if recipients else "todos"
        logger.info(f"Enviando mensagem para {recipient_count} destinatário(s)")
        
        target_users = [r.user_id for r in recipients if r.user_id] if recipients else []
        message = SystemMessage(
            content=content,
            target_users=target_users,
        )
        
        request = ServiceRequest(
            service=ServiceName.MESSAGE_SEND,
            request_body=RequestBody(system_message=message),
        )
        cls._invoke_service(request)
        logger.debug("Mensagem enviada com sucesso")
    
    @classmethod
    def receive_messages(cls) -> str:
        """
        Recebe novas mensagens/avisos desde a última verificação.
        
        Atualiza internamente o timestamp da última verificação.
        
        Returns:
            String serializada com as mensagens recebidas
            
        Example:
            >>> messages = KnowServicesRequestWrapper.receive_messages()
            >>> print(messages)
        """
        cls._ensure_initialized()
        logger.debug("Verificando novas mensagens")
        
        notification = NotificationElem(
            data={"lastNotification": cls._last_time_message_received.isoformat()}
        )
        
        request = ServiceRequest(
            service=ServiceName.WARNING_RECEIVE,
            request_body=RequestBody(notification_elem=notification),
        )
        response = cls._invoke_service(request)
        
        cls._last_time_message_received = datetime.now()
        
        # Serializar resposta
        if response.response_body:
            return str(response.response_body.model_dump_json())
        return ""
    
    # =========================================================================
    # Invoice CRUD Operations
    # =========================================================================
    
    @classmethod
    def create_invoice(
        cls,
        invoice_header: Invoice,
        invoice_items: Optional[List[InvoiceItem]] = None,
    ) -> int:
        """
        Cria uma nova nota fiscal.
        
        Args:
            invoice_header: Dados do cabeçalho da nota
            invoice_items: Lista de itens da nota (opcional)
            
        Returns:
            NUNOTA (número único) da nota criada
            
        Raises:
            ValueError: Se invoice_header for None
            
        Example:
            >>> header = Invoice(partner_code=123, top_code=1)
            >>> items = [InvoiceItem(product_code="PROD1", quantity=10)]
            >>> nunota = KnowServicesRequestWrapper.create_invoice(header, items)
            >>> print(f"Nota criada: {nunota}")
        """
        cls._ensure_initialized()
        
        if invoice_header is None:
            raise ValueError("invoice_header não pode ser None")
        
        item_count = len(invoice_items) if invoice_items else 0
        logger.info(f"Criando nota fiscal com {item_count} item(ns)")
        
        # Copiar header e adicionar itens
        invoice = Invoice(
            **invoice_header.model_dump(exclude={"items"}),
            items=invoice_items or [],
        )
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_INCLUDE,
            request_body=RequestBody(invoice=invoice),
        )
        response = cls._invoke_service(request)
        
        # Extrair NUNOTA da resposta
        nunota = 0
        if response.response_body:
            rb = response.response_body
            if hasattr(rb, "primary_key") and rb.primary_key:
                if hasattr(rb.primary_key, "nunota"):
                    nunota = rb.primary_key.nunota or 0
                elif hasattr(rb.primary_key, "values"):
                    nunota = rb.primary_key.values.get("NUNOTA", 0)
        
        logger.info(f"Nota fiscal criada: NUNOTA={nunota}")
        return nunota
    
    @classmethod
    def remove_invoice(cls, single_number: int) -> None:
        """
        Remove uma nota fiscal pelo seu NUNOTA.
        
        Args:
            single_number: NUNOTA da nota a ser removida
            
        Example:
            >>> KnowServicesRequestWrapper.remove_invoice(12345)
        """
        cls._ensure_initialized()
        logger.info(f"Removendo nota fiscal: NUNOTA={single_number}")
        
        invoices = Invoices(
            items=[Invoice(unique_number=single_number)]
        )
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_REMOVE,
            request_body=RequestBody(invoices=invoices),
        )
        cls._invoke_service(request)
        logger.debug(f"Nota {single_number} removida com sucesso")
    
    @classmethod
    def add_invoice_items(
        cls,
        single_number: int,
        invoice_items: List[InvoiceItem],
    ) -> int:
        """
        Adiciona itens a uma nota fiscal existente.
        
        Args:
            single_number: NUNOTA da nota
            invoice_items: Lista de itens a adicionar
            
        Returns:
            Sequência do último item adicionado (ou 0 em caso de erro)
            
        Example:
            >>> items = [InvoiceItem(product_code="PROD2", quantity=5)]
            >>> seq = KnowServicesRequestWrapper.add_invoice_items(12345, items)
        """
        cls._ensure_initialized()
        logger.info(
            f"Adicionando {len(invoice_items)} item(ns) à nota {single_number}"
        )
        
        try:
            invoice = Invoice(
                unique_number=single_number,
                items=invoice_items,
            )
            
            request = ServiceRequest(
                service=ServiceName.INVOICE_ITEM_INCLUDE,
                request_body=RequestBody(invoice=invoice),
            )
            response = cls._invoke_service(request)
            
            # Tentar extrair sequência
            sequence = 0
            if response.response_body:
                rb = response.response_body
                if hasattr(rb, "sequence"):
                    sequence = rb.sequence or 0
            
            logger.debug(f"Itens adicionados. Última sequência: {sequence}")
            return sequence
            
        except Exception as e:
            logger.error(f"Erro ao adicionar itens à nota {single_number}: {e}")
            return 0
    
    @classmethod
    def remove_invoice_items(cls, invoice_items: List[InvoiceItem]) -> None:
        """
        Remove itens de uma nota fiscal.
        
        Todos os itens devem pertencer à mesma nota.
        
        Args:
            invoice_items: Lista de itens a remover
            
        Raises:
            InvalidServiceRequestOperationException: Se itens de notas diferentes
            
        Example:
            >>> items = [InvoiceItem(sequence=1), InvoiceItem(sequence=2)]
            >>> KnowServicesRequestWrapper.remove_invoice_items(items)
        """
        cls._ensure_initialized()
        
        if not invoice_items:
            logger.warning("Lista de itens vazia para remoção")
            return
        
        # Validar que todos os itens pertencem à mesma nota
        first_single_number = invoice_items[0].extra_data.get("single_number")
        for item in invoice_items:
            item_single_number = item.extra_data.get("single_number")
            if item_single_number != first_single_number:
                raise InvalidServiceRequestOperationException(
                    "Todos os itens devem pertencer à mesma nota fiscal"
                )
        
        logger.info(f"Removendo {len(invoice_items)} item(ns) de nota fiscal")
        
        # Build invoice items with online_update flag matching .NET
        items_with_flags = InvoiceItems(items=invoice_items)
        # Set online_update flag via extra_data
        for item in items_with_flags.items:
            item.extra_data["onlineUpdate"] = "true"
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_ITEM_REMOVE,
            request_body=RequestBody(
                invoice=Invoice(items=invoice_items)
            ),
        )
        cls._invoke_service(request)
        logger.debug("Itens removidos com sucesso")
    
    # =========================================================================
    # Billing Operations
    # =========================================================================
    
    @classmethod
    def bill(
        cls,
        single_number: int,
        code_operation_type: int,
        billing_type: BillingType,
        series: Optional[int] = None,
        request_events: Optional[List[ClientEvent]] = None,
    ) -> Tuple[int, Optional[List[ClientEvent]]]:
        """
        Fatura uma nota fiscal.
        
        Args:
            single_number: NUNOTA da nota a faturar
            code_operation_type: Código do tipo de operação
            billing_type: Tipo de faturamento
            series: Série da nota (opcional)
            request_events: Eventos de requisição (opcional)
            
        Returns:
            Tupla com (NUNOTA faturado, eventos de resposta)
            
        Example:
            >>> nunota, events = KnowServicesRequestWrapper.bill(
            ...     single_number=12345,
            ...     code_operation_type=1,
            ...     billing_type=BillingType.NORMAL
            ... )
        """
        cls._ensure_initialized()
        logger.info(
            f"Faturando nota {single_number} "
            f"(tipo operação: {code_operation_type}, tipo faturamento: {billing_type})"
        )
        
        # Build invoice reference with single_number (matching .NET structure)
        invoice = Invoice()
        invoice.extra_data["value"] = str(single_number)
        
        # Build Invoices with all required billing fields matching .NET
        invoices = Invoices(items=[invoice])
        # Add billing-specific fields via extra_data to match .NET payload structure
        billing_type_value = billing_type.internal_value if hasattr(billing_type, "internal_value") else str(billing_type.value)
        
        # Build request body with proper invoices structure matching .NET
        request_body = RequestBody(invoices=invoices)
        
        # Set invoices extra_data to include all billing fields from .NET
        # .NET sends: BillingType, CodeOperationType, DateBillingNullable=null, 
        # DateExitNullable=null, TimeExitNullable=null, IsDateValidated=true,
        # InvoicesWithCurrency={CurrencyValue="undefined"}, Invoice={Value=singleNumber},
        # OneInvoiceForEach=true
        if request_body.invoices:
            request_body.invoices.items[0].extra_data.update({
                "billingType": billing_type_value,
                "codeOperationType": str(code_operation_type),
                "dateBillingNullable": "",
                "dateExitNullable": "",
                "timeExitNullable": "",
                "isDateValidated": "true",
                "oneInvoiceForEach": "true",
            })
        
        if series is not None:
            # When series is provided, use Direct billing type
            if request_body.invoices and request_body.invoices.items:
                request_body.invoices.items[0].extra_data["billingType"] = "Direct"
                request_body.invoices.items[0].series = str(series)
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_BILL,
            request_body=request_body,
        )
        
        if request_events:
            request.request_body.client_events = ClientEvents(items=request_events)
        
        response = cls._invoke_service(request)
        
        # Extrair NUNOTA e eventos da resposta
        result_nunota = -1
        response_events: Optional[List[ClientEvent]] = None
        
        if response.response_body:
            rb = response.response_body
            if hasattr(rb, "invoices") and rb.invoices:
                if hasattr(rb.invoices, "items") and rb.invoices.items:
                    # Get value from invoice
                    inv = rb.invoices.items[0]
                    if inv.unique_number:
                        result_nunota = inv.unique_number
                    elif "value" in inv.extra_data:
                        result_nunota = int(inv.extra_data["value"])
            if hasattr(rb, "client_events") and rb.client_events:
                response_events = rb.client_events.items
        
        logger.info(f"Nota faturada: NUNOTA={result_nunota}")
        return result_nunota, response_events
    
    @classmethod
    def confirm_invoice(cls, single_number: int) -> None:
        """
        Confirma uma nota fiscal.
        
        Args:
            single_number: NUNOTA da nota a confirmar
            
        Raises:
            NoItemsConfirmInvoiceException: Se a nota não tem produtos
            ConfirmInvoiceException: Se ocorrer erro na confirmação
            
        Example:
            >>> KnowServicesRequestWrapper.confirm_invoice(12345)
        """
        cls._ensure_initialized()
        logger.info(f"Confirmando nota fiscal: NUNOTA={single_number}")
        
        invoice = Invoice(unique_number=single_number)
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_CONFIRM,
            request_body=RequestBody(invoice=invoice),
        )
        
        try:
            cls._invoke_service(request)
            logger.debug(f"Nota {single_number} confirmada com sucesso")
        except SankhyaException as e:
            error_msg = str(e).lower()
            if "confirmar sem produtos" in error_msg or "sem itens" in error_msg:
                raise NoItemsConfirmInvoiceException(
                    single_number=single_number,
                    request=request,
                )
            elif "já foi confirmada" in error_msg or "já confirmada" in error_msg:
                # Ignorar silenciosamente - nota já confirmada
                logger.debug(f"Nota {single_number} já estava confirmada")
                return
            else:
                raise ConfirmInvoiceException(
                    single_number=single_number,
                    request=request,
                    inner_exception=e,
                )
    
    @classmethod
    def duplicate_invoice(
        cls,
        single_number: int,
        code_operation_type: int,
        series: Optional[int] = None,
        date_exit: Optional[datetime] = None,
        should_update_price: bool = False,
    ) -> int:
        """
        Duplica uma nota fiscal existente.
        
        Args:
            single_number: NUNOTA da nota a duplicar
            code_operation_type: Código do tipo de operação da nova nota
            series: Série da nova nota (opcional)
            date_exit: Data de saída da nova nota (opcional)
            should_update_price: Se deve atualizar os preços
            
        Returns:
            NUNOTA da nova nota duplicada
            
        Example:
            >>> new_nunota = KnowServicesRequestWrapper.duplicate_invoice(
            ...     single_number=12345,
            ...     code_operation_type=2,
            ...     should_update_price=True
            ... )
        """
        cls._ensure_initialized()
        logger.info(
            f"Duplicando nota {single_number} "
            f"(tipo operação: {code_operation_type}, série: {series}, "
            f"data saída: {date_exit}, atualizar preço: {should_update_price})"
        )
        
        # Build invoice with single_number_duplication matching .NET
        invoice = Invoice()
        invoice.extra_data["singleNumberDuplication"] = str(single_number)
        
        # Build Invoices with duplication-specific fields matching .NET:
        # - CodeOperationTypeDuplication
        # - DateExitDuplicationNullable
        # - ShouldUpdatePrice
        # - ShouldDuplicateAllItems = true
        # - Invoice (with SingleNumberDuplication)
        invoices = Invoices(items=[invoice])
        
        # Set duplication-specific fields via extra_data
        request_body = RequestBody(invoices=invoices)
        if request_body.invoices and request_body.invoices.items:
            inv = request_body.invoices.items[0]
            inv.extra_data.update({
                "codeOperationTypeDuplication": str(code_operation_type),
                "shouldUpdatePrice": "true" if should_update_price else "false",
                "shouldDuplicateAllItems": "true",
            })
            # Add date exit if provided
            if date_exit is not None:
                inv.extra_data["dateExitDuplicationNullable"] = date_exit.strftime("%d/%m/%Y")
            # Add series if provided
            if series is not None:
                inv.series = str(series)
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_DUPLICATE,
            request_body=request_body,
        )
        response = cls._invoke_service(request)
        
        # Extrair novo NUNOTA from response invoices
        new_nunota = 0
        if response.response_body:
            rb = response.response_body
            if hasattr(rb, "invoices") and rb.invoices:
                if hasattr(rb.invoices, "items") and rb.invoices.items:
                    inv = rb.invoices.items[0]
                    # Try singleNumberDuplicationDestiny from extra_data
                    if "singleNumberDuplicationDestiny" in inv.extra_data:
                        new_nunota = int(inv.extra_data["singleNumberDuplicationDestiny"])
                    elif inv.unique_number:
                        new_nunota = inv.unique_number
            elif hasattr(rb, "primary_key") and rb.primary_key:
                if hasattr(rb.primary_key, "nunota"):
                    new_nunota = rb.primary_key.nunota or 0
                elif hasattr(rb.primary_key, "values"):
                    new_nunota = rb.primary_key.values.get("NUNOTA", 0)
        
        logger.info(f"Nota duplicada: novo NUNOTA={new_nunota}")
        return new_nunota
    
    # =========================================================================
    # Invoice Status Operations
    # =========================================================================
    
    @classmethod
    def flag_invoices_as_not_pending(cls, single_numbers: List[int]) -> None:
        """
        Marca notas como não pendentes.
        
        Args:
            single_numbers: Lista de NUNOTAs a marcar
            
        Example:
            >>> KnowServicesRequestWrapper.flag_invoices_as_not_pending([123, 456, 789])
        """
        cls._ensure_initialized()
        logger.info(
            f"Marcando {len(single_numbers)} nota(s) como não pendente(s): "
            f"{single_numbers}"
        )
        
        invoices = Invoices(
            items=[Invoice(unique_number=n) for n in single_numbers]
        )
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_FLAG_AS_NOT_PENDING,
            request_body=RequestBody(invoices=invoices),
        )
        cls._invoke_service(request)
        logger.debug("Notas marcadas como não pendentes")
    
    @classmethod
    def get_invoice_accompaniments(cls, single_numbers: List[int]) -> List[Invoice]:
        """
        Obtém os acompanhamentos das notas fiscais.
        
        Args:
            single_numbers: Lista de NUNOTAs
            
        Returns:
            Lista de notas com seus acompanhamentos
            
        Example:
            >>> invoices = KnowServicesRequestWrapper.get_invoice_accompaniments([123])
            >>> for inv in invoices:
            ...     print(f"Nota {inv.unique_number}: {len(inv.accompaniments)} acompanhamentos")
        """
        cls._ensure_initialized()
        logger.info(f"Obtendo acompanhamentos de {len(single_numbers)} nota(s)")
        
        invoices = Invoices(
            items=[Invoice(unique_number=n) for n in single_numbers]
        )
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_ACCOMPANIMENTS,
            request_body=RequestBody(invoices=invoices),
        )
        response = cls._invoke_service(request)
        
        result: List[Invoice] = []
        if response.response_body:
            rb = response.response_body
            if hasattr(rb, "invoice_accompaniments") and rb.invoice_accompaniments:
                if hasattr(rb.invoice_accompaniments, "invoices"):
                    result = rb.invoice_accompaniments.invoices
        
        logger.info(f"Acompanhamentos obtidos: {len(result)} nota(s)")
        return result
    
    @classmethod
    def cancel_invoices(
        cls,
        single_numbers: List[int],
        justification: str,
    ) -> Tuple[int, List[int]]:
        """
        Cancela notas fiscais.
        
        Args:
            single_numbers: Lista de NUNOTAs a cancelar
            justification: Justificativa do cancelamento
            
        Returns:
            Tupla com (quantidade cancelada, lista de não cancelados)
            
        Example:
            >>> cancelled, not_cancelled = KnowServicesRequestWrapper.cancel_invoices(
            ...     single_numbers=[123, 456],
            ...     justification="Erro de digitação"
            ... )
            >>> print(f"Canceladas: {cancelled}, Não canceladas: {not_cancelled}")
        """
        cls._ensure_initialized()
        logger.info(
            f"Cancelando {len(single_numbers)} nota(s) "
            f"(justificativa: {justification[:50]}...)"
        )
        
        invoices = Invoices(
            items=[
                Invoice(
                    unique_number=n,
                    extra_data={"justificativa": justification}
                )
                for n in single_numbers
            ]
        )
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_CANCEL,
            request_body=RequestBody(invoices=invoices),
        )
        response = cls._invoke_service(request)
        
        total_cancelled = 0
        not_cancelled: List[int] = []
        
        if response.response_body:
            rb = response.response_body
            if hasattr(rb, "total_cancelled_invoices"):
                total_cancelled = rb.total_cancelled_invoices or 0
            if hasattr(rb, "single_numbers"):
                not_cancelled = rb.single_numbers or []
        
        logger.info(
            f"Notas canceladas: {total_cancelled}, "
            f"não canceladas: {len(not_cancelled)}"
        )
        return total_cancelled, not_cancelled
    
    @classmethod
    def bind_invoice_with_order(
        cls,
        single_number: int,
        code_partner: int,
        movement_type: MovementType,
    ) -> None:
        """
        Vincula uma nota fiscal a um pedido.
        
        Args:
            single_number: NUNOTA da nota
            code_partner: Código do parceiro
            movement_type: Tipo de movimento
            
        Example:
            >>> KnowServicesRequestWrapper.bind_invoice_with_order(
            ...     single_number=12345,
            ...     code_partner=100,
            ...     movement_type=MovementType.VENDA
            ... )
        """
        cls._ensure_initialized()
        logger.info(
            f"Vinculando nota {single_number} ao pedido "
            f"(parceiro: {code_partner}, tipo: {movement_type})"
        )
        
        invoice = Invoice(
            unique_number=single_number,
            partner_code=code_partner,
            extra_data={"tipoMov": movement_type.internal_value},
        )
        
        request = ServiceRequest(
            service=ServiceName.INVOICE_BIND_WITH_ORDER,
            request_body=RequestBody(invoice=invoice),
        )
        cls._invoke_service(request)
        logger.debug("Nota vinculada ao pedido com sucesso")
    
    # =========================================================================
    # NFe Operations
    # =========================================================================
    
    @classmethod
    def get_fiscal_invoice_authorization(cls, single_numbers: List[int]) -> None:
        """
        Busca autorização de NF-e para as notas especificadas.
        
        Args:
            single_numbers: Lista de NUNOTAs
            
        Example:
            >>> KnowServicesRequestWrapper.get_fiscal_invoice_authorization([123, 456])
        """
        cls._ensure_initialized()
        logger.info(f"Buscando autorização NF-e para {len(single_numbers)} nota(s)")
        
        invoices = Invoices(
            items=[Invoice(unique_number=n) for n in single_numbers]
        )
        
        request = ServiceRequest(
            service=ServiceName.NFE_GET_AUTHORIZATION,
            request_body=RequestBody(invoices=invoices),
        )
        cls._invoke_service(request)
        logger.debug("Autorização NF-e verificada")
    
    @classmethod
    def generate_lot(cls, single_numbers: List[int]) -> None:
        """
        Gera lote de NF-e para as notas especificadas.
        
        Args:
            single_numbers: Lista de NUNOTAs
            
        Example:
            >>> KnowServicesRequestWrapper.generate_lot([123, 456])
        """
        cls._ensure_initialized()
        logger.info(f"Gerando lote NF-e para {len(single_numbers)} nota(s)")
        
        invoices = Invoices(
            items=[Invoice(unique_number=n) for n in single_numbers]
        )
        
        request = ServiceRequest(
            service=ServiceName.NFE_GENERATE_LOT,
            request_body=RequestBody(invoices=invoices),
        )
        cls._invoke_service(request)
        logger.debug("Lote NF-e gerado")
    
    # =========================================================================
    # Financial Operations
    # =========================================================================
    
    @classmethod
    def flag_as_payments_paid(
        cls,
        financial_numbers: List[int],
        code_account: int,
    ) -> None:
        """
        Marca títulos financeiros como pagos.
        
        Args:
            financial_numbers: Lista de números financeiros (NUFIN)
            code_account: Código da conta para baixa
            
        Raises:
            MarkAsPaymentPaidException: Se ocorrer erro na baixa
            
        Example:
            >>> KnowServicesRequestWrapper.flag_as_payments_paid(
            ...     financial_numbers=[1001, 1002],
            ...     code_account=123
            ... )
        """
        cls._ensure_initialized()
        logger.info(
            f"Marcando {len(financial_numbers)} título(s) como pago(s) "
            f"(conta: {code_account})"
        )
        
        try:
            # Build LowData with all required fields matching .NET implementation:
            # FinancialNumbersList, Empresa, ContaBco, ChkReceita, ChkDespesa,
            # ChkBaixaSeparada, ChkUsarHist, ChkNossoNum, ChkVlrLiqZero,
            # RbdConcatSobreporHistFin, ChkUsaVenc, ChkSubInf,
            # TipLancRec, TopBaixaRec, TipLancDesp, TopBaixaDesp,
            # TemFiltroAntecipacaoBx, ParamImprimeBoleto
            low_data = LowData(
                data={
                    "nuFins": ",".join(str(n) for n in financial_numbers),
                    "Empresa": "1",
                    "ContaBco": str(code_account),
                    "ChkReceita": "S",
                    "ChkDespesa": "S",
                    "ChkBaixaSeparada": "S",
                    "ChkUsarHist": "N",
                    "ChkNossoNum": "N",
                    "ChkVlrLiqZero": "N",
                    "RbdConcatSobreporHistFin": "1",
                    "ChkUsaVenc": "S",
                    "ChkSubInf": "S",
                    "TipLancRec": "24",
                    "TopBaixaRec": "801",
                    "TipLancDesp": "1",
                    "TopBaixaDesp": "800",
                    "TemFiltroAntecipacaoBx": "N",
                    "ParamImprimeBoleto": "false",
                }
            )
            
            request = ServiceRequest(
                service=ServiceName.INVOICE_AUTOMATIC_LOW,
                request_body=RequestBody(low_data=low_data),
            )
            cls._invoke_service(request)
            logger.debug("Títulos marcados como pagos")
            
        except SankhyaException as e:
            raise MarkAsPaymentPaidException(
                financial_numbers=",".join(str(n) for n in financial_numbers),
                request=request,
                inner_exception=e,
            )
    
    @classmethod
    def reverse_payments(cls, financial_numbers: List[int]) -> None:
        """
        Estorna pagamentos de títulos financeiros.
        
        Args:
            financial_numbers: Lista de números financeiros (NUFIN)
            
        Example:
            >>> KnowServicesRequestWrapper.reverse_payments([1001, 1002])
        """
        cls._ensure_initialized()
        logger.info(f"Estornando {len(financial_numbers)} pagamento(s)")
        
        for nufin in financial_numbers:
            logger.debug(f"Estornando título: NUFIN={nufin}")
            
            low_data = LowData(data={"nuFin": str(nufin)})
            
            request = ServiceRequest(
                service=ServiceName.FINANCIAL_REVERSAL,
                request_body=RequestBody(low_data=low_data),
            )
            cls._invoke_service(request)
        
        logger.debug("Pagamentos estornados")
    
    @classmethod
    def unlink_shipping(cls, financial_number: int) -> None:
        """
        Desvincula remessa de um título financeiro.
        
        Args:
            financial_number: Número financeiro (NUFIN)
            
        Raises:
            UnlinkShippingException: Se ocorrer erro na desvinculação
            
        Example:
            >>> KnowServicesRequestWrapper.unlink_shipping(1001)
        """
        cls._ensure_initialized()
        logger.info(f"Desvinculando remessa do título: NUFIN={financial_number}")
        
        try:
            low_data = LowData(data={"nuFin": str(financial_number)})
            
            request = ServiceRequest(
                service=ServiceName.UNLINK_SHIPPING,
                request_body=RequestBody(low_data=low_data),
            )
            cls._invoke_service(request)
            logger.debug("Remessa desvinculada")
            
        except SankhyaException as e:
            raise UnlinkShippingException(
                financial_numbers=str(financial_number),
                request=request,
                inner_exception=e,
            )
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    @classmethod
    def open_file(cls, path: str) -> str:
        """
        Abre um arquivo do repositório e retorna sua chave.
        
        Args:
            path: Caminho do arquivo no repositório
            
        Returns:
            Chave do arquivo para download posterior
            
        Example:
            >>> key = KnowServicesRequestWrapper.open_file("/path/to/file.pdf")
            >>> file = KnowServicesRequestWrapper.get_file(key)
        """
        cls._ensure_initialized()
        logger.info(f"Abrindo arquivo: {path}")
        
        # Set path on Config matching .NET: Config = new() { Path = path }
        config = Config(path=path)
        
        request = ServiceRequest(
            service=ServiceName.FILE_OPEN,
            request_body=RequestBody(config=config),
        )
        response = cls._invoke_service(request)
        
        key = ""
        if response.response_body:
            rb = response.response_body
            if hasattr(rb, "key") and rb.key:
                key = rb.key.value or ""
        
        logger.debug(f"Arquivo aberto, chave: {key[:20]}...")
        return key
    
    @classmethod
    def delete_files(cls, paths: List[str]) -> None:
        """
        Deleta arquivos do repositório.
        
        Args:
            paths: Lista de caminhos dos arquivos a deletar
            
        Example:
            >>> KnowServicesRequestWrapper.delete_files(["/path/to/file1.pdf", "/path/to/file2.pdf"])
        """
        cls._ensure_initialized()
        logger.info(f"Deletando {len(paths)} arquivo(s)")
        
        path_objects = [Path(value=p) for p in paths]
        
        # Adicionar evento de confirmação
        confirm_event = ClientEvent(
            type="confirmation",
            code="deleteFiles",
            data={"confirmed": "true"},
        )
        
        request = ServiceRequest(
            service=ServiceName.FILE_DELETE,
            request_body=RequestBody(
                paths=Paths(items=path_objects),
                client_events=ClientEvents(items=[confirm_event]),
            ),
        )
        cls._invoke_service(request)
        logger.debug("Arquivos deletados")
    
    @classmethod
    def get_file(cls, key: str) -> ServiceFile:
        """
        Obtém um arquivo pelo sua chave.
        
        Args:
            key: Chave do arquivo retornada por open_file
            
        Returns:
            ServiceFile com os dados do arquivo
            
        Example:
            >>> file = KnowServicesRequestWrapper.get_file("ABC123KEY")
            >>> with open("local_file.pdf", "wb") as f:
            ...     f.write(file.data)
        """
        cls._ensure_initialized()
        logger.debug(f"Obtendo arquivo pela chave: {key[:20]}...")
        
        # Delegar para o contexto
        from sankhya_sdk.core.context import SankhyaContext
        
        if cls._session_token is None:
            raise RuntimeError("Token de sessão não disponível")
        
        return SankhyaContext.get_file_with_token(key, cls._session_token)
    
    @classmethod
    async def get_file_async(cls, key: str) -> ServiceFile:
        """
        Obtém um arquivo pelo sua chave de forma assíncrona.
        
        Args:
            key: Chave do arquivo retornada por open_file
            
        Returns:
            ServiceFile com os dados do arquivo
            
        Example:
            >>> file = await KnowServicesRequestWrapper.get_file_async("ABC123KEY")
        """
        cls._ensure_initialized()
        logger.debug(f"Obtendo arquivo (async) pela chave: {key[:20]}...")
        
        # Delegar para o contexto
        from sankhya_sdk.core.context import SankhyaContext
        
        if cls._session_token is None:
            raise RuntimeError("Token de sessão não disponível")
        
        return await SankhyaContext.get_file_async_with_token(key, cls._session_token)
    
    # =========================================================================
    # Image Operations
    # =========================================================================
    
    @classmethod
    def get_image(cls, entity: T) -> ServiceFile:
        """
        Obtém a imagem associada a uma entidade.
        
        Args:
            entity: Entidade com chaves primárias para identificação
            
        Returns:
            ServiceFile com os dados da imagem
            
        Raises:
            ValueError: Se entity for None
            
        Example:
            >>> product = Product(code=123)
            >>> image = KnowServicesRequestWrapper.get_image(product)
            >>> with open("product_image.jpg", "wb") as f:
            ...     f.write(image.data)
        """
        cls._ensure_initialized()
        
        if entity is None:
            raise ValueError("entity não pode ser None")
        
        entity_name = type(entity).__name__
        logger.debug(f"Obtendo imagem da entidade: {entity_name}")
        
        # Extrair chaves da entidade
        from sankhya_sdk.helpers.entity_extensions import extract_keys
        keys_dict = extract_keys(entity)
        
        # Delegar para o contexto
        if cls._context is None:
            raise RuntimeError("Contexto não disponível")
        
        return cls._context.get_image(entity_name, keys_dict)
    
    @classmethod
    async def get_image_async(cls, entity: T) -> ServiceFile:
        """
        Obtém a imagem associada a uma entidade de forma assíncrona.
        
        Args:
            entity: Entidade com chaves primárias para identificação
            
        Returns:
            ServiceFile com os dados da imagem
            
        Raises:
            ValueError: Se entity for None
            
        Example:
            >>> product = Product(code=123)
            >>> image = await KnowServicesRequestWrapper.get_image_async(product)
        """
        cls._ensure_initialized()
        
        if entity is None:
            raise ValueError("entity não pode ser None")
        
        entity_name = type(entity).__name__
        logger.debug(f"Obtendo imagem (async) da entidade: {entity_name}")
        
        # Extrair chaves da entidade
        from sankhya_sdk.helpers.entity_extensions import extract_keys
        keys_dict = extract_keys(entity)
        
        # Delegar para o contexto
        if cls._context is None:
            raise RuntimeError("Contexto não disponível")
        
        return await cls._context.get_image_async(entity_name, keys_dict)
    
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
