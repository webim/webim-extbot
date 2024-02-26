"""Общие утилиты проекта"""


import json


def pretty_json(data):
    return json.dumps(data, indent=1, ensure_ascii=False)


def to_nested(sequence, items_per_group):
    for start in range(0, len(sequence), items_per_group):
        end = start + items_per_group
        row = sequence[start:end]
        yield row
