from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from flask import session
from fuzzywuzzy import process

import helpers.connection as db


# function to get the list of info e.g images, names, latitude
# for the searched location
def get_places(search, date, api_key):
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    params = {
        'query': 'Places Of Interest in ' + search,
        'type': 'point_of_interest',
        'key': api_key
    }
    # attempt the API call
    try:
        response = requests.get(url, params=params)
        # Process the response data
        if response.status_code == 200:
            data = response.json()["results"]
        else:
            print(f"Request failed with status code: {response.status_code}")
            return []

    except requests.RequestException:
        return []

    # parse the results to produce the desired fields
    # if it lacks any information e.g photo, proceed to store next entry
    response_list = []
    for i in range(len(data)):
        try:
            attr = {
                "longlat": data[i]["geometry"]["location"],
                "name": data[i]["name"],
                "date": date,
                "location": search,
                "photo": data[i]["photos"],
                "place_id": data[i]["place_id"]
            }

            response_list.append(attr)

        except BaseException:
            continue

    # parse the photo fields to generate the image url
    for i in range(len(response_list)):

        photo_params = {
            'maxheight': response_list[i]["photo"][0]["height"],
            'photo_reference': response_list[i]["photo"][0]["photo_reference"],
            'maxwidth': 500,
            'key': api_key,
        }

        encoded_params = urlencode(photo_params)
        base_url = 'https://maps.googleapis.com/maps/api/place/photo'
        response_list[i]["photo"] = f"{base_url}?{encoded_params}"
    return is_location_saved(response_list)


# function to get the country and city name
def get_cname(search_item, api_key):

    geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'latlng': f"{search_item['longlat']['lat']},"
                  f"{search_item['longlat']['lng']}",
        'result_type': 'locality|country',
        'key': api_key
    }

    # attempt the API call, and rename empty strings
    # for both or either fields if not available
    try:
        response_cname = requests.get(geocode_url, params=params)
        cname_data = response_cname.json()["results"][0]["address_components"]
        locality = [entry['long_name']
                    for entry in cname_data
                    if 'locality' in entry.get('types', '')][0]
        cname = [entry['long_name']
                 for entry in cname_data if 'country'
                 in entry.get('types', '')][0]
        return {"country_name": cname, "city": locality}
    except BaseException:
        return {"country_name": '', "city": ''}


# parse the country information returned from API
# in desired format
def cinfo_search(data: list, idx: int):
    ckey = next(iter(data[idx]["currencies"]))
    info = {
        "name": data[idx]["name"]["common"],
        "currencies": data[idx]["currencies"][ckey]["name"] +
        " (" +
        data[idx]["currencies"][ckey]["symbol"] +
        ")",
        "languages": data[idx]["languages"]}
    return info


# set the country information to blank
def cinfo_empty():
    return {"name": "",
            "currencies": "",
            "languages": {"": ""}}


# function to get the country information from API
def get_cinfo(cname):
    country_url = f'https://restcountries.com/v3.1/name/{cname}'
    # attempt the API call for the country information
    # and return empty list if it doesn't find a match
    try:
        response_cninfo = requests.get(country_url)
        if response_cninfo.status_code == 200:
            data_country = response_cninfo.json()
        else:
            data_country = []
    except requests.RequestException:
        data_country = []
    # set empty fields if a matching result is not found
    # from the api
    if len(data_country) == 0:
        return cinfo_empty()

    # if multiple countries are found, use the one that
    # has the same name in the "common" field
    elif len(data_country) > 1:
        for i in range(len(data_country)):
            if data_country[i]["name"]["common"].lower() == cname.lower():
                cinfo = cinfo_search(data_country, i)
                break
        try:
            return cinfo
        except NameError:
            return cinfo_empty()
    else:
        return cinfo_search(data_country, 0)


# process the weather code
def interpret_weather(weather_code: int):
    if weather_code is None:
        return "Cloudy"
    elif weather_code < 3:
        return "Sunny"
    elif 3 <= weather_code <= 49:
        return "Cloudy"
    elif weather_code > 49:
        return "Rainy"


# API call to get the weather information
def get_weather(location, date):
    date = datetime.strptime(date, '%Y-%m-%d')
    current_datetime = datetime.now()

    # Calculate datetime 14 days from now
    datetime_14_d = current_datetime + timedelta(days=14)

    # due to limitation of free API, only 14 days
    # forecasts are available. Historic data is used
    # for data where forecasts are unavailable
    if ((date > current_datetime) & (date <= datetime_14_d)):
        weather_url = 'https://api.open-meteo.com/v1/forecast'
        weather_params = {
            'latitude': f"{location['lat']}",
            'longitude': f"{location['lng']}",
            'daily': "weather_code,temperature_2m_max,"
                     "temperature_2m_min,daylight_duration",
            'timezone': "GMT",
            'start_date': date.strftime('%Y-%m-%d'),
            'end_date': date.strftime('%Y-%m-%d')}
    else:
        weather_url = 'https://archive-api.open-meteo.com/v1/archive'
        weather_params = {
            'latitude': f"{location['lat']}",
            'longitude': f"{location['lng']}",
            'daily': 'weather_code,temperature_2m_max,'
                     'temperature_2m_min,daylight_duration',
            'timezone': "GMT",
            'start_date': (
                date -
                timedelta(
                    days=730)).strftime('%Y-%m-%d'),
            'end_date': (
                        date -
                        timedelta(
                            days=730)).strftime('%Y-%m-%d'),
        }
    # try to call the API. Returns null values if
    # the API is unable to retrieve the weather
    try:
        response_weather = requests.get(weather_url, params=weather_params)
        data_weather = response_weather.json()["daily"]
        return {
            "weather": interpret_weather(data_weather["weather_code"][0]),
            "min_temp": str(data_weather["temperature_2m_min"][0]) + "°C",
            "max_temp": str(data_weather["temperature_2m_max"][0]) + "°C",
            "daylight": round(data_weather["daylight_duration"][0] / 3600, 0),
        }
    except BaseException:
        return {
            "weather": "Cloudy",
            "min_temp": "NA",
            "max_temp": "NA",
            "daylight": "NA"
        }


# utilize fuzzy match to return the correct name for the country
# or city, even if user inserts a search term with spelling errors
def fuzzy_match(search, cname):
    # Get the closest term from the list of country and city name
    return process.extractOne(search, list(cname.values()))[0]


# get the place details
def get_place_details(place_id, date, search, api_key):

    place_det_url = 'https://maps.googleapis.com/maps/api/place/details/json'
    place_det_params = {
        'fields': "name,photos,editorial_summary,"
                  "user_ratings_total,rating,url",
        'place_id': place_id,
        'key': api_key}

    try:
        response_place_det = requests.get(place_det_url,
                                          params=place_det_params)
        # Process the response data
        if response_place_det.status_code == 200:
            data_place_det = response_place_det.json()["result"]
        else:
            print("Request failed with status code:"
                  f"{response_place_det.status_code}")
            return {}

    except requests.RequestException:
        return {}

    # replace editorial summary with null string if it is not found
    editorial_summary = data_place_det.get("editorial_summary", {})
    overview = editorial_summary.get("overview", "")

    # set the dictionary for the place details
    place_info = {
        "place_id": place_id,
        "name": data_place_det.get("name", ""),
        "ratings": data_place_det.get("rating", 0),
        "rating_count": data_place_det.get("user_ratings_total", 0),
        "search_link": data_place_det.get("url",
                                          "www.google.com" +
                                          data_place_det["name"]),
        "photo_reference": [photo for photo in data_place_det["photos"]
                            if photo.get("height", 0) > 900][:4],
        "editorial_summary": overview,
        "date": date,
        "location": search,
        "type": "Places"
    }

    try:
        # encode the photo properties into an image url
        # for the single large image in the details overlay
        det_photo_params = {
            'photo_reference':
                place_info["photo_reference"][0]["photo_reference"],
            'maxheight': 600,
            'key': api_key
        }
        encoded_params = urlencode(det_photo_params)
        base_url = 'https://maps.googleapis.com/maps/api/place/photo'
        place_info["photo_reference"][0] = f"{base_url}?{encoded_params}"

        # encode the photo properties into an image url
        # for the 3 small image in the details overlay
        for i in range(1, 4):
            try:
                det_photo_params = {
                    'photo_reference':
                        place_info["photo_reference"][i]["photo_reference"],
                    'maxwidth': 300,
                    'maxheight': 200,
                    'key': 'AIzaSyA93iUbKdmGyCJOrEVnod8Q15l1Npz3Ono'}
                encoded_params = urlencode(det_photo_params)
                base_url = 'https://maps.googleapis.com/maps/api/place/photo'
                place_info["photo_reference"][i] = \
                    f"{base_url}?{encoded_params}"
            # use empty image if error encountered in google's image
            except BaseException:
                print("Okay")
                place_info["photo_reference"][i] = "https://cdn.shopify.com/"
            "s/files/1/0533/2089/files"
            "/placeholder-images-image"
            "_large.png?format=jpg&qua"
            "lity=90&v=1530129081"

        return is_location_saved(place_info)
    except BaseException:
        # use empty image if error encountered in using google's images
        place_info["photo_reference"] = ["https://cdn.shopify.com/s/files/1"
                                         "/0533/2089/files/"
                                         "placeholder-images-image_large"
                                         ".png?format=jpg&"
                                         "quality=90&v=1530129081"] * 4
        return is_location_saved(place_info)


# check if a location is already added to favourite
# previously, and mark it accordingly
def is_location_saved(locations):
    try:
        conn, cursor = db.connect_to_db()
        cursor.execute("""
                       SELECT placeid FROM placesadded WHERE userid = %s
                       AND date = %s
                       """, (session["_user_id"], locations[0]["date"]))
        # get a tuple of all the placeids from places table
        saved_locations_records = cursor.fetchall()
        conn.commit()
    except Exception as e:
        print(e)
        return locations
    finally:
        cursor.close()
        conn.close()

    # Convert the list of tuples to a set for faster lookup
    # tuple of placeids.
    saved_locations = set(record[0] for record in saved_locations_records)

    # Update the 'is_saved' status for each
    # location if its place_id is already added to the
    # collection of locations previously
    if isinstance(locations, list):
        for details in locations:
            if details['place_id'] in saved_locations:
                details['is_saved'] = True
    else:
        if locations['place_id'] in saved_locations:
            locations['is_saved'] = True
    return locations
