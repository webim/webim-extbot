"""Общие утилиты проекта"""


import json


def pretty_json(data):
    return json.dumps(data, indent=1, ensure_ascii=False)
