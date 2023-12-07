from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from flask import session
from fuzzywuzzy import process

import helpers.connection as db


def get_places(search, date, api_key):
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'

    params = {
        'query': 'Places Of Interest in ' + search,
        'type': 'point_of_interest',
        'key': api_key
    }

    response = requests.get(url, params=params)
    data = response.json()["results"]

    response_list = []
    for i in range(len(data)):
        try:
            response_list.append({
                "longlat": data[i]["geometry"]["location"],
                "name": data[i]["name"],
                "date": date,
                "location": search,
                "photo": data[i]["photos"],
                "place_id": data[i]["place_id"]
            })
        # if it lacks any information e.g photo, proceed to store next entry
        # instead
        except BaseException:
            continue

        photo_params = {
            'maxheight': response_list[i]["photo"][0]["height"],
            'photo_reference': response_list[i]["photo"][0]["photo_reference"],
            'maxwidth': 500,
            'key': api_key,
        }

        encoded_params = urlencode(photo_params)
        base_url = 'https://maps.googleapis.com/maps/api/place/photo'
        response_list[i]["photo"] = f"{base_url}?{encoded_params}"

    return is_restaurant_saved(response_list)


def get_cname(search_item, api_key):

    geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'latlng': f"{search_item['longlat']['lat']},"
                  f"{search_item['longlat']['lng']}",
        'result_type': 'locality|country',
        'key': api_key
    }
    response_cname = requests.get(geocode_url, params=params)
    cname_data = response_cname.json()["results"][0]["address_components"]

    locality = [entry['long_name']
                for entry in cname_data
                if 'locality' in entry.get('types', [])][0]
    cname = [entry['long_name']
             for entry in cname_data if 'country' in entry.get('types', [])][0]

    return {"country_name": cname, "city": locality}


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


def cinfo_empty():
    return {"name": "",
            "currencies": "",
            "languages": ""}


def get_cinfo(cname):
    country_url = f'https://restcountries.com/v3.1/name/{cname}'
    response_cninfo = requests.get(country_url)
    data_country = response_cninfo.json()

    if len(data_country) == 0:
        cinfo = cinfo_empty()
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


# weather forecast

def interpret_weather(weather_code: int):
    if weather_code is None:
        return "Cloudy"
    elif weather_code < 3:
        return "Sunny"
    elif 3 <= weather_code <= 49:
        return "Cloudy"
    elif weather_code > 49:
        return "Rainy"


def get_weather(location, date):
    date = datetime.strptime(date, '%Y-%m-%d')
    current_datetime = datetime.now()

    # Calculate datetime 14 days from now
    datetime_14_d = current_datetime + timedelta(days=14)
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

    response_weather = requests.get(weather_url, params=weather_params)
    data_weather = response_weather.json()["daily"]
    return {
        "weather": interpret_weather(data_weather["weather_code"][0]),
        "min_temp": str(data_weather["temperature_2m_min"][0]) + "°C",
        "max_temp": str(data_weather["temperature_2m_max"][0]) + "°C",
        "daylight": round(data_weather["daylight_duration"][0] / 3600, 0),
    }


def fuzzy_match(search, cname):
    # Get the closest term from the list
    return process.extractOne(search, list(cname.values()))[0]


def get_place_details(place_id, date, search, api_key):

    place_det_url = 'https://maps.googleapis.com/maps/api/place/details/json'
    place_det_params = {
        'fields': "name,photos,editorial_summary,"
                  "user_ratings_total,rating,url",
        'place_id': place_id,
        'key': api_key}

    response_place_det = requests.get(place_det_url, params=place_det_params)
    data_place_det = response_place_det.json()["result"]

    place_info = {
        "place_id": place_id,
        "name": data_place_det["name"],
        "ratings": data_place_det["rating"],
        "rating_count": data_place_det["user_ratings_total"],
        "search_link": data_place_det["url"],
        "photo_reference": [photo for photo in data_place_det["photos"]
                            if photo.get("height", 0) > 900][:4],
        "editorial_summary": data_place_det["editorial_summary"]["overview"],
        "date": date,
        "location": search,
        "type": "Places"
    }

    det_photo_params = {
        'photo_reference': place_info["photo_reference"][0]["photo_reference"],
        'maxheight': 600,
        'key': 'AIzaSyA93iUbKdmGyCJOrEVnod8Q15l1Npz3Ono'
    }

    encoded_params = urlencode(det_photo_params)
    base_url = 'https://maps.googleapis.com/maps/api/place/photo'
    place_info["photo_reference"][0] = f"{base_url}?{encoded_params}"
    for i in range(1, 4):
        det_photo_params = {
            'photo_reference':
                place_info["photo_reference"][i]["photo_reference"],
            'maxwidth': 300,
            'maxheight': 200,
            'key': 'AIzaSyA93iUbKdmGyCJOrEVnod8Q15l1Npz3Ono'}
        encoded_params = urlencode(det_photo_params)
        base_url = 'https://maps.googleapis.com/maps/api/place/photo'
        place_info["photo_reference"][i] = f"{base_url}?{encoded_params}"
    return is_restaurant_saved(place_info)


def is_restaurant_saved(restaurants):
    try:
        conn, cursor = db.connect_to_db()
        cursor.execute("""
                       SELECT placeid FROM placesadded WHERE userid = %s
                       """, session["_user_id"])
        # get a tuple of all the placeids from places table
        saved_restaurants_records = cursor.fetchall()
        conn.commit()
    except Exception as e:
        print(e)
        return restaurants
    finally:
        cursor.close()
        conn.close()

    # Convert the list of tuples to a set for faster lookup
    # tuple of placeids.
    saved_restaurants = set(record[0] for record in saved_restaurants_records)

    # Update the 'is_saved' status for each
    # restaurant if its place_id is in the saved_restaurants set
    if isinstance(restaurants, list):
        for details in restaurants:
            if details['place_id'] in saved_restaurants:
                details['is_saved'] = True
    else:
        if restaurants['place_id'] in saved_restaurants:
            restaurants['is_saved'] = True
    return restaurants
