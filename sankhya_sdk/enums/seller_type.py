from ._metadata import EnumMetadata, MetadataEnum


class SellerType(MetadataEnum):
    """Representa o tipo de um vendedor."""

    NONE = ("None", EnumMetadata(internal_value="0", human_readable="Nenhum"))
    BUYER = ("Buyer", EnumMetadata(internal_value="C", human_readable="Comprador"))
    SELLER = ("Seller", EnumMetadata(internal_value="V", human_readable="Vendedor"))
    SUPERVISOR = ("Supervisor", EnumMetadata(internal_value="S", human_readable="Supervisor"))
    MANAGER = ("Manager", EnumMetadata(internal_value="G", human_readable="Gerente"))
    PERFORMER = ("Performer", EnumMetadata(internal_value="E", human_readable="Executante"))
    REPRESENTATIVE = ("Representative", EnumMetadata(internal_value="R", human_readable="Representante"))
    TECHNICIAN = ("Technician", EnumMetadata(internal_value="T", human_readable="Técnico"))
