# Пример умного бота для Webim

Бот отправляет в чат кнопки со списком доступных действий. Поддерживается External Bot API 2.0 и 1.0. Бот написан на Python, реализация в файле [external-bot.py](external-bot.py).

Реализованный функционал API 2.0:

* Текстовые сообщения
* Файловые сообщения
* Сообщения с кнопками
* Перевод диалога на оператора
* Перевод диалога на отдел
* Закрытие чата

Реализованный функционал API 1.0:

* Текстовые сообщения
* Сообщения с кнопками
* Перевод диалога в очередь

## Запуск бота локально

Для запуска понадобится Python 3.6+ и pip.

Сначала необходимо установить зависимости:

```bash
pip install -r requirements.txt
```

Затем можно запустить бота. Например:

```bash
python external-bot.py --domain demo.webim.ru --token my-secret-token
```

Команда запускает бота и выдаёт ссылки на его API 2.0 и API 1.0 интерфейсы. Для работы API 2.0 в команду необходимо передать параметр `--domain` с доменом, на котором доступен Webim, а также параметр `--token` с токеном бота из настроек Webim (см. "Подключение бота к Webim" ниже). Больше настроек запуска в описании:

```bash
python external-bot.py --help
```

Для подключения к Webim бот должен быть доступен через публичный IP адрес. Если при запуске локально такой возможности нет, то можно воспользоваться [ngrok](https://ngrok.com/download) или [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/run-tunnel/trycloudflare).

К примеру, по-умолчанию бот запускается на `localhost:8000`. Тогда можно запустить ngrok:

```bash
ngrok http 8000
```

И бот будет доступен через `<ngrok-url>/v2` и `<ngrok-url>/v1` для API 2.0 и 1.0 соответственно, где `<ngrok-url>` — ссылка "Forwarding" из вывода ngrok.

## Подключение бота к Webim

* [Инструкции для API 2.0](https://webim.ru/kb/bots/external-api/15043-robot-external-api-2-0/#setting-up)
* [Инструкции для API 1.0](https://webim.ru/kb/bots/external-api/12394-robot-external-api/#bot_settings)

В поле "Ссылка на внешний API" указывается полученная при запуске бота ссылка.
