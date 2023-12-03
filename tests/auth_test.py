import pytest

from helpers.auth import (check_password, check_username, match_password,
                          user_exists)


@pytest.mark.parametrize("test_input,expected",
                         [("", False),
                          ("hello", True),
                          ("你好", True)])
def test_check_username(test_input, expected):
    errors = {}
    check_username(test_input, errors)
    assert not errors == expected


@pytest.mark.parametrize("test_input,expected",
                         [("test", True),
                          ("abc", False)])
def test_check_user_exists(test_input, expected):
    assert user_exists(test_input) == expected


@pytest.mark.parametrize("test_input,test_input_repeat,expected",
                         [("", "", False),
                          ("1", "1", False),
                          ("12345678", "12345678", True),
                          ("1234567", "1234567", False)])
def test_check_password(test_input, test_input_repeat, expected):
    errors = {}
    check_password(test_input, test_input_repeat, errors)
    assert not errors == expected


@pytest.mark.parametrize("test_username,test_password,expected",
                         [("test", "1", False),
                          ("test", "sza;dlkfsa", False)])
def test_match_password(test_username, test_password, expected):
    assert match_password(test_username, test_password) == expected
