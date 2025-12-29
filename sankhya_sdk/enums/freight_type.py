from ._metadata import EnumMetadata, MetadataEnum


class FreightType(MetadataEnum):
    """Representa o tipo de frete."""

    COST_INSURANCE_FREIGHT = ("CostInsuranceFreight", EnumMetadata(internal_value="C", human_readable="CIF"))
    FREE_ON_BOARD = ("FreeOnBoard", EnumMetadata(internal_value="F", human_readable="FOB"))
    NO_FREIGHT = ("NoFreight", EnumMetadata(internal_value="S", human_readable="Sem Frete"))
    THIRD = ("Third", EnumMetadata(internal_value="T", human_readable="Terceiros"))
