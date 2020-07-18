
###########################################################
# Name: Alexandra Crowe
# Date: 18 July 2020
# Version: 1.0
# Description:
# This script is a tool to map a recommended route for military
# movers. The user searches for their start and end locations
# and indicates how many hours per day they'd like to drive.
# The tool then produces a map with the shortest route and recommended
# overnight stops meeting that driving requirement. This is a great
# tool for military members who are given a strict amount of days to
# travel.
#
# References:
# Nominatim API: https://wiki.openstreetmap.org/wiki/Nominatim
# Open Route Service API: https://openrouteservice.org/
# GeoDB API: https://english.api.rakuten.net/wirefreethought/api/geodb-cities/details
# Python GDAL/OGR cookbook: https://pcjericks.github.io/py-gdalogr-cookbook/index.html
#
#
###########################################################
import sys, io, math, json, geojson
import osgeo.ogr as ogr
import osgeo.osr as osr
import gdal
import subprocess

from PyQt5.QtWidgets import QApplication, QMainWindow, QStyle, QFileDialog, QDialog, QMessageBox, QSizePolicy
from PyQt5.QtGui import QStandardItemModel, QStandardItem,  QDoubleValidator, QIntValidator
from PyQt5.QtCore import QVariant
from PyQt5.Qt import Qt
from PyQt5 import QtWidgets, QtWebEngineWidgets

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView as WebMapWidget
except:
    from PyQt5.QtWebKitWidgets import QWebView as WebMapWidget

import gui_main
import mapGUI
import core_functions as core

# =======================================
# GUI event handler and related functions
# =======================================

def runQuery():
    """run the Nominatim query to find start and end locations. Then run the Open Route Service query to
    find distance and duration of the trip. """
    ui.statusbar.showMessage("Finding locations... please wait!")
    try:
        #query start location and update label
        startQueryString = ui.startLE.text()
        runStartLocationQuery(startQueryString)
        startLat = startResult[0]["lat"]
        startLon = startResult[0]["lon"]

        #query end location and update label
        endQueryString = ui.endLE.text()
        runEndLocationQuery(endQueryString)
        endLat = endResult[0]["lat"]
        endLon = endResult[0]["lon"]

        #run route query
        global route
        route = core.queryORS(startLon, startLat, endLon, endLat)

        #find total distance of trip and update label
        data = json.loads(route)
        global distance
        distance = round(data["features"][0]["properties"]["summary"]["distance"])
        resetDistanceLabel(distance)

        #find amount of travel days allowed and update label
        duration = math.ceil((distance/350))
        resetDurationLabel(duration)

        #change status bar, and enable the second group box
        ui.statusbar.showMessage("Found it!")
        ui.mapPB.setEnabled(True)
        ui.hoursLE.setEnabled(True)

    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Querying failed with '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )
        ui.statusbar.clearMessage()

def resetStartLE(startLabel):
    '''change the text underneath the start line edit to read the search result of the Nominatim query'''
    try:
        if startLabel != '':
            ui.startResultL.setText(startLabel)
        else:
            ui.startResultL.setText("No location found. Please try again!")
    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Cannot find start location '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )
        ui.statusbar.clearMessage()

def resetEndLE(endLabel):
    '''change the text underneath the end line edit to read the search result of the Nominatim query'''
    try:
        if endLabel != '':
            ui.endResultL.setText(endLabel)
        else:
            ui.endResultL.setText("No location found. Please try again!")
    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Cannot find end location '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )
        ui.statusbar.clearMessage()

def resetDistanceLabel(distance):
    '''change the text of the distance label in the drive time group box '''
    ui.distanceL.setText("Total distance: " + str(distance) + " miles")

def resetDurationLabel(duration):
    '''change the text of the duration label in the drive time group box '''
    ui.durationL.setText("For military movers: " + str(duration) + " travel days allowed.")

def runStartLocationQuery(query):
    """query nominatim and set text for start label"""
    try:
        global startResult
        startResult = core.queryNominatim(query)
        startLabel = startResult[0]["display_name"]

        resetStartLE(startLabel)

    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Ambiguous input. Please check your spelling! Failed with '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )
        ui.statusbar.clearMessage()

def runEndLocationQuery(query):
    """query nominatim and set text for start label"""
    try:
        global endResult
        endResult = core.queryNominatim(query) # run query

        endLabel = endResult[0]["display_name"]

        resetEndLE(endLabel)

    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Ambiguous input. Please check your spelling! Failed with '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )
        ui.statusbar.clearMessage()

def mapMyRoute():
    """idenitfy stop over locations along the ORS route taking into account the user's
    drive time and plot on leaflet map"""
    ui.statusbar.showMessage("Finding the best route...please wait!")

    try:
        #user determines how many hours per day they'd like to drive and averages 70 miles per hour
        hours = int(ui.hoursLE.text())
        distancePerDay = (hours * 70)

        #create lists to determine way points that match coordinates and match the ideal distance per day
        global coordList
        coordList = core.createCoordList(route)
        distanceList = core.createDistanceList(route)
        WPList = core.createWPList(route)

        #determine if trip is multi-day. If so, find stop over points. Else, just map route.
        travelDays = math.ceil(distance / distancePerDay)
        if travelDays > 1:
            global stopOverPoints
            stopOverPoints = core.findPOILocation(distancePerDay, coordList, distanceList, WPList, travelDays)
            listStopOverPoints(stopOverPoints)
            mapHTML = core.webMapFromGeoJSON(route, stopOverPoints)
            mapWV.setHtml(mapHTML)
        else:
            mapHTML = core.webMapFromGeoJSON(route, [])
            mapWV.setHtml(mapHTML)
            mappedRoute_ui.stopOverLV.hide()

        ui.statusbar.showMessage("We've found the best route for your travels!")

        mappedRoute.open()

    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Mapping your route failed with '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )
        ui.statusbar.clearMessage()

def listStopOverPoints(stopOverPoints):
    """populate list view with word wrapped entries from stop over locations"""
    m = QStandardItemModel()
    for place in stopOverPoints:
        place = QStandardItem(place['city'] + ', ' + (place['state'] ))
        m.appendRow(place)
    mappedRoute_ui.stopOverLV.setModel(m)

def exportRouteShapefile():
    """Reads geoJSON response fron ORS query and saves it as an ESRI Shapefile"""
    try:
        mappedRoute_ui.exportPB.setText("Creating new shapefile...")
        data = geojson.loads(route)
        with open("data.geojson", 'w') as f:
            geojson.dump(data, f)
        args = ['ogr2ogr', '-f', 'ESRI Shapefile', 'trip.shp', "data.geojson"]
        subprocess.Popen(args)
        exportPointShapefile()
    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Creating route shapefile failed with '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )


def exportPointShapefile():
    """Reads list of stop over point dictionaries and saves it as an ESRI Shapefile"""
    try:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource("stops.shp")

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        layer = data_source.CreateLayer("stops", srs, ogr.wkbPoint)

        # Add the fields
        field_city = ogr.FieldDefn("City", ogr.OFTString)
        field_city.SetWidth(24)
        layer.CreateField(field_city)
        field_state = ogr.FieldDefn("State", ogr.OFTString)
        field_state.SetWidth(24)
        layer.CreateField(field_state)


        # Add the attributes and features to the shapefile
        for place in stopOverPoints:
            feature = ogr.Feature(layer.GetLayerDefn())

            feature.SetField("City", place['city'])
            feature.SetField("State", place['state'])

            # create the WKT for the feature using Python string formatting and create the point
            wkt = "POINT(%f %f)" %  (float(place['lon']) , float(place['lat']))
            point = ogr.CreateGeometryFromWkt(wkt)

            feature.SetGeometry(point)
            layer.CreateFeature(feature)
            feature = None

        # Save and close the data source
        data_source = None
        mappedRoute_ui.exportPB.setText("Success!")
    except Exception as e:
        QMessageBox.information(mainWindow, 'Operation failed', 'Creating points shapefile failed with '+ str(e.__class__) + ': ' + str(e), QMessageBox.Ok )

#==========================================
# create app and main window + dialog GUI
# =========================================

app = QApplication(sys.argv)

# set up main window

mainWindow = QMainWindow()
ui = gui_main.Ui_MainWindow()
ui.setupUi(mainWindow)

# set up map dialog

mappedRoute = QDialog(mainWindow)
mappedRoute_ui = mapGUI.Ui_Dialog()
mappedRoute_ui.setupUi(mappedRoute)

#create new map widget in horizontal box layout of map dialog
mapWV = WebMapWidget()
mappedRoute_ui.mapHBL.addWidget(mapWV)
mapWV.setFixedSize(1200,800)
mapWV.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed))


ui.actionExit.setIcon(app.style().standardIcon(QStyle.SP_DialogCancelButton))

ui.hoursLE.setValidator(QIntValidator())

#==========================================
# connect signals
#==========================================

ui.findLocPB.clicked.connect(runQuery)
ui.mapPB.clicked.connect(mapMyRoute)
mappedRoute_ui.exportPB.clicked.connect(exportRouteShapefile)

#=======================================
# run app
#=======================================

mainWindow.show()
sys.exit(app.exec_())
