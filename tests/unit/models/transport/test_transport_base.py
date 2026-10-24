"""
Testes unitários para a serialização XML genérica de TransportEntityBase.

Usa uma entidade declarada neste módulo com ``from __future__ import annotations``
e tipos importados apenas aqui (datetime, timedelta, Decimal, enum), garantindo que
a desserialização resolve os tipos dos campos a partir do módulo da entidade e
converte os valores do protocolo Sankhya ("S"/"N", valor interno do enum, HHMMSS).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from lxml import etree
from pydantic import Field

from sankhya_sdk.attributes.decorators import (
    entity,
    entity_element,
    entity_key,
    entity_reference,
)
from sankhya_sdk.enums.fiscal_person_type import FiscalPersonType
from sankhya_sdk.models.transport.base import TransportEntityBase
from sankhya_sdk.models.transport.code_bars import CodeBars
from sankhya_sdk.models.transport.state import State


@entity("EntidadeTeste")
class _SampleEntity(TransportEntityBase):
    """Entidade de teste com campos de tipos que exigem conversão."""

    code: int = entity_key(entity_element("CODIGO", default=0))
    active: Optional[bool] = entity_element("ATIVO", default=None)
    fiscal_type: Optional[FiscalPersonType] = entity_element("TIPPESSOA", default=None)
    movement_time: Optional[timedelta] = entity_element("HRMOV", default=None)
    value: Optional[Decimal] = entity_element("VALOR", default=None)
    date_changed: Optional[datetime] = entity_element("DTALTER", default=None)
    state: Optional[State] = entity_reference(default=None)
    state_alias: Optional[State] = entity_reference("UnidadeFederativa_AD001", default=None)
    codes_bars: List[CodeBars] = Field(default_factory=list)


class TestTransportEntityBaseDeserialization:
    """Testes de conversão de tipos na desserialização XML."""

    def test_from_xml_converts_sankhya_values_to_field_types(self):
        """Testa conversão de S/N, enum, HHMMSS, Decimal e data a partir do XML."""
        xml_string = """
        <EntidadeTeste>
            <CODIGO>7</CODIGO>
            <ATIVO>S</ATIVO>
            <TIPPESSOA>J</TIPPESSOA>
            <HRMOV>093015</HRMOV>
            <VALOR>10.50</VALOR>
            <DTALTER>01/02/2024 10:20:30</DTALTER>
        </EntidadeTeste>
        """
        entity_obj = _SampleEntity.from_xml(etree.fromstring(xml_string))

        assert entity_obj.code == 7
        assert entity_obj.active is True
        assert entity_obj.fiscal_type is FiscalPersonType.CORPORATION
        assert entity_obj.movement_time == timedelta(hours=9, minutes=30, seconds=15)
        assert entity_obj.value == Decimal("10.50")
        assert entity_obj.date_changed == datetime(2024, 2, 1, 10, 20, 30)

    def test_from_xml_converts_sankhya_false_boolean(self):
        """Testa que "N" é convertido para False (e não rejeitado como string)."""
        xml_string = "<EntidadeTeste><CODIGO>1</CODIGO><ATIVO>N</ATIVO></EntidadeTeste>"

        entity_obj = _SampleEntity.from_xml(etree.fromstring(xml_string))

        assert entity_obj.active is False

    def test_from_xml_reads_references_and_collections(self):
        """Testa desserialização de referências (com e sem alias) e coleções."""
        xml_string = """
        <EntidadeTeste>
            <CODIGO>1</CODIGO>
            <UnidadeFederativa>
                <CODUF>35</CODUF>
                <UF>SP</UF>
            </UnidadeFederativa>
            <UnidadeFederativa_AD001>
                <UnidadeFederativa>
                    <CODUF>33</CODUF>
                    <UF>RJ</UF>
                </UnidadeFederativa>
            </UnidadeFederativa_AD001>
            <CodigoBarras>
                <CODBARRA>789</CODBARRA>
            </CodigoBarras>
        </EntidadeTeste>
        """
        entity_obj = _SampleEntity.from_xml(etree.fromstring(xml_string))

        assert isinstance(entity_obj.state, State)
        assert entity_obj.state.code == 35
        assert entity_obj.state.initials == "SP"
        assert isinstance(entity_obj.state_alias, State)
        assert entity_obj.state_alias.code == 33
        assert entity_obj.state_alias.initials == "RJ"
        assert [cb.code for cb in entity_obj.codes_bars] == ["789"]


class TestTransportEntityBaseSerialization:
    """Testes de serialização XML e simetria com a desserialização."""

    def test_to_xml_writes_sankhya_values(self):
        """Testa que bool, enum e timedelta são escritos no formato Sankhya."""
        entity_obj = _SampleEntity(
            code=1,
            active=False,
            fiscal_type=FiscalPersonType.CORPORATION,
            movement_time=timedelta(hours=9, minutes=5, seconds=3),
        )

        xml = entity_obj.to_xml()

        assert xml.find("ATIVO").text == "N"
        assert xml.find("TIPPESSOA").text == "J"
        assert xml.find("HRMOV").text == "090503"

    def test_to_xml_reference_without_alias_is_not_double_wrapped(self):
        """Testa que referência sem alias gera <Entidade> direto, sem <Entidade><Entidade>."""
        entity_obj = _SampleEntity(code=1, state=State(code=35, initials="SP"))

        xml = entity_obj.to_xml()

        state_elem = xml.find("UnidadeFederativa")
        assert state_elem is not None
        assert state_elem.find("UnidadeFederativa") is None
        assert state_elem.find("CODUF").text == "35"
        assert state_elem.find("UF").text == "SP"

    def test_to_xml_reference_with_alias_wraps_entity(self):
        """Testa que referência com alias gera <Alias><Entidade>...</Entidade></Alias>."""
        entity_obj = _SampleEntity(code=1, state_alias=State(code=33, initials="RJ"))

        xml = entity_obj.to_xml()

        assert xml.find("UnidadeFederativa") is None
        nested = xml.find("UnidadeFederativa_AD001/UnidadeFederativa")
        assert nested is not None
        assert nested.find("CODUF").text == "33"

    def test_roundtrip_preserves_typed_values(self):
        """Testa roundtrip to_xml -> from_xml com todos os tipos convertidos."""
        original = _SampleEntity(
            code=5,
            active=True,
            fiscal_type=FiscalPersonType.CORPORATION,
            movement_time=timedelta(hours=23, minutes=59, seconds=58),
            value=Decimal("1.25"),
            date_changed=datetime(2024, 12, 31, 23, 0, 1),
            state=State(code=35, initials="SP"),
            state_alias=State(code=33, initials="RJ"),
            codes_bars=[CodeBars(code="111"), CodeBars(code="222")],
        )

        xml_string = etree.tostring(original.to_xml(), encoding="unicode")
        restored = _SampleEntity.from_xml(etree.fromstring(xml_string))

        assert restored.code == original.code
        assert restored.active is True
        assert restored.fiscal_type is FiscalPersonType.CORPORATION
        assert restored.movement_time == original.movement_time
        assert restored.value == original.value
        assert restored.date_changed == original.date_changed
        assert restored.state.code == 35
        assert restored.state_alias.code == 33
        assert [cb.code for cb in restored.codes_bars] == ["111", "222"]
