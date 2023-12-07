

let listPlaces = {};
const listSortOrder = {};
const draggable_list = {};
let dragStartIndex;
createList(places);

// Insert list items into DOM
function createList(multiplePlacesArrays) {
    multiplePlacesArrays.forEach(_places => {
        listPlaces[_places.tripid] = []; // Create a key-value pair where the key is _places.tripid and the value is an empty array
        draggable_list[_places.tripid] = document.getElementById(`draggable-list-${_places.tripid}`);
        listSortOrder[_places.tripid] = [];
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
          
            
            listPlaces[_places.tripid].push(listPlace);

            listSortOrder[_places.tripid].push({tripid : _places.tripid, idx: place.index, placeID: place.placeid});
            draggable_list[_places.tripid].appendChild(listPlace);

        });

    addEventListeners();
    })
}

function dragStart() {
  // console.log('Event: ', 'dragstart');
  dragStartIndex = +this.closest('li').getAttribute('data-index');
}

function dragEnter() {
  // console.log('Event: ', 'dragenter');
  this.classList.add('over');
}

function dragLeave() {
  // console.log('Event: ', 'dragleave');
  this.classList.remove('over');
}

function dragOver(e) {
  // console.log('Event: ', 'dragover');
  e.preventDefault();
}

function dragDrop() {
  // console.log('Event: ', 'drop');
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


function optimize(tripid) {

  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', // Specify the content type as JSON
      // Add other headers if required
    },
    body: JSON.stringify(listSortOrder[tripid]) // Convert the data object to JSON
  };

  if (listSortOrder[tripid].length > 2) {
    console.log(listSortOrder[tripid]);
    fetch('/favourites/opt',options)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok.');
                }
                return response.json();
            })
            .then(data => {
                // Handle the data received from the GET request
                console.log('Data received:', data);
                data = data.map(x=> x+2);
                data.unshift(1);
                data.push(data.length+1);
                console.log(data);
                for (let i=0; i<data.length; i++) {
                    if (data[i] !== i+1) {
                        swapPlaces(tripid,data[i]-1,i);
                        data[data[i]-1] = data[i];
                        console.log(data);
                    }
                }
                alert("Route Optimized!")
            })
            .catch(error => {
                // Handle errors from the fetch or the response
                console.error('There was an error with the POST request:', error);
            });
  }

  alert("Unable to optimize as more than 2 locations need to be provided")
}

function save(tripid) {

  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', // Specify the content type as JSON
      // Add other headers if required
    },
    body: JSON.stringify(listSortOrder[tripid]) // Convert the data object to JSON
  };

  console.log(listSortOrder[tripid])
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
              console.error('There was an error with the POST request:', error);
          });

}

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
