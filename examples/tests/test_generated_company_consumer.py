import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import pytest
import requests
from yarl import URL

from examples.src.company_consumer import Company, CompanyConsumer
from pact import Consumer, Format, Like, Provider

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from pact.pact import Pact

logger = logging.getLogger(__name__)

MOCK_URL = URL("http://localhost:8080")


@pytest.fixture
def company_consumer() -> CompanyConsumer:
    return CompanyConsumer(str(MOCK_URL))


@pytest.fixture(scope="module")
def pact(broker: URL, pact_dir: Path) -> Generator[Pact, Any, None]:
    consumer = Consumer("CompanyConsumer")
    pact = consumer.has_pact_with(
        Provider("CompanyProvider"),
        pact_dir=pact_dir,
        publish_to_broker=True,
        host_name=MOCK_URL.host,
        port=MOCK_URL.port,
        broker_base_url=str(broker),
        broker_username=broker.user,
        broker_password=broker.password,
    )

    pact.start_service()
    yield pact
    pact.stop_service()


def test_get_existing_company(pact: Pact, company_consumer: CompanyConsumer) -> None:
    expected: dict[str, Any] = {
        "id": Format().integer,
        "name": "Tech Innovators",
        "created_on": Format().iso_8601_datetime(),
    }

    (
        pact.given("company 456 exists")
        .upon_receiving("a request for company 456")
        .with_request("get", "/Companys/456")
        .will_respond_with(200, body=Like(expected))
    )

    with pact:
        company = company_consumer.get_Company(456)

        assert isinstance(company, Company)
        assert company.name == "Tech Innovators"

        pact.verify()


def test_get_unknown_company(pact: Pact, company_consumer: CompanyConsumer) -> None:
    expected = {"detail": "Company not found"}

    (
        pact.given("company 456 doesn't exist")
        .upon_receiving("a request for company 456")
        .with_request("get", "/Companys/456")
        .will_respond_with(404, body=Like(expected))
    )

    with pact:
        with pytest.raises(requests.HTTPError) as excinfo:
            company_consumer.get_Company(456)
        assert excinfo.value.response is not None
        assert excinfo.value.response.status_code == HTTPStatus.NOT_FOUND
        pact.verify()


def test_create_company(pact: Pact, company_consumer: CompanyConsumer) -> None:
    body = {"name": "Tech Innovators"}
    expected_response: dict[str, Any] = {
        "id": 457,
        "name": "Tech Innovators",
        "created_on": Format().iso_8601_datetime(),
    }

    (
        pact.given("create company 457")
        .upon_receiving("A request to create a new company")
        .with_request(
            method="POST",
            path="/Companys/",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        .will_respond_with(
            status=200,
            body=Like(expected_response),
        )
    )

    with pact:
        company = company_consumer.create_Company(name="Tech Innovators")
        assert company.id > 0
        assert company.name == "Tech Innovators"
        assert company.created_on

        pact.verify()


def test_delete_request_to_delete_company(pact: Pact, company_consumer: CompanyConsumer) -> None:
    (
        pact.given("delete the company 457")
        .upon_receiving("a request for deleting company")
        .with_request(method="DELETE", path="/Companys/457")
        .will_respond_with(status=204)
    )

    with pact:
        company_consumer.delete_Company(457)

        pact.verify()