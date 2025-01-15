from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import pytest
import requests
from yarl import URL

from examples.src.consumer import User, UserConsumer
from pact import Consumer, Format, Like, Provider

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from pact.pact import Pact

logger = logging.getLogger(__name__)

MOCK_URL = URL("http://localhost:8080")


@pytest.fixture
def user_consumer() -> UserConsumer:
    return UserConsumer(str(MOCK_URL))


@pytest.fixture(scope="module")
def pact(broker: URL, pact_dir: Path) -> Generator[Pact, Any, None]:
    consumer = Consumer("UserConsumer")
    pact = consumer.has_pact_with(
        Provider("UserProvider"),
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


def test_get_existing_user(pact: Pact, user_consumer: UserConsumer) -> None:
    expected: dict[str, Any] = {
        "id": Format().integer,
        "name": "Verna Hampton",
        "created_on": Format().iso_8601_datetime(),
    }

    (
        pact.given("user 123 exists")
        .upon_receiving("a request for user 123")
        .with_request("get", "/users/123")
        .will_respond_with(200, body=Like(expected))
    )

    with pact:
        user = user_consumer.get_user(123)

        assert isinstance(user, User)
        assert user.name == "Verna Hampton"

        pact.verify()


def test_get_unknown_user(pact: Pact, user_consumer: UserConsumer) -> None:
    expected = {"detail": "User not found"}

    (
        pact.given("user 123 doesn't exist")
        .upon_receiving("a request for user 123")
        .with_request("get", "/users/123")
        .will_respond_with(404, body=Like(expected))
    )

    with pact:
        with pytest.raises(requests.HTTPError) as excinfo:
            user_consumer.get_user(123)
        assert excinfo.value.response is not None
        assert excinfo.value.response.status_code == HTTPStatus.NOT_FOUND
        pact.verify()


def test_create_user(pact: Pact, user_consumer: UserConsumer) -> None:
    body = {"name": "Verna Hampton"}
    expected_response: dict[str, Any] = {
        "id": 124,
        "name": "Verna Hampton",
        "created_on": Format().iso_8601_datetime(),
    }

    (
        pact.given("create user 124")
        .upon_receiving("A request to create a new user")
        .with_request(
            method="POST",
            path="/users/",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        .will_respond_with(
            status=200,
            body=Like(expected_response),
        )
    )

    with pact:
        user = user_consumer.create_user(name="Verna Hampton")
        assert user.id > 0
        assert user.name == "Verna Hampton"
        assert user.created_on

        pact.verify()


def test_delete_request_to_delete_user(pact: Pact, user_consumer: UserConsumer) -> None:
    (
        pact.given("delete the user 124")
        .upon_receiving("a request for deleting user")
        .with_request(method="DELETE", path="/users/124")
        .will_respond_with(status=204)
    )

    with pact:
        user_consumer.delete_user(124)

        pact.verify()