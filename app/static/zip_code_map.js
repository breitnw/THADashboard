
let map = initMap();
selectedHub = "east"

let geoJSON = L.geoJSON(false);
updateGeoJSON(geoJSONPoints)

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

function updateGeoJSON(pointData) {
    if (map.hasLayer(geoJSON)) {
        map.removeLayer(geoJSON)
    }

    L.geoJSON(pointData, {
        pointToLayer: function (feature, latlng) {
            let color = "#DDDDDD"
            if (feature.properties.hub === selectedHub) {
                color = "#EE1212"
            } else if (feature.properties.hub === "unassigned") {
                color = "#FFFF00"
            }
            return L.circleMarker(latlng, {
                radius: feature.properties.count / 5 + 5,
                fillColor: color,
                color: "#000",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            });
        },
    }).addTo(map);
}