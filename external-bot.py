"""Пример умного бота для Webim.

В этом файле реализован простой умный бот для Webim. Бот отправляет в чат кнопки в
ответ на любое сообщение посетителя. Поддерживается как API 2.0 (class ApiV2Sample),
так и более старый API 1.0 (class ApiV1Sample).

Информация по запуску бота: python external-bot.py --help
"""


##
# Импортирование, константы и прочие служебные вещи
##


import json
import logging

from aiohttp import ClientSession, web


logger = logging.getLogger(__name__)

KEYBOARD = [
    [
        dict(id="button-1", text="One"),
        dict(id="button-2", text="Two"),
    ],
    [
        dict(id="button-3", text="Three"),
        dict(id="button-4", text="Four"),
    ],
]


def pretty_json(data):
    return json.dumps(data, indent=1)


##
# API 2.0
##


class ApiV2Sample:
    """
    Пример работы с Webim External Bot API 2.0
    """

    def __init__(self, api_domain, api_token):
        self._api_domain = api_domain
        self._api_token = api_token

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
        response_text = "Hi! Choose a button:"
        await self._send_text_and_keyboard(chat_id, response_text)

    async def _handle_new_message(self, update):
        chat_id = update["chat_id"]
        message = update["message"]

        if message["kind"] == "keyboard_response":
            button_text = message["data"]["button"]["text"]
            response_text = f"You chose {button_text}. Choose again:"
        else:
            response_text = "You did not choose a button. Try again:"

        await self._send_text_and_keyboard(chat_id, response_text)

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
            buttons=KEYBOARD,
        )
        return await self.send_message(chat_id, message)

    async def send_message(self, chat_id, message):
        """
        Отправить сообщение в чат от имени бота. Сообщение передаётся через HTTP-запрос
        к API Webim
        """

        url = f"https://{self._api_domain}/api/bot/v2/send_message"
        headers = {"Authorization": f"Token {self._api_token}"}

        data = dict(
            chat_id=chat_id,
            message=message,
        )

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


class ApiV1Sample:
    """
    Пример работы с Webim External Bot API 1.0
    """

    @staticmethod
    async def webhook(request):
        """
        Обработчик HTTP-запросов со стороны Webim. В теле запроса получает обновления
        о событиях в чате, в ответе на запрос отправляет сообщения для посетителя
        """

        update = await request.json()
        logger.debug("API v1 received update:\n" + pretty_json(update))

        if update["event"] == "new_chat":
            response_text = "Hi! Choose a button:"
        elif update["event"] == "new_message" and update["kind"] == "keyboard_response":
            button_text = update["response"]["button"]["text"]
            response_text = f"You chose {button_text}. Choose again:"
        else:
            response_text = "You did not choose a button. Try again:"

        response = dict(
            has_answer=True,
            messages=[
                dict(
                    kind="operator",
                    text=response_text,
                ),
                dict(
                    kind="keyboard",
                    buttons=KEYBOARD,
                ),
            ],
        )

        logger.debug("API v1 sending response:\n" + pretty_json(response))
        return web.json_response(response)


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
        help="domain of Webim instance, e.g. demo.webim.ru, only required for API v2",
    )
    parser.add_argument(
        "--token",
        dest="api_token",
        help="token from bot settings, only required for API v2",
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
        v2_bot = ApiV2Sample(args.api_domain, args.api_token)
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
