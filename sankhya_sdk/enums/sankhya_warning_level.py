from ._metadata import EnumMetadata, MetadataEnum


class SankhyaWarningLevel(MetadataEnum):
    """Representa os níveis de alerta no Sankhya."""

    URGENT = ("Urgent", EnumMetadata(internal_value="0", human_readable="Urgente"))
    ERROR = ("Error", EnumMetadata(internal_value="1", human_readable="Erro"))
    WARNING = ("Warning", EnumMetadata(internal_value="2", human_readable="Alerta"))
    INFORMATION = ("Information", EnumMetadata(internal_value="3", human_readable="Informação"))
