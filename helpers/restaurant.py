from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import folium
import json
import requests
from requests.utils import quote

def generate_map(restaurant_data, to_do_lat, to_do_long, radius):
    try:
        # Center the map by calculating the average latitude and longitude
        latitudes = [data['lat'] for data in restaurant_data]
        longitudes = [data['lng'] for data in restaurant_data]
        eq_map = folium.Map(location=[to_do_lat, to_do_long], zoom_start=14)

        # Define two different icons for markers
        to_do_map_pin = folium.Icon(icon='map-pin', prefix='fa', color='red')
                    
        # Create and add the to-do marker to the map
        folium.Marker(
            location=[to_do_lat, to_do_long],
            # tooltip can be added if needed
            # popup can be added if needed
            icon=to_do_map_pin  # Use the red pin icon for to-do locations
        ).add_to(eq_map)

        #radius =  2000

        folium.Circle(
            location=[to_do_lat, to_do_long],
            radius=radius+200, # input is in m
            color='#ADD8E6',
            fill=True,
            fill_color='#ADD8E6',
            fill_opacity=0.30
        ).add_to(eq_map)

        for data in restaurant_data:
            # Create the HTML for the popup
            popup_html = f"""
                <div style='min-width: 200px; max-width: 250px; padding: 1rem; background-color: white; border-radius: 0.5rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);'>
                    <img style='width: 100%; height: auto; border-radius: 0.25rem;' src='{data['image_url']}' alt='Restaurant Image'>
                    <div style='margin-top: 0.5rem;'>
                        <div style='font-weight: 600; font-size: 1.25rem; line-height: 1.75rem; color: #4338ca;'>
                            <a href='{data['website_url']}' target='_blank' style='text-decoration: none; color: #4338ca;'>{data['name']}</a>
                        </div>
                    </div>
                    <div style='text-align: right; margin-top: 0.5rem;'>
                        <span style='font-weight: 700; font-size: 1rem; color: #475569;'>{data['ratings']}/5</span>
                    </div>
                </div>
            """
            iframe = folium.IFrame(popup_html, width=150, height=200)
            popup = folium.Popup(iframe, max_width=150)           

            #map_pin = folium.Icon(icon='location-dot', prefix='fa', color='blue')
            map_pin = folium.Icon(icon='location-dot', prefix='fa', color='blue')
            
            # Create and add a marker to the map
            folium.Marker(
                location=[data['lat'], data['lng']],
                tooltip=data['name'],
                popup=folium.Popup(popup_html, max_width=300),
                icon=map_pin
            ).add_to(eq_map)
        
        return eq_map._repr_html_()  # Return the HTML representation of the map

    except Exception as e:
        app.logger.exception(f"An error occurred: {e}")
        return f"An error occurred: {e}", 500

def fetch_place_details(api_key, place_id):
    """Fetch place details using place_id."""
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={api_key}"
    response = requests.get(geocode_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            result = data['results'][0]
            lat = result['geometry']['location']['lat']
            lng = result['geometry']['location']['lng']
            # will give the street address not the name of the thing
            #place_name = result['formatted_address']
            return lat, lng
    return None, None

def parse_request_parameters():
    #place_id and address not required as passed in from the json 
    #place_id = request.args.get('place_id', 'ChIJz-VvsdMEdkgR1lQfyxijRMw')  # Default to Chinatown London
    #address = request.args.get('address', 'Default: China Town')
    keyword_string = request.args.get('keyword', 'restaurant')       
    price = request.args.get('price', '2')
    dist = int(request.args.get('dist', 1000))
    open_q = request.args.get('open', '')

    return keyword_string, price, dist, open_q

def search_nearby_restaurants(api_key, lat, lng, keyword_string, dist, price, open_q):
   # Create a dictionary for the parameters
    params = {
        'location': f'{lat},{lng}',
        'radius': dist,
        'keyword': keyword_string,
        'key': api_key
    }

    # Conditionally add optional parameters
    if price:
        params['maxprice'] = price
    if open_q:
        params['opennow'] = open_q

    # Make the GET request to the Google Places API
    response = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)

    # Check if the request was successful
    if response.status_code == 200:
        nearby_data = response.json()
        return nearby_data
    else:
        # Handle potential errors
        response.raise_for_status()

def process_restaurant_data(nearby_data):
    all_restaurants = {}        
    for result in nearby_data['results']:
        search_link = "https://www.google.com/search?q=" + quote(result['name'])
        
        restaurant_info = {
            'name': result['name'],
            'rating': result.get('rating', 'No rating'),
            'rating_count': result.get('user_ratings_total', 'No rating count'),
            'search_link': search_link,
            'latitude': result.get('geometry', {}).get('location', {}).get('lat', 0),
            'longitude': result.get('geometry', {}).get('location', {}).get('lng', 0),
            'photo_reference': result.get('photos', [{}])[0].get('photo_reference', None),
            'place_id': result.get('place_id', None)
        }
        
        # Add to dictionary only if rating and rating_count are not default values
        if restaurant_info['rating'] != 'No rating' and restaurant_info['rating_count'] != 'No rating count':
            all_restaurants[restaurant_info['name']] = restaurant_info

    return all_restaurants


def sort_and_slice_restaurants(all_restaurants, top_n=15):
    sorted_restaurants = dict(sorted(all_restaurants.items(), key=lambda item: item[1]['rating_count'], reverse=True))
    return dict(list(sorted_restaurants.items())[:top_n])

def fetch_additional_details(api_key, top_restaurants_dict, max_requests=15):
    counter = 0
    for name, details in top_restaurants_dict.items():
        if counter >= max_requests:
            break

        place_id = details['place_id']  # Now accessed by key
        if place_id:
            place_details_url = (f"https://maps.googleapis.com/maps/api/place/details/json"
                                 f"?place_id={place_id}&fields=name,formatted_phone_number,website,editorial_summary"
                                 f"&key={api_key}")
            response = requests.get(place_details_url)
            place_details_data = response.json()

            if place_details_data.get('status') == 'OK':
                result = place_details_data.get('result', {})
                details['formatted_phone_number'] = result.get('formatted_phone_number', 'Phone number not found')
                details['website'] = result.get('website', details['search_link'])
                details['editorial_summary_overview'] = result.get('editorial_summary', {}).get('overview', 'Editorial summary not found')

                photo_reference = details['photo_reference']
                details['photo_url'] = (f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={api_key}"
                                        if photo_reference else 'Image not found')

        counter += 1
    return top_restaurants_dict