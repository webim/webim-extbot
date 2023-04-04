from extbot.utils import pretty_json


def test_pretty_json():
    obj = dict(
        key="😱",
        list=[1, 2, 3],
    )
    expected = "\n".join(
        (
            "{",
            ' "key": "😱",',
            ' "list": [',
            "  1,",
            "  2,",
            "  3",
            " ]",
            "}",
        )
    )
    dumped = pretty_json(obj)
    assert dumped == expected
