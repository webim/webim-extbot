import logging
from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient

from extbot.api_v1 import ApiV1Sample
from extbot.api_v2 import ApiV2Sample
from extbot.router import ApiVersionRouter


def make_test_app(v1_bot, v2_bot):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL)

    router = ApiVersionRouter(logger, v1_bot, v2_bot)
    routes = router.get_routes()

    app = web.Application()
    app.add_routes(routes)

    return app


@dataclass
class MockedRouterSetup:
    client: TestClient
    v1_bot_mock: Mock
    v2_bot_mock: Mock


@pytest.fixture
def mocked_router_setup(event_loop, aiohttp_client):
    v1_bot_mock = Mock(spec=ApiV1Sample)
    v1_bot_mock.webhook.return_value = web.Response()

    v2_bot_mock = Mock(spec=ApiV2Sample)
    v2_bot_mock.webhook.return_value = web.Response()

    app = make_test_app(v1_bot_mock, v2_bot_mock)
    client = event_loop.run_until_complete(aiohttp_client(app))

    return MockedRouterSetup(client, v1_bot_mock, v2_bot_mock)


@pytest.mark.asyncio
async def test_route_v1(mocked_router_setup: MockedRouterSetup):
    headers = {
        "X-Bot-API-Dialect": "Webim Standard",
        "X-Bot-API-Version": "1.0",
        "X-Webim-Version": "10.5.62",
    }

    resp = await mocked_router_setup.client.post("/", headers=headers)

    assert resp.status == 200
    mocked_router_setup.v1_bot_mock.webhook.assert_called_once()
    mocked_router_setup.v2_bot_mock.webhook.assert_not_called()


@pytest.mark.asyncio
async def test_route_v2(mocked_router_setup: MockedRouterSetup):
    headers = {
        "X-Bot-API-Dialect": "Webim Standard",
        "X-Bot-API-Version": "2.0",
        "X-Webim-Version": "10.5.62",
    }

    resp = await mocked_router_setup.client.post("/", headers=headers)

    assert resp.status == 200
    mocked_router_setup.v1_bot_mock.webhook.assert_not_called()
    mocked_router_setup.v2_bot_mock.webhook.assert_called_once()


@pytest.mark.asyncio
async def test_route_unknown(mocked_router_setup: MockedRouterSetup):
    headers = {
        "X-Bot-API-Dialect": "Webim Standard",
        "X-Bot-API-Version": "3.0",
        "X-Webim-Version": "10.5.62",
    }

    resp = await mocked_router_setup.client.post("/", headers=headers)

    assert resp.status == 404
    mocked_router_setup.v1_bot_mock.webhook.assert_not_called()
    mocked_router_setup.v2_bot_mock.webhook.assert_not_called()


@pytest.mark.asyncio
async def test_route_unset(mocked_router_setup: MockedRouterSetup):
    resp = await mocked_router_setup.client.post("/")

    assert resp.status == 404
    mocked_router_setup.v1_bot_mock.webhook.assert_not_called()
    mocked_router_setup.v2_bot_mock.webhook.assert_not_called()


@pytest.mark.asyncio
async def test_route_v2_when_v2_not_configured(aiohttp_client):
    v1_bot_mock = Mock(spec=ApiV1Sample)
    v1_bot_mock.webhook.return_value = web.Response()
    app = make_test_app(v1_bot_mock, None)
    client = await aiohttp_client(app)

    headers = {
        "X-Bot-API-Dialect": "Webim Standard",
        "X-Bot-API-Version": "2.0",
        "X-Webim-Version": "10.5.62",
    }
    resp = await client.post("/", headers=headers)

    assert resp.status == 404
    v1_bot_mock.webhook.assert_not_called()
