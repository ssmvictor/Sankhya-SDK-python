# -*- coding: utf-8 -*-
"""
Testes unitários para entity_dynamic_serialization.py
"""

import pytest
from datetime import datetime
from decimal import Decimal

from sankhya_sdk.helpers.entity_dynamic_serialization import (
    EntityDynamicSerialization,
    Metadata,
)
from sankhya_sdk.enums.reference_level import ReferenceLevel


class TestMetadata:
    """Testes para Metadata."""

    def test_initialization_empty(self):
        """Verifica inicialização vazia."""
        metadata = Metadata()
        assert metadata.fields == []

    def test_initialization_with_fields(self):
        """Verifica inicialização com campos."""
        fields = [{"name": "CODPARC"}, {"name": "NOMEPARC"}]
        metadata = Metadata(fields=fields)
        
        assert len(metadata.fields) == 2


class TestEntityDynamicSerialization:
    """Testes para EntityDynamicSerialization."""

    def test_initialization_empty(self):
        """Verifica inicialização vazia."""
        serializer = EntityDynamicSerialization()
        
        assert serializer.dictionary == {}

    def test_initialization_with_data(self):
        """Verifica inicialização com dados."""
        data = {"CODPARC": "123", "NOMEPARC": "Test"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.dictionary == data

    def test_get_member(self):
        """Verifica get_member."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.get_member("CODPARC") == "123"

    def test_get_member_case_insensitive(self):
        """
        Verifica que get_member NÃO faz busca case-insensitive.
        
        Assim como TryGetMember do DynamicSerialization (.NET), a busca é
        exata: não há fallback para uppercase em get_member.
        """
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.get_member("codparc") is None
        # O valor continua acessível pela chave exata
        assert serializer.dictionary.get("CODPARC") == "123"

    def test_get_member_returns_falsy_values(self):
        """Verifica que valores falsy (0, "", False) não são descartados."""
        data = {"ativo": False, "vlrdesc": 0, "obs": ""}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.get_member("ativo") is False
        assert serializer.get_member("vlrdesc") == 0
        assert serializer.get_member("obs") == ""

    def test_get_member_does_not_fall_through_to_uppercase_key(self):
        """Verifica que a chave exata prevalece mesmo com valor falsy."""
        data = {"codparc": 0, "CODPARC": 5}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer.get_member("codparc") == 0
        assert serializer.get_member("CODPARC") == 5

    def test_get_member_roundtrip_uppercase_filter(self):
        """
        Verifica que get_member lê o que set_member gravou (uppercase).

        Como no DynamicSerialization (.NET), SetMember guarda a chave como
        informada e TryGetMember faz busca exata; o filtro uppercase só é
        aplicado na serialização.
        """
        serializer = EntityDynamicSerialization(key_filter="uppercase")
        serializer.set_member("codparc", "123")
        
        assert serializer.get_member("codparc") == "123"
        assert serializer.get_member("CODPARC") is None
        assert serializer.to_dict() == {"CODPARC": "123"}

    def test_get_member_roundtrip_lowercase_filter(self):
        """Verifica que get_member lê o que set_member gravou (lowercase)."""
        serializer = EntityDynamicSerialization(key_filter="lowercase")
        serializer.set_member("CODPARC", "123")
        
        assert serializer.get_member("CODPARC") == "123"
        assert serializer.get_member("codparc") is None
        assert serializer.to_dict() == {"codparc": "123"}

    def test_get_member_does_not_apply_key_filter(self):
        """TryGetMember (.NET) não normaliza o nome procurado."""
        serializer = EntityDynamicSerialization(
            {"codparc": "1"}, key_filter="uppercase"
        )

        assert serializer.get_member("codparc") == "1"
        assert serializer.get_member("CODPARC") is None

    def test_set_member(self):
        """Verifica set_member."""
        serializer = EntityDynamicSerialization()
        serializer.set_member("CODPARC", "123")
        
        assert serializer.dictionary["CODPARC"] == "123"

    def test_set_member_uppercase_filter(self):
        """
        Verifica set_member com filtro uppercase.

        A chave é armazenada como informada (SetMember/GetDictionary no .NET)
        e o filtro é aplicado apenas na serialização (to_dict).
        """
        serializer = EntityDynamicSerialization(key_filter="uppercase")
        serializer.set_member("codparc", "123")
        
        assert serializer.dictionary == {"codparc": "123"}
        assert "CODPARC" in serializer.to_dict()

    def test_set_member_lowercase_filter(self):
        """Verifica set_member com filtro lowercase."""
        serializer = EntityDynamicSerialization(key_filter="lowercase")
        serializer.set_member("CODPARC", "123")
        
        assert serializer.dictionary == {"CODPARC": "123"}
        assert "codparc" in serializer.to_dict()

    def test_to_dict_without_filter_keeps_keys(self):
        """Sem filtro, a serialização mantém as chaves e não altera o original."""
        serializer = EntityDynamicSerialization({"CodParc": "1"})

        serialized = serializer.to_dict()
        serialized["X"] = "2"

        assert serialized["CodParc"] == "1"
        assert serializer.dictionary == {"CodParc": "1"}

    def test_contains(self):
        """Verifica operador __contains__."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert "CODPARC" in serializer

    def test_contains_is_exact_like_get_member(self):
        """__contains__ e get_member usam a mesma busca exata."""
        serializer = EntityDynamicSerialization({"CODPARC": "123"})

        assert "codparc" not in serializer
        assert serializer.get_member("codparc") is None

    def test_getitem(self):
        """Verifica operador __getitem__."""
        data = {"CODPARC": "123"}
        serializer = EntityDynamicSerialization(data)
        
        assert serializer["CODPARC"] == "123"

    def test_getitem_returns_falsy_values(self):
        """__getitem__ não descarta valores falsy (0, "", False)."""
        serializer = EntityDynamicSerialization(
            {"vlrdesc": 0, "obs": "", "ativo": False}
        )

        assert serializer["vlrdesc"] == 0
        assert serializer["obs"] == ""
        assert serializer["ativo"] is False

    def test_getitem_falsy_value_does_not_fall_through_to_uppercase(self):
        """Valor falsy na chave exata não é trocado pelo da chave uppercase."""
        serializer = EntityDynamicSerialization({"codparc": 0, "CODPARC": 5})

        assert serializer["codparc"] == 0

    def test_getitem_is_exact_like_get_member(self):
        """__getitem__ e get_member usam a mesma busca exata."""
        serializer = EntityDynamicSerialization({"CODPARC": "123"})

        assert serializer["codparc"] is None
        assert serializer["codparc"] == serializer.get_member("codparc")

    def test_setitem(self):
        """Verifica operador __setitem__."""
        serializer = EntityDynamicSerialization()
        serializer["CODPARC"] = "123"
        
        assert serializer["CODPARC"] == "123"

    def test_repr(self):
        """Verifica __repr__."""
        data = {"key": "value"}
        serializer = EntityDynamicSerialization(data)
        
        assert "EntityDynamicSerialization" in repr(serializer)
        assert "key" in repr(serializer)


class TestValueConversion:
    """Testes para conversão de valores."""

    @pytest.fixture
    def serializer(self):
        return EntityDynamicSerialization()

    def test_convert_to_bool_true(self, serializer):
        """Verifica conversão para bool True."""
        assert serializer._convert_to_bool("true") is True
        assert serializer._convert_to_bool("1") is True
        assert serializer._convert_to_bool("s") is True
        assert serializer._convert_to_bool("sim") is True
        assert serializer._convert_to_bool("yes") is True
        assert serializer._convert_to_bool("y") is True

    def test_convert_to_bool_false(self, serializer):
        """Verifica conversão para bool False."""
        assert serializer._convert_to_bool("false") is False
        assert serializer._convert_to_bool("0") is False
        assert serializer._convert_to_bool("n") is False
        assert serializer._convert_to_bool("no") is False

    def test_convert_to_datetime_formats(self, serializer):
        """Verifica conversão de diferentes formatos de data."""
        # Formato brasileiro
        dt = serializer._convert_to_datetime("25/12/2024")
        assert dt.day == 25
        assert dt.month == 12
        assert dt.year == 2024
        
        # Formato ISO
        dt = serializer._convert_to_datetime("2024-12-25")
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 25

    def test_convert_to_datetime_with_time(self, serializer):
        """Verifica conversão de data com hora."""
        dt = serializer._convert_to_datetime("25/12/2024 14:30:45")
        
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 45

    def test_convert_to_datetime_invalid(self, serializer):
        """Verifica erro com formato inválido."""
        with pytest.raises(ValueError):
            serializer._convert_to_datetime("invalid-date")


class TestConvertToTypeFromStrings:
    """
    Conversão de valores texto (como lidos do XML) para entidades tipadas.

    No .NET, ParseDynamic mantém todos os valores como string e
    ConvertToType converte cada um para o tipo da propriedade.
    """

    def test_partner_from_string_values(self):
        """Documentos mantêm zeros à esquerda; códigos e flags S/N são convertidos."""
        from sankhya_sdk.models.transport.partner import Partner

        serializer = EntityDynamicSerialization({
            "CODPARC": "42",
            "NOMEPARC": "Cliente",
            "CGC_CPF": "01234567890",
            "CEP": "01310100",
            "ATIVO": "S",
            "CLIENTE": "N",
            "CODCID": "007",
        })

        partner = serializer.convert_to_type(Partner)

        assert partner.code == 42
        assert partner.name == "Cliente"
        assert partner.document == "01234567890"
        assert partner.zip_code == "01310100"
        assert partner.is_active is True
        assert partner.is_client is False
        assert partner.code_city == 7

    def test_enum_from_internal_value(self):
        """Enums são convertidos pelo valor interno (TIPPESSOA "F"/"J")."""
        from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType
        from sankhya_sdk.models.transport.partner import Partner

        individual = EntityDynamicSerialization(
            {"CODPARC": "1", "TIPPESSOA": "F"}
        ).convert_to_type(Partner)
        corporation = EntityDynamicSerialization(
            {"CODPARC": "2", "TIPPESSOA": "J"}
        ).convert_to_type(Partner)

        assert individual.fiscal_type is FiscalPersonType.INDIVIDUAL
        assert corporation.fiscal_type is FiscalPersonType.CORPORATION

    def test_timedelta_from_hhmmss(self):
        """Horários no formato HHMMSS (HRMOV) viram timedelta."""
        from datetime import timedelta

        from sankhya_sdk.models.transport.invoice_header import InvoiceHeader

        header = EntityDynamicSerialization(
            {"NUNOTA": "10", "HRMOV": "103015"}
        ).convert_to_type(InvoiceHeader)

        assert header.movement_time == timedelta(hours=10, minutes=30, seconds=15)

    def test_convert_to_bool_uses_sankhya_format(self):
        """Valores S/N e true/false, como deserialize_bool da camada de transporte."""
        serializer = EntityDynamicSerialization()

        assert serializer._convert_to_bool("S") is True
        assert serializer._convert_to_bool("N") is False
        assert serializer._convert_to_bool("true") is True
        assert serializer._convert_to_bool("false") is False


class TestChangeKeys:
    """Testes para change_keys."""

    def test_change_keys_success(self):
        """Verifica renomeação de chaves."""
        data = {"f0": "123", "f1": "Test"}
        serializer = EntityDynamicSerialization(data)
        
        new_keys = Metadata(fields=[
            {"name": "CODPARC"},
            {"name": "NOMEPARC"},
        ])
        
        serializer.change_keys(new_keys)
        
        assert "CODPARC" in serializer.dictionary
        assert serializer.dictionary["CODPARC"] == "123"

    def test_change_keys_mismatch(self):
        """Verifica erro com contagem de chaves diferente."""
        data = {"f0": "123"}
        serializer = EntityDynamicSerialization(data)
        
        new_keys = Metadata(fields=[
            {"name": "CODPARC"},
            {"name": "NOMEPARC"},
        ])
        
        with pytest.raises(ValueError, match="Key count mismatch"):
            serializer.change_keys(new_keys)

    def test_change_keys_none(self):
        """Verifica que None é tratado corretamente."""
        serializer = EntityDynamicSerialization({"key": "value"})
        
        # Não deve lançar exceção
        serializer.change_keys(None)

    def test_change_keys_missing_positional_keys(self):
        """
        Chaves já nomeadas (sem fN) não são apagadas.

        No .NET, ChangeKeys acessa Dictionary["fN"] e lança exceção quando a
        chave não existe; aqui o erro é sinalizado sem alterar o dicionário.
        """
        data = {"CODPARC": "123", "NOMEPARC": "Test"}
        serializer = EntityDynamicSerialization(data)

        new_keys = Metadata(fields=[
            {"name": "CODPARC"},
            {"name": "NOMEPARC"},
        ])

        with pytest.raises(ValueError, match="Key not found"):
            serializer.change_keys(new_keys)

        assert serializer.dictionary == {"CODPARC": "123", "NOMEPARC": "Test"}


class TestLevelConversion:
    """Testes para conversão de níveis."""

    def test_level_to_int(self):
        """Verifica conversão de ReferenceLevel para int."""
        assert EntityDynamicSerialization._level_to_int(ReferenceLevel.NONE) == 0
        assert EntityDynamicSerialization._level_to_int(ReferenceLevel.FIFTH) == 5

    def test_int_to_level(self):
        """Verifica conversão de int para ReferenceLevel."""
        assert EntityDynamicSerialization._int_to_level(0) == ReferenceLevel.NONE
        assert EntityDynamicSerialization._int_to_level(5) == ReferenceLevel.FIFTH
