from datetime import datetime, timedelta
from compute import *
import time
import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt
import SOC

my_dpi = 90

mpl.rcParams["lines.linewidth"] = 3
mpl.rcParams["lines.markersize"] = 15
mpl.rcParams["font.size"] = 22
mpl.rcParams["lines.linestyle"] = "-" 


import random

markers = ['v','^','<','>','1','2','3','4','8','s','p','*','h','H','+','x','D','d','|','_']

def genColors(numColors):
   colors = []
   for i in range(0,numColors):
      dig1 = random.randint(0, 9)
      dig2 = random.randint(0, 9)
      dig3 = random.randint(0, 9)
      dig4 = random.randint(0, 9)
      dig5 = random.randint(0, 9)
      dig6 = random.randint(0, 9)
      colors.append("#{0}{1}{2}{3}{4}{5}".format(str(dig1),str(dig2),str(dig3),str(dig4),str(dig5),str(dig6)))
   return colors


def plotDistanceVsDayAGGREGATE(dbc,imeiList,sMonth,sDay,sYear,numDays):
    
    #build the X list which is the same for all IMEIs
    curDate = datetime(2000+sYear,sMonth,sDay)
    Xs = [i for i in range(0,numDays)]
    Xlabs = []
    for i in range(0,numDays):
        Xlabs.append(curDate.strftime('%y/%m/%d'))
        curDate = curDate+timedelta(days=1)    
    
    #now build the CDF for each user
    d = dict()
    
    for j in imeiList:
        curDate = datetime(2000+sYear,sMonth,sDay)
        
        myCDF = []

        for i in range(0,numDays):
            end = curDate+timedelta(hours=23, minutes=59,seconds=59)
            tripStartTimes, tripEndTimes, dists = detectTrips(dbc,j,curDate,end)
            dday = 0
            cday = 0
            for k in dists:
                dday += k            
            myCDF.append(dday if i == 0 else dday+myCDF[i-1])
            curDate = curDate+timedelta(days=1)
        
        if sum(myCDF) > 0:
            print("finished: {0}".format(j))
            d[j] = dict()
            d[j]["CDFYs"] = myCDF
            
    
    plt.figure(1,figsize=(1080/my_dpi, 800/my_dpi), dpi=my_dpi) 
    
    #plt.xlabel("Date")
    plt.ylabel("cumulative km traveled")
    plt.xlabel("date")
    plt.title("km traveled per day per eBike")
    
    ax = plt.subplot(111)
    
    #plot the two bars
    jcount = 0
    colors = genColors(len(list(d.keys())))
    for j in sorted(d.keys()):
        #UNCOMMENT THE BELOW IF YOU WANT THE ACTUAL IMEI TO SHOW UP INSTEAD OF JUST A NUMBER
        #ax.plot(Xs,d[j]["CDFYs"], label = j, color=colors[jcount], marker = markers[jcount % len(markers)]) #all stuff at end is to choose colors in order from colors dict
        ax.plot(Xs,d[j]["CDFYs"], label = jcount, color=colors[jcount], marker = markers[jcount % len(markers)]) #all stuff at end is to choose colors in order from colors dict
        jcount += 1

    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
    
    #set axis
    ax.set_xticklabels([Xlabs[i] for i in range(0,len(Xlabs),2)], rotation=270 )
    #plt.xlim(0,len(Xs))
    #plt.ylim(0,max(CumYs)+1)
    ax.set_xticks([i for i in range(0,len(Xs),2)])
    
    ax.legend(numpoints=1, loc='best',columnspacing=0,labelspacing=0,handletextpad=0,borderpad=.15,markerscale=0.8) 

    plt.tight_layout()
    plt.savefig("CDF_per_bike.png", format = 'png')
    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio




def plotChargeVsSOC(dbc,imeiList,sMonth,sDay,sYear,eMonth,eDay,eYear):
    
    allChargeStartVoltages = []
    allChargeEndVoltages = []
    
    #build the X list which is the same for all IMEIs
    sDate = datetime(2000+sYear,sMonth,sDay,0,0,0)
    eDate = datetime(2000+eYear,eMonth,eDay,23,23,59)
    
    for i in imeiList:
        chargeStartTimes, chargeEndTimes, chargeStartVolts, chargeEndVolts = detectChargingEvents(dbc,i,sDate,eDate)
        for s in range(0, len(chargeStartVolts)):
            if chargeStartVolts[s] is not None and chargeEndVolts[s] is not None and chargeEndVolts[s] >= chargeStartVolts[s]:
                allChargeStartVoltages.append(chargeStartVolts[s])
                allChargeEndVoltages.append(chargeEndVolts[s])
    
    SOCEstimatesStart = [100*i for i in SOC.returnSOCValsLinear(23,allChargeStartVoltages)]
    SOCEstimatesEnd= [100*i for i in SOC.returnSOCValsLinear(23,allChargeEndVoltages)]
    
    Ys = [0,0,0,0,0,0,0,0,0,0]  
    Ys2 = [0,0,0,0,0,0,0,0,0,0]  
    CumYs = []  
    CumYs2 = []
    
    for k in SOCEstimatesStart:
        Ys[int(k / 10) if k < 100 else 9] += 1
            
    for k in SOCEstimatesEnd:
        Ys2[int(k / 10) if k < 100 else 9] += 1
     
    for aaa in range(0,10):
        CumYs.append(Ys[0] if aaa == 0 else CumYs[aaa-1] + Ys[aaa])
        CumYs2.append(Ys2[0] if aaa == 0 else CumYs2[aaa-1] + Ys2[aaa])
    
    Xs = []
    Xlabs = []   
    
    for k in range(0,10):
        Xs.append(k)
        Xlabs.append("{0}-{1}%".format(k*10,k*10+10))
            
    plt.figure(1,figsize=(1080/my_dpi, 600/my_dpi), dpi=my_dpi) 
        
    plt.ylabel("Number of Charging Events Started @ SOC")
    plt.xlabel("SOC")
    plt.title("Charging Event Start V.S. SOC")
        
    ax = plt.subplot(111)
        
    rects = ax.bar(Xs, CumYs, color="grey",width=1)
    rects = ax.bar(Xs, Ys, color="black",width=1)

    #set axis
    ax.set_xticklabels(Xlabs, rotation=270 )
    ax.set_xticks([i+.5 for i in Xs])
 
    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
        
    plt.xlim(0,10)
    #plt.ylim(0,max(Ys)+1)
    #ax.set_yticks([0.1*x*100 for x in range(0,11)])
    #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
    plt.tight_layout()
    plt.savefig("soc_vs_charging_events.png", format = 'png')
    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio



    #NOW SHOW THE ENDING SOC GRAPH



    plt.figure(1,figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi) 
        
    plt.ylabel("Charging Events Ending @ SOC")
    plt.xlabel("SOC")
    plt.title("Charging Event End V.S. SOC")
        
    ax = plt.subplot(111)
        
    rects = ax.bar(Xs, CumYs2, color="grey",width=1)
    rects = ax.bar(Xs, Ys2, color="black",width=1)

    #set axis
    ax.set_xticklabels(Xlabs, rotation=270 )
    ax.set_xticks([i+.5 for i in Xs])
 
    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
        
    plt.xlim(0,10)
    #plt.ylim(0,max(Ys)+1)
    #ax.set_yticks([0.1*x*100 for x in range(0,11)])
    #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
    plt.tight_layout()
    plt.savefig("soc_vs_charging_events_end.png", format = 'png')
    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio






def plotEmpiricalRange(dbc,imeiList,sMonth,sDay,sYear,eMonth,eDay,eYear):
    
    allTripDists = []
    alltripSOCDeltas = []
    
    #build the X list which is the same for all IMEIs
    sDate = datetime(2000+sYear,sMonth,sDay,0,0,0)
    eDate = datetime(2000+eYear,eMonth,eDay,23,23,59)
    
    for i in imeiList:
        tripStartTimes, tripEndTimes, dists = detectTrips(dbc,i,sDate,eDate)
        tripStartVoltages = []
        tripEndVoltages = []    
        for c in range(0, len(tripStartTimes)):
            """we add a little padding because if the trip start/end time is not perfect, like it actuall started say 2 minutes prior, 
            then due to hills, for example if the person has a hill as soon as their trip starts, the voltage could be totally wonky. 
            this can lead a trip to have a higher voltage at the end than at the start, if the start voltage actaully was read just into 
            the trip on a hill. To totally make sure the bike was at rest both times, we ad a little padding of 5 mins""" 
            startv = getNearestVoltageBeforeTimestamp(dbc, i,tripStartTimes[c]-timedelta(minutes=3))
            endv = getNearestVoltageAfterTimestamp(dbc, i,tripEndTimes[c]+timedelta(minutes=3))
                        
            if startv != -1 and endv != -1: #filter out "bad" trips due to some mysql error
                tripStartVoltages.append(startv)
                tripEndVoltages.append(endv)
                allTripDists.append(dists[c])
        
        import operator
        #compute the startsoc - endsoc for all these trips
        alltripSOCDeltas += map(operator.sub, [100*a for a in SOC.returnSOCValsLinear(23,tripStartVoltages)], [100*b for b in SOC.returnSOCValsLinear(23,tripEndVoltages)])
           
    Xs = []
    Ys = []
    Labs = []
    
    for z in range(0, len(allTripDists)):
        if alltripSOCDeltas[z] >= 5 and allTripDists[z] >= 2 :
            Xs.append(allTripDists[z])
            Ys.append(allTripDists[z]*(100/alltripSOCDeltas[z]))
            Labs.append(alltripSOCDeltas[z])
    
    plt.figure(1,figsize=(1080/my_dpi, 900/my_dpi), dpi=my_dpi) 
    
    plt.ylabel("range (km) assuming all trips have \n identical km/%SOC efficiency to this trip")
    plt.xlabel("lenth of trip (km)")
    plt.title("% of battery required per km vs trip length")
        
    ax = plt.subplot(111)
        
    ax.scatter(Xs, Ys, color="grey", s=200)
    
    for i, txt in enumerate(Labs):
        ax.annotate(str(int(round(txt,0))), (Xs[i],Ys[i]))
    
    
    #rects = ax.bar(Xs, Ys, color="black",width=.5)

    #set axis
    #ax.set_xticklabels(Xlabs, rotation=270 )
    #ax.set_xticks([i+.25 for i in Xs])
 
    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
    ax.xaxis.grid(color='gray', linestyle='solid')

    #plt.xlim(0,10)
    #plt.ylim(0,max(Ys)+1)
    #ax.set_yticks([0.1*x*100 for x in range(0,11)])
    #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
    plt.tight_layout()
    plt.savefig("empiricalrange.png", format = 'png')
    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
        
    
    
"""detectTrips returns the start time and end time of trips. 
       the GPS is gauranteed to be valid at those times because detectTrips enforces this. 
       however, battery voltage may be null at thiose exact times. the below SQL script finds the closest 
       temproally row with a battery voltage and returns it. That way, we know the approiximate battery voltage
       at the start and/or end of any trip. 
       It could be the same row; e.g., the battery voltage might be non null for the exact trip start/end row
       The SQL came from: http://stackoverflow.com/questions/26442472/select-closest-non-null-value-to-timestamp/26443012?noredirect=1#comment41656514_26443012
"""     
def getNearestVoltageBeforeTimestamp(dbc,imei, T):  
    stmt = """SELECT batteryVoltage
    FROM 
      (SELECT batteryVoltage, TIMEDIFF(\'{0}\', `stamp`) AS tdiff
       FROM imei{1}
       WHERE `stamp` <= \'{0}\' AND batteryVoltage IS NOT NULL
       ORDER BY `stamp` DESC
       LIMIT 1) u
    ORDER BY tdiff
    LIMIT 1;""".format(T, imei)
    try:
        return next(dbc.SQLSelectGenerator(stmt))[0]
    except StopIteration as msg:
        return -1 #no null null voltage bfeore this time
    
    
def getNearestVoltageAfterTimestamp(dbc,imei, T):  
    stmt = """SELECT batteryVoltage
    FROM 
      (SELECT batteryVoltage, TIMEDIFF(`stamp`, \'{0}\') AS tdiff
       FROM imei{1}
       WHERE `stamp` > \'{0}\' AND batteryVoltage IS NOT NULL
       ORDER BY `stamp` ASC
       LIMIT 1) u
    ORDER BY tdiff
    LIMIT 1;""".format(T, imei)
    try:
        return next(dbc.SQLSelectGenerator(stmt))[0]
    except StopIteration as msg:
        return -1 #no null null voltage bfeore this time
    


def plotChargeStartVsTime(dbc,imeiList,sMonth,sDay,sYear,eMonth,eDay,eYear):
    
    allChargeStartVoltages = []
    
    #build the X list which is the same for all IMEIs
    sDate = datetime(2000+sYear,sMonth,sDay,0,0,0)
    eDate = datetime(2000+eYear,eMonth,eDay,23,23,59)
    
    BINS = [0 for i in range(0,24)]
    cumBins = []
    
    for i in imeiList:
        chargeStartTimes, chargeEndTimes, chargeStartVolts, chargeEndVolts = detectChargingEvents(dbc,i,sDate,eDate)
        for c in chargeStartTimes:
             BINS[int(c.strftime('%H'))] += 1

    for j in range(0, len(BINS)):
        cumBins.append(BINS[j] if j == 0 else cumBins[j-1] + BINS[j])
                
    plt.figure(1,figsize=(1080/my_dpi, 600/my_dpi), dpi=my_dpi) 
        
    plt.ylabel("# charging events started")
    plt.xlabel("hour of day")
    plt.title("distribution of charging start times")
        
    ax = plt.subplot(111)
    
    Xs = [i for i in range(0,24)]
        
    ax.bar(Xs, cumBins, color="grey",width=1)
    ax.bar(Xs, BINS, color="black",width=1)

    #set axis
    ax.set_xticklabels(Xs, rotation=0 )
    ax.set_xticks([i+.5 for i in Xs])
 
    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
        
    plt.xlim(0,24)
    #plt.ylim(0,max(Ys)+1)
    #ax.set_yticks([0.1*x*100 for x in range(0,11)])
    #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
    plt.tight_layout()
    #plt.show()
    plt.savefig("charge_start_vs_time.png", format = 'png')
    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio
    




    
def plotTripLengthDistributionsAGGREGATE(dbc,imeiList,sMonth,sDay,sYear,numDays):
    allDists = []
    for j in imeiList:
        curDate = datetime(2000+sYear,sMonth,sDay)
        for i in range(0,numDays):
            end = curDate+timedelta(hours=23, minutes=59,seconds=59)
            tripStartTimes, tripEndTimes, dists = detectTrips(dbc,j,curDate,end)
            for k in dists:
                allDists.append(k)        
            curDate = curDate+timedelta(days=1)
            
    Ys = [0,0,0,0,0,0,0,0,0,0,0]  
    Xlabs = []
    Xs = []
        
    for k in allDists:
        if k > 10:
            Ys[10] += 1
        else:
            Ys[int(k)-1] += 1
    
    CumYs = []
    for a in range(0, len(Ys)):
        CumYs.append(Ys[0] if a == 0 else CumYs[a-1] + Ys[a])
                        
    for i in range(1,11):
        Xlabs.append(str(i))
    Xlabs.append("11+")

    Xs = [i for i in range(0,11)]
            
    plt.figure(1,figsize=(1080/my_dpi, 600/my_dpi), dpi=my_dpi) 
    plt.ylabel("number of trips")
    plt.xlabel("distance in km")
    plt.title("trip length distribution")
        
    ax = plt.subplot(111)
        
    ax.bar(Xs, CumYs, color="grey",width=1)
    ax.bar(Xs, Ys, color="black",width=1)

    #make grid go behind bars
    ax.set_axisbelow(True) 
    ax.yaxis.grid(color='gray', linestyle='solid')
        
    #set axis
    ax.set_xticklabels(Xlabs, rotation=0)
    ax.set_xticks([i+.5 for i in range(0,len(Xs))])
    plt.xlim(0,len(Xs))
    #plt.ylim(0,max(Ys)+1)
    #ax.set_yticks([0.1*x*100 for x in range(0,11)])
    #ax.set_yticklabels([0.05*x*100 for x in range(0,21)])
        
    plt.tight_layout()
    #plt.show()
    plt.savefig("trip_length_distribution.png", format = 'png')

    plt.close() #THIS IS CRUCIAL SEE: http://stackoverflow.com/questions/26132693/matplotlib-saving-state-between-different-uses-of-io-bytesio




