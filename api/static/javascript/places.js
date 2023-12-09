
// for the purpose of the masonry gallery foramatting
var $stampElement = $('.stamp');
var $grid = $('.jqueryGrid').masonry({
  itemSelector: '.jqueryGrid-item',
  columnWidth: '.jqueryGrid-sizer',
  stamp: $stampElement 
});

// reload the grid after each image load
$grid.imagesLoaded().progress(function() {
  $grid.masonry();
  
});

// hide overlay
function hideOverlay() {
	// Hide the overlay and details box
    document.querySelector('.overlay').style.display = 'none';
	document.querySelector('#overlayDetails').style.display = 'none';
}

// show the overlay
function showOverlay() {
    // Show the overlay
    document.querySelector('.overlay').style.display = 'flex';
    document.querySelector('#overlayDetails').style.display = 'flex';
}

// get all elements with placid attr
const elementsWithDataName = document.querySelectorAll('[placeid]');

let placedetails;

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

// Add an event listener to elements with data-name attribute
elementsWithDataName.forEach(element => {

    // Event listener to trigger the overlay being rendered 
    // with the details of the place 
    element.addEventListener('click', function(event) {
        const placeID = event.target.getAttribute('placeid');
        if (placeID !== null) {
            fetch(`places/details?placeid=${encodeURIComponent(placeID)}` +
                `&date=${encodeURIComponent(search_date)}&location=` +
                `${encodeURIComponent(search_location)}`)
                .then(response => {
                    if (!response.ok) {   
                        popup.className = red;
                        document.getElementById('alert-text').innerHTML = 
                            "The details for this place are not available.";
                        showPopup();
                    }
                    return response.json();
                })
                .then(data => {
                    // if no details returned, short-circuit the chain
                    if (Object.keys(data).length === 0) {
                        popup.className = red;
                        document.getElementById('alert-text').innerHTML = 
                            "The details for this place are not available.";
                        showPopup();
                        return;
                    }

                    placedetails = data;
                    // Update the title and descriptions
                    document.getElementById('overlay-title').innerHTML = 
                        `${data.name}`;
                    document.getElementById('overlay-desc').innerHTML = 
                        `${data.editorial_summary}`;
                    
                    // update the heart status depending on
                    // whether the location had been previously
                    // saved to favourites
                    const heart = document.getElementById('heart-in-details');
                    if (data.is_saved === true) {
                        heart.classList.add('fas');
                    } else {
                        heart.classList.add('far');
                    }

                    // Update the content in the overlay with images
                    const imageGrid = document.getElementById('imageGrid');
                    // Clear previous content if needed
                    imageGrid.innerHTML = '';

                    // Larger image added
                    const largerImage = document.createElement('img');
                    largerImage.src = data.photo_reference[0];
                    largerImage.className = 'h-[40rem] rounded-lg shadow-2xl'; 
                    imageGrid.appendChild(largerImage);

                    // Add the elements for the smaller images
                    const smallerImagesColumn = document.createElement('div');
                    smallerImagesColumn.className = 
                        'flex flex-col justify-between h-[40rem]';        

                    // Three smaller images (starting from index 1)
                    for (let i = 1; i < 4; i++) {
                        const smallImage = document.createElement('img');
                        smallImage.src = data.photo_reference[i];
                        smallImage.className = 
                            'max-h-[13rem] rounded-lg shadow-2xl'; 
                        smallerImagesColumn.appendChild(smallImage);
                    };
                    // Append the elements to the parent
                    imageGrid.appendChild(smallerImagesColumn);

                    // Show the overlay after updating content
                    showOverlay();
                })
                .catch(error => {
                    // Handle errors from the fetch or the response
                    popup.className = red;
                    document.getElementById('alert-text').innerHTML = 
                        "The details for this place are not available.";
                    showPopup();
                });
        }
    });
});

// prevent the click to propogating to the parent 
document.getElementById('overlayDetails').addEventListener('click', 
                                                           function(event) {
    event.stopPropagation();
});

// get the element that contains the weather ID
const weatherElement  = document.getElementById("weather");
 
// function for raining animation
var makeItRain = function() {
    //clear out everything
    $('.rain').empty();
  
    var increment = 0;
    var drops = "";
    var backDrops = "";
  
    while (increment < 85) {
      //couple random numbers to use for various randomizations
      //random number between 98 and 1
      var randoHundo = (Math.floor(Math.random() * (98 - 1 + 1) + 1));
      //random number between 5 and 2
      var randoFiver = (Math.floor(Math.random() * (5 - 1 + 1) + 2));
      //increment
      increment += randoFiver;
      //add in a new raindrop with various randomizations to certain CSS properties
      drops += '<div class="drop" style="left: ' + (increment+5) + 
        '%; bottom: ' + (randoFiver + randoFiver - 1 + 100) + 
        '%; animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + 
        randoHundo + 's;"><div class="stem" style="animation-delay: 0.' + 
        randoHundo + 's; animation-duration: 0.5' + randoHundo + 
        's;"></div><div class="splat" style="animation-delay: 0.' + 
        randoHundo + 's; animation-duration: 0.5' + randoHundo + 
        's;"></div></div>';
      backDrops += '<div class="drop" style="right: ' + increment + 
        '%; bottom: ' + (randoFiver + randoFiver - 1 + 100) + 
        '%; animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + 
        randoHundo + 's;"><div class="stem" style="animation-delay: 0.' + 
        randoHundo + 's; animation-duration: 0.5' + randoHundo + 
        's;"></div><div class="splat" style="animation-delay: 0.' + 
        randoHundo + 's; animation-duration: 0.5' + randoHundo + 
        's;"></div></div>';
    }
  
    $('.rain.front-row').append(drops);
    $('.rain.back-row').append(backDrops);
}

// set the class based on the weather 
if (weatherData === "Rainy") {
  weatherElement.className = "rain front-row"
  makeItRain();
} else if (weatherData === "Sunny") {
  weatherElement.className = "ball"
} else if (weatherData == "Cloudy") {
weatherElement.className = ""
  weatherElement.innerHTML = `
  <div id="background-wrap">
    <div class="x1">
        <div class="cloud"></div>
    </div>
    <div class="x2">
        <div class="cloud"></div>
    </div>
    <div class="x3">
        <div class="cloud"></div>
    </div>
</div>
`
};

// toggle heart button in the overlay
function toggleHeartInDet() {
    
    const heartIcon = document.getElementById('heart-in-details');
    heartIcon.classList.add('fa-beat'); // Add spinning class on click
    // Determine the current state based on the icon class
    const isSaved = heartIcon.classList.contains('fas');
            
    // Choose the endpoint based on the current state
    const endpoint = isSaved ? '/places/delete-places' : '/places/save-places';
    if (Array.isArray(placedetails.photo_reference)) {
        placedetails.photo_reference = placedetails.photo_reference[0];
    }
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(placedetails),
        credentials: 'include' // test if this fixes log in error
    })
    .then(response => {
        if (!response.ok) {
            popup.className = red
            document.getElementById('alert-text').innerHTML = 
                "There was an error saving the location. Please try again later"
            showPopup()
        }
        return response.json();
    })
    .then(data => {
        heartIcon.classList.remove('fa-beat');

        if (data.status === 'success') {
            // Toggle the icon
            if (isSaved) {
                const heartIconInList = document.getElementById(
                    `heart-in-${placedetails.place_id}`);
                heartIconInList.classList.remove('fas');
                heartIconInList.classList.add('far');
                heartIcon.classList.remove('fas');
                heartIcon.classList.add('far');
            } else {
                const heartIconInList = document.getElementById(
                    `heart-in-${placedetails.place_id}`);
                heartIconInList.classList.remove('far');
                heartIconInList.classList.add('fas');
                heartIcon.classList.remove('far');
                heartIcon.classList.add('fas');
            }
        } else {
            heartIcon.classList.remove('fa-beat');
            popup.className = red
            document.getElementById('alert-text').innerHTML = 
                "There was an error saving the location. Please try again later"
            showPopup()
        }
    })
    .catch((error) => {
        heartIcon.classList.remove('fa-beat');
        popup.className = red
        document.getElementById('alert-text').innerHTML = 
            "There was an error saving the location. Please try again later"
        showPopup()                         
    });
}

// open the restaurant search in a new tab
function searchFood() {
    window.open(`/restaurants?name=${encodeURIComponent(placedetails.name)}` +
        `&place_id=${encodeURIComponent(placedetails.place_id)}&date=` +
        `${encodeURIComponent(search_date)}&location=` +
        `${encodeURIComponent(search_location)}`, '_blank');
}

// toggle heart button in the main page
function toggleHeartInList(heart_placeid) {
    
    const heartIcon = document.getElementById(`heart-in-${heart_placeid}`);
    heartIcon.classList.add('fa-beat'); // Add spinning class on click
    // Determine the current state based on the icon class
    const isSaved = heartIcon.classList.contains('fas');
            
    // Choose the endpoint based on the current state
    const endpoint = isSaved ? '/places/delete-places' : '/places/save-places';
    console.log(endpoint)
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'place_id': heart_placeid,
            'date': search_date,
            'location' : search_location,
        })
        
    })
    .then(response => {
        if (!response.ok) {
            popup.className = red
            document.getElementById('alert-text').innerHTML = 
                "There was an error saving the location. Please try again later"
            showPopup()
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
            heartIcon.classList.remove('fa-beat');
            popup.className = red
            document.getElementById('alert-text').innerHTML = 
                "There was an error saving the location. Please try again later"
            showPopup()
        }
    })
    .catch((error) => {
        heartIcon.classList.remove('fa-beat');
        popup.className = red
        document.getElementById('alert-text').innerHTML =
            "There was an error saving the location. Please try again later"
        showPopup()                        
    });
}