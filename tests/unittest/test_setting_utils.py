import pytest

from pr_agent.algo.setting_utils import normalize_setting_list


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, []),
        ("", []),
        ("/review", ["/review"]),
        (["/review", "/describe"], ["/review", "/describe"]),
        (("/review",), ["/review"]),
        ("opened,reopened", ["opened,reopened"]),
    ],
)
def test_normalize_setting_list(value, expected):
    assert normalize_setting_list(value) == expected


def test_normalize_setting_list_can_split_comma_separated_actions():
    assert normalize_setting_list("opened, reopened", split_commas=True) == ["opened", "reopened"]
