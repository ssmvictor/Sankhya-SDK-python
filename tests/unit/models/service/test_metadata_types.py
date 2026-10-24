"""
Testes unitários para os tipos de metadados de serviço (Pager, Key, Session).

O formato XML esperado segue o SDK .NET (Src/Sankhya/Service/Key.cs,
Src/Sankhya/Service/Session.cs e RequestBody.cs).
"""

from lxml import etree

from sankhya_sdk.models.service.metadata_types import Pager
from sankhya_sdk.models.service.response_body import ResponseBody


class TestPager:
    """Testes para a classe Pager."""

    def test_from_xml_parses_integer_attributes(self):
        """Testa que totalPages/totalRecords são convertidos para int."""
        element = etree.fromstring(
            '<pager totalPages="3" totalRecords="250" pagerId="PG-1"/>'
        )

        pager = Pager.from_xml(element)

        assert pager.total_pages == 3
        assert pager.total_records == 250
        assert pager.pager_id == "PG-1"

    def test_from_xml_without_attributes_returns_none(self):
        """Testa que atributos ausentes resultam em None."""
        pager = Pager.from_xml(etree.fromstring("<pager/>"))

        assert pager.total_pages is None
        assert pager.total_records is None
        assert pager.pager_id is None

    def test_from_xml_invalid_integer_returns_none(self):
        """Testa que valores não numéricos resultam em None."""
        element = etree.fromstring('<pager totalPages="abc" totalRecords=""/>')

        pager = Pager.from_xml(element)

        assert pager.total_pages is None
        assert pager.total_records is None

    def test_round_trip(self):
        """Testa que to_xml/from_xml preservam os valores."""
        original = Pager(total_pages=2, total_records=180, pager_id="PAGER-42")

        restored = Pager.from_xml(original.to_xml())

        assert restored == original

    def test_response_body_parses_pager_element(self):
        """Testa que ResponseBody.from_xml desserializa o elemento <pager>."""
        element = etree.fromstring(
            '<responseBody><pager totalPages="5" totalRecords="42"/></responseBody>'
        )

        body = ResponseBody.from_xml(element)

        assert body.pager.total_pages == 5
        assert body.pager.total_records == 42
