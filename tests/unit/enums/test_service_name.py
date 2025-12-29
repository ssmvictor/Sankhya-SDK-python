import pytest
from sankhya_sdk.enums import (
    ServiceCategory,
    ServiceModule,
    ServiceName,
    ServiceType,
)


@pytest.mark.parametrize(
    "enum_member, expected_internal, expected_human, expected_module, expected_category, expected_type",
    [
        (ServiceName.TEST, "test", "Test", ServiceModule.NONE, ServiceCategory.NONE, ServiceType.NONE),
        (ServiceName.CRUD_FIND, "crud.find", "CRUD - Retrieve", ServiceModule.MGE, ServiceCategory.CRUD, ServiceType.RETRIEVE),
        (ServiceName.CRUD_REMOVE, "crud.remove", "CRUD - Remove", ServiceModule.MGE, ServiceCategory.CRUD, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.CRUD_SAVE, "crud.save", "CRUD - Create/Update", ServiceModule.MGE, ServiceCategory.CRUD, ServiceType.TRANSACTIONAL),
        (ServiceName.CRUD_SERVICE_FIND, "CRUDServiceProvider.loadRecords", "CRUD Service Provider - Retrieve", ServiceModule.MGE, ServiceCategory.CRUD, ServiceType.RETRIEVE),
        (ServiceName.CRUD_SERVICE_REMOVE, "CRUDServiceProvider.removeRecord", "CRUD Service Provider - Remove", ServiceModule.MGE, ServiceCategory.CRUD, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.CRUD_SERVICE_SAVE, "CRUDServiceProvider.saveRecord", "CRUD Service Provider - Create/Update", ServiceModule.MGE, ServiceCategory.CRUD, ServiceType.TRANSACTIONAL),
        (ServiceName.LOGIN, "MobileLoginSP.login", "Login", ServiceModule.MGE, ServiceCategory.AUTHORIZATION, ServiceType.RETRIEVE),
        (ServiceName.LOGOUT, "MobileLoginSP.logout", "Logout", ServiceModule.MGE, ServiceCategory.AUTHORIZATION, ServiceType.RETRIEVE),
        (ServiceName.NFE_GET_AUTHORIZATION, "ServicosNfeSP.buscaProcessamentoLote", "NF-e - Get Authorization", ServiceModule.MGECOM, ServiceCategory.FISCAL_INVOICE, ServiceType.RETRIEVE),
        (ServiceName.NFE_GENERATE_LOT, "ServicosNfeSP.gerarLote", "NF-e - Generate Lot", ServiceModule.MGECOM, ServiceCategory.FISCAL_INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_INCLUDE, "CACSP.incluirNota", "Include Invoice", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.TRANSACTIONAL),
        (ServiceName.INVOICE_HEADER_INCLUDE, "CACSP.incluirAlterarCabecalhoNota", "Include/Change Invoice Header", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.TRANSACTIONAL),
        (ServiceName.INVOICE_ITEM_INCLUDE, "CACSP.incluirAlterarItemNota", "Include/Change Invoice Item", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.TRANSACTIONAL),
        (ServiceName.INVOICE_BILL, "SelecaoDocumentoSP.faturar", "Bill Invoice", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_ACCOMPANIMENTS, "ServicosNfeSP.getAcompanhamentosNota", "Invoice Accompaniment", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.RETRIEVE),
        (ServiceName.INVOICE_AUTOMATIC_LOW, "BaixaAutomaticaSP.baixar", "Automatic Low", ServiceModule.MGEFIN, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_CONFIRM, "CACSP.confirmarNota", "Invoice Confirmation", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_CANCEL, "CACSP.cancelarNota", "Invoice Cancellation", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_DUPLICATE, "CACSP.duplicarNota", "Invoice Duplication", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.TRANSACTIONAL),
        (ServiceName.INVOICE_REMOVE, "CACSP.excluirNotas", "Exclude/Remove Invoice", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_ITEM_REMOVE, "CACSP.excluirItemNota", "Exclude/Remove Invoice Item", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_BIND_WITH_ORDER, "CACSP.ligarPedidoNota", "Bind Invoice With Order", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.INVOICE_FLAG_AS_NOT_PENDING, "CACSP.marcarPedidosComoNaoPendentes", "Flag orders as not pending", ServiceModule.MGECOM, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.FINANCIAL_REVERSAL, "BaixaFinanceiroSP.estornarTitulo", "Financial Reversal", ServiceModule.MGE, ServiceCategory.INVOICE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.WARNING_RECEIVE, "AvisoSistemaSP.getNovosAvisos", "Receive Warnings", ServiceModule.MGE, ServiceCategory.COMMUNICATION, ServiceType.RETRIEVE),
        (ServiceName.WARNING_SEND, "AvisoSistemaSP.enviarAviso", "Send Warning", ServiceModule.MGE, ServiceCategory.COMMUNICATION, ServiceType.TRANSACTIONAL),
        (ServiceName.MESSAGE_SEND, "AvisoSistemaSP.enviarMensagem", "Send Message", ServiceModule.MGE, ServiceCategory.COMMUNICATION, ServiceType.TRANSACTIONAL),
        (ServiceName.FILE_OPEN, "RepositorioArquivoSP.abreArquivo", "File Repository - Open File", ServiceModule.MGE, ServiceCategory.FILE, ServiceType.RETRIEVE),
        (ServiceName.FILE_DELETE, "ImportacaoImagemSP.deletaArquivos", "File Repository - Delete File", ServiceModule.MGE, ServiceCategory.FILE, ServiceType.NON_TRANSACTIONAL),
        (ServiceName.SESSION_GET_ALL, "SessionManagerSP.getCoreSessions", "Get Core Sessions", ServiceModule.MGE, ServiceCategory.AUTHORIZATION, ServiceType.RETRIEVE),
        (ServiceName.SESSION_KILL, "SessionManagerSP.killSession", "Kill Session", ServiceModule.MGE, ServiceCategory.AUTHORIZATION, ServiceType.RETRIEVE),
        (ServiceName.UNLINK_SHIPPING, "MovimentacaoFinanceiraSP.desvincularRemessa", "Unlink shipping", ServiceModule.MGEFIN, ServiceCategory.INVOICE, ServiceType.TRANSACTIONAL),
    ],
)
def test_service_name_metadata(enum_member, expected_internal, expected_human, expected_module, expected_category, expected_type):
    assert enum_member.internal_value == expected_internal
    assert enum_member.human_readable == expected_human
    assert enum_member.service_module == expected_module
    assert enum_member.service_category == expected_category
    assert enum_member.service_type == expected_type
    assert str(enum_member) == expected_internal