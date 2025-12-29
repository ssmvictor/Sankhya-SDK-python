from ._metadata import EnumMetadata, MetadataEnum


class SankhyaWarningType(MetadataEnum):
    """Representa os tipos de alerta no Sankhya."""

    NONE = ("None", EnumMetadata(internal_value="0", human_readable="Nenhum"))
    USER = ("User", EnumMetadata(internal_value="usuario", human_readable="Usuário"))
    GROUP = ("Group", EnumMetadata(internal_value="grupo", human_readable="Grupo"))
