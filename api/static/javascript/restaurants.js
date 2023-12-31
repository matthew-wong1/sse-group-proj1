const popup = document.getElementById('alert-popup');

// hide the alert popup
function hidePopup() {
    popup.classList.remove('opacity-100');
    popup.classList.add('opacity-0');
    setTimeout(() => {
        popup.style.display = 'none';
        popup.classList.remove('opacity-0'); // Reset opacity class
        popup.classList.add('opacity-100'); // Reset opacity class
}, 500);
}

// show the alert popup
function showPopup() {
  popup.style.display = 'flex';
  setTimeout(hidePopup, 5000);
}

// class of the popup
const red = "fixed top-20 z-50 left-1/2 transform -translate-x-1/2 \
	flex items-center p-4 mb-4 rounded-lg text-red-800 border-t-4 \
	shadow-2xl border-red-300 bg-red-50 opacity-100 transition-opacity \
	duration-500";
const green = "fixed top-20 z-50 left-1/2 transform -translate-x-1/2 flex \
	items-center p-4 mb-4 rounded-lg text-green-800 border-t-4 shadow-2xl \
	border-green-300 bg-green-50 opacity-100 transition-opacity duration-500"


// JavaScript function to initialize the 3D Mapbox GL map
function initialize3DMap(coords, restaurant_data) {
    // mapboxAccessToken from JS outside
    mapboxgl.accessToken = mapboxAccessToken;
    var map3D = new mapboxgl.Map({
        container: 'map3D',
        style: 'mapbox://styles/mapbox/streets-v11', // streets-v8
        center: coords,
        zoom: 15,
        pitch: 45,
        bearing: -17.6,
        antialias: true, 
        showZoom: true, 
    });

    map3D.on('load', function() {
        // Set the terrain for 3D terrain
        map3D.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });

        // Add the 3D buildings layer using the fill-extrusion type
        map3D.addLayer({
            'id': '3d-buildings',
            'source': 'composite',
            'source-layer': 'building',
            'filter': ['==', 'extrude', 'true'],
            'type': 'fill-extrusion',
            'minzoom': 15,
            'paint': {
                'fill-extrusion-color': '#aaa',
                'fill-extrusion-height': [
                    "interpolate", ["linear"], ["zoom"],
                    15, 0,
                    15.05, ["get", "height"]
                ],
                'fill-extrusion-base': [
                    "interpolate", ["linear"], ["zoom"],
                    15, 0,
                    15.05, ["get", "min_height"]
                ],
                'fill-extrusion-opacity': .6
            }
        }, 'waterway-label'); // Place the layer beneath the waterway-label layer

        // Add a sky layer to the map
        map3D.addLayer({
            'id': 'sky',
            'type': 'sky',
            'paint': {
                'sky-type': 'atmosphere',
                'sky-atmosphere-sun': [0.0, 0.0],
                'sky-atmosphere-sun-intensity': 15
            }
        });

        new mapboxgl.Marker({ color: 'red' })
            .setLngLat(coords)
            .setPopup(new mapboxgl.Popup({ offset: 25 })
                    .setHTML('<h3>' +'test name '+ '</h3>'))
            .addTo(map3D);


        // Add markers for each restaurant from the restaurant_data array
        restaurant_data.forEach(function(restaurant) {
            new mapboxgl.Marker()
                .setLngLat([restaurant.lng, restaurant.lat])
                .setPopup(new mapboxgl.Popup({ offset: 25 })
                    .setHTML('<h3>' + restaurant.name + '</h3><p>' + restaurant.ratings + '</p>'))
                .addTo(map3D);
        });
    });
}
// JavaScript functions to show/hide the 3D map
function show3DMap() {
    document.getElementById('map3D-container').classList.remove('hidden');
    document.getElementById('restaurants-container').classList.add('hidden');
    initialize3DMap(toDoCoords, latLong);
}

function hide3DMap() {
    document.getElementById('map3D-container').classList.add('hidden');
    document.getElementById('restaurants-container').classList.remove('hidden');
}
function showMapView() {
    document.getElementById('map-container').classList.remove('hidden');
    document.getElementById('restaurants-container').classList.add('hidden');
}

function hideMapView() {
    document.getElementById('map-container').classList.add('hidden');
    document.getElementById('restaurants-container').classList.remove('hidden');
}

// JS for distance slider...
const distanceSlider = document.getElementById('distance');
const distanceValue = document.getElementById('distanceValue');
distanceSlider.oninput = function() {
    distanceValue.textContent = this.value + ' kilometers';
}

// to hide the spinner
window.onload = function() {
        // Hide the spinner once the page is fully loaded
    document.getElementById('loadingSpinner').style.display = 'none';
    // Show the main content
    document.getElementById('contentBody').style.display = 'block';    
};

// Function to handle price selection
function togglePrice(level) {
    let priceSpans = document.querySelectorAll('#priceIndicator span');
    for (let i = 0; i < priceSpans.length; i++) {
        if (i < level) {
            priceSpans[i].classList.add('text-logo-contrast');
            priceSpans[i].classList.remove('text-gray-400');
        } else {
            priceSpans[i].classList.remove('text-logo-contrast');
            priceSpans[i].classList.add('text-gray-400');
        }
    }
}

// Function to handle type selection
let selectedType = null;
function toggleType(type) {
    selectedType = selectedType === type ? null : type;
    document.querySelectorAll('#typeIndicator span').forEach(span => {
    const isActive = span.textContent.toLowerCase() === selectedType;
    span.classList.toggle('text-logo-contrast', isActive);
    span.classList.toggle('text-gray-400', !isActive);
});      
}

function getRestaurantData(place_id) {
    // Loop through all restaurants to find the one with the matching place_id
    for (const [name, details] of Object.entries(jsRestaurants)) { // Updated variable name here
        if (details['place_id'] === place_id) {
            // Construct the restaurantData dictionary with the needed details
            const restaurantData = {
                place_id: details['place_id'],
                name: name,
                ratings: details['rating'],
                rating_count: details['rating_count'],
                search_link: details['website'],
                photo_reference: details['photo_url'],
                editorial_summary: details['editorial_summary'],
                phone_number: details['formatted_phone_number'],
                date: details['date'], 
                location: details['location'], 
                type: "restaurant"
            };
            return restaurantData;
        }
    }
    return null; // Return null if no matching restaurant is found
}

function toggleRestaurant(place_id) {
    const restaurantData = getRestaurantData(place_id);

    if (!restaurantData) {
        console.error('Restaurant with place_id not found');
        return;
    }

    const heartIcon = document.getElementById('heart-' + place_id);
    heartIcon.classList.add('fa-beat'); // Add spinning class on click
    // Determine the current state based on the icon class
    const isSaved = heartIcon.classList.contains('fas');
            
    // Choose the endpoint based on the current state
    const endpoint = isSaved ? '/delete-restaurant' : '/save-restaurant';

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(restaurantData),
        credentials: 'include' // test if this fixes log in error
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error("User not logged in")
            }
        }
        return response.json();
    })
    .then(data => {
        heartIcon.classList.remove('fa-beat');
        if (data.status === 'success') {
            // Toggle the icon
            if (isSaved) {
                heartIcon.classList.remove('fas');
                heartIcon.classList.add('far');
            } else {
                heartIcon.classList.remove('far');
                heartIcon.classList.add('fas');
            }
        } else {
            popup.className = red
            document.getElementById('alert-text').innerHTML = 
                "There was an error updating your favourites. Please try again"
            showPopup()
        }
    })
    .catch((error) => {
        heartIcon.classList.remove('fa-beat');
        if (error.message === "User not logged in") {
            if (confirm('You need to be logged in to save to favourites. Would you like to log in now?')) {
            // If they confirm, redirect them to the login page
            window.location.href = '/login'; 
            }
        } else {
            popup.className = red
            document.getElementById('alert-text').innerHTML = 
                "There was an error updating your favourites. Please try again later"
            showPopup()
        }                      
    });
}

function submitRequest() {
    // Show the full-screen spinner
    document.getElementById('loadingSpinner').style.display = 'flex';

    // Hide the main content
    document.getElementById('restaurants-container').style.display = 'none';

    // Retrieve current values from URL
    var currentParams = new URLSearchParams(window.location.search);
    var currentName = currentParams.get('name') || 'soho london'; 
    var currentPrice = currentParams.get('price') || '2'; // Default price level
    var currentKeyword = currentParams.get('keyword') || 'restaurant'; // Default keyword
    var currentPlace_id = currentParams.get('place_id') || 'ChIJz-VvsdMEdkgR1lQfyxijRMw';
    var currentDate = currentParams.get('date') || '2023-12-12';

    // Getting new values from user selection
    var distanceInKm = document.getElementById('distance').value;
    var distanceInMeters = distanceInKm * 1000; // Converting km to meters

    var selectedPriceLevel = document.querySelectorAll('#priceIndicator .text-logo-contrast').length || currentPrice;
    var selectedType = document.querySelector('#typeIndicator .text-logo-contrast')?.textContent.toLowerCase() || currentKeyword;

    // Updating query string with new or default values
    currentParams.set('dist', distanceInMeters);
    currentParams.set('price', selectedPriceLevel);
    currentParams.set('keyword', selectedType);
    currentParams.set('name', currentName); // Include the name in the query string for title
    currentParams.set('place_id', currentPlace_id); 
    currentParams.set('date', currentDate); 

    // Refreshing the page with updated parameters
    window.location.href = '/restaurants?' + currentParams.toString();
}