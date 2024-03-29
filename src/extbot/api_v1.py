"""
Реализация бота на External Bot API 1.0

Bot API 1.0 считается устаревшим и поддерживается в Webim только для обратной
совместимости. Новых ботов следует реализовывать на Bot API 2.0.
"""


from enum import Enum

from aiohttp import web

from .utils import pretty_json


class ButtonIds(str, Enum):
    SAY_HI = "say_hi"
    SAY_BYE = "say_bye"
    FORWARD_TO_QUEUE = "forward_to_queue"
    CUSTOM = "custom"


SAY_HI_BUTTON = dict(id=ButtonIds.SAY_HI, text="Say hi")
SAY_BYE_BUTTON = dict(id=ButtonIds.SAY_BYE, text="Say bye")
FORWARD_TO_QUEUE_BUTTON = dict(id=ButtonIds.FORWARD_TO_QUEUE, text="Forward to queue")

DEFAULT_KEYBOARD = [
    [SAY_HI_BUTTON, SAY_BYE_BUTTON],
    [FORWARD_TO_QUEUE_BUTTON],
]

GREETING_TEXT = "Hi! I am External API 1.0 sample bot. What should I do?"
DEFAULT_CUSTOM_BUTTON_TEXT = "Custom button"
DEFAULT_CUSTOM_BUTTON_RESPONSE_TEXT = (
    "Wow, you clicked my custom button. What should I do next?"
)
FAREWELL_TEXT = "Bye! In case you come back, here is what I can do:"
UNEXPECTED_UPDATE_TEXT = "Oops, I couldn't understand you. Here is what I can do:"
DO_NOT_UNDERSTAND_TEXT = (
    "I don't understand natural languages yet... But you can use my buttons:"
)


class ApiV1Sample:
    """
    Пример работы с Webim External Bot API 1.0
    """

    def __init__(self, logger, custom_button_text, custom_button_response):
        self._log = logger
        self._custom_button_text = custom_button_text
        self._custom_button_response = custom_button_response
        self._keyboard = self._build_keyboard()

    def _build_keyboard(self):
        keyboard = DEFAULT_KEYBOARD[:]

        if self._custom_button_text or self._custom_button_response:
            custom_button = dict(
                id=ButtonIds.CUSTOM,
                text=self._custom_button_text or DEFAULT_CUSTOM_BUTTON_TEXT,
            )
            keyboard.append([custom_button])

        return keyboard

    async def webhook(self, request):
        """
        Обработчик HTTP-запросов со стороны Webim. В теле запроса получает обновления
        о событиях в чате, в ответе на запрос отправляет сообщения для посетителя
        """

        update = await request.json()
        self._log.debug("Received update:\n" + pretty_json(update))
        chat_id = update.get("chat", {}).get("id")
        event = update["event"]

        response = self._text_and_keyboard_response(UNEXPECTED_UPDATE_TEXT)

        if event == "new_chat":
            self._log.info(f"New chat {chat_id!r}")
            response = self._text_and_keyboard_response(GREETING_TEXT)

        elif event == "new_message":
            self._log.info(f"New message in chat {chat_id!r}")
            message_kind = update["kind"]

            if message_kind == "keyboard_response":
                button_id = update["response"]["button"]["id"]

                if button_id == ButtonIds.SAY_HI:
                    response = self._text_and_keyboard_response(GREETING_TEXT)
                elif button_id == ButtonIds.SAY_BYE:
                    response = self._text_and_keyboard_response(FAREWELL_TEXT)
                elif button_id == ButtonIds.FORWARD_TO_QUEUE:
                    response = dict(has_answer=False)
                elif button_id == ButtonIds.CUSTOM:
                    response = self._text_and_keyboard_response(
                        self._custom_button_response
                        or DEFAULT_CUSTOM_BUTTON_RESPONSE_TEXT
                    )
                else:
                    self._log.warning(f"Unexpected button id {button_id!r}")

            elif message_kind == "visitor":
                response = self._text_and_keyboard_response(DO_NOT_UNDERSTAND_TEXT)

            else:
                self._log.warning(f"Unsupported message kind {message_kind!r}")

        else:
            self._log.warning(f"Unsupported event {event!r}")

        self._log.debug("Sending response:\n" + pretty_json(response))
        return web.json_response(response)

    def _text_and_keyboard_response(self, text):
        return dict(
            has_answer=True,
            messages=[
                dict(
                    kind="operator",
                    text=text,
                ),
                dict(
                    kind="keyboard",
                    buttons=self._keyboard,
                ),
            ],
        )
