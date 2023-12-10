import configparser
import json
import os

import requests

import helpers.connection as db

config = configparser.ConfigParser()
file_path = 'ini/favourites.ini'
absolute_path = os.path.join(os.getcwd(), file_path)
config.read(absolute_path)


# function to return the locations user had saved as favourites
# from the database along with the place details
def retrieve_favourites(user):
    if 'UserSettings' in config:
        print("UserSettings section found.")
    print(config['query']['retrieve_favourites'])
    conn, cursor = db.connect_to_db()
    cursor.execute(config['query']['retrieve_favourites'], (user,))
    sql_results = cursor.fetchall()
    cursor.close()
    conn.close()

    return sql_results


# retrieve the locations saved to favourites.
# The locations in each collection are
# stored in a list and grouped by the tripid.
# The position of each location in the list
# is also sorted based on their saved sort
# order (if any), to facilitate display
# frontend
def get_favourites(user):

    results = retrieve_favourites(user)

    keys = [
        'tripid',
        'index',
        'location',
        'date',
        'placeid',
        'name',
        'ratings',
        'rating_count',
        'search_link',
        'photo_reference',
        'editorial_summary',
        'type',
        'sortorder']
    data = [{k: v for k, v in zip(keys, result)} for result in results]
    # create a dictionary, with each tripid mapped to the
    # list of locations associated with the trip as well
    # as the sort order
    transformed_data = {}
    for entry in data:
        trip_id = entry['tripid']
        if trip_id not in transformed_data:
            transformed_data[trip_id] = {
                'tripid': trip_id,
                'sortorder': entry['sortorder'],
                'place_list': []}
        transformed_data[trip_id]['place_list'].append(
            {
                'index': entry['index'],
                'location': entry['location'],
                'placeid': entry['placeid'],
                'name': entry['name'],
                'ratings': entry['ratings'],
                'rating_count': entry['rating_count'],
                'search_link': entry['search_link'],
                'photo_reference': entry['photo_reference'],
                'editorial_summary': entry['editorial_summary'],
                'type': entry['type']})
    # sort the list of locations according to the saved
    # sort order if it is available
    for trip_data in transformed_data.values():
        if trip_data["sortorder"] is not None:
            if (len(trip_data["sortorder"]) ==
                    len(trip_data["place_list"])):
                trip_data['place_list'] = sorted(
                    trip_data['place_list'],
                    key=lambda x: trip_data["sortorder"].index(
                        x['index']))
    return list(transformed_data.values())


# function to save the sorted order of the
# locations into the databse
def save_favourites_order(user, sortedList):
    trip_id = sortedList[0]['tripid']
    sorted_idx = [x['idx'] for x in sortedList]
    conn, cursor = db.connect_to_db()
    cursor.execute(config['query']['save_fav_order'],
                   (user + trip_id, sorted_idx, sorted_idx))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


# API call to google routes to get the
# optimize path based on the list of
# placeID provided. It will return a
# list of the optimized order of the
# intermediate waypoints.
def get_route(placeID_list, api_key):
    url = 'https://routes.googleapis.com/directions/v2:computeRoutes'
    payload = {
        "origin": {
            "placeId": placeID_list[0]["placeID"]
        },
        "destination": {
            "placeId": placeID_list[-1]["placeID"]
        },
        "intermediates": [{"placeId": x["placeID"]}
                          for x in placeID_list[1:-1]],
        "travelMode": "DRIVE",
        "optimizeWaypointOrder": "true"
    }
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'routes.optimizedIntermediateWaypointIndex'
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()["routes"][0]['optimizedIntermediateWaypointIndex']
