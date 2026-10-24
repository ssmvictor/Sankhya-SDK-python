"""
Testes unitários para os tipos de nota fiscal (invoice_types).

Os formatos esperados vêm do SDK .NET de referência
(Sankhya-SDK-dotnet/Src/Sankhya/Service/Invoice.cs, Invoices.cs e
InvoicesWithCurrency.cs) e dos payloads montados em
KnowServicesRequestWrapper.Bill/DuplicateInvoice.
"""

from datetime import datetime, timedelta

from lxml import etree

from sankhya_sdk.enums.billing_type import BillingType
from sankhya_sdk.models.service.invoice_types import (
    Invoice,
    Invoices,
    InvoicesWithCurrency,
)
from sankhya_sdk.models.service.service_response import ServiceResponse


def _parse(xml: str) -> etree._Element:
    return etree.fromstring(xml)


class TestInvoiceResponseFields:
    """Campos de <nota> lidos das respostas de faturamento/duplicação."""

    def test_from_xml_reads_element_text_as_value(self):
        """.NET Invoice.Value é [XmlText]: <nota>12345</nota>."""
        invoice = Invoice.from_xml(_parse("<nota>12345</nota>"))

        assert invoice.value == "12345"

    def test_from_xml_value_is_none_without_text(self):
        """Sem texto, value fica None (e não string vazia)."""
        invoice = Invoice.from_xml(_parse('<nota numero="1"><dtMov>x</dtMov></nota>'))

        assert invoice.value is None

    def test_from_xml_reads_duplication_attributes(self):
        """nuNota/nuNotaOrig (.NET SingleNumberDuplicationDestiny/Source)."""
        invoice = Invoice.from_xml(_parse('<nota nuNota="54321" nuNotaOrig="12345"/>'))

        assert invoice.single_number_duplication_destiny == 54321
        assert invoice.single_number_duplication_source == 12345

    def test_from_xml_reads_upper_case_nunota_attribute(self):
        """Atributo NUNOTA (.NET SingleNumberDuplication)."""
        invoice = Invoice.from_xml(_parse('<nota NUNOTA="777"/>'))

        assert invoice.single_number_duplication == 777
        # O atributo legado "nunota" (minúsculo) continua mapeado separadamente
        assert invoice.unique_number is None

    def test_bill_response_value_through_service_response(self):
        """Resposta real do faturamento: <notas><nota>NUNOTA</nota></notas>."""
        response = ServiceResponse.from_xml_string(
            '<serviceResponse serviceName="SelecaoDocumentoSP.faturar" status="1">'
            "<responseBody><notas><nota>12345</nota></notas></responseBody>"
            "</serviceResponse>"
        )

        assert response.response_body.invoices.items[0].value == "12345"

    def test_duplicate_response_destiny_through_service_response(self):
        """Resposta real da duplicação: <nota nuNota=... nuNotaOrig=.../>."""
        response = ServiceResponse.from_xml_string(
            '<serviceResponse serviceName="CACSP.duplicarNota" status="1">'
            '<responseBody><notas><nota nuNota="54321" nuNotaOrig="12345"/>'
            "</notas></responseBody></serviceResponse>"
        )

        invoice = response.response_body.invoices.items[0]
        assert invoice.single_number_duplication_destiny == 54321
        assert invoice.single_number_duplication_source == 12345


class TestInvoiceRequestFields:
    """Serialização de <nota> para requisições."""

    def test_to_xml_writes_value_as_text(self):
        xml = Invoice(value="12345").to_xml()

        assert xml.tag == "nota"
        assert xml.text == "12345"
        assert len(xml) == 0
        assert dict(xml.attrib) == {}

    def test_value_accepts_int(self):
        """O .NET tipa Value como int; aceita int e guarda como texto."""
        invoice = Invoice(value=12345)

        assert invoice.value == "12345"
        assert invoice.to_xml().text == "12345"

    def test_to_xml_writes_duplication_attributes(self):
        xml = Invoice(
            single_number_duplication=1,
            single_number_duplication_destiny=2,
            single_number_duplication_source=3,
        ).to_xml()

        assert xml.get("NUNOTA") == "1"
        assert xml.get("nuNota") == "2"
        assert xml.get("nuNotaOrig") == "3"

    def test_unset_new_fields_are_not_serialized(self):
        xml = Invoice(unique_number=10).to_xml()

        assert dict(xml.attrib) == {"nunota": "10"}
        assert xml.text is None

    def test_existing_fields_round_trip(self):
        """Campos existentes continuam funcionando."""
        original = Invoice(
            number=5,
            unique_number=10,
            series="1",
            company_code=2,
            partner_code=3,
            top_code=4,
            issue_date="01/01/2024",
            total_value=99.5,
            extra_data={"justificativa": "teste"},
        )

        parsed = Invoice.from_xml(original.to_xml())

        assert parsed.number == 5
        assert parsed.unique_number == 10
        assert parsed.series == "1"
        assert parsed.company_code == 2
        assert parsed.partner_code == 3
        assert parsed.top_code == 4
        assert parsed.issue_date == "01/01/2024"
        assert parsed.total_value == 99.5
        assert parsed.extra_data == {"justificativa": "teste"}


class TestInvoicesBillPayload:
    """Payload de SelecaoDocumentoSP.faturar (.NET KnowServicesRequestWrapper.Bill)."""

    def _bill_invoices(self, **overrides) -> Invoices:
        data = dict(
            billing_type=BillingType.NORMAL,
            code_operation_type=1100,
            date_billing=None,
            date_exit=None,
            time_exit=None,
            is_date_validated=True,
            invoices_with_currency=InvoicesWithCurrency(currency_value="undefined"),
            items=[Invoice(value="12345")],
            one_invoice_for_each=True,
        )
        data.update(overrides)
        return Invoices(**data)

    def test_attributes_match_dotnet(self):
        xml = self._bill_invoices().to_xml()

        assert xml.tag == "notas"
        assert dict(xml.attrib) == {
            "codTipOper": "1100",
            "dataValidada": "S",
            "umaNotaParaCada": "S",
            # .NET define DateBillingNullable/DateExitNullable/TimeExitNullable
            # = null, serializados como atributos vazios
            "dtFaturamento": "",
            "dtSaida": "",
            "hrSaida": "",
            "tipoFaturamento": "FaturamentoNormal",
        }

    def test_children_match_dotnet(self):
        xml = self._bill_invoices().to_xml()

        assert [child.tag for child in xml] == ["notasComMoeda", "nota"]
        assert xml[0].get("valorMoeda") == "undefined"
        assert xml[1].text == "12345"

    def test_series_and_direct_billing(self):
        """Com série, o .NET troca para BillingType.Direct e envia serie."""
        xml = self._bill_invoices(
            billing_type=BillingType.DIRECT, series=2
        ).to_xml()

        assert xml.get("tipoFaturamento") == "FaturamentoDireto"
        assert xml.get("serie") == "2"

    def test_dates_with_values_use_invariant_culture(self):
        xml = self._bill_invoices(
            date_billing=datetime(2026, 10, 24, 8, 5, 9),
            date_exit=datetime(2026, 1, 2, 23, 0, 0),
            time_exit=timedelta(hours=14, minutes=30),
        ).to_xml()

        assert xml.get("dtFaturamento") == "10/24/2026 08:05:09"
        assert xml.get("dtSaida") == "01/02/2026 23:00:00"
        assert xml.get("hrSaida") == "14:30:00"

    def test_round_trip(self):
        original = self._bill_invoices()

        parsed = Invoices.from_xml(original.to_xml())

        assert parsed.billing_type == BillingType.NORMAL
        assert parsed.code_operation_type == 1100
        assert parsed.is_date_validated is True
        assert parsed.one_invoice_for_each is True
        assert parsed.invoices_with_currency.currency_value == "undefined"
        assert parsed.items[0].value == "12345"
        assert etree.tostring(parsed.to_xml()) == etree.tostring(original.to_xml())


class TestInvoicesDuplicatePayload:
    """Payload de CACSP.duplicarNota (.NET KnowServicesRequestWrapper.DuplicateInvoice)."""

    def test_attributes_and_nota_match_dotnet(self):
        xml = Invoices(
            code_operation_type_duplication=2,
            date_exit_duplication=datetime(2026, 10, 24, 13, 5, 9),
            should_update_price=False,
            should_duplicate_all_items=True,
            series=3,
            items=[Invoice(single_number_duplication=12345)],
        ).to_xml()

        assert dict(xml.attrib) == {
            "top": "2",
            "serie": "3",
            "atualizaPreco": "false",
            "duplicarTodosItens": "true",
            "dataSaida": "10/24/2026 13:05:09",
        }
        assert len(xml) == 1
        assert xml[0].tag == "nota"
        assert dict(xml[0].attrib) == {"NUNOTA": "12345"}

    def test_date_exit_explicitly_none_is_empty_attribute(self):
        """.NET atribui DateExitDuplicationNullable = dateExit mesmo se null."""
        xml = Invoices(
            code_operation_type_duplication=2,
            date_exit_duplication=None,
            items=[Invoice(single_number_duplication=1)],
        ).to_xml()

        assert xml.get("dataSaida") == ""

    def test_should_update_price_true(self):
        xml = Invoices(should_update_price=True).to_xml()

        assert xml.get("atualizaPreco") == "true"


class TestInvoicesOtherFields:
    """Demais campos de Invoices.cs."""

    def test_unset_fields_are_not_serialized(self):
        xml = Invoices(items=[Invoice(unique_number=1)]).to_xml()

        assert dict(xml.attrib) == {}
        assert [child.tag for child in xml] == ["nota"]

    def test_single_numbers_are_nunota_elements(self):
        """.NET SingleNumbers é [XmlElement("nunota")] (repetido)."""
        xml = Invoices(single_numbers=[10, 20], return_disapproved_invoices=False).to_xml()

        assert [(child.tag, child.text) for child in xml] == [
            ("nunota", "10"),
            ("nunota", "20"),
        ]
        assert xml.get("retNotasReprovadas") == "N"

    def test_single_numbers_round_trip(self):
        parsed = Invoices.from_xml(
            _parse('<notas retNotasReprovadas="S"><nunota>1</nunota><nunota>2</nunota></notas>')
        )

        assert parsed.single_numbers == [1, 2]
        assert parsed.return_disapproved_invoices is True

    def test_time_exit_with_days_and_fraction(self):
        """Formato "c" do TimeSpan: [-][d.]hh:mm:ss[.fffffff]."""
        xml = Invoices(
            time_exit=timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=500000)
        ).to_xml()

        assert xml.get("hrSaida") == "1.02:03:04.5000000"
        parsed = Invoices.from_xml(xml)
        assert parsed.time_exit == timedelta(
            days=1, hours=2, minutes=3, seconds=4, microseconds=500000
        )

    def test_empty_date_attribute_round_trips_as_set(self):
        parsed = Invoices.from_xml(_parse('<notas dtFaturamento=""/>'))

        assert parsed.date_billing is None
        assert parsed.to_xml().get("dtFaturamento") == ""

    def test_existing_items_only_usage_still_works(self):
        parsed = Invoices.from_xml(
            _parse('<notas><nota nunota="1"/><nota nunota="2"/></notas>')
        )

        assert [invoice.unique_number for invoice in parsed.items] == [1, 2]


class TestInvoicesWithCurrency:
    """<notasComMoeda valorMoeda="..."/> (.NET InvoicesWithCurrency.CurrencyValue)."""

    def test_to_xml_currency_value(self):
        xml = InvoicesWithCurrency(currency_value="undefined").to_xml()

        assert xml.tag == "notasComMoeda"
        assert dict(xml.attrib) == {"valorMoeda": "undefined"}

    def test_from_xml_currency_value(self):
        parsed = InvoicesWithCurrency.from_xml(
            _parse('<notasComMoeda valorMoeda="undefined"/>')
        )

        assert parsed.currency_value == "undefined"
