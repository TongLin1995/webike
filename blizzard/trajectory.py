#!/usr/bin/env python
from databaseConnector import *
from datetime import datetime
from compute import haversine, detectTrips
import matplotlib.pyplot as plt


# Calculate Haversine distance between subsequent points
def haversineDistance(lon, lat):  # pass the lists with coordinates (longitude and latitude)
    haversineDistance = []
    for i in range(1, len(lat)):
        haversineDistance.append(haversine(lat[i - 1], lat[i], lon[i - 1], lon[i]))
    return haversineDistance


# Add points to the connected components (on both sides), it stops when it finds a local maxima
def increaseCC(cc, maxi, mini, distances):  # pass: list of connected components lists, list of maxima, list of minima, list of distances
    for i in range(len(cc)):
        while (cc[i][0] not in maxi) and (cc[i][2] not in maxi):
            if cc[i][0] > 0 and cc[i][2] < len(distances) - 1:  # Excluding the fist and last indexes
                if(distances[cc[i][0] - 1] > distances[cc[i][2] + 1]):
                    cc[i][0] -= 1
                else:
                    cc[i][2] += 1
            elif cc[i][0] == 0:
                cc[i][2] += 1
            elif cc[i][2] == len(distances) - 1:
                cc[i][0] -= 1
    return cc


# Joins connected components when they share a local maxima and also returns the bars (ranges) identified
def joinCC(cc, distances):
    barTemp = []
    keep = []
    for i in range(len(cc) - 1):
        if(cc[i][2] == cc[i + 1][0]):
            if(distances[cc[i][1]] > distances[cc[i + 1][1]]):
                barTemp.append(cc[i])  # append the non-surviving cc to the list of bars
                cc[i + 1][0] = c[i][0]  # change value of the last point of the cc that remains
                keep.append(i + 1)  # saving the one that should stay-contrary to the one that should be deleted
            else:
                barTemp.append(cc[i])  # append the non-surviving cc to the list of bars
                cc[i][2] = cc[i + 1][2]  # change value of the first point of the cc that remains
                keep.append(i)  # saving the one that should stay-contrary to the one that should be deleted
        else:
            keep.append(i)
    newCC = [cc[i] for i in keep]
    return barTemp, newCC  # return the identified bars and the list of new connectec components


def gpsSimplification(lon, lat, stamps, beta):
    distances = haversineDistance(lon, lat)  # obtain list with distances between points
    
    mini = []  # list of local minima
    maxi = []  # list of local maxima
    # get local minima and local maxima
    for i in range(2, len(distances) - 1):
        if distances[i - 1] < distances[i] > distances[i + 1]:
            maxi.append(i)
        elif (distances[i - 1] > distances[i] < distances[i + 1]) or (distances[i - 1] == distances[i] < distances[i + 1]) or (distances[i - 1] > distances[i] == distances[i + 1]):
            mini.append(i)
    bar = []  # list of bars detected
    cc = []  # list of connected components
    for i in mini:
        cc.append([i, i, i])

    # while there is more than one connected component keep joining component together
    while(len(cc) != 1):
        barTemporary = []
        cc = increaseCC(cc, maxi, mini, distances)
        barTemporary, cc = joinCC(cc, distances)
        bar.extend(barTemporary)

    # beta simplification
    newBar = []
    for i in range(len(bar)):
        if(abs(distances[bar[i][0]] - distances[bar[i][2]]) > beta):
            newBar.append(bar[i])

    # extracting all values from list // values is a list with other lists inside
    valuesTemp = []
    for i in newBar:
        for j in i:
            if(j not in valuesTemp):
                valuesTemp.append(j)

    # deleting equal values
    valuesTemp2 = []
    for i in range(1, len(valuesTemp)):
   		if distances[valuesTemp[i]] != distances[valuesTemp[i-1]]:
   			valuesTemp2.append(valuesTemp[i])

    # copying only remaining points
    finalValues = []
    for i in range(len(distances)):
        if (i in valuesTemp2):
            finalValues.append(distances[i])
        else:
            finalValues.append(None)

    
    # obtaining plottable points
    xplottable = []
    plottable = []
    for i in range(len(finalValues)):
        if finalValues[i] is not None:
            xplottable.append(i)
            plottable.append(finalValues[i])

    newLat = []
    newLon = []
    newStamp = []
    newLon.append(lon[0])
    newLat.append(lat[0])
    newStamp.append(stamps[0])
    for i in range(len(xplottable)):
        newLat.append(lat[xplottable[i] + 1])
        newLon.append(lon[xplottable[i] + 1])
        newStamp.append(stamps[xplottable[i] + 1])
    if(lon[-1] not in newLon):
        newLon.append(lon[-1])
        newLat.append(lat[-1])
        newStamp.append(stamps[-1])
    return newLon, newLat, newStamp
def totalDistance(dist):
    d = 0.0
    for i in range(len(dist)):
        d+=dist[i]
    return d

def trajectoryClean(dbc, imei, beta, syear, smonth, sday):
    curDate = datetime(2014, smonth, sday, 0, 0, 0)
    endDate = datetime(2014, smonth, sday, 23, 59, 59)
    newLon = []
    newLat = []
    newStamp = []
    # obtaining the trips in one day
    tripStartTimes, tripEndTimes, dists = detectTrips(dbc, imei, curDate, endDate)
    if (len(tripStartTimes) > 0):
        #obtaining the data about all trips and then copying it to the arrays containing this information
        for tripNumber in range(len(tripStartTimes)):
            lat = []
            lon = []
            stamps = []
            tempLon = []
            tempLat = []
            tempStamp = []
            stmt = "select stamp, LatGPS, LongGPS from imei{0} where stamp >= \"{1}\" and stamp <= \"{2}\" and latgps is not null and longgps is not null and latgps!= 0.0 and longgps!=0 order by stamp;".format(imei, tripStartTimes[tripNumber], tripEndTimes[tripNumber])
            for l in dbc.SQLSelectGenerator(stmt):
                stamps.append(l[0])
                lat.append(l[1])
                lon.append(l[2])
            tempLon, tempLat, tempStamp = gpsSimplification(lon, lat, stamps, beta)
            newLon.append(tempLon)
            newLat.append(tempLat)
            newStamp.append(tempStamp)
        dist = []
        for i in range(len(newLon)):
            dist.append(totalDistance(haversineDistance(newLon[i], newLat[i])))

        #calculating total time of every trip detected
        totalTime = []
        for i in range(len(tripStartTimes)):
            totalTime.append((tripEndTimes[i]-tripStartTimes[i]).total_seconds()/60)
        
        #converting start and end times to string to put them in json format
        startStr = []
        endStr = []
        for i in range(len(tripEndTimes)):
            startStr.append(tripStartTimes[i].strftime('%H:%M'))
            endStr.append(tripEndTimes[i].strftime('%H:%M'))
        #converting stamps to string to put them in json format
        stampsStr = []
        for i in range(len(newStamp)):
            tempStampStr = []
            for j in range(len(newStamp[i])):
                tempStampStr.append(newStamp[i][j].strftime('%H:%M'))
            stampsStr.append(tempStampStr)

        return newLon, newLat, startStr, endStr, dist, totalTime, stampsStr
    else:
        newLon = []
        newLat = []
        startStr = []
        endStr = []
        dist = []
        totalTime = []
        stampsStr = []
        return newLon, newLat, startStr, endStr, dist, totalTime, stampsStr
