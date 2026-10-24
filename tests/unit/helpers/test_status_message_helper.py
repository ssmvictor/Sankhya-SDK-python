# -*- coding: utf-8 -*-
"""
Testes unitários para status_message_helper.py
"""

import pytest
from unittest.mock import Mock, MagicMock

from sankhya_sdk.enums.service_name import ServiceName
from sankhya_sdk.exceptions import (
    ServiceRequestAttributeException,
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
    ServiceRequestTemporarilyException,
    ServiceRequestTimeoutException,
    ServiceRequestUnavailableException,
    ServiceRequestUnbalancedDelimiterException,
    ServiceRequestUnexpectedResultException,
)
from sankhya_sdk.helpers import status_message_helper
from sankhya_sdk.helpers.status_message_helper import (
    StatusMessageHelper,
    PROPERTY_VALUE_ERROR_PATTERN,
    PROPERTY_NAME_ERROR_PATTERN,
    REFERENCE_FIELDS_FIRST_LEVEL_PATTERN,
    REFERENCE_FIELDS_SECOND_LEVEL_PATTERN,
)
from sankhya_sdk.models.service.basic_types import LiteralCriteria
from sankhya_sdk.models.service.entity_types import DataSet, Entity
from sankhya_sdk.models.service.metadata_types import Config
from sankhya_sdk.models.service.service_request import ServiceRequest
from sankhya_sdk.validations.entity_validation import EntityValidation


def _status_response(message):
    """Cria mock de ServiceResponse com a mensagem de status informada."""
    response = Mock()
    response.status_message = Mock(decoded_value=message)
    return response


def _entity_request(service=ServiceName.CRUD_FIND, entity_name="Parceiro"):
    """Cria uma ServiceRequest real com a entidade informada."""
    request = ServiceRequest(service=service)
    request.request_body.entity = Entity(name=entity_name)
    return request


class TestStatusMessageHelper:
    """Testes para StatusMessageHelper."""

    @pytest.fixture
    def mock_request(self):
        """Cria mock de ServiceRequest."""
        return Mock()

    @pytest.fixture
    def mock_response(self):
        """Cria mock de ServiceResponse."""
        response = Mock()
        response.status_message = None
        return response

    @pytest.fixture
    def mock_service(self):
        """Cria mock de ServiceName."""
        return Mock()

    def test_no_status_message_does_nothing(
        self, mock_service, mock_request, mock_response
    ):
        """Não deve lançar exceção se não houver status_message."""
        mock_response.status_message = None
        
        # Não deve lançar exceção
        StatusMessageHelper.process_status_message(
            mock_service, mock_request, mock_response
        )

    def test_empty_status_message_does_nothing(
        self, mock_service, mock_request, mock_response
    ):
        """Não deve lançar exceção se status_message estiver vazio."""
        mock_response.status_message = Mock(decoded_value="")

        StatusMessageHelper.process_status_message(
            mock_service, mock_request, mock_response
        )


class TestStatusMessageHelperCommonMessages:
    """
    Testes do mapeamento de mensagens comuns para exceções.

    Referência: Sankhya-SDK-dotnet/Src/Sankhya/Helpers/StatusMessageHelper.cs
    (dicionário CommonMessages).
    """

    @staticmethod
    def _response(message):
        response = Mock()
        response.status_message = Mock(decoded_value=message)
        return response

    @pytest.mark.parametrize(
        "message",
        [
            "Operation not allowed after ResultSet object is closed",
            "Falha no objeto de acesso a dados",
            "The connection object is closed",
            "I/O Error: Connection reset",
            "TDS Protocol error: Invalid TDS packet header",
            "Erro ao executar STP_SET_SESSION",
            "java.lang.NullPointerException",
        ],
    )
    def test_unavailable_messages_raise_unavailable_exception(self, message):
        """Mensagens de indisponibilidade devem gerar ServiceRequestUnavailableException."""
        request = Mock()
        response = self._response(message)

        with pytest.raises(ServiceRequestUnavailableException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_FIND, request, response
            )

        assert isinstance(exc_info.value, ServiceRequestTemporarilyException)
        assert exc_info.value.request is request
        assert exc_info.value.response is response

    @pytest.mark.parametrize(
        "message",
        [
            "Ocorreu uma situação de concorrência ao gravar o registro",
            "Não foi possível gravar no log de acessos",
            "Violação da restrição PRIMARY KEY 'PK_TSIRLG'",
        ],
    )
    def test_competition_messages_raise_competition_exception(self, message):
        """Mensagens de concorrência devem gerar ServiceRequestCompetitionException."""
        request = Mock()
        response = self._response(message)

        with pytest.raises(ServiceRequestCompetitionException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_SAVE, request, response
            )

        assert exc_info.value.request is request
        assert exc_info.value.response is response

    def test_deadlock_message_raises_deadlock_exception(self):
        """Mensagem de deadlock deve gerar ServiceRequestDeadlockException com a mensagem original."""
        message = (
            "Transaction (Process ID 52) was deadlocked on lock resources with "
            "another process and has been chosen as the deadlock victim."
        )
        request = Mock()
        response = self._response(message)

        with pytest.raises(ServiceRequestDeadlockException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_SAVE, request, response
            )

        assert str(exc_info.value) == message
        assert exc_info.value.request is request
        assert exc_info.value.response is response

    def test_internal_npe_message_raises_external_exception(self):
        """Mensagem de erro interno (NPE) deve gerar ServiceRequestExternalException."""
        request = Mock()
        response = self._response("Ocorreu um erro interno (NPE) no servidor")

        with pytest.raises(ServiceRequestExternalException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_FIND, request, response
            )

        assert exc_info.value.request is request
        assert exc_info.value.response is response

    def test_invalid_credentials_message_raises_invalid_credentials(self):
        """Mensagem de usuário/senha inválido deve gerar ServiceRequestInvalidCredentialsException."""
        response = self._response("Usuário/Senha inválido!")

        with pytest.raises(ServiceRequestInvalidCredentialsException):
            StatusMessageHelper.process_status_message(
                ServiceName.LOGIN, Mock(), response
            )


# Uma mensagem de exemplo e o tipo de exceção esperado para cada chave de
# COMMON_MESSAGES, conforme o dicionário CommonMessages do .NET
# (Src/Sankhya/Helpers/StatusMessageHelper.cs:15-124).
COMMON_MESSAGE_CASES = [
    ("Delimitador ''' desbalanceado", "Delimitador ''' desbalanceado.", ServiceRequestUnbalancedDelimiterException),
    ("situação de concorrência", "Ocorreu uma situação de concorrência ao gravar o registro", ServiceRequestCompetitionException),
    ("log de acessos", "Não foi possível gravar no log de acessos", ServiceRequestCompetitionException),
    ("violação da restrição primary key 'PK_TSIRLG'", "Violação da restrição PRIMARY KEY 'PK_TSIRLG'. Não é possível inserir a chave duplicada.", ServiceRequestCompetitionException),
    ("deadlock", "Transaction (Process ID 52) was deadlocked on lock resources with another process and has been chosen as the deadlock victim.", ServiceRequestDeadlockException),
    ("não autorizado", "Não autorizado.", ServiceRequestInvalidAuthorizationException),
    ("tempo limite da consulta", "O tempo limite da consulta expirou", ServiceRequestTimeoutException),
    ("resultset object is closed", "Operation not allowed after ResultSet object is closed", ServiceRequestUnavailableException),
    ("objeto de acesso a dados", "Falha no objeto de acesso a dados", ServiceRequestUnavailableException),
    ("the connection object is closed", "The connection object is closed.", ServiceRequestUnavailableException),
    ("I/O error", "I/O Error: Connection reset", ServiceRequestUnavailableException),
    ("TDS protocol error", "TDS Protocol error: Invalid TDS packet header", ServiceRequestUnavailableException),
    ("STP_SET_SESSION", "Erro ao executar STP_SET_SESSION", ServiceRequestUnavailableException),
    ("java.lang.NullPointerException", "java.lang.NullPointerException", ServiceRequestUnavailableException),
    ("erro interno (NPE)", "Ocorreu um erro interno (NPE) no servidor", ServiceRequestExternalException),
    ("Expressão inválida", "Expressão inválida: CODPARC =", ServiceRequestInvalidExpressionException),
    ("Usuário/Senha inválido", "Usuário/Senha inválido!", ServiceRequestInvalidCredentialsException),
    ("Usuário expirou", "Usuário expirou.", ServiceRequestExpiredAuthenticationException),
    ("A consulta foi cancelada", "A consulta foi cancelada.", ServiceRequestCanceledQueryException),
    ("Arquivo/Diretório não foi encontrado no repositório", "Arquivo/Diretório não foi encontrado no repositório", ServiceRequestFileNotFoundException),
    ("O sistema não pode encontrar o arquivo especificado", "O sistema não pode encontrar o arquivo especificado", ServiceRequestPaginationException),
    ("Na ausência da Inscrição Estadual, apenas a Classificação ICMS", "Na ausência da Inscrição Estadual, apenas a Classificação ICMS 'Consumidor Final Não Contribuinte' e 'Produtor Rural' são permitidas", ServiceRequestPartnerFiscalClassificationException),
    ("Insira a palavra ISENTO para este tipo de inscrição estadual", "Insira a palavra ISENTO para este tipo de inscrição estadual", ServiceRequestPartnerStateInscriptionException),
    ("Tamanho do CNPJ/CPF inválido para pessoa Física!", "Tamanho do CNPJ/CPF inválido para pessoa Física!", ServiceRequestPartnerInvalidDocumentLengthException),
    ("A subconsulta retornou mais de 1 valor", "A subconsulta retornou mais de 1 valor.", ServiceRequestInvalidSubqueryException),
]

# Entradas em que o .NET repassa a requisição/resposta para a exceção.
COMMON_MESSAGES_WITHOUT_REQUEST = {
    "não autorizado",
    "Usuário/Senha inválido",
    "Usuário expirou",
}
COMMON_MESSAGES_WITH_RESPONSE = {
    "situação de concorrência",
    "log de acessos",
    "violação da restrição primary key 'PK_TSIRLG'",
    "deadlock",
    "resultset object is closed",
    "objeto de acesso a dados",
    "the connection object is closed",
    "I/O error",
    "TDS protocol error",
    "STP_SET_SESSION",
    "java.lang.NullPointerException",
    "erro interno (NPE)",
    "Expressão inválida",
}


class TestStatusMessageHelperEveryCommonMessage:
    """
    Um teste por entrada de COMMON_MESSAGES: cada mensagem deve gerar
    exatamente a exceção tipada do .NET (e nunca TypeError).
    """

    def test_every_common_message_has_a_case(self):
        """Toda chave de COMMON_MESSAGES deve ter um caso de teste, na mesma ordem do .NET."""
        assert [key for key, _, _ in COMMON_MESSAGE_CASES] == list(
            StatusMessageHelper.COMMON_MESSAGES
        )

    @pytest.mark.parametrize(
        "key,message,expected",
        COMMON_MESSAGE_CASES,
        ids=[key for key, _, _ in COMMON_MESSAGE_CASES],
    )
    def test_common_message_raises_dotnet_exception(self, key, message, expected):
        request = _entity_request()
        response = _status_response(message)

        with pytest.raises(Exception) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_FIND, request, response
            )

        assert type(exc_info.value) is expected
        if key not in COMMON_MESSAGES_WITHOUT_REQUEST:
            assert exc_info.value.request is request
        if key in COMMON_MESSAGES_WITH_RESPONSE:
            assert exc_info.value.response is response

    def test_canceled_query_keeps_status_message(self):
        """.NET: ServiceRequestCanceledQueryException(message, request)."""
        message = "A consulta foi cancelada."

        with pytest.raises(ServiceRequestCanceledQueryException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_SERVICE_FIND, _entity_request(), _status_response(message)
            )

        assert str(exc_info.value) == message

    def test_invalid_expression_uses_request_literal_criteria(self):
        """.NET: a expressão vem do LiteralCriteria do DataSet (CRUDServiceProvider.loadRecords)."""
        request = ServiceRequest(service=ServiceName.CRUD_SERVICE_FIND)
        request.request_body.data_set = DataSet(
            root_entity="Parceiro",
            literal_criteria=LiteralCriteria(expression="CODPARC = AND"),
        )

        with pytest.raises(ServiceRequestInvalidExpressionException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_SERVICE_FIND,
                request,
                _status_response("Expressão inválida: CODPARC = AND"),
            )

        assert str(exc_info.value) == (
            "The filter expression 'CODPARC = AND' is invalid, check if it is a valid SQL expression!"
        )

    def test_file_not_found_uses_request_config_path(self):
        """.NET: o caminho vem de RequestBody.Config.Path."""
        request = ServiceRequest(service=ServiceName.CRUD_FIND)
        request.request_body.config = Config(path="Repo/Contratos/contrato.pdf")

        with pytest.raises(ServiceRequestFileNotFoundException) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_FIND,
                request,
                _status_response("Arquivo/Diretório não foi encontrado no repositório"),
            )

        assert str(exc_info.value) == (
            "Unable to load the file from path Repo/Contratos/contrato.pdf. "
            "File or directory not found."
        )


class TestStatusMessageHelperEntityValidationPatterns:
    """
    Mensagens reais do servidor reconhecidas pelos padrões de
    Validations/EntityValidation.cs (StatusMessageHelper.cs:144-270).
    """

    @staticmethod
    def _process(message, request=None, response=None):
        request = request if request is not None else _entity_request()
        response = response if response is not None else _status_response(message)
        with pytest.raises(Exception) as exc_info:
            StatusMessageHelper.process_status_message(
                ServiceName.CRUD_FIND, request, response
            )
        return exc_info.value

    def test_property_value_error(self):
        exc = self._process("Erro ao obter valor da propriedade 'CODPARC'")

        assert type(exc) is ServiceRequestPropertyValueException
        assert exc.property_name == "CODPARC"
        assert str(exc) == (
            "The call to the service CRUD - Retrieve couldn't find the field CODPARC on entity Parceiro"
        )

    def test_property_value_error_with_reference(self):
        exc = self._process("Erro ao obter valor da propriedade 'CODCID->NOMECID'")

        assert type(exc) is ServiceRequestPropertyValueException
        assert exc.property_name == "CODCID->NOMECID"

    def test_property_name_error(self):
        exc = self._process("Descritor do campo 'CODPARCX' inválido")

        assert type(exc) is ServiceRequestPropertyNameException
        assert str(exc) == (
            "The call to the service CRUD - Retrieve couldn't find the field CODPARCX "
            "on entity  in Parceiro entity request"
        )

    def test_property_name_invalid_error(self):
        exc = self._process("Nome de coluna 'NOMEPARCX' inválido.")

        assert type(exc) is ServiceRequestPropertyNameException
        assert "couldn't find the field NOMEPARCX on entity  in Parceiro" in str(exc)

    def test_property_name_association_error(self):
        exc = self._process(
            'O identificador de várias partes "PAR.NOMEPARCX" não pôde ser associado.'
        )

        assert type(exc) is ServiceRequestPropertyNameException
        assert "couldn't find the field NOMEPARCX on entity PAR in Parceiro" in str(exc)

    def test_property_not_found(self):
        exc = self._process("Campo não existe: Parceiro->XPTO")

        assert type(exc) is ServiceRequestPropertyNameException
        assert "couldn't find the field XPTO on entity Parceiro in Parceiro" in str(exc)

    def test_missing_relation(self):
        exc = self._process("Relacionamento: 'Cidade' não encontrado em: 'Parceiro'")

        assert type(exc) is ServiceRequestInvalidRelationException
        assert str(exc) == "The relation Cidade of entity Parceiro cannot be found on Sankhya"

    @pytest.mark.parametrize(
        "message",
        [
            # Texto reconhecido pelo padrão do .NET (EntityValidation.cs:86-90)
            'A instrução INSERT conflitou com a restrição do FOREIGN KEY "FK_TGFPAR_TSICID". '
            'O conflito ocorreu no bando de dados "SANKHYA", tabela "dbo.TSICID", column \'CODCID\'.',
            # Texto do SQL Server pt-BR
            'A instrução INSERT conflitou com a restrição do FOREIGN KEY "FK_TGFPAR_TSICID". '
            'O conflito ocorreu no banco de dados "SANKHYA", tabela "dbo.TSICID", column \'CODCID\'.',
        ],
    )
    def test_foreign_key_restriction(self, message):
        response = _status_response(message)
        exc = self._process(message, response=response)

        assert type(exc) is ServiceRequestForeignKeyException
        assert str(exc) == "The value supplied to dbo.TSICID.CODCID reference isn't valid."
        assert exc.response is response

    def test_duplicated_document(self):
        message = "CNPJ/CPF já existente para o parceiro: 'João da Silva'"
        response = _status_response(message)
        exc = self._process(message, response=response)

        assert type(exc) is ServiceRequestDuplicatedDocumentException
        assert str(exc) == "The partner João da Silva has the document duplicated with another partner"
        assert exc.response is response

    def test_business_rule_restriction(self):
        message = (
            'A regra "Validação de Crédito" não permitiu a operação.\r\n'
            "Cliente com limite de crédito excedido."
        )
        response = _status_response(message)
        exc = self._process(message, response=response)

        assert type(exc) is ServiceRequestBusinessRuleRestrictionException
        assert exc.business_rule_name == "Validação de Crédito"
        assert exc.error_message == "Cliente com limite de crédito excedido."
        assert exc.response is response

    def test_full_transaction_logs(self):
        message = " Log de transações do banco de dados 'SANKHYA' cheio devido a 'LOG_BACKUP'."
        response = _status_response(message)
        exc = self._process(message, response=response)

        assert type(exc) is ServiceRequestFullTransactionLogsException
        assert str(exc) == "The transaction logs of 'SANKHYA' database is full"
        assert exc.database == "SANKHYA"
        assert exc.response is response

    def test_missing_attribute(self):
        exc = self._process("É necessário informar o atributo 'NOMEPARC'")

        assert type(exc) is ServiceRequestAttributeException
        assert str(exc) == "The service CRUD - Retrieve requires the attribute NOMEPARC"

    def test_property_width_error(self):
        exc = self._process(
            "Propriedade 'NOMEPARC' com largura acima do limite: (120 > 100)"
        )

        assert type(exc) is ServiceRequestPropertyWidthException
        assert exc.property_name == "NOMEPARC"
        assert exc.allowed_width == 100
        assert "Current width: 120. Width allowed: 100" in str(exc)

    def test_unmatched_message_raises_unexpected_result(self):
        message = "Mensagem desconhecida do servidor"
        response = _status_response(message)
        exc = self._process(message, response=response)

        assert type(exc) is ServiceRequestUnexpectedResultException
        assert exc.error_message == message
        assert exc.response is response


class TestRegexPatterns:
    """Testes para padrões regex."""

    def test_patterns_are_entity_validation_patterns(self):
        """Os padrões do helper são os de EntityValidation, como no .NET."""
        for name in (
            "PROPERTY_VALUE_ERROR_PATTERN",
            "PROPERTY_NAME_ERROR_PATTERN",
            "PROPERTY_NAME_INVALID_ERROR_PATTERN",
            "PROPERTY_NAME_ASSOCIATION_ERROR_PATTERN",
            "PROPERTY_NOT_FOUND_PATTERN",
            "MISSING_RELATION_PATTERN",
            "PROPERTY_FOREIGN_KEY_RESTRICTION_PATTERN",
            "DUPLICATED_DOCUMENT_PATTERN",
            "BUSINESS_RULE_RESTRICTION_PATTERN",
            "FULL_TRANSACTION_LOGS_PATTERN",
            "MISSING_ATTRIBUTE_PATTERN",
            "PROPERTY_WIDTH_ERROR_PATTERN",
            "REFERENCE_FIELDS_FIRST_LEVEL_PATTERN",
            "REFERENCE_FIELDS_SECOND_LEVEL_PATTERN",
        ):
            assert getattr(status_message_helper, name) is getattr(EntityValidation, name), name

    def test_property_value_error_pattern(self):
        """Testa padrão de erro de valor de propriedade (EntityValidation.cs:32-36)."""
        text = "Erro ao obter valor da propriedade 'CODPARC'"
        match = PROPERTY_VALUE_ERROR_PATTERN.search(text)

        assert match is not None
        assert match.group("propertyName") == "CODPARC"

    def test_property_name_error_pattern(self):
        """Testa padrão de erro de nome de propriedade (EntityValidation.cs:41-45)."""
        text = "Descritor do campo 'XPTO' inválido"
        match = PROPERTY_NAME_ERROR_PATTERN.search(text)

        assert match is not None
        assert match.group("propertyName") == "XPTO"

    def test_reference_first_level_pattern_ignores_custom_fields(self):
        """Campos AD_ não são referências (EntityValidation.cs:14-18, (?!AD))."""
        assert REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match("AD_CAMPO") is None

    def test_reference_first_level_pattern(self):
        """Testa padrão de referência primeiro nível."""
        text = "Parceiro_NomeParceiro"
        match = REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(text)
        
        assert match is not None
        assert match.group("entity") == "Parceiro"
        assert match.group("field") == "NomeParceiro"

    def test_reference_second_level_pattern(self):
        """Testa padrão de referência segundo nível."""
        text = "Produto_Familia_Descricao"
        match = REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(text)
        
        assert match is not None
        assert match.group("parentEntity") == "Produto"
        assert match.group("entity") == "Familia"
        assert match.group("field") == "Descricao"

    def test_first_level_pattern_no_match_for_simple_field(self):
        """Padrão primeiro nível não deve casar com campo simples."""
        text = "CODPARC"
        match = REFERENCE_FIELDS_FIRST_LEVEL_PATTERN.match(text)
        
        assert match is None

    def test_second_level_pattern_no_match_for_first_level(self):
        """Padrão segundo nível não deve casar com primeiro nível."""
        text = "Parceiro_Nome"
        match = REFERENCE_FIELDS_SECOND_LEVEL_PATTERN.match(text)
        
        assert match is None
