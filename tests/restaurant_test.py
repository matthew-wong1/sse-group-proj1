# import pytest
# from helpers.restaurant import (generate_map, fetch_place_details, parse_request_parameters, 
#                                 search_nearby_restaurants, process_restaurant_data, 
#                                 sort_and_slice_restaurants, fetch_additional_details)

# import unittest.mock as mock

# import os
# api_key = os.getenv('GCLOUD_KEY', '')  
# place_id = 'ChIJz-VvsdMEdkgR1lQfyxijRMw'  #default place id      

# def test_generate_map():
#     # Mock data
#     restaurant_data = [{'lat': 51.5114, 'lng': -0.1335, 'image_url': 'http://example.com/image.jpg', 'website_url': 'http://example.com', 'name': 'Test Restaurant', 'ratings': 4.5}]
#     to_do_lat = 51.5114
#     to_do_long = -0.1335
#     radius = 2000

#     # Call the function
#     result = generate_map(restaurant_data, to_do_lat, to_do_long, radius)

#     # Assertions
#     assert 'Test Restaurant' in result  # Check if the restaurant's name is in the map
#     assert 'http://example.com/image.jpg' in result  # Check if the image URL is included
#     assert '51.5114' in result and '-0.1335' in result  # Check if the restaurant's location is correct

# def test_fetch_place_details():
#     # Mock data
#     mock_response_json = {
#         "status": "OK",
#         "results": [{
#             "geometry": {
#                 "location": {"lat": 51.5114, "lng": -0.1335}
#             }
#         }]
#     }
    
#     # Setup the mock to replace requests.get
#     with mock.patch('requests.get') as mock_get:
#         mock_get.return_value.status_code = 200  # Set the mock status code
#         mock_get.return_value.json.return_value = mock_response_json  # Set the mock json data

#         # Call the function
#         lat, lng = fetch_place_details(api_key, place_id)

#         # Assertions
#         assert lat == 51.5114
#         assert lng == -0.1335

# def test_parse_request_parameters():
#     from app import app
#     with app.test_request_context('/?place_id=test_place_id&address=Test+Address&keyword=testaurant&price=1&dist=500&open=true'):
#         place_id, address, keyword_string, price, dist, open_q = parse_request_parameters()

#         assert place_id == 'test_place_id'
#         assert address == 'Test Address'
#         assert keyword_string == 'testaurant'
#         assert price == '1'
#         assert dist == 500
#         assert open_q == 'true'


# def test_search_nearby_restaurants():
#     # Mock data
#     mock_response_data = {
#         "results": [
#             {
#                 "name": "Sample Restaurant",
#                 "geometry": {
#                     "location": {"lat": 51.5114, "lng": -0.1325}
#                 },
#                 "vicinity": "123 Sample Street, London",
#                 "rating": 4.5,
#                 "user_ratings_total": 200,
#                 "types": ["restaurant", "food", "point_of_interest", "establishment"],
#                 "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
#                 "plus_code": {
#                     "compound_code": "VXX7+39 London, United Kingdom",
#                     "global_code": "9C3XVXX7+39"
#                 },
#                 "price_level": 2,
#                 "opening_hours": {
#                     "open_now": True
#                 },
#                 "photos": [
#                     {
#                         "height": 400,
#                         "html_attributions": [
#                             "<a href=\"https://maps.google.com/maps/contrib/104444627635874232424\">A Google User</a>"
#                         ],
#                         "photo_reference": "CmRaAAAAEItaW...",
#                         "width": 600
#                     }
#                 ]
#             },
#             # ... Add more items as needed
#         ],
#         "status": "OK"
#     }
#     lat, lng = 51.5114, -0.1325
#     keyword_string = 'restaurant'
#     dist = 1000
#     price = '2'
#     open_q = 'true'

#     # Setup the mock to replace requests.get or similar
#     with mock.patch('requests.get') as mock_get:
#         mock_get.return_value.status_code = 200  # Mock status code
#         mock_get.return_value.json.return_value = mock_response_data  # Mock json response

#         # Call the function
#         result = search_nearby_restaurants(api_key, lat, lng, keyword_string, dist, price, open_q)

#         # Assertions
#         assert 'results' in result
#         assert len(result['results']) > 0
    
# def test_process_restaurant_data():
#     # Mock data
#     nearby_data = {
#         'results': [
#             {
#                 'name': 'Test Restaurant',
#                 'rating': 4.5,
#                 'user_ratings_total': 100,
#                 'geometry': {'location': {'lat': 51.5114, 'lng': -0.1325}},
#                 'photos': [{'photo_reference': 'test_photo_ref'}],
#                 'place_id': 'test_place_id'
#             }
#         ]
#     }

#     # Call the function
#     all_restaurants = process_restaurant_data(nearby_data)

#     # Assertions
#     assert len(all_restaurants) == 1
#     assert 'Test Restaurant' in all_restaurants
#     assert all_restaurants['Test Restaurant'][0] == 4.5  # Rating
#     assert all_restaurants['Test Restaurant'][1] == 100  # Rating count

# def test_sort_and_slice_restaurants():
#     # Mock data
#     all_restaurants = {
#         'Restaurant A': (4.5, 100, 'search_link', 51.5114, -0.1325, 'photo_ref', 'place_id'),
#         'Restaurant B': (4.0, 200, 'search_link', 51.5114, -0.1335, 'photo_ref', 'place_id')
#     }

#     # Call the function
#     sorted_restaurants = sort_and_slice_restaurants(all_restaurants, top_n=1)

#     # Assertions
#     assert len(sorted_restaurants) == 1
#     assert 'Restaurant B' in sorted_restaurants  # The one with the highest rating count

# def test_fetch_additional_details():
#     # Mock data
#     top_restaurants_dict = {
#         'Test Restaurant': (4.5, 100, 'search_link', 51.5114, -0.1335, 'photo_ref', 'place_id')
#     }
#     ## TO DO!! - add example json
#     # Mock the requests.get response within the test

#     # Call the function
#     updated_restaurants = fetch_additional_details(api_key, top_restaurants_dict, max_requests=1)

#     # Assertions
#     assert len(updated_restaurants) == 1
#     assert 'Test Restaurant' in updated_restaurants
#     # Optionally, check for additional details that should be added by the function

