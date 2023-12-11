import os

import pytest
from dotenv import load_dotenv

from helpers.places import (cinfo_empty, cinfo_search, fuzzy_match, get_cinfo,
                            get_cname, get_place_details, get_places,
                            get_weather, interpret_weather, is_location_saved)

load_dotenv()
api_key = os.getenv("GCLOUD_KEY", "")
print(api_key)
place_id = "ChIJz-VvsdMEdkgR1lQfyxijRMw"  # default place id


@pytest.mark.parametrize("search, date, expected",
                         [("London", '2023-01-01', 'London')])
def test_get_places(search, date, expected):
    assert get_places(search, date, api_key)[0]['location'] == expected


dummy_location = {'longlat': {'lat': 51.5044028, 'lng': -0.0865331}}
expected_cname = {'country_name': 'United Kingdom', 'city': 'London'}


def test_get_cname():
    assert get_cname(dummy_location, api_key) == expected_cname


dummy_search = [{'name': {'common': 'United Kingdom', 'official':
                          'United Kingdom of Great Britain \
                           and Northern Ireland'},
                 'currencies': {'GBP': {'name': 'British pound',
                                        'symbol': '£'}},
                 'languages': {'eng': 'English'}}]
dummy_search_result = {'name': 'United Kingdom',
                       'currencies': 'British pound (£)',
                       'languages': {'eng': 'English'}}


def test_cinfo_search():
    assert cinfo_search(dummy_search, 0) == dummy_search_result


def test_cinfo_empty():
    assert cinfo_empty() == {"name": "",
                             "currencies": "",
                             "languages": {"": ""}}


def test_get_cinfo():
    assert get_cinfo('United Kingdom') == dummy_search_result


@pytest.mark.parametrize("test_input,expected",
                         [(2, 'Sunny'),
                          (10, 'Cloudy'),
                          (60, 'Rainy')])
def test_interpret_weather(test_input, expected):
    result = interpret_weather(test_input)
    assert result == expected


dummy_weather_result = {'weather': 'Rainy', 'min_temp': '-2.3°C',
                        'max_temp': '4.2°C', 'daylight': 8.0}


def test_get_weather():
    assert get_weather(dummy_location["longlat"],
                       '2023-01-01') == dummy_weather_result


def test_fuzzy_match():
    fuzzy_match("Londxn", expected_cname) == "London"


def test_get_place_details():
    assert get_place_details(place_id, '2023-01-01',
                             'London', api_key)['place_id'] == place_id
    assert get_place_details(place_id, '2023-01-01',
                             'London', api_key)['type'] == "Places"
    assert get_place_details(place_id, '2023-01-01',
                             'London', api_key)['location'] == "London"


dummy_places = [{'longlat': {'lat': 51.5044028, 'lng': -0.0865331},
                 'name': 'The View from The Shard',
                 'date': '2023-01-01', 'location': 'London',
                 'place_id': "ChIJz-VvsdMEdkgR1lQfyxijRMw"}]


def test_is_location_saved():
    assert is_location_saved(dummy_places[0])[0]["name"] == (
        'The View from The Shard')
