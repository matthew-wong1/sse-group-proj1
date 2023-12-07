

let listPlaces = {};
const listSortOrder = {};
const draggable_list = {};
let dragStartIndex;
createList(places);

// Insert saved favourite places into the DOM 
// this has to be done dynamically for the 
// drag and drop effect.
function createList(multiplePlacesArrays) {
    //multiplePlaceArrys as there can be multiple collections of trips
    multiplePlacesArrays.forEach(_places => {
        // Create a key-value pair where the key is tripid 
        // and the value is an empty array
        listPlaces[_places.tripid] = []; 
        // get the associated DOM for each trip collection
        draggable_list[_places.tripid] = document.getElementById(`draggable-list-${_places.tripid}`);
        // Create a key-value pair where the key is tripid and 
        // the value is an empty array
        listSortOrder[_places.tripid] = [];
        // for each location in the collection, render
        // the associated html elements and set the attributes
        [..._places.place_list].forEach((place, index) => {

            const listPlace = document.createElement('li');
            listPlace.setAttribute('data-index', index);
            listPlace.setAttribute('trip-id', _places.tripid);
            listPlace.innerHTML = `
            <div class="flex justify-center items-center relative w-10">
                <div class="flex justify-center pointer-events-none items-center text-center text-2xl rounded-full bg-white z-20 w-7 h-7">${index + 1}</div>
                <div class="absolute w-11 h-10 bg-red-500 rounded-full top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10"></div>
                <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 h-full w-4 bg-red-500 z-9"></div>
            </div>
            <div class="draggable my-2" draggable="true">
                <div class="flex w-full bg-white rounded-lg shadow-lg overflow-hidden my-2 justify-between">
                    <div class='flex'>
                    <!-- Adjustments to image container for equal spacing -->
                    <div class="flex w-[18.75rem] h-[12.5rem] overflow-hidden items-center justify-center py-2">     
                        <img class="w-full object-cover rounded-lg" src="${place.photo_reference}" alt="Photo of ${place.name}" style="max-height: 200px;">
                    </div>
                    <div class="p-4 flex flex-col justify-between flex-grow">
                        <div>
                            <div class="uppercase tracking-wide text-sm text-indigo-500 font-semibold">
                                ${place.name}
                            </div>
                            <div class="star-rating" style="--rating: ${place.ratings};"></div>
                            <p class="text-gray-500 mt-2">${place.editorial_summary}</p>
                        </div>
                        <div class="flex justify-between items-end">
                            <div>
                                <span class="text-lg font-semibold text-blue-800">${place.ratings}/5</span>
                                <span class="text-xs text-gray-600">${place.rating_count} reviews</span>
                                
                            </div>
                        </div>
                        
                    </div>
                    </div>
                    <div class='flex items-center'>
                        <i class="fas fa-grip-lines fa-2x pr-5 "></i>
                    </div> 
                </div> 
            </div>
                
            `;
          
            // add the html elements to the listPlaces array
            // so that their order can be manipulated by 
            // reference later 
            listPlaces[_places.tripid].push(listPlace);

            // add the places information and index into the
            // listSortOrder array to facilitate sorting later
            listSortOrder[_places.tripid].push({tripid : _places.tripid, idx: place.index, placeID: place.placeid});

            // add the html elements generated to the parent element
            draggable_list[_places.tripid].appendChild(listPlace);

        });

    addEventListeners();
    })
}

// save the index of the item being dragged
function dragStart() {
  // console.log('Event: ', 'dragstart');
  dragStartIndex = +this.closest('li').getAttribute('data-index');
}

// interaction when the dragged object
// enters the area
function dragEnter() {
  // console.log('Event: ', 'dragenter');
  this.classList.add('over');
}

// interaction when the dragged object
// leaves the area
function dragLeave() {
  this.classList.remove('over');
}
// prevent default interactions
// when something is being dragged over it
function dragOver(e) {
  e.preventDefault();
}

// swap the items' locations when the drag 
// is released
function dragDrop() {
  const dragEndIndex = +this.getAttribute('data-index');
  const tripid = this.getAttribute('trip-id');
  swapPlaces(tripid, dragStartIndex, dragEndIndex);

  this.classList.remove('over');
}

// Swap list items that are drag and drop
function swapPlaces(tripid, fromIndex, toIndex) {
  const placeOne = listPlaces[tripid][fromIndex].querySelector('.draggable');
  const placeTwo = listPlaces[tripid][toIndex].querySelector('.draggable');
  const sortOne = listSortOrder[tripid][fromIndex]
  const sortTwo = listSortOrder[tripid][toIndex]
  listSortOrder[tripid][toIndex] = sortOne;
  listSortOrder[tripid][fromIndex] = sortTwo;
  listPlaces[tripid][fromIndex].appendChild(placeTwo);
  listPlaces[tripid][toIndex].appendChild(placeOne);
}

// function to trigger the call to the Route API
// which would return the optimized waypoints.
// this function further updates the frontend 
// route to display the optimized route.
function optimize(tripid) {

  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', // Specify the content type as JSON
      // Add other headers if required
    },
    body: JSON.stringify(listSortOrder[tripid]) // Convert the data object to JSON
  };

  if (listSortOrder[tripid].length <= 2) {
    alert("Unable to optimize as more than 2 locations need to be provided")

  } else if (listSortOrder[tripid].length > 2) {
    fetch('/favourites/opt',options)
            .then(response => {
                if (!response.ok) {
                  alert("There was an error optimizing the path. Please try again later.");
                }
                return response.json();
            })
            .then(data => {
                // Handle the data received from the GET request
                // by re-sorting the items based on the optimized
                // route. Some appending and adjustments of the 
                // index has to be done as Route API returns 
                // only the order of the intermediate waypoints
                data = data.map(x=> x+2);
                data.unshift(1);
                data.push(data.length+1);
                console.log(data);
                for (let i=0; i<data.length; i++) {
                    if (data[i] !== i+1) {
                        swapPlaces(tripid,data[i]-1,i);
                        data[data[i]-1] = data[i];
                    }
                }
                alert("Route Optimized!")
            })
            .catch(error => {
                // Handle errors from the fetch or the response
                alert("There was an error optimizing the path. Please try again later.");
            });
  }

  
}

// save the route to the database
function save(tripid) {
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', // Specify the content type as JSON
    },
    body: JSON.stringify(listSortOrder[tripid]) // Convert the data object to JSON
  };
  fetch('/favourites/save',options) 
          .then(response => {
              if (!response.ok) {
                  throw new Error('Network response was not ok.');
              }
              return response.json();
          }) 
          .then(data => { 
              // Handle the data received from the GET request
              console.log('Data received:', data);
              alert("Route saved!")
          })
          .catch(error => {
              // Handle errors from the fetch or the response
              alert("There was an error saving the route. Please try again later");
          });

}

// add event listeners to handle the drag and drop of the locations
function addEventListeners() {
  const draggables = document.querySelectorAll('.draggable');
  const dragListItems = document.querySelectorAll('.draggable-list li');

  draggables.forEach(draggable => {
    draggable.addEventListener('dragstart', dragStart);
  });

  dragListItems.forEach(item => {
    item.addEventListener('dragover', dragOver);
    item.addEventListener('drop', dragDrop);
    item.addEventListener('dragenter', dragEnter);
    item.addEventListener('dragleave', dragLeave);
  });
}
