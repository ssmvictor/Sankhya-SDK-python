from ._metadata import EnumMetadata, MetadataEnum


class TradingSubType(MetadataEnum):
    """Representa os subtipos de negociação."""

    NONE = ("None", EnumMetadata(internal_value="0", human_readable="Nenhum"))
    IN_CASH = ("InCash", EnumMetadata(internal_value="1", human_readable="A vista"))
    DEFERRED = ("Deferred", EnumMetadata(internal_value="2", human_readable="A prazo"))
    PARCELED_OUT = ("ParceledOut", EnumMetadata(internal_value="3", human_readable="Parcelada"))
    POSTDATED_CHECK = ("PostdatedCheck", EnumMetadata(internal_value="4", human_readable="Cheque pré-datado"))
    INSTALLMENT_CREDIT = ("InstallmentCredit", EnumMetadata(internal_value="5", human_readable="Crediário"))
    FINANCIAL = ("Financial", EnumMetadata(internal_value="6", human_readable="Financeira"))
    CREDIT_CARD = ("CreditCard", EnumMetadata(internal_value="7", human_readable="Cartão de crédito"))
    DEBIT_CARD = ("DebitCard", EnumMetadata(internal_value="8", human_readable="Cartão de débito"))
