import json

import requests

import helpers.connection as db


# function to return the locations user had saved as favourites
# from the database along with the place details
def retrieve_favourites(user):

    conn, cursor = db.connect_to_db()
    sql = """
        SELECT
            CONCAT(a.location, ' (',CAST(a.date AS VARCHAR),')') AS trip,
            a.id AS index, a.location, a.date, a.placeid, b.name,
            CAST(b.ratings AS FLOAT) AS ratings,
            b.rating_count, b.search_link, b.photo_reference,
            b.editorial_summary, b.type, c.sortorder
        FROM placesadded a
        LEFT JOIN places b
            ON a.placeid = b.placeid
        LEFT JOIN placesorder c
            ON CONCAT(a.userid, a.location,
                ' (',CAST(a.date AS VARCHAR),')')
                = c.id
        WHERE a.userid = %s
        ORDER BY a.date DESC, index;
        """
    cursor.execute(sql, (user,))
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
                try:
                    trip_data['place_list'] = sorted(
                        trip_data['place_list'],
                        key=lambda x: trip_data["sortorder"].index(
                            x['index']))
                except BaseException:
                    trip_data['place_list'] = trip_data['place_list']
    return list(transformed_data.values())


# function to save the sorted order of the
# locations into the databse
def save_favourites_order(user, sortedList):
    trip_id = sortedList[0]['tripid']
    sorted_idx = [x['idx'] for x in sortedList]
    conn, cursor = db.connect_to_db()
    sql = """
        INSERT INTO placesorder (id, sortorder)
        VALUES (%(id)s, %(sortorder)s)
        ON CONFLICT (id) DO UPDATE
        SET sortorder = %(sortorder)s;
        """
    cursor.execute(sql,
                   {"id": user + trip_id,
                    "sortorder": (sorted_idx)})
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
