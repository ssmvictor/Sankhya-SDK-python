from ._metadata import EnumMetadata, MetadataEnum


class MovementType(MetadataEnum):
    """Representa o tipo de movimento."""

    NONE = ("None", EnumMetadata(internal_value="", human_readable="Nenhum"))
    DEPOSIT = ("Deposit", EnumMetadata(internal_value="1", human_readable="NF Depósito"))
    WARRANT = ("Warrant", EnumMetadata(internal_value="2", human_readable="PD Devol. / Procuração / Warrant"))
    OUTPUT = ("Output", EnumMetadata(internal_value="3", human_readable="Saídas"))
    BILLING = ("Billing", EnumMetadata(internal_value="4", human_readable="Faturamento"))
    RD8 = ("Rd8", EnumMetadata(internal_value="8", human_readable="RD8"))
    BANK_MOVEMENT = ("BankMovement", EnumMetadata(internal_value="B", human_readable="Movimento bancário"))
    PURCHASE = ("Purchase", EnumMetadata(internal_value="C", human_readable="Compra"))
    SALES_RETURN = ("SalesReturn", EnumMetadata(internal_value="D", human_readable="Devolução de venda"))
    PURCHASE_RETURN = ("PurchaseReturn", EnumMetadata(internal_value="E", human_readable="Devolução de compra"))
    PRODUCTION = ("Production", EnumMetadata(internal_value="F", human_readable="Produção"))
    PAYMENT = ("Payment", EnumMetadata(internal_value="G", human_readable="Pagamento"))
    FINANCIAL = ("Financial", EnumMetadata(internal_value="I", human_readable="Financeiro"))
    REQUEST_ORDER = ("RequestOrder", EnumMetadata(internal_value="J", human_readable="Pedido de Requisição"))
    TRANSFER_ORDER = ("TransferOrder", EnumMetadata(internal_value="K", human_readable="Pedido de Transferência"))
    REQUEST_RETURN = ("RequestReturn", EnumMetadata(internal_value="L", human_readable="Devolução de Requisição"))
    TRANSFER_RETURN = ("TransferReturn", EnumMetadata(internal_value="M", human_readable="Devolução de Transferência"))
    INPUT = ("Input", EnumMetadata(internal_value="N", human_readable="Entradas"))
    PURCHASE_ORDER = ("PurchaseOrder", EnumMetadata(internal_value="O", human_readable="Pedido de compra"))
    SALES_ORDER = ("SalesOrder", EnumMetadata(internal_value="P", human_readable="Pedido de venda"))
    REQUEST = ("Request", EnumMetadata(internal_value="Q", human_readable="Requisição"))
    RECEIPT = ("Receipt", EnumMetadata(internal_value="R", human_readable="Recebimento"))
    TRANSFER = ("Transfer", EnumMetadata(internal_value="T", human_readable="Transferência"))
    SALES = ("Sales", EnumMetadata(internal_value="V", human_readable="Venda"))
    MODEL = ("Model", EnumMetadata(internal_value="Z", human_readable="Modelo"))
