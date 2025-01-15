from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import pytest
import requests
from yarl import URL

from examples.src.employee_consumer import Employee, EmployeeConsumer
from pact import Consumer, Format, Like, Provider

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from pact.pact import Pact

logger = logging.getLogger(__name__)

MOCK_URL = URL("http://localhost:8080")


@pytest.fixture
def employee_consumer() -> EmployeeConsumer:
    return EmployeeConsumer(str(MOCK_URL))


@pytest.fixture(scope="module")
def pact(broker: URL, pact_dir: Path) -> Generator[Pact, Any, None]:
    consumer = Consumer("EmployeeConsumer")
    pact = consumer.has_pact_with(
        Provider("EmployeeProvider"),
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


def test_get_existing_employee(pact: Pact, employee_consumer: EmployeeConsumer) -> None:
    expected: dict[str, Any] = {
        "id": Format().integer,
        "name": "Verna Hampton",
        "created_on": Format().iso_8601_datetime(),
    }

    (
        pact.given("employee 123 exists")
        .upon_receiving("a request for employee 123")
        .with_request("get", "/employees/123")
        .will_respond_with(200, body=Like(expected))
    )

    with pact:
        employee = employee_consumer.get_employee(123)

        assert isinstance(employee, Employee)
        assert employee.name == "Verna Hampton"

        pact.verify()


def test_get_unknown_employee(pact: Pact, employee_consumer: EmployeeConsumer) -> None:
    expected = {"detail": "Employee not found"}

    (
        pact.given("employee 123 doesn't exist")
        .upon_receiving("a request for employee 123")
        .with_request("get", "/employees/123")
        .will_respond_with(404, body=Like(expected))
    )

    with pact:
        with pytest.raises(requests.HTTPError) as excinfo:
            employee_consumer.get_employee(123)
        assert excinfo.value.response is not None
        assert excinfo.value.response.status_code == HTTPStatus.NOT_FOUND
        pact.verify()


def test_create_employee(pact: Pact, employee_consumer: EmployeeConsumer) -> None:
    body = {"name": "Verna Hampton"}
    expected_response: dict[str, Any] = {
        "id": 124,
        "name": "Verna Hampton",
        "created_on": Format().iso_8601_datetime(),
    }

    (
        pact.given("create employee 124")
        .upon_receiving("A request to create a new employee")
        .with_request(
            method="POST",
            path="/employees/",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        .will_respond_with(
            status=200,
            body=Like(expected_response),
        )
    )

    with pact:
        employee = employee_consumer.create_employee(name="Verna Hampton")
        assert employee.id > 0
        assert employee.name == "Verna Hampton"
        assert employee.created_on

        pact.verify()


def test_delete_employee(pact: Pact, employee_consumer: EmployeeConsumer) -> None:
    (
        pact.given("delete the employee 124")
        .upon_receiving("a request for deleting employee")
        .with_request(method="DELETE", path="/employees/124")
        .will_respond_with(status=204)
    )

    with pact:
        employee_consumer.delete_employee(124)

        pact.verify()
