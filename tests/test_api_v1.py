import logging

import pytest
from aiohttp import web

from extbot.api_v1 import (
    DEFAULT_CUSTOM_BUTTON_RESPONSE_TEXT,
    DEFAULT_CUSTOM_BUTTON_TEXT,
    DEFAULT_KEYBOARD,
    DO_NOT_UNDERSTAND_TEXT,
    FAREWELL_TEXT,
    FORWARD_TO_QUEUE_BUTTON,
    GREETING_TEXT,
    SAY_BYE_BUTTON,
    SAY_HI_BUTTON,
    UNEXPECTED_UPDATE_TEXT,
    ApiV1Sample,
    ButtonIds,
)


async def make_client(aiohttp_client, *bot_args, **bot_kwargs):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL)

    sample_bot = ApiV1Sample(logger, *bot_args, **bot_kwargs)
    app = web.Application()
    app.router.add_post("/", sample_bot.webhook)

    return await aiohttp_client(app)


@pytest.fixture
def client(event_loop, aiohttp_client):
    return event_loop.run_until_complete(
        make_client(
            aiohttp_client, custom_button_text=None, custom_button_response=None
        )
    )


SOME_CHAT_ID = "9401b039-ace3-4619-b884-a24e0aaf7adb"
UNEXPECTED_UPDATE_RESPONSE = {
    "has_answer": True,
    "messages": [
        {
            "kind": "operator",
            "text": UNEXPECTED_UPDATE_TEXT,
        },
        {
            "kind": "keyboard",
            "buttons": DEFAULT_KEYBOARD,
        },
    ],
}


@pytest.mark.asyncio
async def test_new_chat(client):
    update = {
        "event": "new_chat",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "visitor": {
            "id": "51b6d2d74ac24af38cbfbb7cf5529845",
        },
        "messages": [
            {
                "kind": "visitor",
                "text": "Hello",
            },
            {
                "kind": "visitor",
                "text": "Could you help me?",
            },
        ],
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    expected_body = {
        "has_answer": True,
        "messages": [
            {
                "kind": "operator",
                "text": GREETING_TEXT,
            },
            {
                "kind": "keyboard",
                "buttons": DEFAULT_KEYBOARD,
            },
        ],
    }
    assert body == expected_body


@pytest.mark.asyncio
async def test_say_hi(client):
    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "keyboard_response",
        "response": {
            "button": SAY_HI_BUTTON,
        },
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    expected_body = {
        "has_answer": True,
        "messages": [
            {
                "kind": "operator",
                "text": GREETING_TEXT,
            },
            {
                "kind": "keyboard",
                "buttons": DEFAULT_KEYBOARD,
            },
        ],
    }
    assert body == expected_body


@pytest.mark.asyncio
async def test_say_bye(client):
    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "keyboard_response",
        "response": {
            "button": SAY_BYE_BUTTON,
        },
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    expected_body = {
        "has_answer": True,
        "messages": [
            {
                "kind": "operator",
                "text": FAREWELL_TEXT,
            },
            {
                "kind": "keyboard",
                "buttons": DEFAULT_KEYBOARD,
            },
        ],
    }
    assert body == expected_body


@pytest.mark.asyncio
async def test_forward_to_queue(client):
    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "keyboard_response",
        "response": {
            "button": FORWARD_TO_QUEUE_BUTTON,
        },
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    expected_body = {
        "has_answer": False,
    }
    assert body == expected_body


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "custom_button_option",
        "custom_button_response_option",
        "expected_custom_button_text",
        "expected_custom_button_response_text",
    ),
    [
        ("Custom", None, "Custom", DEFAULT_CUSTOM_BUTTON_RESPONSE_TEXT),
        (None, "Custom response", DEFAULT_CUSTOM_BUTTON_TEXT, "Custom response"),
        ("Custom", "Custom response", "Custom", "Custom response"),
    ],
)
async def test_click_custom_button(
    aiohttp_client,
    custom_button_option,
    custom_button_response_option,
    expected_custom_button_text,
    expected_custom_button_response_text,
):
    client = await make_client(
        aiohttp_client,
        custom_button_text=custom_button_option,
        custom_button_response=custom_button_response_option,
    )
    custom_button = {
        "id": ButtonIds.CUSTOM,
        "text": expected_custom_button_text,
    }

    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "keyboard_response",
        "response": {
            "button": custom_button,
        },
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    expected_body = {
        "has_answer": True,
        "messages": [
            {
                "kind": "operator",
                "text": expected_custom_button_response_text,
            },
            {
                "kind": "keyboard",
                "buttons": DEFAULT_KEYBOARD + [[custom_button]],
            },
        ],
    }
    assert body == expected_body


@pytest.mark.asyncio
async def test_new_message_not_keyboard_response(client):
    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "visitor",
        "text": SAY_HI_BUTTON["text"],  # Текст с кнопки, но без нажатия на кнопку
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    expected_body = {
        "has_answer": True,
        "messages": [
            {
                "kind": "operator",
                "text": DO_NOT_UNDERSTAND_TEXT,
            },
            {
                "kind": "keyboard",
                "buttons": DEFAULT_KEYBOARD,
            },
        ],
    }
    assert body == expected_body


@pytest.mark.asyncio
async def test_unknown_button(client):
    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "keyboard_response",
        "response": {
            "button": {
                "id": "unknown",
                "text": "Unknown button",
            },
        },
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    assert body == UNEXPECTED_UPDATE_RESPONSE


@pytest.mark.asyncio
async def test_unknown_message_kind(client):
    update = {
        "event": "new_message",
        "chat": {
            "id": SOME_CHAT_ID,
        },
        "kind": "unknown",
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    assert body == UNEXPECTED_UPDATE_RESPONSE


@pytest.mark.asyncio
async def test_unknown_event(client):
    update = {
        "event": "unknown",
    }

    resp = await client.post("/", json=update)
    assert resp.status == 200

    body = await resp.json()
    assert body == UNEXPECTED_UPDATE_RESPONSE
