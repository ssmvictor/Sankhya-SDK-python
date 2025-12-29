from ._metadata import EnumMetadata, MetadataEnum


class ServiceRequestType(MetadataEnum):
    """Representa o tipo de requisição de serviço."""

    DEFAULT = ("Default", EnumMetadata(human_readable="Default"))
    SIMPLE_CRUD = ("SimpleCrud", EnumMetadata(human_readable="Simple CRUD"))
    PAGED_CRUD = ("PagedCrud", EnumMetadata(human_readable="Paged CRUD (retrieve)"))
    QUERYABLE_CRUD = ("QueryableCrud", EnumMetadata(human_readable="Queryable CRUD"))
    ON_DEMAND_CRUD = ("OnDemandCrud", EnumMetadata(human_readable="On demand CRUD (Create, Update, Delete)"))
    KNOW_SERVICES = ("KnowServices", EnumMetadata(human_readable="Know services"))
