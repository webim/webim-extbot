"""Пример умного бота для Webim.

В этом файле реализован простой умный бот для Webim. Поддерживается как API 2.0
(class ApiV2Sample), так и более старый API 1.0 (class ApiV1Sample).

Информация по запуску бота: python external-bot.py --help
"""


##
# Импортирование и прочие служебные вещи
##


import json
import logging
from enum import Enum

from aiohttp import ClientSession, web

logger = logging.getLogger(__name__)


def pretty_json(data):
    return json.dumps(data, indent=1)


##
# API 2.0
##


class ApiV2ButtonIds(str, Enum):
    SAY_HI = "say_hi"
    CLOSE_CHAT = "close_chat"
    SEND_IMAGE = "send_image"
    SEND_DOCUMENT = "send_document"
    FORWARD_TO_AGENT = "forward_to_agent"
    FORWARD_TO_DEPARTMENT = "forward_to_department"


V2_SAMPLE_DEFAULT_KEYBOARD = [
    [
        dict(id=ApiV2ButtonIds.SAY_HI, text="Say hi"),
        dict(id=ApiV2ButtonIds.CLOSE_CHAT, text="Close chat"),
    ],
    [
        dict(id=ApiV2ButtonIds.SEND_IMAGE, text="Send image"),
        dict(id=ApiV2ButtonIds.SEND_DOCUMENT, text="Send document"),
    ],
]

V2_SAMPLE_FWD_AGENT_BUTTON = dict(
    id=ApiV2ButtonIds.FORWARD_TO_AGENT, text="Forward to agent"
)
V2_SAMPLE_FWD_DEPARTMENT_BUTTON = dict(
    id=ApiV2ButtonIds.FORWARD_TO_DEPARTMENT, text="Forward to department"
)

V2_SAMPLE_GREETING_TEXT = "Hi! I am External API 2.0 sample bot. What should I do?"
V2_SAMPLE_DO_NOT_UNDERSTAND_TEXT = "What do you mean? Here is what I can do:"
V2_SAMPLE_WHAT_NEXT_TEXT = "What should I do next?"
V2_SAMPLE_FILE_RECEIVED_TEXT = "Thanks for the file. What should I do next?"
V2_SAMPLE_FAREWELL_TEXT = "Bye!"

V2_SAMPLE_IMAGE = {
    "url": "https://i.pinimg.com/originals/90/0a/b7/900ab76cf0c3b2fe8683e0e2039beb00.png",
    "name": "shlepa.png",
    "media_type": "image/png",
}
V2_SAMPLE_DOCUMENT = {
    "url": "https://filesamples.com/samples/document/doc/sample2.doc",
    "name": "sample.doc",
    "media_type": "application/msword",
}


class ApiV2Sample:
    """
    Пример работы с Webim External Bot API 2.0
    """

    def __init__(self, api_domain, api_token, fwd_agent_id, fwd_department_key):
        self._api_domain = api_domain
        self._api_token = api_token
        self._fwd_agent_id = fwd_agent_id
        self._fwd_department_key = fwd_department_key

        self._keyboard = self._build_keyboard()

    def _build_keyboard(self):
        keyboard = V2_SAMPLE_DEFAULT_KEYBOARD[:]
        forward_row = []

        if self._fwd_agent_id is not None:
            forward_row.append(V2_SAMPLE_FWD_AGENT_BUTTON)
        if self._fwd_department_key is not None:
            forward_row.append(V2_SAMPLE_FWD_DEPARTMENT_BUTTON)

        if forward_row:
            keyboard.append(forward_row)

        return keyboard

    async def webhook(self, request):
        """
        Обработчик HTTP-запросов со стороны Webim. В теле запроса получает обновления
        о событиях в чате, для ответа на сообщения отправляет ответные запросы к Webim
        """

        update = await request.json()
        logger.debug("API v2 received update:\n" + pretty_json(update))

        if update["event"] == "new_chat":
            await self._handle_new_chat(update)
        elif update["event"] == "new_message":
            await self._handle_new_message(update)

        response = dict(result="ok")
        return web.json_response(response)

    async def _handle_new_chat(self, update):
        chat_id = update["chat"]["id"]
        await self._send_text_and_keyboard(chat_id, V2_SAMPLE_GREETING_TEXT)

    async def _handle_new_message(self, update):
        chat_id = update["chat_id"]
        message = update["message"]

        if message["kind"] == "keyboard_response":
            button_id = message["data"]["button"]["id"]

            if button_id == ApiV2ButtonIds.SAY_HI:
                await self._send_text_and_keyboard(chat_id, V2_SAMPLE_GREETING_TEXT)

            elif button_id == ApiV2ButtonIds.SEND_IMAGE:
                await self.send_file(chat_id, V2_SAMPLE_IMAGE)
                await self._send_text_and_keyboard(chat_id, V2_SAMPLE_WHAT_NEXT_TEXT)

            elif button_id == ApiV2ButtonIds.SEND_DOCUMENT:
                await self.send_file(chat_id, V2_SAMPLE_DOCUMENT)
                await self._send_text_and_keyboard(chat_id, V2_SAMPLE_WHAT_NEXT_TEXT)

            elif button_id == ApiV2ButtonIds.CLOSE_CHAT:
                await self.send_text_message(chat_id, V2_SAMPLE_FAREWELL_TEXT)
                await self.close_chat(chat_id)

            elif button_id == ApiV2ButtonIds.FORWARD_TO_AGENT:
                forward_info = dict(operator_id=self._fwd_agent_id)
                await self.send_text_message(chat_id, V2_SAMPLE_FAREWELL_TEXT)
                await self.forward_chat(chat_id, forward_info)

            elif button_id == ApiV2ButtonIds.FORWARD_TO_DEPARTMENT:
                forward_info = dict(dep_key=self._fwd_department_key)
                await self.send_text_message(chat_id, V2_SAMPLE_FAREWELL_TEXT)
                await self.forward_chat(chat_id, forward_info)

            else:
                await self._send_text_and_keyboard(
                    chat_id, V2_SAMPLE_DO_NOT_UNDERSTAND_TEXT
                )

        elif message["kind"] == "file_visitor":
            await self._send_text_and_keyboard(chat_id, V2_SAMPLE_FILE_RECEIVED_TEXT)

        else:
            await self._send_text_and_keyboard(
                chat_id, V2_SAMPLE_DO_NOT_UNDERSTAND_TEXT
            )

    async def _send_text_and_keyboard(self, chat_id, text):
        await self.send_text_message(chat_id, text)
        await self.send_keyboard(chat_id)

    async def send_text_message(self, chat_id, text):
        """
        Отправить сообщение с заданным текстом в чат
        """

        message = dict(
            kind="operator",
            text=text,
        )
        return await self.send_message(chat_id, message)

    async def send_keyboard(self, chat_id):
        """
        Отправить в чат клавиатуру с кнопками бота
        """

        message = dict(
            kind="keyboard",
            buttons=self._keyboard,
        )
        return await self.send_message(chat_id, message)

    async def send_message(self, chat_id, message):
        """
        Отправить сообщение в чат от имени бота
        """

        data = dict(
            chat_id=chat_id,
            message=message,
        )

        await self.make_request("send_message", data)

    async def close_chat(self, chat_id):
        """
        Закрыть диалог с посетителем
        """

        data = dict(chat_id=chat_id)
        await self.make_request("close_chat", data)

    async def forward_chat(self, chat_id, forward_info):
        """
        Перенаправить диалог на заданного оператора или в заданный отдел
        """

        data = dict(chat_id=chat_id, **forward_info)
        await self.make_request("redirect_chat", data)

    async def send_file(self, chat_id, file_data):
        """
        Отправить в чат файл
        """

        message = dict(
            kind="file_operator",
            data=file_data,
        )
        await self.send_message(chat_id, message)

    async def make_request(self, method, data=None):
        """
        Выполнить HTTP-запрос к API Webim
        """

        url = f"https://{self._api_domain}/api/bot/v2/" + method
        headers = {"Authorization": f"Token {self._api_token}"}

        async with ClientSession() as http:
            logger.debug("API v2 sending message:\n" + pretty_json(data))
            response = await http.post(url, headers=headers, json=data)

            response_content = await response.json()
            logger.debug("API v2 received response:\n" + pretty_json(response_content))

            error = response_content.get("error")
            if error:
                logger.error(f"API v2 request error: {error}")


##
# API 1.0
##


class ApiV1ButtonIds(str, Enum):
    SAY_HI = "say_hi"
    SAY_BYE = "say_bye"
    FORWARD_TO_QUEUE = "forward_to_queue"


V1_SAMPLE_KEYBOARD = [
    [
        dict(id=ApiV1ButtonIds.SAY_HI, text="Say hi"),
        dict(id=ApiV1ButtonIds.SAY_BYE, text="Say bye"),
    ],
    [
        dict(id=ApiV1ButtonIds.FORWARD_TO_QUEUE, text="Forward to queue"),
    ],
]

V1_SAMPLE_GREETING_TEXT = "Hi! I am External API 1.0 sample bot. What should I do?"
V1_SAMPLE_FAREWELL_TEXT = "Bye! In case you come back, here is what I can do:"
V1_SAMPLE_DO_NOT_UNDERSTAND_TEXT = "What do you mean? Here is what I can do:"


class ApiV1Sample:
    """
    Пример работы с Webim External Bot API 1.0
    """

    @classmethod
    async def webhook(cls, request):
        """
        Обработчик HTTP-запросов со стороны Webim. В теле запроса получает обновления
        о событиях в чате, в ответе на запрос отправляет сообщения для посетителя
        """

        update = await request.json()
        logger.debug("API v1 received update:\n" + pretty_json(update))

        if update["event"] == "new_chat":
            response = cls._text_and_keyboard_response(V1_SAMPLE_GREETING_TEXT)

        elif update["event"] == "new_message" and update["kind"] == "keyboard_response":
            button_id = update["response"]["button"]["id"]

            if button_id == ApiV1ButtonIds.SAY_HI:
                response = cls._text_and_keyboard_response(V1_SAMPLE_GREETING_TEXT)
            elif button_id == ApiV1ButtonIds.SAY_BYE:
                response = cls._text_and_keyboard_response(V1_SAMPLE_FAREWELL_TEXT)
            elif button_id == ApiV1ButtonIds.FORWARD_TO_QUEUE:
                response = dict(has_answer=False)

        else:
            response = cls._text_and_keyboard_response(V1_SAMPLE_DO_NOT_UNDERSTAND_TEXT)

        logger.debug("API v1 sending response:\n" + pretty_json(response))
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
                    buttons=V1_SAMPLE_KEYBOARD,
                ),
            ],
        )


##
# Настройка логирования, запуск HTTP-сервера и прочие служебные вещи
##


if __name__ == "__main__":
    import sys
    from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description="Webim external bot sample",
    )
    parser.add_argument("--host", default="localhost", help="bind webhook to this host")
    parser.add_argument(
        "--port", default=8000, type=int, help="bind webhook to this port"
    )
    parser.add_argument(
        "--domain",
        dest="api_domain",
        help="(required for API v2) domain of Webim instance, e.g. demo.webim.ru",
    )
    parser.add_argument(
        "--token",
        dest="api_token",
        help="(required for API v2) token from bot settings",
    )
    parser.add_argument(
        "--agent-id", type=int, help="(API v2) add button to forward chat to this agent"
    )
    parser.add_argument(
        "--dep-key", help="(API v2) add button to forward chat to this department"
    )
    parser.add_argument(
        "--debug", action="store_true", help="display verbose debug messages"
    )
    args = parser.parse_args()

    formatter = logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    routes = []

    if args.api_domain and args.api_token:
        v2_bot = ApiV2Sample(
            args.api_domain, args.api_token, args.agent_id, args.dep_key
        )
        v2_route = web.post("/v2", v2_bot.webhook)
        routes.append(v2_route)
        logger.info(f"API v2 URL: http://{args.host}:{args.port}/v2")
    else:
        logger.info(
            f"API v2 not available, see {parser.prog} --help for required arguments"
        )

    v1_route = web.post("/v1", ApiV1Sample.webhook)
    routes.append(v1_route)
    logger.info(f"API v1 URL: http://{args.host}:{args.port}/v1")

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=args.host, port=args.port, print=None)
