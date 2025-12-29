from ._metadata import EnumMetadata, MetadataEnum


class ServiceModule(MetadataEnum):
    """Representa os módulos de serviço."""

    NONE = ("None", EnumMetadata(internal_value="none", human_readable="Test"))
    MGE = ("Mge", EnumMetadata(internal_value="mge", human_readable="MGE"))
    MGECOM = ("Mgecom", EnumMetadata(internal_value="mgecom", human_readable="MGECOM"))
    MGEFIN = ("Mgefin", EnumMetadata(internal_value="mgefin", human_readable="MGEFIN"))
