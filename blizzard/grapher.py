from datetime import datetime, timedelta
from compute import detectTrips, haversine
import time
import json
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import io
from urllib import request as urlreq
import SOC
import matplotlib.colors as colors
from trajectory import trajectoryClean

my_dpi = 90

mpl.rcParams["lines.linewidth"] = 6
mpl.rcParams["font.size"] = 20
mpl.rcParams["lines.linestyle"] = "-" 
mpl.rcParams["lines.marker"] = "" 

from sys import stderr
def print_err(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


def plotVoltage(dbc,imei,sMonth,sDay,sYear):
    startDate = datetime(sYear,sMonth,sDay)
    s = startDate.strftime('%y-%m-%d') + " 00:00:00"
    e = startDate.strftime('%y-%m-%d') + " 23:59:59"
    
    interpolate_starts = dict()
    interpolate_ends = dict()
    
    tripStartTimes, tripEndTimes, dists = detectTrips(dbc,imei,s,e)

    stmt = "select stamp, batteryVoltage from imei{0} where stamp >= \"{1}\" and stamp <= \"{2}\" and batteryVoltage is not null and batteryVoltage != 0 order by stamp".format(imei, s, e)
        
    Xs = []
    Xdatetimes = []
    Xlabs = []
    Ys = []
        
    """there might not be a row where battery voltage is not null at exactly the same time as each trio start and trip end. 
    thus, we cant just use the list of tripstarttimes and tripendtimes and find the SOC at exactly those rows. 
    Instead, well look at all rows between each (tripstart,tripend) pair, use the earliest with a NONNULL voltage
    as the tripStartSOC, and use the latest as the tripEndSOC."""
    count = 0
    for l in dbc.SQLSelectGenerator(stmt):
        Xs.append(count)  
        for j in range(0, len(tripStartTimes)):
            if tripStartTimes[j] <= l[0] <= tripEndTimes[j] :
                if j not in interpolate_starts:
                    interpolate_starts[j] = 1000000000000
                if j not in interpolate_ends:
                    interpolate_ends[j] = -1
                interpolate_starts[j] = min(interpolate_starts[j], count)
                interpolate_ends[j] = max(interpolate_ends[j], count)          
        
        Xlabs.append(l[0].strftime('%H:%M:%S'))
        Ys.append(float(l[1]))
        count += 1
    
    if (count == 0):
        return urlreq.urlopen("http://blizzard.cs.uwaterloo.ca/~sensordc/notfound.png").read()
    else:
        
        Ysmoothed = []
    
        for i in range(0, len(Ys)):
           if i == 0:
               Ysmoothed.append(Ys[i])
           else:
               Ysmoothed.append(.95*Ysmoothed[i-1] + .05*Ys[i-1])
        
        
        #todo
        """TODO: INSTEAD OF ASSUMING 23 DEGREES, QUERY THE BATTERY TEMPERATURE IN THE DATABASE AND USE THE CORRECT CURVE OF
        -20,-10,0,23,45"""
                
        SOCEstimates = [100*i for i in SOC.SOCVals(23,Ysmoothed)]
        
        """now we have to replace the portions of SOCEstimates relating to biking trips. 
        this is because battery voltage can fluctuate violently during biking. 
        so we will compute the SOC at trip end points and linearly intropolate during periods of biking. 
        
        with respect to the PADDING parameter below, the list of "tripendtimes" is not EXACTLY accurate. these
        can be up to five minutes prior to when the bike was actually at rest. so we will actually compute the SOC
        at 5 minutes past each trip and and linearly intropolate in there. 
        
        We do the same for trip starts. So we actually interpiolate in the range(5 mins before bike start, 5 mins after bike start) for each trip."""
        PADDING = 180
        for i in range(0, len(SOCEstimates)):
            for k in sorted(interpolate_starts.keys()):
                if i == interpolate_starts[k]:
                    #this will bomb if a trip starts within 5 minutes of midnight... fixlater
                    SOC_Start = SOCEstimates[i-PADDING]
                    SOC_End = SOCEstimates[interpolate_ends[k]+PADDING]
                    delta = (SOC_Start-SOC_End)/(interpolate_ends[k]-interpolate_starts[k]+PADDING + PADDING)
                    for n in range(i-PADDING,interpolate_ends[k]+PADDING):
                        SOCEstimates[n] = SOC_Start-delta*(n-i+PADDING)
                    i = interpolate_ends[k] #sklip to this point to save time
                    
        plt.figure(1, figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi)
        
        plt.title("Voltage over day")#.format(imei))
        
        ax = plt.subplot(211)
        ax.plot(Xs,Ys,color='blue')
        ax.plot(Xs,Ysmoothed, color='red',linestyle="-")
        ax.yaxis.set_tick_params(labelsize=14)
        ax.xaxis.set_tick_params(labelsize=14)
        #make grid go behind bars
        ax.set_axisbelow(True) 
        ax.yaxis.grid(color='gray', linestyle='solid')
        ax.xaxis.grid(color='gray', linestyle='solid')
        plt.ylabel("Voltage (V)")

        plt.xlim(0,len(Xs))
        plt.ylim(min(Ys),max(Ys))       

        ax2 = plt.subplot(212)
        plt.ylabel("SOC Estimation (%)")

        ax2.plot(Xs,SOCEstimates, color='red')
        #set axis
        samplesec = 300
        ax2.set_xticklabels([Xlabs[i] for i in range(0,len(Xlabs),samplesec )], rotation=90, fontsize = 14 )
        ax2.yaxis.set_tick_params(labelsize=14)
        ax2.set_xticks([i for i in range(0,len(Xs),samplesec )])
        plt.xlabel("Time of day")
        plt.gcf().subplots_adjust(bottom=0.5)

        #make grid go behind bars
        ax2.set_axisbelow(True) 
        ax2.yaxis.grid(color='gray', linestyle='solid')
        ax2.xaxis.grid(color='gray', linestyle='solid')
        
        plt.xlim(0,len(Xs))
        #plt.ylim(0,100)       

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
        buf.seek(0)
        return buf.read() 

def debugWrite(s):
    f = open("bikelog.txt", "a");
    f.write(s)
    f.write("\n")
    f.close()
    
def plotTripsOnDay(dbc,imei,sMonth,sDay,sYear):
    curDate = datetime(sYear,sMonth,sDay)
    end = curDate+timedelta(hours=23, minutes=59,seconds=59)
    tripStartTimes, tripEndTimes, dists = detectTrips(dbc,imei,curDate,end)  
    
    if len(tripStartTimes) == 0:
        return urlreq.urlopen("http://blizzard.cs.uwaterloo.ca/~sensordc/notfound.png").read()
    else:
        Xs = []
        Ys = []
        
        Ycounts = []
        Xlabs = []
        for i in range(0, len(tripStartTimes)):
            Xlabs.append("{0} -\n{1}".format(tripStartTimes[i].strftime('%H:%M'), tripEndTimes[i].strftime('%H:%M')))
            Xs.append(i) 
            Ys.append(dists[i])

        plt.figure(1,figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi) 
        
        plt.ylabel("Distance (km)")
        plt.xlabel("Start time - Stop time ")
        plt.title("Trips {0}/{1}/{2}".format(sMonth, sDay, sYear))#.format(imei))
        
        ax = plt.subplot(111)
        
        #plot
        rects = ax.bar(Xs, Ys, color="blue",width=.5)
        
        #make grid go behind bars
        ax.set_axisbelow(True) 
        ax.yaxis.grid(color='gray', linestyle='solid')
        
        #set axis
        ax.set_xticklabels(Xlabs, rotation=0, fontsize = 14)
        ax.yaxis.set_tick_params(labelsize=14)
        plt.xlim(0,len(Xs))
        plt.ylim(0,max(Ys)+1)
        ax.set_xticks([i+.25 for i in range(0,len(Xs))])
        #ax.set_yticks([0.1*x*100 for x in range(0,11)])
        #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
        plt.tight_layout()
        #plt.show()
        
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
        buf.seek(0)
        return buf.read() 
          


def plotMaxSpeedTripOnDay(dbc,imei,sMonth,sDay,sYear):
    curDate = datetime(sYear,sMonth,sDay)
    end = curDate+timedelta(hours=23, minutes=59,seconds=59)
    stmt = "select * from imei{0} where stamp >= \"{1}\" and stamp <= \"{2}\" and latgps is not null and longgps is not null and longgps!=0 and latgps!=0  order by stamp".format(imei, curDate, end)
      
    lastRow = ""
    lastRowTime = ""
    
    Xs = []
    Ys = []
    Xlabs = []
    count = 0
    for l in dbc.SQLSelectGenerator(stmt):
        if l is not None:
            if lastRow == "" :
                lastRow = l
                lastRowTime = l[0]
            else:
                TIMELAPSE = (l[0]-lastRowTime).total_seconds() #in seconds
                if (TIMELAPSE >= 20): #only consider rows 10 seconds apart    
                    d = haversine(l[3],lastRow[3], l[4], lastRow[4])
                    kmph = d*(3600/TIMELAPSE) #if we go d in timelapse, then we can go d times this in an hour
                    if kmph > 5:
                        Xs.append(count)
                        count += 1
                        Ys.append(kmph)
                        Xlabs.append(l[0].strftime('%H:%M  '))
                    lastRow = l
                    lastRowTime = l[0]
    
    if (count == 0):
        return urlreq.urlopen("http://blizzard.cs.uwaterloo.ca/~sensordc/notfound.png").read()
    else:
        plt.figure(1,figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi) 
        #plt.xlabel("Date")
        plt.ylabel("Speed (kmph)")
        plt.title("Speed over day") #.format(imei))
        ax = plt.subplot(111)
    
        ax.bar(Xs,Ys,color='blue')
        #ax.plot(Xs,Ysmoothed, color='red')
              
        #make grid go behind bars
        ax.set_axisbelow(True) 
        ax.yaxis.grid(color='gray', linestyle='solid')
        ax.xaxis.grid(color='gray', linestyle='solid')
    
        #set axis
        samplesec = 1
        ax.set_xticklabels([Xlabs[i] for i in range(0,len(Xlabs),samplesec )], fontsize = 14, rotation=90)
        ax.yaxis.set_tick_params(labelsize=14)
        ax.set_xticks([i for i in range(0,len(Xs),samplesec )])
        plt.xlim(0,len(Xs))
        plt.ylim(0,max(Ys)+0.05*max(Ys))
        #ax.set_yticks([0.1*x*100 for x in range(0,11)])
        #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
        buf.seek(0)
        return buf.read() 
    



def plotTripLengthDistribution(dbc,imei,sMonth,sDay,sYear,numdays):
    curDate = datetime(sYear,sMonth,sDay)
    end = curDate+timedelta(days=numdays, hours=23, minutes=59,seconds=59)
    """sDates = [datetime(sYear, sMonth, sDay)+timedelta(days = i) for i in range(numdays)]
    dists = []
    for i in sDates:
        distsTemp = []
        _, _, _, _, distsTemp, _, _ = trajectoryClean(dbc, imei, 0.08, i.year, i.month, i.day)  
        dists.extend(distsTemp)
    print(dists)"""
    tripStartTimes, tripEndTimes, dists = detectTrips(dbc,imei,curDate,end)
    if len(dists) == 0:  
        return urlreq.urlopen("http://blizzard.cs.uwaterloo.ca/~sensordc/notfound.png").read()
    else:
        Xs = []
        Xlabs = []  
        Ys = [0,0,0,0,0,0,0,0,0,0]  
        
        for k in dists:
            if k > 20:
                Ys[9] += 1
            else:
                Ys[int(k / 2)] += 1
                    
        for i in range(0,10):
            Xlabs.append("{0}-{1}".format(i*2,i*2+2))
            Xs.append(i)
        Xlabs[9] = "18-" 
        plt.figure(1,figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi) 
        
        #plt.xlabel("Date")
        plt.ylabel("Number of Trips")
        plt.xlabel("Distance (km)")
        plt.title("Trip length distribution")#.format(imei))
        
        ax = plt.subplot(111)
        
        #plot
        rects = ax.bar(Xs, Ys, color="blue",width=.5)
        #ax.bar(Xs, Ys, color="black",width=.5)
        
        #label with number of valid rows
        #def autolabel(rects, whicharr):
        #    for x in range (0, len(rects)):
        #        height = 0 #might worki with maxYs
        #        ax.text(rects[x].get_x()+rects[x].get_width()/2, 1.01*height, "{0}".format(whicharr[x]), ha='center', va='bottom', color='red',rotation=270)
        #autolabel(rects,Ycounts)
        
        #make grid go behind bars
        ax.set_axisbelow(True) 
        ax.yaxis.grid(color='gray', linestyle='solid')
        
        #set axis
        ax.set_xticklabels(Xlabs, rotation=0, fontsize = 14 )
        ax.yaxis.set_tick_params(labelsize=14)
        ax.set_xticks([i+.25 for i in range(0,len(Xs))])
        plt.xlim(0,len(Xs))
        plt.ylim(0,max(Ys)+1)
        #ax.set_yticks([0.1*x*100 for x in range(0,11)])
        #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
        plt.tight_layout()
        #plt.show()
        
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
        buf.seek(0)
        return buf.read() 


def plotDistanceVsDay(dbc,imei,sMonth,sDay,sYear,numDays):
    curDate = datetime(sYear,sMonth,sDay)
    Xs = [i for i in range(0,numDays)]
    Xlabs = []
    Ycounts = []
    Ys = []
    CumYs = []
    for i in range(0,numDays):
        Xlabs.append(curDate.strftime('%m/%d/%y'))
        end = curDate+timedelta(hours=23, minutes=59,seconds=59)
        tripStartTimes, tripEndTimes, dists = detectTrips(dbc,imei,curDate,end)
        dday = 0
        cday = 0
        for j in dists:
            dday += j
        
        Ys.append(dday)
        Ycounts.append(cday)
        CumYs.append(dday if i == 0 else dday+CumYs[i-1])
        curDate = curDate+timedelta(days=1)
  
    plt.figure(1,figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi) 
    
    #plt.xlabel("Date")
    plt.ylabel("Distance (km) \n(gray = CDF)")
    plt.title("Distance traveled per day")#.format(imei))
    
    ax = plt.subplot(111)
    
    #plot the two bars
    ax.bar(Xs,CumYs, color="grey",width=1)
    rects = ax.bar(Xs, Ys, color="blue",width=1)

    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
    
    #set axis
    ax.set_xticklabels(Xlabs, rotation=90, fontsize = 14)
    ax.yaxis.set_tick_params(labelsize=14)
    plt.xlim(0,len(Xs))
    plt.ylim(0,max(CumYs)+1)
    ax.set_xticks([i+.5 for i in range(0,len(Xs))])
    
    plt.tight_layout()
    #plt.show()
    
    buf = io.BytesIO()
    plt.savefig(buf, format = 'png')
    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
    buf.seek(0)
    return buf.read() 

########### NEW APIs ###########

def getDistanceVsDay(dbc,imei,sMonth,sDay,sYear,numDays):
    curDate = datetime(sYear,sMonth,sDay)
    Xs = [i for i in range(0,numDays)]
    Xlabs = []
    Ycounts = []
    Ys = []
    CumYs = []

    totalDistance = 0;
    countTrips = 0;
    for i in range(0,numDays):
        Xlabs.append(curDate.strftime('%m/%d/%y'))
        end = curDate+timedelta(hours=23, minutes=59,seconds=59)
        tripStartTimes, tripEndTimes, dists = detectTrips(dbc,imei,curDate,end)
        dday = 0
        cday = 0
        for j in dists:
            dday += j
        
        Ys.append(dday)
        Ycounts.append(cday)
        CumYs.append(dday if i == 0 else dday+CumYs[i-1])
        curDate = curDate+timedelta(days=1)

        # we want to add up total distances to calculate the average
        if (dday > 0):
            totalDistance += dday
            countTrips += 1
  
    return { 
        'xAxis' : Xlabs,
        'distance' : Ys,
        'cummulative' : CumYs,
        'average' : totalDistance/countTrips
    }

def getTripLengthDistribution(dbc,imei,sMonth,sDay,sYear,numdays):
    curDate = datetime(sYear,sMonth,sDay)
    end = curDate+timedelta(days=numdays, hours=23, minutes=59,seconds=59)

    tripStartTimes, tripEndTimes, dists = detectTrips(dbc,imei,curDate,end)
    if len(dists) == 0:  
        return { 
            'xAxis' : [],
            'yAxis' : []
        }
    else:
        Xs = []
        Xlabs = []  
        Ys = [0,0,0,0,0,0,0,0,0,0]  
        
        for k in dists:
            if k > 20:
                Ys[9] += 1
            else:
                Ys[int(k / 2)] += 1
                    
        for i in range(0,10):
            Xlabs.append("{0}-{1}".format(i*2,i*2+2))
            Xs.append(i)
        Xlabs[9] = "18-" 

        return { 
            'xAxis' : Xlabs,
            'yAxis' : Ys
        }

########### END of NEW APIs ###########

"""google maps"""   
def plotDay(dbc,imei,sYear,sMonth,sDay):
        
    startDate = datetime(sYear,sMonth,sDay)
    s = startDate.strftime('%y-%m-%d') + " 00:00:00"
    e = startDate.strftime('%y-%m-%d') + " 23:59:59"
    stmt = "select * from imei{0} where stamp >= \"{1}\" and stamp <= \"{2}\" and latgps is not null and longgps is not null order by stamp".format(imei, s, e)
        
    import simplekml
    kml = simplekml.Kml()
    
    #This results in a single styles
    fol = kml.newfolder(name="temp")
    style = simplekml.Style()
    style.labelstyle.color = simplekml.Color.red  # Make the text red
    style.labelstyle.scale = 2  # Make the text twice as big
    style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'

    lastRow = ""
    lastRowTime = ""
    lastTrip = "1"
    for l in dbc.SQLSelectGenerator(stmt):
        if l is not None and abs(l[3]) > 1 and abs(l[4]) > 1:
            if lastRow == "" :
                lastRow = l
                lastRowTime = l[0]
            elif ((l[0]-lastRowTime).total_seconds() >= 10): #only consider rows 10 seconds apart  
                lastTrip = ("2" if lastTrip == "1" else "1")
                pnt = fol.newpoint(name=lastTrip, coords=[(l[4],l[3])])#KML requires long, lat
                pnt.style = style#(sharedstyle1 if lastTrip == "1" else sharedstyle2)
                lastRow = l
                lastRowTime = l[0]
    kml.save("/Users/tcarpent/Desktop/test16.kml")    
 
 







