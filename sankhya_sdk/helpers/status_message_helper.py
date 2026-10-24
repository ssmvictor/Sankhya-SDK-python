# -*- coding: utf-8 -*-
"""
Helper para processamento de mensagens de status de serviço.

Processa mensagens de status das respostas do Sankhya e lança
exceções apropriadas baseadas no conteúdo da mensagem.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/StatusMessageHelper.cs
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Optional, Type

from sankhya_sdk.exceptions import (
    ServiceRequestBusinessRuleRestrictionException,
    ServiceRequestCanceledQueryException,
    ServiceRequestCompetitionException,
    ServiceRequestDeadlockException,
    ServiceRequestDuplicatedDocumentException,
    ServiceRequestExpiredAuthenticationException,
    ServiceRequestExternalException,
    ServiceRequestFileNotFoundException,
    ServiceRequestForeignKeyException,
    ServiceRequestFullTransactionLogsException,
    ServiceRequestInvalidAuthorizationException,
    ServiceRequestInvalidCredentialsException,
    ServiceRequestInvalidExpressionException,
    ServiceRequestInvalidRelationException,
    ServiceRequestInvalidSubqueryException,
    ServiceRequestPaginationException,
    ServiceRequestPartnerFiscalClassificationException,
    ServiceRequestPartnerInvalidDocumentLengthException,
    ServiceRequestPartnerStateInscriptionException,
    ServiceRequestPropertyNameException,
    ServiceRequestPropertyValueException,
    ServiceRequestPropertyWidthException,
    ServiceRequestTimeoutException,
    ServiceRequestUnavailableException,
    ServiceRequestUnbalancedDelimiterException,
    ServiceRequestUnexpectedResultException,
)
from sankhya_sdk.validations.entity_validation import EntityValidation

if TYPE_CHECKING:
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.models.service.service_response import ServiceResponse


# Tipo para funções que criam exceções
ExceptionFactory = Callable[
    [str, "ServiceName", "ServiceRequest", "ServiceResponse"], 
    Exception
]


# Padrões regex para validação de entidades.
# Assim como no .NET (StatusMessageHelper usa Validations/EntityValidation.cs),
# os padrões são os de EntityValidation, que reconhecem as mensagens reais
# retornadas pelo servidor Sankhya.
PROPERTY_VALUE_ERROR_PATTERN = EntityValidation.PROPERTY_VALUE_ERROR_PATTERN

PROPERTY_NAME_ERROR_PATTERN = EntityValidation.PROPERTY_NAME_ERROR_PATTERN

PROPERTY_NAME_INVALID_ERROR_PATTERN = EntityValidation.PROPERTY_NAME_INVALID_ERROR_PATTERN

PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN = (
    EntityValidation.PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN
)

PROPERTY_NOT_FOUND_PATTERN = EntityValidation.PROPERTY_NOT_FOUND_PATTERN

MISSING_RELATION_PATTERN = EntityValidation.MISSING_RELATION_PATTERN

PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN = (
    EntityValidation.PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN
)

DUPLICATED_DOCUMENT_PATTERN = EntityValidation.DUPLICATED_DOCUMENT_PATTERN

BUSINESS_RULE_RESTRICTION_PATTERN = EntityValidation.BUSINESS_RULE_RESTRICTION_PATTERN

FULL_TRANSACTION_LOGS_PATTERN = EntityValidation.FULL_TRANSACTION_LOGS_PATTERN

MISSING_ATTRIBUTE_PATTERN = EntityValidation.MISSING_ATTRIBUTE_PATTERN

PROPERTY_WIDTH_ERROR_PATTERN = EntityValidation.PROPERTY_WIDTH_ERROR_PATTERN

REFERENCE_FIELDS_FIRST_LEVEL_PATTERN = (
    EntityValidation.REFERENCE_FIELDS_FIRST_LEVEL_PATTERN
)

REFERENCE_FIELDS_SECOND_LEVEL_PATTERN = (
    EntityValidation.REFERENCE_FIELDS_SECOND_LEVEL_PATTERN
)


class StatusMessageHelper:
    """
    Helper para processamento de mensagens de status de serviço.
    
    Analisa mensagens de status retornadas pelo Sankhya e lança
    exceções apropriadas baseadas no conteúdo da mensagem.
    
    Example:
        >>> StatusMessageHelper.process_status_message(
        ...     ServiceName.CRUD_FIND, request, response
        ... )  # Raises appropriate exception if error
    """

    # Mapeamento de mensagens comuns para funções que criam exceções
    COMMON_MESSAGES: Dict[str, ExceptionFactory] = {
        "Delimitador ''' desbalanceado": lambda msg, svc, req, res: (
            ServiceRequestUnbalancedDelimiterException(request=req)
        ),
        "situação de concorrência": lambda msg, svc, req, res: (
            ServiceRequestCompetitionException(request=req, response=res)
        ),
        "log de acessos": lambda msg, svc, req, res: (
            ServiceRequestCompetitionException(request=req, response=res)
        ),
        "violação da restrição primary key 'PK_TSIRLG'": lambda msg, svc, req, res: (
            ServiceRequestCompetitionException(request=req, response=res)
        ),
        "deadlock": lambda msg, svc, req, res: (
            ServiceRequestDeadlockException(message=msg, request=req, response=res)
        ),
        "não autorizado": lambda msg, svc, req, res: (
            ServiceRequestInvalidAuthorizationException()
        ),
        "tempo limite da consulta": lambda msg, svc, req, res: (
            ServiceRequestTimeoutException(service=svc, request=req)
        ),
        "resultset object is closed": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "objeto de acesso a dados": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "the connection object is closed": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "I/O error": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "TDS protocol error": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "STP_SET_SESSION": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "java.lang.NullPointerException": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "erro interno (NPE)": lambda msg, svc, req, res: (
            ServiceRequestExternalException(service=svc, request=req, response=res)
        ),
        "Expressão inválida": lambda msg, svc, req, res: (
            ServiceRequestInvalidExpressionException(request=req, response=res)
        ),
        "Usuário/Senha inválido": lambda msg, svc, req, res: (
            ServiceRequestInvalidCredentialsException()
        ),
        "Usuário expirou": lambda msg, svc, req, res: (
            ServiceRequestExpiredAuthenticationException()
        ),
        "A consulta foi cancelada": lambda msg, svc, req, res: (
            ServiceRequestCanceledQueryException(message=msg, request=req)
        ),
        "Arquivo/Diretório não foi encontrado no repositório": lambda msg, svc, req, res: (
            ServiceRequestFileNotFoundException(request=req)
        ),
        "O sistema não pode encontrar o arquivo especificado": lambda msg, svc, req, res: (
            ServiceRequestPaginationException(request=req)
        ),
        "Na ausência da Inscrição Estadual, apenas a Classificação ICMS": lambda msg, svc, req, res: (
            ServiceRequestPartnerFiscalClassificationException(request=req)
        ),
        "Insira a palavra ISENTO para este tipo de inscrição estadual": lambda msg, svc, req, res: (
            ServiceRequestPartnerStateInscriptionException(request=req)
        ),
        "Tamanho do CNPJ/CPF inválido para pessoa Física!": lambda msg, svc, req, res: (
            ServiceRequestPartnerInvalidDocumentLengthException(request=req)
        ),
        "A subconsulta retornou mais de 1 valor": lambda msg, svc, req, res: (
            ServiceRequestInvalidSubqueryException(request=req)
        ),
    }

    @classmethod
    def process_status_message(
        cls,
        service: "ServiceName",
        request: "ServiceRequest",
        response: "ServiceResponse",
    ) -> None:
        """
        Processa a mensagem de status e lança exceção apropriada.
        
        Analisa a mensagem de status da resposta e, se corresponder
        a um padrão de erro conhecido, lança a exceção apropriada.
        
        Args:
            service: Nome do serviço chamado
            request: Requisição original
            response: Resposta recebida
            
        Raises:
            Exceção apropriada baseada no conteúdo da mensagem
        """
        if not response.status_message:
            return
        
        status_message = response.status_message.decoded_value
        if not status_message:
            return

        # Verifica mensagens comuns
        for pattern, factory in cls.COMMON_MESSAGES.items():
            if pattern.lower() in status_message.lower():
                raise factory(status_message, service, request, response)

        # Verifica padrões regex
        cls._check_regex_patterns(status_message, service, request, response)

    @classmethod
    def _check_regex_patterns(
        cls,
        status_message: str,
        service: "ServiceName",
        request: "ServiceRequest",
        response: "ServiceResponse",
    ) -> None:
        """
        Verifica padrões regex e lança exceções apropriadas.
        
        Args:
            status_message: Mensagem de status a verificar
            service: Nome do serviço
            request: Requisição original
            response: Resposta recebida
        """
        # Property value error
        match = PROPERTY_VALUE_ERROR_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyValueException(
                property_name=match.group("propertyName"),
                request=request,
            )

        # Property name error
        match = PROPERTY_NAME_ERROR_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyNameException(
                property_name=match.group("propertyName"),
                request=request,
            )

        # Property name invalid error
        match = PROPERTY_NAME_INVALID_ERROR_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyNameException(
                property_name=match.group("propertyName"),
                request=request,
            )

        # Property name association error
        match = PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyNameException(
                property_name=match.group("propertyName"),
                request=request,
                entity_name=match.group("entity"),
            )

        # Property not found
        match = PROPERTY_NOT_FOUND_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyNameException(
                property_name=match.group("propertyName"),
                request=request,
                entity_name=match.group("entity"),
            )

        # Missing relation
        match = MISSING_RELATION_PATTERN.search(status_message)
        if match:
            raise ServiceRequestInvalidRelationException(
                match.group("missingRelation"),
                match.group("entity"),
                request,
            )

        # Foreign key restriction
        match = PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN.search(status_message)
        if match:
            raise ServiceRequestForeignKeyException(
                match.group("table"),
                match.group("column") or "",
                request,
                response,
            )

        # Duplicated document
        match = DUPLICATED_DOCUMENT_PATTERN.search(status_message)
        if match:
            raise ServiceRequestDuplicatedDocumentException(
                match.group("name"),
                request,
                response,
            )

        # Business rule restriction
        match = BUSINESS_RULE_RESTRICTION_PATTERN.search(status_message)
        if match:
            raise ServiceRequestBusinessRuleRestrictionException(
                match.group("ruleName"),
                match.group("errorMessage"),
                request,
                response,
            )

        # Full transaction logs
        match = FULL_TRANSACTION_LOGS_PATTERN.search(status_message)
        if match:
            raise ServiceRequestFullTransactionLogsException(
                match.group("database"),
                request,
                response,
            )

        # Missing attribute
        match = MISSING_ATTRIBUTE_PATTERN.search(status_message)
        if match:
            from sankhya_sdk.exceptions import ServiceRequestAttributeException
            raise ServiceRequestAttributeException(
                attribute_name=match.group("attributeName"),
                service=service,
                request=request,
            )

        # Property width error
        match = PROPERTY_WIDTH_ERROR_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyWidthException(
                property_name=match.group("propertyName"),
                request=request,
                width_allowed=int(match.group("widthAllowed")),
                current_width=int(match.group("currentWidth")),
            )

        # Se nenhum padrão correspondeu, lança exceção genérica
        raise ServiceRequestUnexpectedResultException(
            message=status_message,
            request=request,
            response=response,
        )
