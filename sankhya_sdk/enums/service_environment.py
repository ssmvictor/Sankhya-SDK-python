from ._metadata import EnumMetadata, MetadataEnum


class ServiceEnvironment(MetadataEnum):
    """Representa os ambientes de serviço."""

    NONE = ("None", EnumMetadata(internal_value="0", human_readable="Nenhum"))
    PRODUCTION = ("Production", EnumMetadata(internal_value="8180", human_readable="Produção"))
    SANDBOX = ("Sandbox", EnumMetadata(internal_value="8280", human_readable="Sandbox"))
    TRAINING = ("Training", EnumMetadata(internal_value="8380", human_readable="Treinamento"))
