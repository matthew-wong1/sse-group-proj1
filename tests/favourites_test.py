import os

import pytest
# from dotenv import load_dotenv

from helpers.favourites import (get_favourites, get_route, retrieve_favourites,
                                save_favourites_order)

# load_dotenv()
api_key = os.getenv("GCLOUD_KEY", "")
place_id = "ChIJz-VvsdMEdkgR1lQfyxijRMw"  # default place id


@pytest.mark.parametrize("test_input,expected",
                         [("9", 'london (2023-12-09)')])
def test_retrieve_favourites(test_input, expected):
    assert retrieve_favourites(test_input)[0][0] == expected


@pytest.mark.parametrize("test_input,expected",
                         [("9", 110)])
def test_get_favourites(test_input, expected):
    assert get_favourites(test_input)[0]["place_list"][0]["index"] == expected


mock_save_input = [{'tripid': 'london (2023-12-09)',
                    'idx': 110,
                    'placeID': 'ChIJ2dGMjMMEdkgRqVqkuXQkj7c'}]


@pytest.mark.parametrize("user,test_input,expected",
                         [('9', mock_save_input, {"status": "success"})])
def test_save_favourites_order(user, test_input, expected):
    assert save_favourites_order(user, test_input) == expected


mock_route_input = [{'tripid': 'london (2023-12-12)',
                     'idx': 59,
                     'placeID': 'ChIJq4lX1doEdkgR5JXPstgQjc0'},
                    {'tripid': 'london (2023-12-12)',
                     'idx': 60, 'placeID': 'ChIJH-tBOc4EdkgRJ8aJ8P1CUxo'},
                    {'tripid': 'london (2023-12-12)', 'idx': 63,
                     'placeID': 'ChIJB9OTMDIbdkgRp0JWbQGZsS8'},
                    {'tripid': 'london (2023-12-12)', 'idx': 62,
                     'placeID': 'ChIJ3TgfM0kDdkgRZ2TV4d1Jv6g'},
                    {'tripid': 'london (2023-12-12)', 'idx': 64,
                     'placeID': 'ChIJSdtli0MDdkgRLW9aCBpCeJ4'}]


@pytest.mark.parametrize("test_input,api_key,expected",
                         [(mock_route_input, api_key, [0, 1, 2])])
def test_get_route(test_input, api_key, expected):
    assert get_route(test_input, api_key) == expected
