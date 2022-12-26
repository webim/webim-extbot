"""Реализация бота на External Bot API 1.0"""


from enum import Enum

from aiohttp import web

from .utils import pretty_json


class ButtonIds(str, Enum):
    SAY_HI = "say_hi"
    SAY_BYE = "say_bye"
    FORWARD_TO_QUEUE = "forward_to_queue"


KEYBOARD = [
    [
        dict(id=ButtonIds.SAY_HI, text="Say hi"),
        dict(id=ButtonIds.SAY_BYE, text="Say bye"),
    ],
    [
        dict(id=ButtonIds.FORWARD_TO_QUEUE, text="Forward to queue"),
    ],
]

GREETING_TEXT = "Hi! I am External API 1.0 sample bot. What should I do?"
FAREWELL_TEXT = "Bye! In case you come back, here is what I can do:"
DO_NOT_UNDERSTAND_TEXT = "What do you mean? Here is what I can do:"


class ApiV1Sample:
    """
    Пример работы с Webim External Bot API 1.0
    """

    def __init__(self, logger):
        self._log = logger

    async def webhook(self, request):
        """
        Обработчик HTTP-запросов со стороны Webim. В теле запроса получает обновления
        о событиях в чате, в ответе на запрос отправляет сообщения для посетителя
        """

        update = await request.json()
        self._log.debug("API v1 received update:\n" + pretty_json(update))

        if update["event"] == "new_chat":
            response = self._text_and_keyboard_response(GREETING_TEXT)

        elif update["event"] == "new_message" and update["kind"] == "keyboard_response":
            button_id = update["response"]["button"]["id"]

            if button_id == ButtonIds.SAY_HI:
                response = self._text_and_keyboard_response(GREETING_TEXT)
            elif button_id == ButtonIds.SAY_BYE:
                response = self._text_and_keyboard_response(FAREWELL_TEXT)
            elif button_id == ButtonIds.FORWARD_TO_QUEUE:
                response = dict(has_answer=False)

        else:
            response = self._text_and_keyboard_response(DO_NOT_UNDERSTAND_TEXT)

        self._log.debug("API v1 sending response:\n" + pretty_json(response))
        return web.json_response(response)

    @staticmethod
    def _text_and_keyboard_response(text):
        return dict(
            has_answer=True,
            messages=[
                dict(
                    kind="operator",
                    text=text,
                ),
                dict(
                    kind="keyboard",
                    buttons=KEYBOARD,
                ),
            ],
        )
