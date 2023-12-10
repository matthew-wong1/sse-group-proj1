import os
import unittest.mock as mock
from json.decoder import JSONDecodeError

from flask import Flask
from requests.exceptions import HTTPError, RequestException

from helpers.restaurant import (fetch_additional_details,
                                fetch_and_update_restaurant_details,
                                fetch_place_details, generate_map,
                                generate_map_html, get_api_key_or_error,
                                get_lat_lng_or_error, get_nearby_data_or_error,
                                get_request_data, get_search_details,
                                handle_error, is_restaurant_saved,
                                parse_request_parameters,
                                prepare_restaurant_data_for_map,
                                process_and_sort_restaurants,
                                process_restaurant_data,
                                search_nearby_restaurants,
                                sort_and_slice_restaurants)

api_key = os.environ.get("GCLOUD_KEY", "")
place_id = "ChIJz-VvsdMEdkgR1lQfyxijRMw"  # default place id


def test_generate_map():
    # Mock data
    restaurant_data = [
        {
            "lat": 51.5114,
            "lng": -0.1335,
            "image_url": "http://example.com/image.jpg",
            "website_url": "http://example.com",
            "name": "Test Restaurant",
            "ratings": 4.5,
        }
    ]
    to_do_lat = 51.5114
    to_do_long = -0.1335
    radius = 2000

    # Call the function
    result = generate_map(restaurant_data, to_do_lat, to_do_long, radius)

    # Assertions
    assert (
        "Test Restaurant" in result
    )  # Check if the restaurant's name is in the map
    assert (
        "http://example.com/image.jpg" in result
    )  # Check if the image URL is included
    assert (
        "51.5114" in result and "-0.1335" in result
    )  # Check if the restaurant's location is correct


def test_fetch_place_details():
    # Mock data
    mock_response_json = {
        "status": "OK",
        "results": [
            {"geometry": {"location": {"lat": 51.5114, "lng": -0.1335}}}
        ],
    }

    # Setup the mock to replace requests.get
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200  # Set the mock status code
        mock_get.return_value.json.return_value = (
            mock_response_json  # Set the mock json data
        )

        # Call the function
        lat, lng = fetch_place_details(api_key, place_id)

        # Assertions
        assert lat == 51.5114
        assert lng == -0.1335


def test_parse_request_parameters():
    from flask import Flask

    app = Flask(__name__)

    # Create a test request context with relevant parameters
    with app.test_request_context(
        "/?keyword=testaurant&price=1&dist=500&open=true"
    ):
        # Call the function
        keyword_string, price, dist, open_q = parse_request_parameters()

        # Assertions
        assert keyword_string == "testaurant"
        assert price == "1"
        assert dist == 500
        assert open_q == "true"


def test_search_nearby_restaurants():
    # Mock data
    mock_response_data = {
        "results": [
            {
                "name": "Sample Restaurant",
                "geometry": {"location": {"lat": 51.5114, "lng": -0.1325}},
                "vicinity": "123 Sample Street, London",
                "rating": 4.5,
                "user_ratings_total": 200,
                "types": [
                    "restaurant",
                    "food",
                    "point_of_interest",
                    "establishment",
                ],
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "plus_code": {
                    "compound_code": "VXX7+39 London, United Kingdom",
                    "global_code": "9C3XVXX7+39",
                },
                "price_level": 2,
                "opening_hours": {"open_now": True},
                "photos": [
                    {
                        "height": 400,
                        "html_attributions": [
                            (
                                '<a href="https://maps.google.com/maps/'
                                'contrib/104444627635874232424">A Google'
                                " User</a>"
                            )
                        ],
                        "photo_reference": "CmRaAAAAEItaW...",
                        "width": 600,
                    }
                ],
            },
        ],
        "status": "OK",
    }
    lat, lng = 51.5114, -0.1325
    keyword_string = "restaurant"
    dist = 1000
    price = "2"
    open_q = "true"

    # Setup the mock to replace requests.get or similar
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200  # Mock status code
        mock_get.return_value.json.return_value = (
            mock_response_data  # Mock json response
        )

        # Call the function
        result = search_nearby_restaurants(
            api_key, lat, lng, keyword_string, dist, price, open_q
        )

        # Assertions
        assert "results" in result
        assert len(result["results"]) > 0


def test_process_restaurant_data():
    # Mock data
    nearby_data = {
        "results": [
            {
                "name": "Sample Restaurant",
                "geometry": {"location": {"lat": 51.5114, "lng": -0.1325}},
                "vicinity": "123 Sample Street, London",
                "rating": 4.5,
                "user_ratings_total": 200,
                "types": [
                    "restaurant",
                    "food",
                    "point_of_interest",
                    "establishment",
                ],
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "price_level": 2,
                "opening_hours": {"open_now": True},
                "photos": [
                    {
                        "height": 400,
                        "html_attributions": [
                            '<a href="https://maps.google.com/maps'
                            '/contrib/104444627635874232424">A Google User</a>'
                        ],
                        "photo_reference": "CmRaAAAAEItaW...",
                        "width": 600,
                    }
                ],
            }
        ]
    }

    # Call the function
    all_restaurants = process_restaurant_data(nearby_data)

    # Assertions
    assert len(all_restaurants) == 1
    assert "Sample Restaurant" in all_restaurants
    assert all_restaurants["Sample Restaurant"]["rating"] == 4.5  # Rating
    assert (
        all_restaurants["Sample Restaurant"]["rating_count"] == 200
    )  # Rating count


def test_sort_and_slice_restaurants():
    # Mock data with the correct format
    all_restaurants = {
        "Restaurant A": {
            "rating": 4.5,
            "rating_count": 100,
            "search_link": "link",
            "latitude": 51.5114,
            "longitude": -0.1325,
            "photo_reference": "photo_ref",
            "place_id": "place_id",
        },
        "Restaurant B": {
            "rating": 4.0,
            "rating_count": 200,
            "search_link": "link",
            "latitude": 51.5114,
            "longitude": -0.1335,
            "photo_reference": "photo_ref",
            "place_id": "place_id",
        },
    }

    # Call the function
    sorted_restaurants = sort_and_slice_restaurants(all_restaurants, top_n=1)

    # Assertions
    assert len(sorted_restaurants) == 1
    # The one with the highest rating count
    assert "Restaurant B" in sorted_restaurants

    # Call the function
    sorted_restaurants = sort_and_slice_restaurants(all_restaurants, top_n=2)

    # Assertions
    assert len(sorted_restaurants) == 2


def test_fetch_additional_details():
    # Mock data
    top_restaurants_dict = {
        "Test Restaurant": {
            "rating": 4.5,
            "user_ratings_total": 100,
            "search_link": "search_link",
            "lat": 51.5114,
            "lng": -0.1335,
            "photo_reference": "photo_ref",
            "place_id": "place_id",
        }
    }

    # Sample response JSON
    sample_response = {
        "html_attributions": [],
        "result": {
            "editorial_summary": {
                "language": "en",
                "overview": "Anatolian food from "
                "eastern Turkey in a modern restaurant with outside seating.",
            },
            "formatted_phone_number": "020 7637 4555",
            "name": "TAS Restaurant Bloomsbury",
            "website": ("https://tasrestaurants."
                        "co.uk/tas-bloomsbury-restaurant/"
                        ),
        },
        "status": "OK",
    }

    # Mock the requests.get response within the test
    with mock.patch("requests.get") as mocked_get:
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.json.return_value = sample_response

        # Call the function
        updated_restaurants = fetch_additional_details(
            "fake_api_key",
            top_restaurants_dict,
            "2023-12-08",
            "London",
            max_requests=1,
        )

        # Checking the details added by the function
        details = updated_restaurants["Test Restaurant"]
        assert (
            details["formatted_phone_number"]
            == sample_response["result"]["formatted_phone_number"]
        )
        assert details["website"] == sample_response["result"]["website"]

        # Adjusted assertion for editorial_summary
        assert (
            details["editorial_summary"]
            == sample_response["result"]["editorial_summary"]["overview"]
        )


def test_get_api_key_or_error():
    from api.app import app
    with app.test_request_context('/'):
        with mock.patch.dict(os.environ, {"GCLOUD_KEY": "test_key"}):
            api_key = get_api_key_or_error()
            assert api_key == "test_key"

        with mock.patch.dict(os.environ, {"GCLOUD_KEY": ""}):
            response, status_code = get_api_key_or_error()
            assert status_code == 404


def test_handle_error():
    from api.app import app
    with app.test_request_context('/'):
        e = HTTPError()
        response, status_code = handle_error(e)
        assert status_code == 500

        e = JSONDecodeError(msg="Error", doc="", pos=0)
        response, status_code = handle_error(e)
        assert status_code == 500

        e = RequestException()
        response, status_code = handle_error(e)
        assert status_code == 500

        e = Exception("Generic error")
        response, status_code = handle_error(e)
        assert status_code == 500


def test_get_request_data():
    app = Flask(__name__)
    with app.test_request_context(
        "/?place_id=test_place_id&location=London&date=2023-01-01"
    ):
        data = get_request_data()
        assert data["place_id"] == "test_place_id"
        assert data["location"] == "London"
        assert data["date"] == "2023-01-01"


def test_get_search_details():
    app = Flask(__name__)
    with app.test_request_context(
        "/?keyword=restaurant&price=2&dist=1000&open=true"
    ):
        data = {
            "name": "Test Place",
            "keyword": "restaurant",
            "price": "2",
            "dist": 1000,
            "open": "true",
        }
        details = get_search_details(data)
        assert details["name"] == "Test Place"
        assert details["keyword"] == "restaurant"
        assert details["price"] == "2"
        assert details["dist"] == 1000
        assert details["open"] == "true"


def test_get_lat_lng_or_error():
    with mock.patch("helpers.restaurant.fetch_place_details") as mock_fetch:
        mock_fetch.return_value = (51.5114, -0.1325)
        lat, lng = get_lat_lng_or_error("dummy_api_key", "test_place_id")
        assert lat == 51.5114
        assert lng == -0.1325


def test_get_nearby_data_or_error():
    with mock.patch(
        "helpers.restaurant.search_nearby_restaurants"
    ) as mock_search:
        mock_search.return_value = {"status": "OK", "results": []}
        data = get_nearby_data_or_error(
            "dummy_api_key",
            51.5114,
            -0.1325,
            {
                "keyword": "restaurant",
                "dist": 1000,
                "price": "2",
                "open": True,
            },
        )
        assert "status" in data
        assert data["status"] == "OK"


def test_process_and_sort_restaurants():
    mock_nearby_data = {
        "results": [
            {
                "name": "Restaurant A",
                "rating": 4.5,
                "user_ratings_total": 200,
                "geometry": {"location": {"lat": 51.5114, "lng": -0.1325}},
                "photos": [{"photo_reference": "ref1"}],
                "place_id": "place_id_A",
            },
            {
                "name": "Restaurant B",
                "rating": 4.0,
                "user_ratings_total": 150,
                "geometry": {"location": {"lat": 51.5115, "lng": -0.1326}},
                "photos": [{"photo_reference": "ref2"}],
                "place_id": "place_id_B",
            },
        ]
    }
    sorted_restaurants = process_and_sort_restaurants(mock_nearby_data)
    assert (
        len(sorted_restaurants) <= 15
    )  # Ensure the list is sorted and sliced
    assert (
        "Restaurant A" in sorted_restaurants
    )  # Check if a specific restaurant is in the result


def test_fetch_and_update_restaurant_details():
    mock_data = {
        "Test Restaurant": {
            "name": "Test Restaurant",
            "rating": 4.5,
            "user_ratings_total": 100,
            "search_link": "https://example.com",
            "latitude": 51.5114,
            "longitude": -0.1335,
            "photo_reference": "photo_ref",
            "place_id": "test_place_id",
        }
    }
    with mock.patch(
        "helpers.restaurant.fetch_additional_details"
    ) as mock_fetch:
        mock_fetch.return_value = mock_data
        updated_data = fetch_and_update_restaurant_details(
            "dummy_api_key",
            mock_data,
            {"date": "2023-01-01", "location": "London"},
        )
        assert "Test Restaurant" in updated_data
        assert updated_data["Test Restaurant"]["name"] == "Test Restaurant"


def test_prepare_restaurant_data_for_map():
    mock_data = {
        "Test Restaurant": {
            "name": "Test Restaurant",
            "latitude": 51.5114,
            "longitude": -0.1335,
            "website": "https://example.com",
            "photo_url": "https://example.com/photo.jpg",
            "rating": 4.5,
        }
    }
    restaurant_data = prepare_restaurant_data_for_map(mock_data)
    assert len(restaurant_data) == 1
    assert restaurant_data[0]["name"] == "Test Restaurant"
    assert restaurant_data[0]["lat"] == 51.5114
    assert restaurant_data[0]["lng"] == -0.1335


def test_generate_map_html():
    mock_restaurant_data = [
        {
            "name": "Test Restaurant",
            "lat": 51.5114,
            "lng": -0.1335,
            "website_url": "https://example.com",
            "image_url": "https://example.com/photo.jpg",
            "ratings": 4.5,
        }
    ]
    with mock.patch("helpers.restaurant.generate_map") as mock_generate:
        mock_generate.return_value = "<div>Mock Map HTML</div>"
        map_html = generate_map_html(
            mock_restaurant_data, 51.5114, -0.1325, 1000
        )
        assert "<div>Mock Map HTML</div>" in map_html


def test_is_restaurant_saved():
    app = Flask(__name__)
    with app.test_request_context(), mock.patch(
        "helpers.restaurant.connect_to_db"
    ) as mock_db, mock.patch(
        "flask.session", new_callable=mock.MagicMock
    ) as mock_session:
        mock_data = {
            "Test Restaurant": {
                "place_id": "test_place_id",
                "date": "2023-01-01",
                "is_saved": "true",
            }
        }
        mock_session.return_value = {"_user_id": "user123"}
        mock_db.return_value = (mock.MagicMock(), mock.MagicMock())
        mock_db.return_value[1].fetchall.return_value = [("test_place_id",)]
        saved_data = is_restaurant_saved(mock_data)
        assert saved_data["Test Restaurant"]["is_saved"]
