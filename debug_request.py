
import logging
from sankhya_sdk.config import settings
from sankhya_sdk.core.context import SankhyaContext
from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.models.service import ServiceRequest, RequestBody, DataSet, Entity, Field, LiteralCriteria
from lxml import etree

# Setup logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

SANKHYA_HOST = settings.url
SANKHYA_PORT = settings.port
SANKHYA_USERNAME = settings.username
SANKHYA_PASSWORD = settings.password

def debug_request():
    from sankhya_sdk.request_wrappers import PagedRequestWrapper
    
    ctx = SankhyaContext(
        host=SANKHYA_HOST,
        port=SANKHYA_PORT,
        username=SANKHYA_USERNAME,
        password=SANKHYA_PASSWORD,
    )

    try:
        print(f"Token: {ctx.token}")
        
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body = RequestBody(
            data_set=DataSet(
                root_entity="Parceiro",
                include_presentation=True,
                entity=Entity(
                    path="",
                    fields=[
                        Field(name="CODPARC"),
                        Field(name="NOMEPARC"),
                        Field(name="ATIVO")
                    ]
                ),
                criteria=LiteralCriteria(expression="ATIVO = 'S'")
            )
        )

        # Execute request
        response = ctx.service_invoker(request)
        
        print("\n=== RESPONSE STATUS ===")
        print(f"Success: {response.is_success}")
        print(f"Status: {response.status}")
        
        if response.response_body:
            print("\n=== ENTITIES INSPECTION ===")
            entities = response.entities
            print(f"Count: {len(entities)}")
            if entities:
                first = entities[0]
                print(f"First entity type: {type(first)}")
                print(f"First entity content: {first}")
                import inspect
                print(f"MRO: {inspect.getmro(type(first))}")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ctx.dispose()

if __name__ == "__main__":
    debug_request()
