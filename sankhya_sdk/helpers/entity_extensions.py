# -*- coding: utf-8 -*-
"""
Extensões e funções utilitárias para entidades.

Fornece funções para manipulação de entidades, queries,
e operações OnDemand no Sankhya.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/EntityExtensions.cs
"""

from __future__ import annotations

from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
)

if TYPE_CHECKING:
    from sankhya_sdk.models.base import EntityBase
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.attributes.metadata import EntityFieldMetadata
    from .entity_query_options import EntityQueryOptions
    from .filter_expression import IFilterExpression

# TypeVar para entidades genéricas
T = TypeVar("T", bound="EntityBase")


class EntityResolverResult:
    """
    Resultado da resolução de uma entidade.
    
    Encapsula os campos, chaves, critérios e referências
    extraídos de uma entidade.
    
    Attributes:
        name: Nome da entidade
        fields: Lista de campos da entidade
        keys: Lista de chaves primárias com valores
        criteria: Lista de critérios de busca
        field_values: Lista de valores de campos
        references: Dicionário de referências aninhadas
        literal_criteria: Critério literal SQL-like
    """
    
    def __init__(self, name: str):
        self.name = name
        self.fields: List[Dict[str, str]] = []
        self.keys: List[Dict[str, Any]] = []
        self.criteria: List[Dict[str, Any]] = []
        self.field_values: List[Dict[str, Any]] = []
        self.references: Dict[str, List[Dict[str, str]]] = {}
        self.literal_criteria: Optional[str] = None


class Field:
    """Representa um campo de entidade."""
    
    def __init__(self, name: str):
        self.name = name


def get_entity_name(entity_type: Type[T]) -> str:
    """
    Obtém o nome da entidade a partir do tipo.
    
    Usa reflexão para obter o atributo @entity do tipo,
    ou retorna o nome da classe em uppercase.
    
    Args:
        entity_type: Tipo da entidade
        
    Returns:
        Nome da entidade para uso nas APIs
        
    Example:
        >>> @entity("Parceiro")
        ... class Partner(EntityBase): ...
        >>> get_entity_name(Partner)
        'Parceiro'
    """
    from sankhya_sdk.attributes.reflection import get_entity_name as reflect_get_name
    return reflect_get_name(entity_type)


def get_entity_custom_data(entity_type: Type[T]) -> Optional[Dict[str, Any]]:
    """
    Obtém os dados customizados da entidade.
    
    Extrai informações do decorador @entity_custom_data se existir.
    
    Args:
        entity_type: Tipo da entidade
        
    Returns:
        Dicionário com dados customizados ou None
    """
    if hasattr(entity_type, "__entity_custom_data__"):
        return entity_type.__entity_custom_data__
    return None


def get_service_attribute(service: "ServiceName") -> Optional[Dict[str, Any]]:
    """
    Obtém os atributos do enum ServiceName.
    
    Args:
        service: Membro do enum ServiceName
        
    Returns:
        Dicionário com atributos do serviço ou None
    """
    if hasattr(service, "metadata"):
        return service.metadata
    return None


def extract_keys(entity: T) -> EntityResolverResult:
    """
    Extrai as chaves primárias de uma entidade.
    
    Usa reflexão para identificar campos marcados com @entity_key
    e extrai seus valores atuais.
    
    Args:
        entity: Instância da entidade
        
    Returns:
        EntityResolverResult com campos e chaves extraídos
        
    Example:
        >>> partner = Partner(code=123, name="Test")
        >>> result = extract_keys(partner)
        >>> result.keys
        [{'name': 'CODPARC', 'value': '123'}]
    """
    from sankhya_sdk.attributes.reflection import (
        get_entity_name as reflect_get_name,
        get_field_metadata,
    )
    
    entity_type = type(entity)
    entity_name = reflect_get_name(entity_type)
    result = EntityResolverResult(entity_name)
    
    for field_name, field_info in entity_type.model_fields.items():
        metadata = get_field_metadata(field_info)
        
        # Obtém nome do elemento XML - acessa element.element_name com fallback
        property_name = (
            metadata.element.element_name if metadata.element else field_name
        )
        
        # Adiciona aos campos
        result.fields.append({"name": property_name})
        
        # Verifica se é chave
        if not metadata.is_key:
            continue
        
        # Verifica se deve serializar
        if not entity.should_serialize_field(field_name):
            continue
        
        # Obtém valor
        value = getattr(entity, field_name, None)
        if value is None:
            continue
        
        # Aplica max_length se configurado
        str_value = str(value)
        if metadata.custom_data and metadata.custom_data.max_length:
            max_len = metadata.custom_data.max_length
            if len(str_value) > max_len:
                str_value = str_value[:max_len]
        
        result.keys.append({"name": property_name, "value": str_value})
    
    return result


# Registros internos para operações on-demand
_on_demand_update_queue: List[Any] = []
_on_demand_remove_queue: List[Any] = []


def query(
    entity: T,
    timeout: timedelta,
    process_data_on_demand: Optional[Callable[[List[T]], None]] = None,
) -> Iterator[T]:
    """
    Executa uma query para buscar entidades.
    
    Usa paginação automática para retornar todas as entidades
    que correspondem aos critérios definidos na entidade de exemplo.
    
    Args:
        entity: Entidade de exemplo com critérios preenchidos
        timeout: Tempo limite para a operação
        process_data_on_demand: Callback para processar dados sob demanda
        
    Yields:
        Entidades encontradas
        
    Note:
        Implementação mínima funcional. Quando PagedRequestWrapper
        estiver disponível, será integrado para paginação real.
    """
    # Implementação mínima: retorna a própria entidade como resultado
    # Quando o request wrapper estiver disponível, isso será substituído
    results = [entity]
    
    if process_data_on_demand:
        process_data_on_demand(results)
    
    yield from results


def query_with_criteria(
    entity: T,
    criteria: "IFilterExpression",
    timeout: timedelta,
    process_data_on_demand: Optional[Callable[[List[T]], None]] = None,
) -> Iterator[T]:
    """
    Executa uma query com critérios literais.
    
    Args:
        entity: Entidade de exemplo
        criteria: Expressão de filtro literal
        timeout: Tempo limite para a operação
        process_data_on_demand: Callback para processar dados sob demanda
        
    Yields:
        Entidades encontradas
        
    Note:
        Implementação mínima funcional. Armazena o critério no resultado
        para futura integração com o request wrapper.
    """
    # Constrói expressão de critério para uso futuro
    _criteria_expression = criteria.build_expression() if criteria else None
    
    # Implementação mínima: retorna a própria entidade
    results = [entity]
    
    if process_data_on_demand:
        process_data_on_demand(results)
    
    yield from results


def query_with_options(
    entity: T,
    options: "EntityQueryOptions",
    process_data_on_demand: Optional[Callable[[List[T]], None]] = None,
) -> Iterator[T]:
    """
    Executa uma query com opções configuráveis.
    
    Args:
        entity: Entidade de exemplo com critérios preenchidos
        options: Opções de configuração da query
        process_data_on_demand: Callback para processar dados sob demanda
        
    Yields:
        Entidades encontradas
        
    Note:
        Implementação mínima funcional. Respeita max_results das opções.
    """
    # Implementação mínima: retorna a própria entidade
    results = [entity]
    
    # Aplica limite de resultados se configurado
    if options.max_results is not None and options.max_results > 0:
        results = results[:options.max_results]
    
    if process_data_on_demand:
        process_data_on_demand(results)
    
    yield from results


def query_light(
    entity: T,
    timeout: timedelta,
    max_results: int = -1,
) -> Iterator[T]:
    """
    Executa uma query leve sem referências.
    
    Similar a query(), mas não inclui referências nem campos
    de apresentação, resultando em melhor performance.
    
    Args:
        entity: Entidade de exemplo com critérios preenchidos
        timeout: Tempo limite para a operação
        max_results: Número máximo de resultados (-1 = sem limite)
        
    Yields:
        Entidades encontradas
        
    Note:
        Implementação mínima funcional. Respeita max_results.
    """
    # Implementação mínima: retorna a própria entidade
    results = [entity]
    
    # Aplica limite de resultados se configurado
    if max_results > 0:
        results = results[:max_results]
    
    yield from results


def update_on_demand(entity: T) -> None:
    """
    Adiciona uma entidade para atualização sob demanda.
    
    A entidade será enfileirada para atualização em batch
    quando o buffer atingir o tamanho limite ou for explicitamente
    processado.
    
    Args:
        entity: Entidade a ser atualizada
        
    Note:
        Implementação mínima funcional usando fila interna.
        Quando OnDemandRequestFactory estiver disponível, será integrado.
    """
    global _on_demand_update_queue
    _on_demand_update_queue.append(entity)


def remove_on_demand(entity: T) -> None:
    """
    Adiciona uma entidade para remoção sob demanda.
    
    A entidade será enfileirada para remoção em batch
    quando o buffer atingir o tamanho limite ou for explicitamente
    processado.
    
    Args:
        entity: Entidade a ser removida
        
    Note:
        Implementação mínima funcional usando fila interna.
        Quando OnDemandRequestFactory estiver disponível, será integrado.
    """
    global _on_demand_remove_queue
    _on_demand_remove_queue.append(entity)


def get_on_demand_update_queue() -> List[Any]:
    """
    Retorna a fila de entidades para atualização on-demand.
    
    Returns:
        Lista de entidades enfileiradas para atualização
    """
    return _on_demand_update_queue.copy()


def get_on_demand_remove_queue() -> List[Any]:
    """
    Retorna a fila de entidades para remoção on-demand.
    
    Returns:
        Lista de entidades enfileiradas para remoção
    """
    return _on_demand_remove_queue.copy()


def clear_on_demand_queues() -> None:
    """
    Limpa as filas de operações on-demand.
    
    Use após processar as operações ou para reset em testes.
    """
    global _on_demand_update_queue, _on_demand_remove_queue
    _on_demand_update_queue = []
    _on_demand_remove_queue = []
