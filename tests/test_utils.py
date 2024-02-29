import sys

sys.path.append(".")

import re

from dart.utils import (
    get_valid_tag_list,
    get_patterns_from_tag_list,
    _get_tag_pattern,
    escape_webui_special_symbols,
    unescape_webui_special_symbols,
)


def test_valid_tag_list():
    text = "simple background, ,, animal ears,   umbrella,"
    expected = ["simple background", "animal ears", "umbrella"]

    assert get_valid_tag_list(text) == expected


def test_get_tag_pattern():
    test_cases: list[tuple[str, re.Pattern, str]] = [
        ("1girl", re.compile(r"1girl"), "1girl"),
        (
            "character (copyright)",
            re.compile(r"character \(copyright\)"),
            "character (copyright)",
        ),
        ("* ears", re.compile(r".* ears"), "cat ears"),
        ("looking *", re.compile(r"looking .*"), "looking to the side"),
        ("* (cosplay)", re.compile(r".* \(cosplay\)"), "hatsune miku (cosplay)"),
    ]

    for input, expected, matches in test_cases:
        assert expected.match(matches)
        assert _get_tag_pattern(input).match(matches)


def test_get_patterns_from_tag_list():
    test_cases: list[tuple[str, list[re.Pattern], list[str]]] = [
        (
            "1boy, umbrella,very long hair",
            [
                re.compile(
                    r"1boy",
                ),
                re.compile(
                    r"umbrella",
                ),
                re.compile(
                    r"very long hair",
                ),
            ],
            ["1boy", "umbrella", "very long hair"],
        ),
        (
            "* ears,holding *, animal *",
            [
                re.compile(
                    r".* ears",
                ),
                re.compile(
                    r"holding .*",
                ),
                re.compile(
                    r"animal .*",
                ),
            ],
            ["cat ears", "holding weapon", "animal ears"],
        ),
        (
            "copyright (character), star (sky)",
            [
                re.compile(
                    r"copyright \(character\)",
                ),
                re.compile(
                    r"star \(sky\)",
                ),
            ],
            ["copyright (character)", "star (sky)"],
        ),
    ]

    for input, expected, matches in test_cases:
        for pattern, target in zip(expected, matches):
            assert pattern.match(target)
        for pattern, target in zip(
            get_patterns_from_tag_list(get_valid_tag_list(input)), matches
        ):
            assert pattern.match(target)


def test_escape_webui_special_symbols():
    test_cases: list[tuple[list[str], list[str]]] = [
        (["1girl", "solo"], ["1girl", "solo"]),
        (
            ["star (sky)", "kafka (honkai:star rail)"],
            [r"star \(sky\)", r"kafka \(honkai:star rail\)"],
        ),
    ]
    for input, expected in test_cases:
        assert escape_webui_special_symbols(input) == expected


def test_unescape_webui_special_symbols():
    test_cases: list[tuple[list[str], list[str]]] = [
        (["1girl", "solo"], ["1girl", "solo"]),
        (
            [r"star \(sky\)", r"kafka \(honkai:star rail\)"],
            ["star (sky)", "kafka (honkai:star rail)"],
        ),
    ]
    for input, expected in test_cases:
        assert unescape_webui_special_symbols(input) == expected
