//set the selected hub
let selectedHub = "east"
let saved = true

//init the map
let map = L.map('map').setView([44.9778, -93.2650], 10);
L.tileLayer('https://api.maptiler.com/maps/basic-v2/{z}/{x}/{y}.png?key=Lpwn9fHg25lYklktmWQz', {
    tileSize: 512,
    maxZoom: 19,
    zoomOffset: -1,
    minZoom: 1,
    attribution: "\u003ca href=\"https://www.maptiler.com/copyright/\" target=\"_blank\"\u003e\u0026copy; MapTiler\u003c/a\u003e \u003ca href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\"\u003e\u0026copy; OpenStreetMap contributors\u003c/a\u003e",
    crossOrigin: true
}).addTo(map);

//add the geojson data
let geojson;

function highlightFeature(e) {
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
}

function resetHighlight(e) {
    let feature = e.target.feature
    e.target.setStyle(style(feature));
}

function setHub(e) {
    // TODO: send the dict back to Flask on post
    let feature = e.target.feature

    // Set the new hub both in the feature's properties and in the dict
    hubData[feature.properties.zip] = (hubData[feature.properties.zip] === "unassigned") ? selectedHub : "unassigned"

    // Update the element's style
    e.target.setStyle(style(feature));
    document.getElementById("info").innerText = feature.properties.zip + ": " + hubData[feature.properties.zip];

    // Set 'saved' to reflect a change has been made without saving
    saved = false
    updateSaveButton()
}

function style(feature) {
    let hub = hubData[feature.properties.zip]

    let color = "#333333"
    let border_color = "#FFFFFF"
    let weight = 1

    if (hub === selectedHub) {
        color = "#6da83a"
    } else if (hub === "unassigned") {
        color = "#e0b424"
        // weight = 2
    }

    return {
        fillColor: color,
        weight: weight,
        opacity: 1,
        color: border_color,
        dashArray: '3',
        fillOpacity: getOpacity(feature.properties.count)
    };
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: setHub
    });
}

geojson = L.geoJSON(gjData, {
    style: style,
    onEachFeature: onEachFeature
}).addTo(map);

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

// Make a POST request to the server
function submitToServer() {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", window.location.href, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(hubData));
    saved = true
    updateSaveButton()
}

// Disable the save button if already saved
function updateSaveButton() {
    document.getElementById("saveButton").disabled = saved
}

// Confirmation to save before exiting
window.onbeforeunload = function(){
    if (!saved) {
        return 'Are you sure you want to leave? Any unsaved changes will be lost.';
    }
};