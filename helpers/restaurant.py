import os
from json.decoder import JSONDecodeError

import folium
import requests
from flask import jsonify, request
from flask_login import current_user
from requests.exceptions import HTTPError, RequestException
from requests.utils import quote

from helpers.connection import connect_to_db


def generate_map(restaurant_data, to_do_lat, to_do_long, radius):
    try:
        # Center the map by calculating the average latitude and longitude
        token = os.environ.get("MAPBOX_KEY")
        mapbox_url = (
            f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/512/"
            f"{{z}}/{{x}}/{{y}}?access_token={token}"
        )

        attribution = (
            "&copy; <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> "
            "&copy; <a href='https://www.openstreetmap.org/about/'"
            ">OpenStreetMap</a> "
            "<strong><a href='https://www.mapbox.com/map-feedback/' "
            "target='_blank'>Improve this map</a></strong>"
        )

        # Create the map centered on the central point
        eq_map = folium.Map(
            location=[to_do_lat, to_do_long],
            zoom_start=14,
            tiles=mapbox_url,
            attr=attribution,
        )

        # Define two different icons for markers
        to_do_map_pin = folium.Icon(icon="map-pin", prefix="fa", color="red")

        # Create and add the to-do marker to the map
        folium.Marker(
            location=[to_do_lat, to_do_long],
            # tooltip can be added if needed
            # popup can be added if needed
            icon=to_do_map_pin,  # Use the red pin icon for to-do locations
        ).add_to(eq_map)

        folium.Circle(
            location=[to_do_lat, to_do_long],
            radius=radius + 200,  # input is in m
            color="#ADD8E6",
            fill=True,
            fill_color="#ADD8E6",
            fill_opacity=0.30,
        ).add_to(eq_map)

        for data in restaurant_data:
            # Create the HTML for the popup
            popup_html = (
                "<div style='min-width: 200px; max-width: 250px; "
                "padding: 1rem; background-color: white; "
                "border-radius: 0.5rem; "
                "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);'>"
                "<img style='width: 100%; height: auto;"
                " border-radius: 0.25rem;' "
                f"src='{data['image_url']}' alt='Restaurant Image'>"
                "<div style='margin-top: 0.5rem;'>"
                "<div style='font-weight: 600; font-size: 1.25rem; "
                "line-height: 1.75rem; color: #4338ca;'>"
                f"<a href='{data['website_url']}' target='_blank' "
                "style='text-decoration: none; color: #4338ca;'>"
                f"{data['name']}</a>"
                "</div>"
                "</div>"
                "<div style='text-align: right; margin-top: 0.5rem;'>"
                "<span style='font-weight: 700; "
                "font-size: 1rem; color: #475569;'>"
                f"{data['ratings']}/5</span>"
                "</div>"
                "</div>"
            )

            # iframe = folium.IFrame(popup_html, width=150, height=200)

            # map_pin = folium.Icon(icon='location-dot',
            # prefix='fa', color='blue')
            map_pin = folium.Icon(
                icon="location-dot", prefix="fa", color="blue"
            )

            # Create and add a marker to the map
            folium.Marker(
                location=[data["lat"], data["lng"]],
                tooltip=data["name"],
                popup=folium.Popup(popup_html, max_width=300),
                icon=map_pin,
            ).add_to(eq_map)

        return (
            eq_map._repr_html_()
        )  # Return the HTML representation of the map

    except Exception as e:
        # app.logger.exception(f"An error occurred: {e}")
        return f"An error occurred: {e}", 500


def fetch_place_details(api_key, place_id):
    """Fetch place details using place_id."""
    geocode_url = (
        f"https://maps.googleapis.com/maps/api/geocode/json?"
        f"place_id={place_id}&key={api_key}"
    )
    response = requests.get(geocode_url)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            result = data["results"][0]
            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]
            # will give the street name not the name of the thing
            # place_name = result['formatted_name']
            return lat, lng
    return None, None


def parse_request_parameters():
    # place_id and name not required as passed in from the json
    # place_id = request.args.get('place_id',
    # 'ChIJz-VvsdMEdkgR1lQfyxijRMw')  # Default to Chinatown London
    # name = request.args.get('name', 'Default: China Town')
    keyword_string = request.args.get("keyword", "restaurant")
    price = request.args.get("price", "2")
    dist = int(request.args.get("dist", 1000))
    open_q = request.args.get("open", "")

    return keyword_string, price, dist, open_q


def search_nearby_restaurants(
    api_key, lat, lng, keyword_string, dist, price, open_q
):
    # Create a dictionary for the parameters
    params = {
        "location": f"{lat},{lng}",
        "radius": dist,
        "keyword": keyword_string,
        "key": api_key,
    }

    # Conditionally add optional parameters
    if price:
        params["maxprice"] = price
    if open_q:
        params["opennow"] = open_q

    # Make the GET request to the Google Places API
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
        params=params,
    )

    # Check if the request was successful
    if response.status_code == 200:
        nearby_data = response.json()
        return nearby_data
    else:
        # Handle potential errors
        response.raise_for_status()


def process_restaurant_data(nearby_data):
    all_restaurants = {}
    for result in nearby_data["results"]:
        search_link = "https://www.google.com/search?q=" + quote(
            result["name"]
        )

        restaurant_info = {
            "name": result["name"],
            "rating": result.get("rating", "No rating"),
            "rating_count": result.get(
                "user_ratings_total", "No rating count"
            ),
            "search_link": search_link,
            "latitude": result.get("geometry", {})
            .get("location", {})
            .get("lat", 0),
            "longitude": result.get("geometry", {})
            .get("location", {})
            .get("lng", 0),
            "photo_reference": result.get("photos", [{}])[0].get(
                "photo_reference", None
            ),
            "place_id": result.get("place_id", None),
        }

        # Add to dictionary only if
        # rating and rating_count are not default values
        if (
            restaurant_info["rating"] != "No rating"
            and restaurant_info["rating_count"] != "No rating count"
        ):
            all_restaurants[restaurant_info["name"]] = restaurant_info

    return all_restaurants


def sort_and_slice_restaurants(all_restaurants, top_n=15):
    sorted_restaurants = dict(
        sorted(
            all_restaurants.items(),
            key=lambda item: item[1]["rating_count"],
            reverse=True,
        )
    )
    return dict(list(sorted_restaurants.items())[:top_n])


def fetch_additional_details(
    api_key, top_restaurants_dict, date, location, max_requests=15
):
    counter = 0
    for name, details in top_restaurants_dict.items():
        if counter >= max_requests:
            break

        place_id = details["place_id"]  # Now accessed by key
        if place_id:
            place_details_url = (
                f"https://maps.googleapis.com/maps/api/place/details/json"
                f"?place_id={place_id}&fields=name,formatted_phone_number,"
                f"website,editorial_summary"
                f"&key={api_key}"
            )
            response = requests.get(place_details_url)
            place_details_data = response.json()

            if place_details_data.get("status") == "OK":
                result = place_details_data.get("result", {})
                details["formatted_phone_number"] = result.get(
                    "formatted_phone_number", "Phone number not found"
                )
                details["website"] = result.get(
                    "website", details["search_link"]
                )
                details["editorial_summary"] = result.get(
                    "editorial_summary", {}
                ).get("overview", "Editorial summary not found")

                photo_reference = details["photo_reference"]
                details["photo_url"] = (
                    f"https://maps.googleapis.com/maps/api/place/photo?"
                    f"maxwidth=400&photoreference"
                    f"={photo_reference}&key={api_key}"
                    if photo_reference
                    else "Image not found"
                )
                # location, place_id and date are used for the table!
                details["date"] = date
                details["location"] = location
                # default is_saved false
                details["is_saved"] = False

        counter += 1
    return top_restaurants_dict


def is_restaurant_saved(restaurants):
    try:
        first_restaurant_name = next(iter(restaurants))
        date = restaurants[first_restaurant_name]["date"]
        location = restaurants[first_restaurant_name]["location"]
        conn, cursor = connect_to_db()
        # cursor.execute("SELECT placeid FROM places")
        cursor.execute(
            """
                       SELECT placeid FROM placesadded
                       WHERE userid = %s AND date = %s AND location = %s
                       """, (current_user.id, date, location))
        # get a tuple of all the placeids from places table
        saved_restaurants_records = cursor.fetchall()
        conn.commit()
    except Exception:
        return restaurants
    finally:
        cursor.close()
        conn.close()

    # Convert the list of tuples to a set for faster lookup
    # tuple of placeids.
    saved_restaurants = set(
        record[0] for record in saved_restaurants_records
    )

    # Update the 'is_saved' status for each
    # restaurant if its place_id is in the saved_restaurants set
    for restaurant_name, details in restaurants.items():
        if (
            "place_id" in details
            and details["place_id"] in saved_restaurants
        ):
            details["is_saved"] = True

    return restaurants


def get_api_key_or_error():
    api_key = os.environ.get("GCLOUD_KEY")
    if not api_key:
        raise ValueError("API key is empty")
    return api_key


def get_request_data():
    default_data = {
        "place_id": "ChIJz-VvsdMEdkgR1lQfyxijRMw",
        "name": "Default: China Town",
        "location": "London",
        "date": "2023-01-01",
    }
    if request.method == "POST":
        routes_data = request.get_json() or {}
    else:
        routes_data = request.args
    data = {
        key: routes_data.get(key, default_value)
        for key, default_value in default_data.items()
    }
    return data


def get_search_details(data):
    keyword_string, price, dist, open_q = parse_request_parameters()
    search_details = {
        "name": data["name"],
        "keyword": keyword_string,
        "price": price,
        "dist": dist,
        "open": open_q,
    }
    return search_details


def get_lat_lng_or_error(api_key, place_id):
    lat, lng = fetch_place_details(api_key, place_id)
    if not lat or not lng:
        raise ValueError("Failed to retrieve place details")
    return lat, lng


def get_nearby_data_or_error(api_key, lat, lng, search_details):
    nearby_data = search_nearby_restaurants(
        api_key,
        lat,
        lng,
        search_details["keyword"],
        search_details["dist"],
        search_details["price"],
        search_details["open"],
    )
    if "status" not in nearby_data or nearby_data["status"] != "OK":
        raise ValueError("Failed to retrieve data")
    return nearby_data


def process_and_sort_restaurants(nearby_data):
    all_restaurants = process_restaurant_data(nearby_data)
    top_restaurants_dict = sort_and_slice_restaurants(all_restaurants)
    return top_restaurants_dict


def fetch_and_update_restaurant_details(api_key, restaurants, data):
    updated_restaurants = fetch_additional_details(
        api_key, restaurants, data["date"], data["location"]
    )
    updated_restaurants = is_restaurant_saved(updated_restaurants)
    return updated_restaurants


def prepare_restaurant_data_for_map(restaurants_dict):
    restaurant_data = [
        {
            "name": details["name"],
            "lat": details["latitude"],
            "lng": details["longitude"],
            "website_url": details["website"],
            "image_url": details["photo_url"],
            "ratings": details["rating"],
        }
        for _, details in restaurants_dict.items()
    ]
    return restaurant_data


def generate_map_html(restaurant_data, lat, lng, dist):
    map_html = generate_map(restaurant_data, lat, lng, dist)
    return map_html


def handle_error(e):
    if isinstance(e, HTTPError):
        return jsonify({"error": "HTTP error occurred"}), 500
    elif isinstance(e, JSONDecodeError):
        return jsonify({"error": "No Restaurants found"}), 500
    elif isinstance(e, RequestException):
        return jsonify({"error": "Please check your connection"}), 500
    else:
        return jsonify({"error": str(e)}), 500


def handle_places_table(cursor, data):
    # Check if the row exists using EXISTS
    check_query = """
        SELECT EXISTS(
            SELECT 1 FROM places
            WHERE placeid = %s
        )
    """
    cursor.execute(check_query, (data["place_id"],))
    exists = cursor.fetchone()[0]

    # Update or Insert based on the check
    if exists:
        # Update existing record
        update_query = """
            UPDATE places
            SET name = %s, ratings = %s, rating_count = %s,
            search_link = %s, photo_reference = %s,
            editorial_summary = %s, type = %s
            WHERE placeid = %s
        """
        cursor.execute(
            update_query,
            (
                data["name"],
                data["ratings"],
                data["rating_count"],
                data["search_link"],
                data["photo_reference"],
                data["editorial_summary"],
                data["type"],
                data["place_id"],
            ),
        )
    else:
        # Insert new record
        insert_query = """
            INSERT INTO places (placeid, name, ratings,
            rating_count, search_link, photo_reference,
            editorial_summary, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                data["place_id"],
                data["name"],
                data["ratings"],
                data["rating_count"],
                data["search_link"],
                data["photo_reference"],
                data["editorial_summary"],
                data["type"],
            ),
        )


def handle_placesadded_table(cursor, user_id, data):
    # Insert into placesadded table
    insert_query = """
        INSERT INTO placesadded
        (userid, location, date, placeid)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(
        insert_query,
        (
            user_id,
            data["location"],
            data["date"],
            data["place_id"],
        ),
    )


def delete_from_placesadded(cursor, user_id, data):
    sql_delete = """
        DELETE FROM placesadded
        WHERE userid = %s AND location = %s
        AND date = %s AND placeid = %s
    """
    cursor.execute(
        sql_delete,
        (user_id, data["location"],
         data["date"], data["place_id"]),
    )


def delete_from_places_if_needed(cursor, place_id):
    # Check if no users have place_id in placesadded table
    sql_check = ("SELECT EXISTS (SELECT 1 FROM "
                 "placesadded WHERE placeid = %s)")
    cursor.execute(sql_check, (place_id,))
    exists = cursor.fetchone()[0]

    # If place_id is not in the placesadded table
    if not exists:
        sql_delete = "DELETE FROM places WHERE placeid = %s"
        cursor.execute(sql_delete, (place_id,))


def save_restaurant_data(user_id, data):
    conn, cursor = None, None
    try:
        # Set up DB connection
        conn, cursor = connect_to_db()

        # Handle 'places' table
        handle_places_table(cursor, data)

        # Handle 'placesadded' table
        handle_placesadded_table(cursor, user_id, data)

        # Commit changes to the database
        conn.commit()

        return {"status": "success"}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_restaurant_data(user_id, data):
    conn, cursor = None, None
    try:
        # Set up DB connection
        conn, cursor = connect_to_db()

        # Delete from placesadded table
        delete_from_placesadded(cursor, user_id, data)

        # Check and delete from places table if needed
        delete_from_places_if_needed(cursor, data["place_id"])

        # Commit changes to the database
        conn.commit()
        return {"status": "success", "message": "Operation successful"}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
