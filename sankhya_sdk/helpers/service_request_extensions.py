# -*- coding: utf-8 -*-
"""
Extensões para ServiceRequest.

Fornece métodos para resolver entidades em requisições de serviço,
construindo automaticamente o XML de requisição baseado em metadados.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/ServiceRequestExtensions.cs
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.enums.reference_level import ReferenceLevel
from sankhya_sdk.exceptions import (
    InvalidServiceRequestOperationException,
    TooInnerLevelsException,
)

if TYPE_CHECKING:
    from sankhya_sdk.models.base import EntityBase
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from .entity_query_options import EntityQueryOptions
    from .filter_expression import IFilterExpression

# TypeVar para entidades genéricas
T = TypeVar("T", bound="EntityBase")


# Padrões regex para campos de referência
REFERENCE_FIELDS_FIRST_LEVEL_PATTERN = re.compile(
    r"^(?P<entity>\w+)_(?P<field>\w+)$"
)

REFERENCE_FIELDS_SECOND_LEVEL_PATTERN = re.compile(
    r"^(?P<parentEntity>\w+)_(?P<entity>\w+)_(?P<field>\w+)$"
)


class ParsePropertyModel:
    """Modelo interno para parsing de propriedades."""
    
    def __init__(self):
        self.property_name: str = ""
        self.is_ignored: bool = False
        self.is_entity_key: bool = False
        self.is_entity_reference: bool = False
        self.is_entity_reference_inline: bool = False
        self.ignore_entity_reference_inline: bool = False
        self.custom_relation_name: str = ""
        self.is_criteria: bool = False
        self.custom_data: Optional[Any] = None


class EntityResolverResult:
    """Resultado da resolução de uma entidade."""
    
    def __init__(self, name: str):
        self.name = name
        self.fields: List[Dict[str, str]] = []
        self.keys: List[Dict[str, Any]] = []
        self.criteria: List[Dict[str, Any]] = []
        self.field_values: List[Dict[str, Any]] = []
        self.references: Dict[str, List[Dict[str, str]]] = {}
        self.literal_criteria: str = ""


class ServiceRequestExtensions:
    """
    Extensões para resolver entidades em requisições de serviço.
    
    Fornece métodos estáticos para construir requisições de serviço
    baseado em metadados de entidades.
    
    Example:
        >>> request = ServiceRequest(ServiceName.CRUD_FIND)
        >>> ServiceRequestExtensions.resolve(request, Partner)
    """

    @staticmethod
    def _get_unix_timestamp() -> str:
        """Retorna timestamp Unix atual como string."""
        return str(int(datetime.now().timestamp()))

    @staticmethod
    def _parse_properties(
        request: "ServiceRequest",
        criteria: T,
        max_level: ReferenceLevel,
        current_level: ReferenceLevel = ReferenceLevel.NONE,
    ) -> EntityResolverResult:
        """
        Faz o parsing recursivo das propriedades de uma entidade.
        
        Args:
            request: Requisição de serviço
            criteria: Entidade com critérios
            max_level: Nível máximo de referências
            current_level: Nível atual de recursão
            
        Returns:
            EntityResolverResult com campos e critérios extraídos
        """
        from sankhya_sdk.attributes.reflection import (
            get_entity_name,
            get_field_metadata,
        )
        
        entity_type = type(criteria)
        entity_name = get_entity_name(entity_type)
        
        # Verifica profundidade máxima
        if max_level == ReferenceLevel.FIFTH:
            raise TooInnerLevelsException(entity_name)
        
        result = EntityResolverResult(entity_name)
        ignored_fields: List[str] = []
        
        for field_name, field_info in entity_type.model_fields.items():
            ServiceRequestExtensions._parse_property(
                request,
                criteria,
                max_level,
                current_level,
                field_name,
                field_info,
                ignored_fields,
                result,
                entity_type,
                entity_name,
            )
        
        return result

    @staticmethod
    def _parse_property(
        request: "ServiceRequest",
        criteria_entity: T,
        max_level: ReferenceLevel,
        current_level: ReferenceLevel,
        field_name: str,
        field_info: Any,
        ignored_fields: List[str],
        result: EntityResolverResult,
        entity_type: Type[T],
        entity_name: str,
    ) -> None:
        """
        Processa uma única propriedade da entidade.
        
        Args:
            request: Requisição de serviço
            criteria_entity: Entidade com critérios
            max_level: Nível máximo de referências
            current_level: Nível atual
            field_name: Nome do campo
            field_info: Informações do campo Pydantic
            ignored_fields: Lista de campos ignorados
            result: Resultado acumulado
            entity_type: Tipo da entidade
            entity_name: Nome da entidade
        """
        from sankhya_sdk.attributes.reflection import get_field_metadata
        
        model = ParsePropertyModel()
        metadata = get_field_metadata(field_info)
        
        # Parse custom attributes
        ServiceRequestExtensions._parse_custom_attributes(
            field_name, metadata, model
        )
        
        # Verifica se deve ignorar
        if ServiceRequestExtensions._check_if_element_is_ignored(
            field_name, ignored_fields, model
        ):
            return
        
        # Detecta referências inline
        if (
            not model.is_entity_reference
            and not model.ignore_entity_reference_inline
        ):
            if (
                REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(model.property_name)
                or REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(model.property_name)
            ):
                model.is_entity_reference_inline = True
        
        # Processa a propriedade
        ServiceRequestExtensions._process_parse(
            request,
            criteria_entity,
            max_level,
            current_level,
            field_name,
            field_info,
            result,
            entity_type,
            entity_name,
            model,
        )

    @staticmethod
    def _parse_custom_attributes(
        field_name: str,
        metadata: Any,
        model: ParsePropertyModel,
    ) -> None:
        """
        Extrai atributos customizados do campo.
        
        Args:
            field_name: Nome do campo
            metadata: Metadados do campo
            model: Modelo para preencher
        """
        model.property_name = metadata.element_name or field_name
        model.is_ignored = metadata.is_ignored
        model.is_entity_key = metadata.is_key
        model.is_entity_reference = metadata.is_reference
        model.custom_relation_name = metadata.custom_relation_name or ""
        model.custom_data = metadata.custom_data

    @staticmethod
    def _check_if_element_is_ignored(
        field_name: str,
        ignored_fields: List[str],
        model: ParsePropertyModel,
    ) -> bool:
        """
        Verifica se o elemento deve ser ignorado.
        
        Args:
            field_name: Nome do campo
            ignored_fields: Lista de campos ignorados
            model: Modelo com flags
            
        Returns:
            True se deve ignorar
        """
        if model.is_ignored:
            ignored_fields.append(model.property_name)
            return True
        
        if model.property_name.lower() in [f.lower() for f in ignored_fields]:
            if not field_name.endswith("Internal"):
                return True
        
        return False

    @staticmethod
    def _process_parse(
        request: "ServiceRequest",
        criteria_entity: T,
        max_level: ReferenceLevel,
        current_level: ReferenceLevel,
        field_name: str,
        field_info: Any,
        result: EntityResolverResult,
        entity_type: Type[T],
        entity_name: str,
        model: ParsePropertyModel,
    ) -> None:
        """
        Processa o parsing baseado no tipo de campo.
        
        Args:
            request: Requisição de serviço
            criteria_entity: Entidade com critérios
            max_level: Nível máximo
            current_level: Nível atual
            field_name: Nome do campo
            field_info: Informações do campo
            result: Resultado acumulado
            entity_type: Tipo da entidade
            entity_name: Nome da entidade
            model: Modelo de parsing
        """
        if not model.is_entity_reference and not model.is_entity_reference_inline:
            ServiceRequestExtensions._process_fields_and_criteria(
                request,
                criteria_entity,
                current_level,
                field_name,
                field_info,
                result,
                entity_type,
                entity_name,
                model,
            )
        elif model.is_entity_reference_inline:
            ServiceRequestExtensions._process_entity_reference_inline(
                result, entity_type, entity_name, model
            )
        else:
            ServiceRequestExtensions._process_entity_reference(
                request,
                criteria_entity,
                max_level,
                current_level,
                field_name,
                field_info,
                result,
                model,
            )

    @staticmethod
    def _process_fields_and_criteria(
        request: "ServiceRequest",
        criteria_entity: T,
        current_level: ReferenceLevel,
        field_name: str,
        field_info: Any,
        result: EntityResolverResult,
        entity_type: Type[T],
        entity_name: str,
        model: ParsePropertyModel,
    ) -> None:
        """
        Processa campos e critérios de busca.
        
        Args:
            request: Requisição de serviço
            criteria_entity: Entidade com critérios
            current_level: Nível atual
            field_name: Nome do campo
            field_info: Informações do campo
            result: Resultado acumulado
            entity_type: Tipo da entidade
            entity_name: Nome da entidade
            model: Modelo de parsing
        """
        result.fields.append({"name": model.property_name})
        
        # Verifica se deve serializar
        if hasattr(criteria_entity, "should_serialize_field"):
            model.is_criteria = criteria_entity.should_serialize_field(field_name)
        
        # Se não é critério e não é chave em nível raiz, retorna
        if (
            not model.is_criteria
            and (
                not model.is_entity_key
                or current_level != ReferenceLevel.NONE
                or request.service in [ServiceName.CRUD_SAVE, ServiceName.CRUD_SERVICE_SAVE]
            )
        ):
            return
        
        # Obtém valor
        value = getattr(criteria_entity, field_name, None)
        if value is None:
            return
        
        # Converte para string
        str_value = str(value)
        
        # Aplica max_length
        if model.custom_data and hasattr(model.custom_data, "max_length"):
            max_len = model.custom_data.max_length
            if max_len and max_len > 0 and len(str_value) > max_len:
                str_value = str_value[:max_len]
        
        # Adiciona à lista apropriada
        if model.is_entity_key:
            result.keys.append({"name": model.property_name, "value": str_value})
        
        if model.is_criteria:
            result.criteria.append({"name": model.property_name, "value": str_value})
            
            # Constrói literal criteria
            is_numeric = isinstance(value, (int, float))
            quote = "" if is_numeric else "'"
            condition = f"{model.property_name} = {quote}{str_value}{quote}"
            
            if result.literal_criteria:
                result.literal_criteria += f" AND {condition}"
            else:
                result.literal_criteria = condition
        
        result.field_values.append({"name": model.property_name, "value": str_value})

    @staticmethod
    def _process_entity_reference_inline(
        result: EntityResolverResult,
        entity_type: Type[T],
        entity_name: str,
        model: ParsePropertyModel,
    ) -> None:
        """
        Processa referências inline (convenção de nome).
        
        Args:
            result: Resultado acumulado
            entity_type: Tipo da entidade
            entity_name: Nome da entidade
            model: Modelo de parsing
        """
        second_level = REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(model.property_name)
        
        if second_level:
            match = second_level
            ref_entity = f"{match.group('parentEntity')}.{match.group('entity')}"
            ref_field = {"name": match.group("field")}
        else:
            match = REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(model.property_name)
            if not match:
                return
            ref_entity = match.group("entity")
            ref_field = {"name": match.group("field")}
        
        if ref_entity in result.references:
            result.references[ref_entity].append(ref_field)
        else:
            result.references[ref_entity] = [ref_field]

    @staticmethod
    def _process_entity_reference(
        request: "ServiceRequest",
        criteria_entity: T,
        max_level: ReferenceLevel,
        current_level: ReferenceLevel,
        field_name: str,
        field_info: Any,
        result: EntityResolverResult,
        model: ParsePropertyModel,
    ) -> None:
        """
        Processa referências de entidade aninhadas.
        
        Args:
            request: Requisição de serviço
            criteria_entity: Entidade com critérios
            max_level: Nível máximo
            current_level: Nível atual
            field_name: Nome do campo
            field_info: Informações do campo
            result: Resultado acumulado
            model: Modelo de parsing
        """
        from sankhya_sdk.attributes.reflection import get_entity_name
        
        # Verifica profundidade
        current_int = _reference_level_to_int(current_level)
        max_int = _reference_level_to_int(max_level)
        
        if max_int <= current_int:
            return
        
        # Obtém valor da referência
        inner_value = getattr(criteria_entity, field_name, None)
        if inner_value is None:
            return
        
        inner_type = type(inner_value)
        inner_level = _int_to_reference_level(current_int + 1)
        
        # Parse recursivo
        inner_result = ServiceRequestExtensions._parse_properties(
            request, inner_value, max_level, inner_level
        )
        
        # Determina nome da referência
        inner_name = model.custom_relation_name or get_entity_name(inner_type)
        
        # Adiciona campos às referências
        for inner_field in inner_result.fields:
            if inner_name in result.references:
                result.references[inner_name].append(inner_field)
            else:
                result.references[inner_name] = [inner_field]
        
        # Adiciona referências aninhadas
        for ref_key, ref_fields in inner_result.references.items():
            if ref_key.lower() == inner_name.lower():
                continue
            
            nested_ref = f"{inner_name}.{ref_key}"
            
            if nested_ref in result.references:
                result.references[nested_ref].extend(ref_fields)
            else:
                result.references[nested_ref] = ref_fields
        
        # Adiciona critérios aninhados
        for crit in inner_result.criteria:
            result.criteria.append({
                "name": f"{inner_name}->{crit['name']}",
                "value": crit["value"],
            })

    @staticmethod
    def resolve_generic(
        request: "ServiceRequest",
        entity_type: Type[T],
    ) -> None:
        """
        Resolve uma requisição baseado apenas no tipo da entidade.
        
        Cria uma instância vazia da entidade e configura a requisição
        para buscar todos os campos.
        
        Args:
            request: Requisição a configurar
            entity_type: Tipo da entidade
            
        Raises:
            InvalidServiceRequestOperationException: Se o serviço não for suportado
        """
        if request.service not in [ServiceName.CRUD_FIND, ServiceName.CRUD_SERVICE_FIND]:
            raise InvalidServiceRequestOperationException(service=request.service)
        
        criteria = entity_type()
        result = ServiceRequestExtensions._parse_properties(
            request, criteria, ReferenceLevel.THIRD
        )
        
        ServiceRequestExtensions._apply_result_to_request(request, result)

    @staticmethod
    def resolve_with_entity(
        request: "ServiceRequest",
        criteria: T,
        max_reference_level: ReferenceLevel = ReferenceLevel.FOURTH,
    ) -> None:
        """
        Resolve uma requisição baseado em uma entidade com critérios.
        
        Args:
            request: Requisição a configurar
            criteria: Entidade com valores de critério
            max_reference_level: Profundidade máxima de referências
        """
        max_ref = max_reference_level
        
        # Ajusta limite para CrudServiceFind
        if request.service == ServiceName.CRUD_SERVICE_FIND:
            if max_ref == ReferenceLevel.FOURTH:
                max_ref = ReferenceLevel.THIRD
        
        result = ServiceRequestExtensions._parse_properties(
            request, criteria, max_ref
        )
        
        ServiceRequestExtensions._apply_result_to_request(request, result)

    @staticmethod
    def resolve_with_collection(
        request: "ServiceRequest",
        criteria_list: List[T],
    ) -> None:
        """
        Resolve uma requisição para operações em batch.
        
        Args:
            request: Requisição a configurar
            criteria_list: Lista de entidades
            
        Raises:
            InvalidServiceRequestOperationException: Se o serviço não for suportado
        """
        if not criteria_list:
            return
        
        results = [
            ServiceRequestExtensions._parse_properties(
                request, criteria, ReferenceLevel.THIRD
            )
            for criteria in criteria_list
        ]
        
        sample = results[0]
        
        ServiceRequestExtensions._apply_batch_result_to_request(
            request, sample, results
        )

    @staticmethod
    def resolve_with_literal_criteria(
        request: "ServiceRequest",
        entity_type: Type[T],
        literal_criteria: "IFilterExpression",
    ) -> None:
        """
        Resolve uma requisição com critérios literais.
        
        Args:
            request: Requisição a configurar
            entity_type: Tipo da entidade
            literal_criteria: Expressão de filtro
        """
        ServiceRequestExtensions.resolve_generic(request, entity_type)
        
        expression = literal_criteria.build_expression()
        
        # Aplica o critério literal
        if request.request_body.entity:
            request.request_body.entity.literal_criteria = expression
        elif request.request_body.data_set:
            request.request_body.data_set.literal_criteria = expression

    @staticmethod
    def resolve_with_options(
        request: "ServiceRequest",
        entity: T,
        options: "EntityQueryOptions",
    ) -> None:
        """
        Resolve uma requisição com opções configuráveis.
        
        Args:
            request: Requisição a configurar
            entity: Entidade com critérios
            options: Opções de configuração
        """
        max_depth = ReferenceLevel.FOURTH
        if options.max_reference_depth is not None:
            max_depth = _int_to_reference_level(options.max_reference_depth)
        
        ServiceRequestExtensions.resolve_with_entity(request, entity, max_depth)
        
        # Aplica opções
        ServiceRequestExtensions._apply_options_to_request(request, options)

    @staticmethod
    def _apply_result_to_request(
        request: "ServiceRequest",
        result: EntityResolverResult,
    ) -> None:
        """
        Aplica o resultado do parsing à requisição.
        
        Args:
            request: Requisição a configurar
            result: Resultado do parsing
        """
        timestamp = ServiceRequestExtensions._get_unix_timestamp()
        
        if request.service == ServiceName.CRUD_FIND:
            # Configura Entity para CRUD.find
            if request.request_body.entity is None:
                from sankhya_sdk.models.service.request_body import Entity
                request.request_body.entity = Entity()
            
            entity = request.request_body.entity
            entity.name = result.name
            entity.fields = [f["name"] for f in result.fields]
            entity.criteria = result.criteria
            entity.include_presentation_fields = False
            
            if result.references:
                entity.references_fetch = [
                    {"name": k, "fields": [f["name"] for f in v]}
                    for k, v in result.references.items()
                ]
        
        elif request.service == ServiceName.CRUD_SERVICE_FIND:
            # Configura DataSet para CRUDServiceProvider.find
            if request.request_body.data_set is None:
                from sankhya_sdk.models.service.request_body import DataSet
                request.request_body.data_set = DataSet()
            
            ds = request.request_body.data_set
            ds.root_entity = result.name
            ds.include_presentation_fields = False
            ds.parallel_loader = True
            ds.data_set_id = f"{timestamp}_1"
            ds.literal_criteria = result.literal_criteria
            
            # Configura entidades
            entities = [{"path": "", "fieldset": ",".join(f["name"] for f in result.fields)}]
            
            for ref_key, ref_fields in result.references.items():
                entities.append({
                    "path": ref_key,
                    "fieldset": ",".join(f["name"] for f in ref_fields),
                })
            
            ds.entities = entities
        
        elif request.service in [ServiceName.CRUD_SAVE, ServiceName.CRUD_REMOVE]:
            # Configura para operações de CRUD
            if request.request_body.entity is None:
                from sankhya_sdk.models.service.request_body import Entity
                request.request_body.entity = Entity()
            
            entity = request.request_body.entity
            entity.name = result.name
            entity.campos = result.field_values
        
        elif request.service == ServiceName.CRUD_SERVICE_SAVE:
            # Configura DataSet para save
            if request.request_body.data_set is None:
                from sankhya_sdk.models.service.request_body import DataSet
                request.request_body.data_set = DataSet()
            
            ds = request.request_body.data_set
            ds.root_entity = result.name
            ds.include_presentation_fields = False
            ds.parallel_loader = True
            ds.data_set_id = f"{timestamp}_1"
            ds.entities = [{"path": "", "fieldset": "*"}]
            ds.data_rows = [{
                "keys": {k["name"]: k["value"] for k in result.keys},
                "local_fields": {
                    f["name"]: f["value"]
                    for f in result.field_values
                    if f not in result.keys
                },
            }]
        
        elif request.service == ServiceName.CRUD_SERVICE_REMOVE:
            # Configura para remoção
            if request.request_body.entity is None:
                from sankhya_sdk.models.service.request_body import Entity
                request.request_body.entity = Entity()
            
            entity = request.request_body.entity
            entity.root_entity = result.name
            entity.data_set_id = f"{timestamp}_2"
            entity.ids = [{k["name"]: k["value"] for k in result.keys}]
        
        else:
            raise InvalidServiceRequestOperationException(service=request.service)

    @staticmethod
    def _apply_batch_result_to_request(
        request: "ServiceRequest",
        sample: EntityResolverResult,
        results: List[EntityResolverResult],
    ) -> None:
        """
        Aplica resultados em batch à requisição.
        
        Args:
            request: Requisição a configurar
            sample: Resultado de exemplo para estrutura
            results: Lista de resultados
        """
        timestamp = ServiceRequestExtensions._get_unix_timestamp()
        
        if request.service == ServiceName.CRUD_SERVICE_SAVE:
            if request.request_body.data_set is None:
                from sankhya_sdk.models.service.request_body import DataSet
                request.request_body.data_set = DataSet()
            
            ds = request.request_body.data_set
            ds.root_entity = sample.name
            ds.include_presentation_fields = False
            ds.parallel_loader = True
            ds.data_set_id = f"{timestamp}_1"
            ds.entities = [{"path": "", "fieldset": "*"}]
            
            data_rows = []
            for result in results:
                row = {
                    "keys": {k["name"]: k["value"] for k in result.keys},
                    "local_fields": {
                        f["name"]: f["value"]
                        for f in result.field_values
                        if f not in result.keys
                    },
                }
                data_rows.append(row)
            
            ds.data_rows = data_rows
        
        elif request.service == ServiceName.CRUD_SERVICE_REMOVE:
            if request.request_body.entity is None:
                from sankhya_sdk.models.service.request_body import Entity
                request.request_body.entity = Entity()
            
            entity = request.request_body.entity
            entity.root_entity = sample.name
            entity.data_set_id = f"{timestamp}_2"
            entity.ids = [
                {k["name"]: k["value"] for k in result.keys}
                for result in results
            ]
        
        else:
            raise InvalidServiceRequestOperationException(service=request.service)

    @staticmethod
    def _apply_options_to_request(
        request: "ServiceRequest",
        options: "EntityQueryOptions",
    ) -> None:
        """
        Aplica opções de query à requisição.
        
        Args:
            request: Requisição a configurar
            options: Opções de configuração
        """
        if request.service == ServiceName.CRUD_FIND:
            entity = request.request_body.entity
            if entity:
                if options.include_presentation_fields is not None:
                    entity.include_presentation_fields = options.include_presentation_fields
                
                if options.include_references is not None and not options.include_references:
                    entity.references_fetch = None
                
                if options.max_results is not None:
                    entity.rows_limit = options.max_results
        
        elif request.service == ServiceName.CRUD_SERVICE_FIND:
            ds = request.request_body.data_set
            if ds:
                if options.include_presentation_fields is not None:
                    ds.include_presentation_fields = options.include_presentation_fields
                
                if options.include_references is not None and not options.include_references:
                    # Remove referências mantendo apenas a entidade raiz
                    if ds.entities and len(ds.entities) > 1:
                        ds.entities = [ds.entities[0]]
                
                if options.max_results is not None:
                    ds.rows_limit = options.max_results


def _reference_level_to_int(level: ReferenceLevel) -> int:
    """Converte ReferenceLevel para inteiro."""
    mapping = {
        ReferenceLevel.NONE: 0,
        ReferenceLevel.FIRST: 1,
        ReferenceLevel.SECOND: 2,
        ReferenceLevel.THIRD: 3,
        ReferenceLevel.FOURTH: 4,
        ReferenceLevel.FIFTH: 5,
        ReferenceLevel.SIXTH: 6,
    }
    return mapping.get(level, 0)


def _int_to_reference_level(value: int) -> ReferenceLevel:
    """Converte inteiro para ReferenceLevel."""
    mapping = {
        0: ReferenceLevel.NONE,
        1: ReferenceLevel.FIRST,
        2: ReferenceLevel.SECOND,
        3: ReferenceLevel.THIRD,
        4: ReferenceLevel.FOURTH,
        5: ReferenceLevel.FIFTH,
        6: ReferenceLevel.SIXTH,
    }
    return mapping.get(value, ReferenceLevel.NONE)


# Funções de conveniência para uso standalone
def resolve(
    request: "ServiceRequest",
    entity_or_type: Union[T, Type[T]],
    max_reference_level: ReferenceLevel = ReferenceLevel.FOURTH,
) -> None:
    """
    Resolve uma requisição de serviço.
    
    Função de conveniência que detecta automaticamente
    se recebeu um tipo ou uma instância.
    
    Args:
        request: Requisição a configurar
        entity_or_type: Tipo da entidade ou instância com critérios
        max_reference_level: Profundidade máxima de referências
    """
    if isinstance(entity_or_type, type):
        ServiceRequestExtensions.resolve_generic(request, entity_or_type)
    else:
        ServiceRequestExtensions.resolve_with_entity(
            request, entity_or_type, max_reference_level
        )
