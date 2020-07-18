import urllib.parse, requests, os, json, math

#Set base query and keys for APIs
nominatimBaseURL = 'https://nominatim.openstreetmap.org/search/'
ORSKey = "5b3ce3597851110001cf62488ad066f5960f48e28aae44a1f27a245c"
rapidapiKey = "b556bb1579mshd569aae7bd0e958p1636c1jsnedf76d939275"

def queryNominatim(query):
    """query nominatim web service with parameters provided and return list of features as JSON"""
    queryURL = nominatimBaseURL + urllib.parse.quote(query, safe='') + '?format=json&countrycodes=US&limit=1'
    # run query and return JSON response
    r = requests.get(queryURL)
    return r.json()


def queryORS(startLon, startLat, endLon, endLat):
    """query ORS API using account key (user: Alexncrowe) with parameters from start and end locatin and return
    linestring as a geoJSON"""
    body = {"coordinates":[[startLon, startLat],[endLon, endLat]],"preference":"shortest","units":"mi"}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': ORSKey,
        'Content-Type': 'application/json; charset=utf-8'
        }
    call = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/geojson', json=body, headers=headers)
    routeGeoJSON = (call.text)
    #createCoordList(routeGeoJSON)

    return routeGeoJSON

def createCoordList(routeGeoJSON):
    """create a list of all coordinates from the GeoJSON to match to way points"""
    data = json.loads(routeGeoJSON)
    coordList = (data["features"][0]["geometry"]["coordinates"])
    return coordList

def createDistanceList(routeGeoJSON):
    """create a list of distances between way points to determine stop over locations"""
    distanceList = []
    data = json.loads(routeGeoJSON)

    for element in data["features"][0]["properties"]["segments"][0]["steps"]:
        distanceList.append(element["distance"])
    return distanceList

def createWPList(routeGeoJSON):
    """create a list of way points to match to coordinates for stop over points"""
    WPList = []
    data = json.loads(routeGeoJSON)

    for element in data["features"][0]["properties"]["segments"][0]["steps"]:
        WPList.append(element["way_points"])

    return WPList

def findPOILocation(distancePerDay, coordList, distanceList, WPList, travelDays):
    """Calculate distance and find way point and coordinate at that point for each travel day"""
    distance = 0
    index = 0
    count = 0
    coordsPOI = [] #stopOver points coordinate list
    if count <= travelDays: #only calculate as many travel days as necessary
        for item in distanceList:
            if distance < distancePerDay:
                distance += item #add distances until you get at or around the user's ideal distance per day
                index += 1
            else: #find the way point and coordinate of that distance location.
                wp = WPList[index]
                coord = coordList[wp[0]]
                lat = coord[1]
                lon = coord[0]
                correctedCoord = lat, lon
                coordsPOI.append(correctedCoord)
                count += 1
                distance = 0 #reset distance to calculate next stop over point

    result = queryGeoDB(coordsPOI)
    return result


def queryGeoDB(coordsPOI):
    """user GeoDB API for find nearest town to the stop over coordinate. Query prioritizes distances > 500000 population.
    And searches a radius of 50 miles."""
    stopOverPoints = []
    for coord in coordsPOI:#loop through each stop over coordinate to find nearest city.
        url = "https://wft-geo-db.p.rapidapi.com/v1/geo/locations/" + str(coord[0]) + str(coord[1]) + "/nearbyCities"

        querystring = {"limit":"1","minPopulation":"500000","distanceUnit":"MI","radius":"35"}

        headers = {
            'x-rapidapi-host': "wft-geo-db.p.rapidapi.com",
            'x-rapidapi-key': rapidapiKey #use key from above variables
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        responseData = json.loads(response.text)
        responseCount = responseData["metadata"]["totalCount"]

        if responseCount == 0: #if no cities with population > 5000000, change population requirement.
            url = "https://wft-geo-db.p.rapidapi.com/v1/geo/locations/" + str(coord[0]) + str(coord[1]) + "/nearbyCities"

            querystring = {"limit":"1","distanceUnit":"MI","radius":"35"}

            headers = {
                'x-rapidapi-host': "wft-geo-db.p.rapidapi.com",
                'x-rapidapi-key': rapidapiKey
                }

            response = requests.request("GET", url, headers=headers, params=querystring)

            stopOver = (response.text)

        else:
            stopOver = (response.text)

        data = json.loads(stopOver)
        city = data["data"][0]["name"]
        state = data["data"][0]["region"]
        lat = data["data"][0]["latitude"]
        lon = data["data"][0]["longitude"]

        #create a dictionary of stop over locations from query result.
        location = {"city": city, "state": state, "lat": lat, "lon": lon}
        #append stop over points list with dictionary
        stopOverPoints.append(location)
    return (stopOverPoints)


def webMapFromGeoJSON(geoJSONRoute, stopOverPoints):
    """creates html page with Leaflet based web map displaying a geoJSON route result and
     list of point features provided as parameters as a list of dictionaries with city, state, lat, lon properties"""
    html =  '''
<!DOCTYPE html>
  <html>
    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css"
   integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ=="
   crossorigin=""/>
   <script src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js"
integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew=="
crossorigin=""></script>
      <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>

      <style>

        #mapid {
    width: 1195px;
    height: 795px;
    border: 1px solid #ccc;
}

body {
margin: 0;
padding: 0;
}

.leaflet-container {
    background: #fff;
}

      </style>

      <script type="text/javascript">

        var map;
        var geoJSONFeatures = ''' + (geoJSONRoute) +''';
        var features = ''' + str(stopOverPoints) +''';


        function init() {
          // create map and set center and zoom level
          map = new L.map('mapid', { zoomControl:false });
          map.setView([40.844904, -97.965285],5);

          // create and add osm tile layer
          var osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          });
         osm.addTo(map);

         var routeLayer = L.geoJSON().addTo(map);
         routeLayer.addData(geoJSONFeatures);

         markers = [];

         for (var i = 0; i < features.length; i++) {
                 var marker =
                  new L.CircleMarker([features[i]['lat'], features[i]['lon']],  {
                  radius: 6,
            color: 'red',
            fillColor: '#bbf',
            fillOpacity: 0.5
        }).addTo(map);
                 markers.push(marker);
                 marker.bindPopup(features[i]['city'] + ',' + features[i]["state"] + ' ('+features[i]['lat']+','+features[i]['lon']+')', { maxWidth : 150 });
        }

        group = new L.featureGroup(markers);

        map.fitBounds(routeLayer.getBounds());

      }

      </script>
    </head>

  <body onload="init()">
                <div id="mapid">
                </div>
  </body>
</html>
'''
    return html
