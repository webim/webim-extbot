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
    [
        dict(id='button-5', text='Send photo'),
        dict(id='button-6', text='Send document'),
        dict(id='button-7', text='Close chat'),
    ],
    [
        dict(id='button-8', text='Redirect to operator'),
        dict(id='button-9', text='Redirect to department')
    ]
]

FILE_BUTTON_IDS = [f'button-{i}' for i in range(5, 7)]
TEXT_BUTTON_IDS = [f'button-{i}' for i in range(1, 5)]
CLOSE_BUTTON_ID = ['button-7']
REDIRECT_BUTTON_IDS = [f'button-{i}' for i in range(8, 10)]

def pretty_json(data):
    return json.dumps(data, indent=1)


##
# API 2.0
##


class ApiV2Sample:
    """
    Пример работы с Webim External Bot API 2.0
    """

    def __init__(self, api_domain, api_token, operator_id=None, department_id=None):
        self._api_domain = api_domain
        self._api_token = api_token
        self._redirect_operator_id = operator_id
        self._redirect_department_id = department_id

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
        await self._send_response(chat_id, response_text, self.send_text_message)

    async def _handle_new_message(self, update):
        chat_id = update["chat_id"]
        message = update["message"]

        response_func = self.send_text_message
        response_data = "You did not choose a button or sent a file. Try again:"
        if message["kind"] == "keyboard_response":
            button_id = message['data']['button']['id']
            if button_id in TEXT_BUTTON_IDS:
                button_text = message["data"]["button"]["text"]
                response_data = f"You chose {button_text}. Choose again:"

            elif button_id in FILE_BUTTON_IDS:
                if button_id == 'button-5':
                    response_data = {
                        'url': 'https://i.pinimg.com/originals/90/0a/b7/900ab76cf0c3b2fe8683e0e2039beb00.png',
                        'name': 'shlepa.png',
                        'media_type': 'image/png'
                    }
                elif button_id == 'button-6':
                    response_data = {
                        'url': 'https://filesamples.com/samples/document/doc/sample2.doc',
                        'name': 'sample.doc',
                        'media_type': 'application/msword'
                    }
                response_func = self.send_file

            elif button_id in CLOSE_BUTTON_ID:
                await self.close_chat(chat_id)
                return

            elif button_id in REDIRECT_BUTTON_IDS:
                redirect_info = {}
                if button_id == 'button-8':
                    redirect_info = dict(operator_id=self._redirect_operator_id)
                elif button_id == 'button-9':
                    redirect_info = dict(dep_key=self._redirect_department_id)
                await self.redirect_visitor(chat_id, redirect_info)
                return
        elif message['kind'] == 'file_visitor':
            if message.get('data'):
                response_data = f'File received successfully. File: {message["data"]}'
            else:
                response_data = 'An error occurred while transferring the file'

        await self._send_response(chat_id, response_data, response_func)

    async def _send_response(self, chat_id, response_data, response_func):
        await response_func(chat_id, response_data)
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
        keyboard = KEYBOARD if self._redirect_department_id and self._redirect_operator_id else KEYBOARD[:3]
        message = dict(
            kind="keyboard",
            buttons=keyboard,
        )
        return await self.send_message(chat_id, message)

    async def send_message(self, chat_id, message):
        """
        Отправить сообщение в чат от имени бота. Сообщение передаётся через HTTP-запрос
        к API Webim
        """

        data = dict(
            chat_id=chat_id,
            message=message,
        )

        await self.make_request('send_message', data)

    async def close_chat(self, chat_id):
        data = dict(chat_id=chat_id)
        await self.make_request('close_chat', data)

    async def redirect_visitor(self, chat_id, redirect_info):
        data = dict(chat_id=chat_id, **redirect_info)
        await self.make_request('redirect_chat', data)

    async def make_request(self, method, data=None):
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

    async def send_file(self, chat_id, file_data):
        """
        Отправить в чат файл
        """

        message = dict(
            kind="file_operator",
            data=file_data,
        )
        await self.send_message(chat_id, message)


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
    parser.add_argument(
        '--operator', dest='operator_id', help='redirect operator id'
    )
    parser.add_argument(
        '--department', dest='department_id', help='redirect department id'
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
        v2_bot = ApiV2Sample(args.api_domain, args.api_token, args.operator_id, args.department_id)
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
