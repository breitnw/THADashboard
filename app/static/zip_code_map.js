//DOM elements
const hubSelector = document.getElementById("hubSelector")
const saveButton = document.getElementById("saveButton")
const savingText = document.getElementById("savingText")
const savedText = document.getElementById("savedText")

let saved = true

// TODO: Display total deliveries for each hub

// Init the map
let map = L.map('map').setView([44.9778, -93.2650], 10);
L.tileLayer('https://api.maptiler.com/maps/pastel/{z}/{x}/{y}.png?key=Lpwn9fHg25lYklktmWQz',{
    tileSize: 512,
    zoomOffset: -1,
    minZoom: 1,
    attribution: "\u003ca href=\"https://www.maptiler.com/copyright/\" target=\"_blank\"\u003e\u0026copy; MapTiler\u003c/a\u003e \u003ca href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\"\u003e\u0026copy; OpenStreetMap contributors\u003c/a\u003e",
    crossOrigin: true
}).addTo(map);


// Add markers to the map representing the locations of the hubs
let hubMarkers = []
for (let key in hubInfo) {
    let location = hubInfo[key][1]
    let marker = new L.CircleMarker(location, {radius: 5})
            .bindPopup('Hub: ' + key)
            .addTo(map)
    marker.hub = key
    hubMarkers.push(marker)
}

// Add the geojson data
let geojson;

function mouseOver(e) {
    let layer = e.target;
    layer.setStyle({
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.9
    });
    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
    info.update(layer.feature.properties)
    for (let marker of hubMarkers){
        marker.bringToFront()
    }
}

function mouseOut(e) {
    resetHighlight(e.target)
    info.update(e.target.feature.properties)
}

function resetHighlight(layer) {
    layer.setStyle(style(layer.feature));
    if (hubAssignmentData[layer.feature.properties.zip] !== "unassigned") {
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
            layer.bringToBack();
        }
    }
}

function setHub(e) {
    let feature = e.target.feature
    // Set the new hub both in the feature's properties and in the dict
    hubAssignmentData[feature.properties.zip] = (hubAssignmentData[feature.properties.zip] === hubSelector.value) ? "unassigned" : hubSelector.value
    // Update the element's style
    e.target.setStyle(style(feature));
    // Set 'saved' to reflect a change has been made without saving
    saved = false
    // Update the UI to reflect this change
    setUISaveStatus(SaveStatus.UNSAVED)
}

function style(feature) {
    let hub = hubAssignmentData[feature.properties.zip]

    let color = "#999999"
    let borderColor = "#FFFFFF"
    let weight = 1
    let dashArray = '1'

    if (hub === hubSelector.value) {
        color = "#6da83a"
    } else if (hub === "unassigned") {
        color = "#e0b424"
        borderColor = "#c9972c"
        weight = 2
    }

    return {
        fillColor: color,
        weight: weight,
        opacity: 1,
        color: borderColor,
        dashArray: dashArray,
        fillOpacity: getOpacity(feature.properties.count)
    };
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: mouseOver,
        mouseout: mouseOut,
        click: setHub
    });
}

// Add the geoJSON data to the map
geojson = L.geoJSON(gjData, {
    style: style,
    onEachFeature: onEachFeature
}).addTo(map);

// Determine layer opacity depending on number of orders
function getOpacity(d) {
    return d > 100 ? 0.9 :
           d > 50  ? 0.8 :
           d > 20  ? 0.7 :
           d > 10  ? 0.65 :
           d > 5   ? 0.6 :
           d > 2   ? 0.65 :
           d > 1   ? 0.6 :
                      0.5;
}


// Iterate through all the markers and geoJSON layers and update their colors
function resetAllLayers() {
    geojson.eachLayer(function(layer) {
        resetHighlight(layer)
    })
    // TODO: gray out inactive markers here
    for (let marker of hubMarkers) {
        console.log(marker.hub);
        let color = (hubSelector.value === marker.hub ? '#007FFF' : '#657065')
        marker.setStyle({
            fillColor: color,
            color: color,
        })
    }
}
hubSelector.addEventListener('change', resetAllLayers);


// Add an info box to the map to display current zipcode and other stats
let info = L.control();
info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};
info.update = function (props) {
    this._div.innerHTML = '<h4>Details</h4>' + (props ?
        '<b>' + props.zip + '</b><br>' + props.count + (props.count === '1' ? ' delivery' : ' deliveries') +
        '<br>' + 'hub: ' + hubInfo[hubAssignmentData[props.zip]][0]
        : 'Hover over a ZIP Code'
    );
};
info.addTo(map);


// Make a POST request to the server if all the zip codes have been assigned
function submitToServer() {
    if (Object.values(hubAssignmentData).includes("unassigned")) {
        let err = "The following ZIP Codes still need to be assigned before saving:"
        for (let key in hubAssignmentData) {
            if (hubAssignmentData[key] === "unassigned") {
                err += "\n- " + key
            }
        }
        alert(err);
        return
    }
    let xhr = new XMLHttpRequest();
    xhr.open("POST", window.location.href, true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    setUISaveStatus(SaveStatus.SAVING)

    xhr.onload = function(e) {
        if (xhr.status === 200) {
            saved = true
            setUISaveStatus(SaveStatus.SAVED)
        } else {
            alert("Unable to save zip code data. Are you logged in?")
            setUISaveStatus(SaveStatus.UNSAVED)
        }
    }
    xhr.send(JSON.stringify(hubAssignmentData));
}

// Change the UI depending on if the map is saved, saving, or unsaved
const SaveStatus = {
	UNSAVED: 0,
	SAVING: 1,
	SAVED: 2,
}
function setUISaveStatus(status) {
    switch (status) {
        case SaveStatus.UNSAVED:
            saveButton.disabled = false
            savingText.hidden = true
            savedText.hidden = true
            break
        case SaveStatus.SAVING:
            saveButton.disabled = true
            savingText.hidden = false
            savedText.hidden = true
            break
        case SaveStatus.SAVED:
            saveButton.disabled = true
            savingText.hidden = true
            savedText.hidden = false
            break
    }
}

// Confirmation to save before exiting
window.onbeforeunload = function(){
    if (!saved) {
        return 'Are you sure you want to leave? Any unsaved changes will be lost.';
    }
};

// Run these functions when the page is loaded
resetAllLayers()