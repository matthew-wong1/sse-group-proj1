/*document.addEventListener("DOMContentLoaded", function() {
    // Initialize Masonry on the grid container
    var grid = document.querySelector('.jqueryGrid');
    var masonry = new Masonry(grid, {
        itemSelector: '.jqueryGrid-item'
    });
    
});
*/

var $stampElement = $('.stamp');
var $grid = $('.jqueryGrid').masonry({
  itemSelector: '.jqueryGrid-item',
  columnWidth: '.jqueryGrid-sizer',
  stamp: $stampElement 
});

$grid.imagesLoaded().progress(function() {
  $grid.masonry();
  
});

// external js: masonry.pkgd.js


function handleClick() {
    alert('Div clicked!');
    // You can add any JavaScript code to handle the click event here
}

function hideOverlay() {
	// Hide the overlay and details box
	document.querySelector('.overlay').style.display = 'none';
	document.querySelector('#overlayDetails').style.display = 'none';
}


function showOverlay() {
    // Show the overlay
    document.querySelector('.overlay').style.display = 'flex';
    document.querySelector('#overlayDetails').style.display = 'flex';
}

const elementsWithDataName = document.querySelectorAll('[placeid]');

let placedetails;

// Add an event listener to elements with data-name attribute
elementsWithDataName.forEach(element => {

    // Event listener on the parent container or document
    element.addEventListener('click', function(event) {
        const placeID = event.target.getAttribute('placeid');
        if (placeID !== null) {
            fetch(`places/details?placeid=${encodeURIComponent(placeID)}&date=${encodeURIComponent(search_date)}&location=${encodeURIComponent(search_location)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok.');
                    }
                    return response.json();
                })
                .then(data => {
                    // Handle the data received from the GET request
                    console.log('Data received:', data);
                    placedetails = data;
                    // Update the title
                    document.getElementById('overlay-title').innerHTML = `${data.name}`;
                    document.getElementById('overlay-desc').innerHTML = `${data.editorial_summary}`;

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

                    // Larger image
                    const largerImage = document.createElement('img');
                    largerImage.src = data.photo_reference[0]; // First image in the list is the larger image
                    largerImage.className = 'h-[40rem] rounded-lg shadow-2xl'; // Apply Tailwind classes for responsiveness and margin
                    imageGrid.appendChild(largerImage);

                    const smallerImagesColumn = document.createElement('div');
                    smallerImagesColumn.className = ' flex flex-col justify-between h-[40rem]';        

                    // Four smaller images (starting from index 1)
                    for (let i = 1; i < 4; i++) {
                        const smallImage = document.createElement('img');
                        smallImage.src = data.photo_reference[i];
                        smallImage.className = 'max-h-[13rem] rounded-lg shadow-2xl'; // Apply Tailwind classes for responsiveness
                        smallerImagesColumn.appendChild(smallImage);
                    };

                    imageGrid.appendChild(smallerImagesColumn);

                    

                    // Show the overlay after updating content
                    showOverlay();
                })
                .catch(error => {
                    // Handle errors from the fetch or the response
                    console.error(`There was a problem with the GET request for button with ID ${placeID}:`, error);
                });
        }
    });
});

// WEATHER 

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
      drops += '<div class="drop" style="left: ' + (increment+5) + '%; bottom: ' + (randoFiver + randoFiver - 1 + 100) + '%; animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + randoHundo + 's;"><div class="stem" style="animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + randoHundo + 's;"></div><div class="splat" style="animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + randoHundo + 's;"></div></div>';
      backDrops += '<div class="drop" style="right: ' + increment + '%; bottom: ' + (randoFiver + randoFiver - 1 + 100) + '%; animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + randoHundo + 's;"><div class="stem" style="animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + randoHundo + 's;"></div><div class="splat" style="animation-delay: 0.' + randoHundo + 's; animation-duration: 0.5' + randoHundo + 's;"></div></div>';
    }
  
    $('.rain.front-row').append(drops);
    $('.rain.back-row').append(backDrops);
}


document.getElementById('overlayDetails').addEventListener('click', function(event) {
    
    event.stopPropagation();
    
});

const weatherElement  = document.getElementById("weather");


if (weatherData === "Rainy") {
  weatherElement.className = "rain front-row"
  makeItRain();
} else if (weatherData === "Sunny") {
  weatherElement.className = "ball"
} else if (weatherData == "Cloudy") {
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

//heart button
function toggleHeartInDet() {
    
    const heartIcon = document.getElementById('heart-in-details');
    heartIcon.classList.add('fa-spin'); // Add spinning class on click
    // Determine the current state based on the icon class
    const isSaved = heartIcon.classList.contains('fas');
            
    // Choose the endpoint based on the current state
    const endpoint = isSaved ? '/delete-restaurant' : '/save-restaurant';
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
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        heartIcon.classList.remove('fa-spin');

        if (data.status === 'success') {
            // Toggle the icon
            if (isSaved) {
                const heartIconInList = document.getElementById(`heart-in-${placedetails.place_id}`);
                heartIconInList.classList.remove('fas');
                heartIconInList.classList.add('far');
                heartIcon.classList.remove('fas');
                heartIcon.classList.add('far');
            } else {
                const heartIconInList = document.getElementById(`heart-in-${placedetails.place_id}`);
                heartIconInList.classList.remove('far');
                heartIconInList.classList.add('fas');
                heartIcon.classList.remove('far');
                heartIcon.classList.add('fas');
            }
        } else {
            alert('Operation failed.');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        // Confirm with the user if they want to log in
        if (confirm('You need to be logged in to save to favourites. Would you like to log in now?')) {
            // If they confirm, redirect them to the login page
            window.location.href = '/login'; // Use the correct route for your login page
        }                           
    });
}

function searchFood() {
    
    window.open(`/restaurants?name=${encodeURIComponent(placedetails.name)}&place_id=${encodeURIComponent(placedetails.place_id)}&date=${encodeURIComponent(search_date)}&location=${encodeURIComponent(search_location)}`, '_blank');
}



//heart button
function toggleHeartInList(heart_placeid) {
    
    const heartIcon = document.getElementById(`heart-in-${heart_placeid}`);
    heartIcon.classList.add('fa-spin'); // Add spinning class on click
    // Determine the current state based on the icon class
    const isSaved = heartIcon.classList.contains('fas');
            
    // Choose the endpoint based on the current state
    const endpoint = isSaved ? `/delete-restaurant?placeid=${encodeURIComponent(heart_placeid)}&date=${encodeURIComponent(search_date)}&location=${encodeURIComponent(search_location)}` : 
        `/save-restaurant?placeid=${encodeURIComponent(heart_placeid)}&date=${encodeURIComponent(search_date)}&location=${encodeURIComponent(search_location)}`;
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include' // test if this fixes log in error
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        heartIcon.classList.remove('fa-spin');
        console.log(data.status)
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
            alert('Operation failed.');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        // Confirm with the user if they want to log in
        if (confirm('You need to be logged in to save to favourites. Would you like to log in now?')) {
            // If they confirm, redirect them to the login page
            window.location.href = '/login'; // Use the correct route for your login page
        }                           
    });
}