from extbot.utils import pretty_json, to_nested


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


def test_to_nested():
    assert list(to_nested([0, 1, 2, 3], 1)) == [[0], [1], [2], [3]]
    assert list(to_nested([0, 1, 2, 3], 2)) == [[0, 1], [2, 3]]
    assert list(to_nested([0, 1, 2, 3], 3)) == [[0, 1, 2], [3]]
    assert list(to_nested([0, 1, 2, 3], 4)) == [[0, 1, 2, 3]]
    assert list(to_nested([0, 1, 2, 3], 5)) == [[0, 1, 2, 3]]
