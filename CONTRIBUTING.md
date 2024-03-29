# Участие в разработке бота

Помочь с развитием проекта можно, создав Pull Request, исправляющий ошибку, реализующий нововведения или как-то ещё улучшающий бота. Ниже описаны советы по работе с исходным кодом.

## Подготовка окружения

Чтобы бот не конфликтовал с другими установленными пакетами, разработку лучше вести в виртуальном окружении. Для этого можно в директории с исходным кодом выполнить команды:

```shell
# Создать окружение
python -m venv venv

# Активировать окружение
source venv/bin/activate

# Установить бота и зависимости
pip install -e .[dev]
```

Группа `[dev]` установит дополнительные зависимости для разработки. Благодаря флагу `-e` pip установит пакет в "редактируемом режиме", то есть изменения в исходном коде будут вступать в силу без переустановки. Исключение — изменения в [setup.py](setup.py), например добавление зависимостей. После таких изменений нужно заново выполнить установку.

## Тесты

Каждому модулю из `src/extbot/` соответствует или будет соответствовать модуль тестов в `tests/`. Если в код вносятся изменения, которые затрагивают один из модулей, для которых тесты уже есть, то скорее всего нужно отразить эти изменения и в тестах: покрыть тестами новую функциональность, написать тест для проверки исправленного бага или изменить логику существующих тестов.

Запустить тесты можно через Coverage:

```shell
coverage run
```

Просмотреть отчёт по тестовому покрытию:

```shell
coverage report
```

Для запуска тестов Coverage использует команду `pytest tests/`. При необходимости можно запускать pytest и напрямую, без Coverage, но тогда отчёт по покрытию сформирован не будет.

## Оформление работы

Пожалуйста, перед сохранением коммита отформатируйте код и проверьте его линтером:

```shell
ruff format
ruff .
```

В сообщении коммита на русском языке опишите внесённые изменения. Если изменения расширяют функционал или изменяют логику существующего, отразите это в документации: в docstring метода, класса или модуля и/или в [README.md](README.md).
