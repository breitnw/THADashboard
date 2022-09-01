
let map = initMap();
selectedHub = "east"

updateGeoJSON(geojsonData)

function initMap() {
    let map = L.map('map').setView([44.9778, -93.2650], 10);
    L.tileLayer('https://api.maptiler.com/maps/basic-v2/{z}/{x}/{y}.png?key=Lpwn9fHg25lYklktmWQz', {
        tileSize: 512,
        maxZoom: 19,
        zoomOffset: -1,
        minZoom: 1,
        attribution: "\u003ca href=\"https://www.maptiler.com/copyright/\" target=\"_blank\"\u003e\u0026copy; MapTiler\u003c/a\u003e \u003ca href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\"\u003e\u0026copy; OpenStreetMap contributors\u003c/a\u003e",
        crossOrigin: true
    }).addTo(map);
    return map
}

function updateGeoJSON(data) {
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
        // TODO: make a new dict to keep track of changes and send it back to Flask on post
        let feature = e.target.feature
        feature.properties.hub = (feature.properties.hub === "unassigned") ? selectedHub : "unassigned"
        e.target.setStyle(style(feature));
        document.getElementById("info").innerText = feature.properties.zip_code + ": " + feature.properties.hub;
    }

    function style(feature) {
        let color = "#333333"
        let border_color = "#FFFFFF"
        let weight = 1
        if (feature.properties.hub === selectedHub) {
            color = "#426425"
        } else if (feature.properties.hub === "unassigned") {
            color = "#c79818"
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

    geojson = L.geoJSON(data, {
        style: style,
        onEachFeature: onEachFeature
    }).addTo(map);
}

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