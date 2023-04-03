"""Реализация бота на External Bot API 2.0"""


from enum import Enum
from json import JSONDecodeError

from aiohttp import ClientError, ClientSession, ContentTypeError, web
from aiojobs import Scheduler

from .utils import pretty_json


class ButtonIds(str, Enum):
    SAY_HI = "say_hi"
    CLOSE_CHAT = "close_chat"
    SEND_IMAGE = "send_image"
    SEND_DOCUMENT = "send_document"
    FORWARD_TO_AGENT = "forward_to_agent"
    FORWARD_TO_DEPARTMENT = "forward_to_department"


DEFAULT_KEYBOARD = [
    [
        dict(id=ButtonIds.SAY_HI, text="Say hi"),
        dict(id=ButtonIds.CLOSE_CHAT, text="Close chat"),
    ],
    [
        dict(id=ButtonIds.SEND_IMAGE, text="Send image"),
        dict(id=ButtonIds.SEND_DOCUMENT, text="Send document"),
    ],
]

FWD_AGENT_BUTTON = dict(id=ButtonIds.FORWARD_TO_AGENT, text="Forward to agent")
FWD_DEPARTMENT_BUTTON = dict(
    id=ButtonIds.FORWARD_TO_DEPARTMENT, text="Forward to department"
)

GREETING_TEXT = "Hi! I am External API 2.0 sample bot. What should I do?"
UNEXPECTED_UPDATE_TEXT = "Oops, I couldn't understand you. Here is what I can do:"
DO_NOT_UNDERSTAND_TEXT = (
    "I don't understand natural languages yet... But you can use my buttons:"
)
WHAT_NEXT_TEXT = "What should I do next?"
FILE_RECEIVED_TEXT = "Thanks for the file. What should I do next?"
FORWARD_TO_AGENT_TEXT = "Forwarding to agent {agent_id}. Bye!"
FORWARD_TO_DEPARTMENT_TEXT = "Forwarding to department {dep_key}. Bye!"
FAREWELL_TEXT = "Bye!"

SAMPLE_IMAGE = {
    "url": (
        "https://i.pinimg.com/originals/90/0a/b7/900ab76cf0c3b2fe8683e0e2039beb00.png"
    ),
    "name": "shlepa.png",
    "media_type": "image/png",
}
SAMPLE_DOCUMENT = {
    "url": "https://filesamples.com/samples/document/doc/sample2.doc",
    "name": "sample.doc",
    "media_type": "application/msword",
}


class ApiV2Sample:
    """
    Пример работы с Webim External Bot API 2.0
    """

    def __init__(self, logger, api_domain, api_token, fwd_agent_id, fwd_department_key):
        self._log = logger
        self._api_domain = api_domain
        self._api_token = api_token
        self._fwd_agent_id = fwd_agent_id
        self._fwd_department_key = fwd_department_key

        self._keyboard = self._build_keyboard()
        self._init_async_done = False

    def _init_async(self):
        """
        Проинициализировать атрибуты, которые необходимо инициализировать внутри event
        loop. Если инициализация уже произошла ранее, то ничего не делать
        """

        if self._init_async_done:
            return

        self._api_session = ClientSession()
        self._background = Scheduler()
        self._init_async_done = True

    async def cleanup(self, *_):
        if self._init_async_done:
            await self._api_session.close()
            await self._background.close()

    def _build_keyboard(self):
        keyboard = DEFAULT_KEYBOARD[:]
        forward_row = []

        if self._fwd_agent_id is not None:
            forward_row.append(FWD_AGENT_BUTTON)
        if self._fwd_department_key is not None:
            forward_row.append(FWD_DEPARTMENT_BUTTON)

        if forward_row:
            keyboard.append(forward_row)

        return keyboard

    async def webhook(self, request):
        """
        Обработчик HTTP-запросов со стороны Webim. В теле запроса получает обновления
        о событиях в чате, для ответа на сообщения отправляет ответные запросы к Webim
        """

        self._init_async()

        update = await request.json()
        await self._background.spawn(self._handle_update(update))

        response = dict(result="ok")
        return web.json_response(response)

    async def _handle_update(self, update):
        self._log.debug("Received update:\n" + pretty_json(update))
        event = update["event"]

        if event == "new_chat":
            await self._handle_new_chat(update)
        elif event == "new_message":
            await self._handle_new_message(update)
        else:
            self._log.warning(f"Unsupported event {event!r}")

    async def _handle_new_chat(self, update):
        chat_id = update["chat"]["id"]
        self._log.info(f"New chat {chat_id!r}")
        await self._send_text_and_keyboard(chat_id, GREETING_TEXT)

    async def _handle_new_message(self, update):
        chat_id = update["chat_id"]
        self._log.info(f"New message in chat {chat_id!r}")
        message = update["message"]
        message_kind = message["kind"]

        if message_kind == "keyboard_response":
            button_id = message["data"]["button"]["id"]

            if button_id == ButtonIds.SAY_HI:
                await self._send_text_and_keyboard(chat_id, GREETING_TEXT)

            elif button_id == ButtonIds.SEND_IMAGE:
                await self.send_file(chat_id, SAMPLE_IMAGE)
                await self._send_text_and_keyboard(chat_id, WHAT_NEXT_TEXT)

            elif button_id == ButtonIds.SEND_DOCUMENT:
                await self.send_file(chat_id, SAMPLE_DOCUMENT)
                await self._send_text_and_keyboard(chat_id, WHAT_NEXT_TEXT)

            elif button_id == ButtonIds.CLOSE_CHAT:
                await self.send_text_message(chat_id, FAREWELL_TEXT)
                await self.close_chat(chat_id)

            elif button_id == ButtonIds.FORWARD_TO_AGENT:
                forward_info = dict(operator_id=self._fwd_agent_id)
                forward_text = FORWARD_TO_AGENT_TEXT.format(agent_id=self._fwd_agent_id)
                await self.send_text_message(chat_id, forward_text)
                await self.forward_chat(chat_id, forward_info)

            elif button_id == ButtonIds.FORWARD_TO_DEPARTMENT:
                forward_info = dict(dep_key=self._fwd_department_key)
                forward_text = FORWARD_TO_DEPARTMENT_TEXT.format(
                    dep_key=self._fwd_department_key
                )
                await self.send_text_message(chat_id, forward_text)
                await self.forward_chat(chat_id, forward_info)

            else:
                self._log.warning(f"Unexpected button id {button_id!r}")
                await self._send_text_and_keyboard(chat_id, UNEXPECTED_UPDATE_TEXT)

        elif message_kind == "file_visitor":
            await self._send_text_and_keyboard(chat_id, FILE_RECEIVED_TEXT)

        elif message_kind == "visitor":
            await self._send_text_and_keyboard(chat_id, DO_NOT_UNDERSTAND_TEXT)

        else:
            self._log.warning(f"Unsupported message kind {message_kind!r}")
            await self._send_text_and_keyboard(chat_id, UNEXPECTED_UPDATE_TEXT)

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
        Выполнить HTTP-запрос к API Webim и обработать возможные ошибки
        """

        url = f"https://{self._api_domain}/api/bot/v2/{method}"
        headers = {"Authorization": f"Token {self._api_token}"}

        self._log.debug(f"Requesting {url} with data:\n" + pretty_json(data))

        try:
            response = await self._api_session.post(url, headers=headers, json=data)
            response_content = await response.json()
        except ContentTypeError:
            ct = response.content_type
            self._log.error(
                f"Webim returned unexpected Content-Type {ct!r} for url {url!r}"
            )
            return
        except JSONDecodeError:
            # если дошло до декодирования, то response уже определён и тело получено
            body = await response.text()
            self._log.error(f"Webim returned invalid json {body!r} for url {url!r}")
            return
        except ClientError as e:
            self._log.error(f"Request error: {e}")
            return

        self._log.debug("Received response:\n" + pretty_json(response_content))

        if not response.ok or "error" in response_content:
            error_details = dict(
                status=response.status,
                error=response_content.get("error"),
                desc=response_content.get("desc"),
                url=url,
            )
            error_items = (f"{k}={v!r}" for k, v in error_details.items() if v)
            error_string = ", ".join(error_items)
            self._log.error(f"Error returned by Webim: {error_string}")
