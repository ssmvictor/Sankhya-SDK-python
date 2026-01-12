from ._metadata import EnumMetadata, MetadataEnum
from .service_category import ServiceCategory
from .service_module import ServiceModule
from .service_type import ServiceType


class ServiceName(MetadataEnum):
    """Representa os nomes dos serviços."""

    TEST = ("Test", EnumMetadata(
        internal_value="test",
        human_readable="Test",
        service_module=ServiceModule.NONE,
        service_category=ServiceCategory.NONE,
        service_type=ServiceType.NONE
    ))
    CRUD_FIND = ("CrudFind", EnumMetadata(
        internal_value="crud.find",
        human_readable="CRUD - Retrieve",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.RETRIEVE
    ))
    CRUD_REMOVE = ("CrudRemove", EnumMetadata(
        internal_value="crud.remove",
        human_readable="CRUD - Remove",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    CRUD_SAVE = ("CrudSave", EnumMetadata(
        internal_value="crud.save",
        human_readable="CRUD - Create/Update",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.TRANSACTIONAL
    ))
    CRUD_SERVICE_FIND = ("CrudServiceFind", EnumMetadata(
        internal_value="CRUDServiceProvider.loadRecords",
        human_readable="CRUD Service Provider - Retrieve",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.RETRIEVE
    ))
    CRUD_SERVICE_REMOVE = ("CrudServiceRemove", EnumMetadata(
        internal_value="CRUDServiceProvider.removeRecord",
        human_readable="CRUD Service Provider - Remove",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    CRUD_SERVICE_SAVE = ("CrudServiceSave", EnumMetadata(
        internal_value="CRUDServiceProvider.saveRecord",
        human_readable="CRUD Service Provider - Create/Update",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.TRANSACTIONAL
    ))
    LOGIN = ("Login", EnumMetadata(
        internal_value="MobileLoginSP.login",
        human_readable="Login",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.AUTHORIZATION,
        service_type=ServiceType.RETRIEVE
    ))
    LOGOUT = ("Logout", EnumMetadata(
        internal_value="MobileLoginSP.logout",
        human_readable="Logout",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.AUTHORIZATION,
        service_type=ServiceType.RETRIEVE
    ))
    NFE_GET_AUTHORIZATION = ("NfeGetAuthorization", EnumMetadata(
        internal_value="ServicosNfeSP.buscaProcessamentoLote",
        human_readable="NF-e - Get Authorization",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.FISCAL_INVOICE,
        service_type=ServiceType.RETRIEVE
    ))
    NFE_GENERATE_LOT = ("NfeGenerateLot", EnumMetadata(
        internal_value="ServicosNfeSP.gerarLote",
        human_readable="NF-e - Generate Lot",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.FISCAL_INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_INCLUDE = ("InvoiceInclude", EnumMetadata(
        internal_value="CACSP.incluirNota",
        human_readable="Include Invoice",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.TRANSACTIONAL
    ))
    INVOICE_HEADER_INCLUDE = ("InvoiceHeaderInclude", EnumMetadata(
        internal_value="CACSP.incluirAlterarCabecalhoNota",
        human_readable="Include/Change Invoice Header",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.TRANSACTIONAL
    ))
    INVOICE_ITEM_INCLUDE = ("InvoiceItemInclude", EnumMetadata(
        internal_value="CACSP.incluirAlterarItemNota",
        human_readable="Include/Change Invoice Item",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.TRANSACTIONAL
    ))
    INVOICE_BILL = ("InvoiceBill", EnumMetadata(
        internal_value="SelecaoDocumentoSP.faturar",
        human_readable="Bill Invoice",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_ACCOMPANIMENTS = ("InvoiceAccompaniments", EnumMetadata(
        internal_value="ServicosNfeSP.getAcompanhamentosNota",
        human_readable="Invoice Accompaniment",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.RETRIEVE
    ))
    INVOICE_AUTOMATIC_LOW = ("InvoiceAutomaticLow", EnumMetadata(
        internal_value="BaixaAutomaticaSP.baixar",
        human_readable="Automatic Low",
        service_module=ServiceModule.MGEFIN,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_CONFIRM = ("InvoiceConfirm", EnumMetadata(
        internal_value="CACSP.confirmarNota",
        human_readable="Invoice Confirmation",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_CANCEL = ("InvoiceCancel", EnumMetadata(
        internal_value="CACSP.cancelarNota",
        human_readable="Invoice Cancellation",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_DUPLICATE = ("InvoiceDuplicate", EnumMetadata(
        internal_value="CACSP.duplicarNota",
        human_readable="Invoice Duplication",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.TRANSACTIONAL
    ))
    INVOICE_REMOVE = ("InvoiceRemove", EnumMetadata(
        internal_value="CACSP.excluirNotas",
        human_readable="Exclude/Remove Invoice",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_ITEM_REMOVE = ("InvoiceItemRemove", EnumMetadata(
        internal_value="CACSP.excluirItemNota",
        human_readable="Exclude/Remove Invoice Item",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_BIND_WITH_ORDER = ("InvoiceBindWithOrder", EnumMetadata(
        internal_value="CACSP.ligarPedidoNota",
        human_readable="Bind Invoice With Order",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    INVOICE_FLAG_AS_NOT_PENDING = ("InvoiceFlagAsNotPending", EnumMetadata(
        internal_value="CACSP.marcarPedidosComoNaoPendentes",
        human_readable="Flag orders as not pending",
        service_module=ServiceModule.MGECOM,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    FINANCIAL_REVERSAL = ("FinancialReversal", EnumMetadata(
        internal_value="BaixaFinanceiroSP.estornarTitulo",
        human_readable="Financial Reversal",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    WARNING_RECEIVE = ("WarningReceive", EnumMetadata(
        internal_value="AvisoSistemaSP.getNovosAvisos",
        human_readable="Receive Warnings",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.COMMUNICATION,
        service_type=ServiceType.RETRIEVE
    ))
    WARNING_SEND = ("WarningSend", EnumMetadata(
        internal_value="AvisoSistemaSP.enviarAviso",
        human_readable="Send Warning",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.COMMUNICATION,
        service_type=ServiceType.TRANSACTIONAL
    ))
    MESSAGE_SEND = ("MessageSend", EnumMetadata(
        internal_value="AvisoSistemaSP.enviarMensagem",
        human_readable="Send Message",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.COMMUNICATION,
        service_type=ServiceType.TRANSACTIONAL
    ))
    FILE_OPEN = ("FileOpen", EnumMetadata(
        internal_value="RepositorioArquivoSP.abreArquivo",
        human_readable="File Repository - Open File",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.FILE,
        service_type=ServiceType.RETRIEVE
    ))
    FILE_DELETE = ("FileDelete", EnumMetadata(
        internal_value="ImportacaoImagemSP.deletaArquivos",
        human_readable="File Repository - Delete File",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.FILE,
        service_type=ServiceType.NON_TRANSACTIONAL
    ))
    SESSION_GET_ALL = ("SessionGetAll", EnumMetadata(
        internal_value="SessionManagerSP.getCoreSessions",
        human_readable="Get Core Sessions",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.AUTHORIZATION,
        service_type=ServiceType.RETRIEVE
    ))
    SESSION_KILL = ("SessionKill", EnumMetadata(
        internal_value="SessionManagerSP.killSession",
        human_readable="Kill Session",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.AUTHORIZATION,
        service_type=ServiceType.RETRIEVE
    ))
    UNLINK_SHIPPING = ("UnlinkShipping", EnumMetadata(
        internal_value="MovimentacaoFinanceiraSP.desvincularRemessa",
        human_readable="Unlink shipping",
        service_module=ServiceModule.MGEFIN,
        service_category=ServiceCategory.INVOICE,
        service_type=ServiceType.TRANSACTIONAL
    ))
    DB_EXPLORER_EXECUTE_QUERY = ("DbExplorerExecuteQuery", EnumMetadata(
        internal_value="DbExplorerSP.executeQuery",
        human_readable="Execute SQL Query",
        service_module=ServiceModule.MGE,
        service_category=ServiceCategory.CRUD,
        service_type=ServiceType.RETRIEVE
    ))

    @property
    def service_module(self) -> ServiceModule:
        """Retorna o módulo do serviço."""
        from typing import cast
        return cast(ServiceModule, self.metadata.service_module)

    @property
    def service_category(self) -> ServiceCategory:
        """Retorna a categoria do serviço."""
        from typing import cast
        return cast(ServiceCategory, self.metadata.service_category)

    @property
    def service_type(self) -> ServiceType:
        """Retorna o tipo do serviço."""
        from typing import cast
        return cast(ServiceType, self.metadata.service_type)
