import pytest

from helpers.auth import (check_password, check_repeat, check_username,
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


@pytest.mark.parametrize("test_input,expected",
                         [("", False),
                          ("1", False),
                          ("12345678", True),
                          ("1234567", False)])
def test_check_password(test_input, expected):
    errors = {}
    check_password(test_input, errors)
    assert not errors == expected


@pytest.mark.parametrize("test_input,test_input_repeat,expected",
                         [("123", "123", True),
                          ("1", "2", False)])
def test_check_repeat(test_input, test_input_repeat, expected):
    errors = {}
    check_repeat(test_input, test_input_repeat, errors)
    assert not errors == expected
