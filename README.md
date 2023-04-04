# Extbot: пример умного бота для Webim

Бот отправляет в чат кнопки со списком доступных действий. Поддерживается External Bot API 2.0 и 1.0. Бот написан на Python, основная логика в файлах [api_v2.py](src/extbot/api_v2.py) и [api_v1.py](src/extbot/api_v1.py).

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

## Установка бота

Для работы понадобится Python 3.8+ и pip.

Сначала нужно установить бота в операционную систему. Для этого можно найти ссылку на скачивание репозитория в формате ZIP и установить пакет по ней:

```bash
pip install "<ссылка-на-пакет>"
```

Чтобы проверить, что бот установлен, можно посмотреть его справку:

```bash
extbot --help
```

Если команда `extbot` не определяется, то вместо неё можно использовать `python -m extbot`. Время от времени стоит повторять команду установки, чтобы установить последние обновления бота.

## Запуск бота

Когда бот успешно установлен, его можно запустить. Например:

```bash
extbot --domain demo.webim.ru --token my-secret-token
```

Команда запускает бота и выдаёт ссылки на его API 2.0 и API 1.0 интерфейсы. Для работы API 2.0 в команду необходимо передать параметр `--domain` с доменом, на котором доступен Webim, а также параметр `--token` с токеном бота из настроек Webim (см. "Подключение бота к Webim" ниже). Больше настроек запуска в справке `extbot --help`.

Для подключения к Webim бот должен быть доступен через публичный IP адрес. Если при запуске локально такой возможности нет, то можно воспользоваться [ngrok](https://ngrok.com/download) или [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/run-tunnel/trycloudflare).

К примеру, по-умолчанию бот запускается на `localhost:8000`. Тогда можно запустить ngrok:

```bash
ngrok http 8000
```

Бот будет доступен по ссылке "Forwarding" из экрана ngrok до тех пор, пока ngrok запущен.

## Подключение бота к Webim

* [Инструкции для API 2.0](https://webim.ru/kb/bots/external-api/15043-robot-external-api-2-0/#setup)
* [Инструкции для API 1.0](https://webim.ru/kb/bots/external-api/12394-robot-external-api/#setup)

В поле "Ссылка на внешний API" указывается полученная при запуске бота ссылка.

## Дополнительные возможности

### Раздельные URL для API 2.0 и 1.0

Когда боту приходит запрос со стороны Webim, бот определяет используемую версию API по заголовку X-Bot-API-Version. Заголовок появился только в Webim 10.3, поэтому для более старых релизов у бота есть дополнительные URL-пути `/v2` и `/v1` для API 2.0 и 1.0 соответственно.

Предположим, после запуска бота он выдаёт API URL: `http://localhost:8000/`. Далее запускается `ngrok http 8000`, который выдаёт Forwarding: `https://extbot.example.com/`. Тогда в настройках бота в Webim можно указать одну из ссылок:

* `https://extbot.example.com/` — бот определит версию API автоматически, но только для Webim 10.3+
* `https://extbot.example.com/v2` — бот будет использовать только API 2.0
* `https://extbot.example.com/v1` — бот будет использовать только API 1.0

### Перевод диалога на оператора

При использовании API 2.0 в меню бота можно добавить кнопку, по нажатию на которую диалог будет переводиться на заданного оператора. Для этого необходимо при запуске бота передать id нужного оператора в опции `--agent-id`. Найти id можно в адресной строке браузера, зайдя в настройки оператора в разделе "Сотрудники" в Webim.

К примеру, если в адресной строке указано `https://demo.webim.ru/agent/agents/240001/general`, то id — 240001. Тогда запустить бота можно так:

```bash
extbot --domain demo.webim.ru --token <секретный-токен-бота> --agent-id 240001
```

### Перевод диалога на отдел

Также в API 2.0 в меню бота можно добавить кнопку, по нажатию на которую диалог будет переводиться в заданный отдел. Для этого необходимо передать буквенный идентификатор нужного отдела в опции `--dep-key`. Найти идентификатор можно в соответствующем поле в настройках отдела в Webim.

Пример запуска:

```bash
extbot --domain demo.webim.ru --token <секретный-токен-бота> --dep-key my_department
```

### Реакции на файловые сообщения

При использовании API 2.0 бот сможет отличить входящее файловое сообщение от текстового и ответит на него иначе.

### Логи внутренней работы бота

Бота можно запустить с опцией `--debug`, тогда он будет выводить более подробную информацию о своей внутренней работе, в том числе данные, которыми он обменивается по сети с Webim. В большинстве случаев бота лучше запускать без этой опции, чтобы среди внутренних сообщений не затерялись более важные, например сообщения об ошибках.

### Удаление бота из ОС

Если нужно удалить бота из операционной системы, это можно сделать командой `pip uninstall extbot`.

## Журнал изменений

См. [CHANGELOG.md](CHANGELOG.md)

## Участие в разработке бота

См. [CONTRIBUTING.md](CONTRIBUTING.md)
