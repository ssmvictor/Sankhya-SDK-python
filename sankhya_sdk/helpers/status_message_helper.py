# -*- coding: utf-8 -*-
"""
Helper para processamento de mensagens de status de serviço.

Processa mensagens de status das respostas do Sankhya e lança
exceções apropriadas baseadas no conteúdo da mensagem.

Migrado de: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/StatusMessageHelper.cs
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable, Dict, Optional, Type

from sankhya_sdk.exceptions import (
    ServiceRequestBusinessRuleRestrictionException,
    ServiceRequestCanceledQueryException,
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

if TYPE_CHECKING:
    from sankhya_sdk.enums.service_name import ServiceName
    from sankhya_sdk.models.service.service_request import ServiceRequest
    from sankhya_sdk.models.service.service_response import ServiceResponse


# Tipo para funções que criam exceções
ExceptionFactory = Callable[
    [str, "ServiceName", "ServiceRequest", "ServiceResponse"], 
    Exception
]


# Padrões regex para validação de entidades
PROPERTY_VALUE_ERROR_PATTERN = re.compile(
    r"O valor do campo '(?P<propertyName>\w+)' é inválido",
    re.IGNORECASE
)

PROPERTY_NAME_ERROR_PATTERN = re.compile(
    r"O campo '(?P<propertyName>\w+)' não existe",
    re.IGNORECASE
)

PROPERTY_NAME_INVALID_ERROR_PATTERN = re.compile(
    r"Campo inválido: (?P<propertyName>\w+)",
    re.IGNORECASE
)

PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN = re.compile(
    r"O campo '(?P<propertyName>\w+)' não pertence à entidade '(?P<entity>\w+)'",
    re.IGNORECASE
)

PROPERTY_NOT_FOUND_PATTERN = re.compile(
    r"Campo '(?P<propertyName>\w+)' não encontrado na entidade '(?P<entity>\w+)'",
    re.IGNORECASE
)

MISSING_RELATION_PATTERN = re.compile(
    r"Relacionamento '(?P<missingRelation>\w+)' não encontrado para a entidade '(?P<entity>\w+)'",
    re.IGNORECASE
)

PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN = re.compile(
    r"violação.*chave estrangeira.*tabela '(?P<table>\w+)'.*coluna '(?P<column>\w+)'",
    re.IGNORECASE
)

DUPLICATED_DOCUMENT_PATTERN = re.compile(
    r"documento duplicado.*'(?P<name>\w+)'",
    re.IGNORECASE
)

BUSINESS_RULE_RESTRICTION_PATTERN = re.compile(
    r"Regra de negócio '(?P<ruleName>\w+)'.*(?P<errorMessage>.+)",
    re.IGNORECASE
)

FULL_TRANSACTION_LOGS_PATTERN = re.compile(
    r"log de transações.*banco de dados '(?P<database>\w+)'",
    re.IGNORECASE
)

MISSING_ATTRIBUTE_PATTERN = re.compile(
    r"Atributo '(?P<attributeName>\w+)' é obrigatório",
    re.IGNORECASE
)

PROPERTY_WIDTH_ERROR_PATTERN = re.compile(
    r"O campo '(?P<propertyName>\w+)' excede o tamanho máximo de (?P<widthAllowed>\d+).*atual: (?P<currentWidth>\d+)",
    re.IGNORECASE
)

REFERENCE_FIELDS_FIRST_LEVEL_PATTERN = re.compile(
    r"^(?P<entity>\w+)_(?P<field>\w+)$"
)

REFERENCE_FIELDS_SECOND_LEVEL_PATTERN = re.compile(
    r"^(?P<parentEntity>\w+)_(?P<entity>\w+)_(?P<field>\w+)$"
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
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "log de acessos": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "violação da restrição primary key 'PK_TSIRLG'": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
        ),
        "deadlock": lambda msg, svc, req, res: (
            ServiceRequestUnavailableException(service=svc, request=req, response=res)
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
                entity=match.group("entity"),
                request=request,
            )

        # Property not found
        match = PROPERTY_NOT_FOUND_PATTERN.search(status_message)
        if match:
            raise ServiceRequestPropertyNameException(
                property_name=match.group("propertyName"),
                entity=match.group("entity"),
                request=request,
            )

        # Missing relation
        match = MISSING_RELATION_PATTERN.search(status_message)
        if match:
            raise ServiceRequestInvalidRelationException(
                missing_relation=match.group("missingRelation"),
                entity=match.group("entity"),
                request=request,
            )

        # Foreign key restriction
        match = PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN.search(status_message)
        if match:
            raise ServiceRequestForeignKeyException(
                table=match.group("table"),
                column=match.group("column"),
                request=request,
                response=response,
            )

        # Duplicated document
        match = DUPLICATED_DOCUMENT_PATTERN.search(status_message)
        if match:
            raise ServiceRequestDuplicatedDocumentException(
                name=match.group("name"),
                request=request,
                response=response,
            )

        # Business rule restriction
        match = BUSINESS_RULE_RESTRICTION_PATTERN.search(status_message)
        if match:
            raise ServiceRequestBusinessRuleRestrictionException(
                rule_name=match.group("ruleName"),
                error_message=match.group("errorMessage"),
                request=request,
                response=response,
            )

        # Full transaction logs
        match = FULL_TRANSACTION_LOGS_PATTERN.search(status_message)
        if match:
            raise ServiceRequestFullTransactionLogsException(
                database=match.group("database"),
                request=request,
                response=response,
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
