import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.optimize as opt                                                        
import scipy as sp  
import math
from scipy.interpolate import UnivariateSpline, InterpolatedUnivariateSpline
import numpy as np


d = dict()

d["-20"] = dict()
d["-10"] = dict()
d["0"] = dict()
d["23"] = dict()
d["45"] = dict()

d["-20"]["Xs"] = [8* i for i in [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720,
            760, 800, 840, 880, 920, 960, 1000, 1040, 1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360,
            1400, 1440, 1480, 1520, 1560, 1600, 1640, 1680, 1720, 1760, 1800, 1840, 1840, 1840,1840,1840]]

d["-10"]["Xs"] = [8* i for i in [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720,
         760, 800, 840, 880, 920, 960, 1000, 1040, 1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360,
         1400, 1440, 1480, 1520, 1560, 1600, 1640, 1680, 1720, 1760, 1800, 1840, 1880, 1880, 1880,1880]]

d["0"]["Xs"] = [8* i for i in [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720,
         760, 800, 840, 880, 920, 960, 1000, 1040, 1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360,
         1400, 1440, 1480, 1520, 1560, 1600, 1640, 1680, 1720, 1760, 1800, 1840, 1880, 1920,1920,1920]]

d["23"]["Xs"] = [8* i for i in [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720,
         760, 800, 840, 880, 920, 960, 1000, 1040, 1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360,
         1400, 1440, 1480, 1520, 1560, 1600, 1640, 1680, 1720, 1760, 1800, 1840, 1880, 1920, 1960,1960]]

d["45"]["Xs"] = [8* i for i in [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 560, 600, 640, 680, 720,
         760, 800, 840, 880, 920, 960, 1000, 1040, 1080, 1120, 1160, 1200, 1240, 1280, 1320, 1360,
         1400, 1440, 1480, 1520, 1560, 1600, 1640, 1680, 1720, 1760, 1800, 1840, 1880, 1920, 1960, 2000]]


#battery OEM graphs show that max voltage should be 32, but we have tos tep down the voltage to 8 or so. 
offset =22/32

d["-20"]["Ys"] = [10*offset*i for i in [2.6,2.55,2.6,2.8,3.1,3.15,3.14375, 3.1374999999999997, 3.13125, 3.125, 3.11875,
            3.1125, 3.1062499999999997, 3.1, 3.09375, 3.0875, 3.08125, 3.0749999999999997, 3.06875,
            3.0625, 3.05625, 3.05, 3.0437499999999997, 3.0375, 3.03125, 3.025, 3.01875,
            3.0124999999999997, 3.00625, 3.0, 2.99375, 2.9875, 2.9812499999999997, 2.975, 2.96875,
            2.9625, 2.95625, 2.9499999999999997, 2.94375, 2.9375, 2.93125, 2.925, 2.9187499999999997,
            2.9125, 2.90625,2.9,2.7199999999999998, 2.54, 2.36, 2.1799999999999997, 2.0]]

d["-10"]["Ys"]  = [10*offset*i for i in [3.2,3.1,3.15,3.2,3.25,3.3,3.29125, 3.2824999999999998, 3.2737499999999997,
         3.2649999999999997, 3.2562499999999996, 3.2475, 3.23875, 3.23, 3.22125, 3.2125, 3.20375,
         3.195, 3.18625, 3.1774999999999998, 3.16875, 3.16, 3.15125, 3.1425, 3.13375, 3.125,
         3.11625, 3.1075, 3.09875, 3.09, 3.08125, 3.0725000000000002, 3.06375, 3.055, 3.04625,
         3.0375, 3.02875, 3.02, 3.01125, 3.0025, 2.9937500000000004, 2.9850000000000003,
         2.9762500000000003, 2.9675000000000002, 2.95875,2.95,2.8600000000000003, 2.77, 2.68, 2.59, 2.5]]

d["0"]["Ys"]  = [10*offset*i for i in [3.6,3.5,3.4,3.4,3.4,3.4,3.39125, 3.3825, 3.37375, 3.3649999999999998,
         3.3562499999999997, 3.3474999999999997, 3.33875, 3.33, 3.32125, 3.3125, 3.30375, 3.295,
         3.28625, 3.2775, 3.26875, 3.26, 3.2512499999999998, 3.2424999999999997, 3.2337499999999997,
         3.2249999999999996, 3.21625, 3.2075, 3.19875, 3.19, 3.18125, 3.1725, 3.16375, 3.155,
         3.1462499999999998, 3.1374999999999997, 3.1287499999999997, 3.1199999999999997, 3.11125,
         3.1025, 3.09375, 3.085, 3.07625, 3.0675, 3.05875,3.05,2.94, 2.83, 2.7199999999999998, 2.61, 2.5]]

d["23"]["Ys"]  = [10*offset*i for i in [3.95,3.85, 3.8,3.75,3.7,3.7,3.6862500000000002, 3.6725000000000003, 3.65875, 3.645,
         3.63125, 3.6175, 3.6037500000000002, 3.5900000000000003, 3.57625, 3.5625, 3.54875, 3.535,
         3.52125, 3.5075000000000003, 3.49375, 3.48, 3.46625, 3.4525, 3.43875, 3.425, 3.41125,
         3.3975, 3.38375, 3.37, 3.35625, 3.3425, 3.32875, 3.315, 3.30125, 3.2875, 3.27375, 3.26,
         3.24625, 3.2325, 3.21875, 3.205, 3.19125, 3.1775, 3.16375,3.15,3.02, 2.89, 2.76, 2.63, 2.5]]

d["45"]["Ys"] = [10*offset*i for i in [4,3.95, 3.9,3.85,3.8,3.8,3.7849999999999997, 3.77, 3.755, 3.7399999999999998,
         3.7249999999999996, 3.71, 3.695, 3.6799999999999997, 3.665, 3.65, 3.635, 3.62, 3.605, 3.59,
         3.575, 3.56, 3.545, 3.53, 3.515, 3.5, 3.485, 3.47, 3.455, 3.44, 3.425, 3.41, 3.395, 3.38,
         3.365, 3.35, 3.335, 3.3200000000000003, 3.305, 3.29, 3.2750000000000004,
         3.2600000000000002, 3.245, 3.2300000000000004, 3.2150000000000003,3.2,3.06, 2.92, 2.7800000000000002, 2.64, 2.5]]

d["-20"]["maxwh"] = d["-20"]["Xs"][-1]*max(d["-20"]["Ys"])/1000
d["-10"]["maxwh"] = d["-10"]["Xs"][-1]*max(d["-10"]["Ys"])/1000
d["0"]["maxwh"] = d["0"]["Xs"][-1]*max(d["0"]["Ys"])/1000
d["23"]["maxwh"] = d["23"]["Xs"][-1]*max(d["23"]["Ys"])/1000
d["45"]["maxwh"] = d["45"]["Xs"][-1]*max(d["45"]["Ys"])/1000


def model_funcLinear(x,m,b):
   ans = []
   for i in x:
       ans.append(m*i + b)
   return ans



def clip(inpt):
   if inpt > 1:
      return 1
   elif inpt < 0:
      return 0
   else:
      return inpt

"""
ignore first 5 and lsat 6, cooresponing to modes  1 and 3, when training linear model
"""  
linearN20, parm_cov = sp.optimize.curve_fit(model_funcLinear, d["-20"]["Ys"][5:47],
      [(d["-20"]["maxwh"]-d["-20"]["Xs"][i]*d["-20"]["Ys"][i]/1000)/d["-20"]["maxwh"]  for i in range(5,47)])
linearN10, parm_cov = sp.optimize.curve_fit(model_funcLinear, d["-10"]["Ys"][5:47],
      [(d["-10"]["maxwh"] -d["-10"]["Xs"][i]*d["-10"]["Ys"][i]/1000)/d["-10"]["maxwh"]  for i in range(5,47)])
linear0,   parm_cov = sp.optimize.curve_fit(model_funcLinear, d["0"]["Ys"][5:47],
      [(d["0"]["maxwh"]-d["0"]["Xs"][i]*d["0"]["Ys"][i]/1000)/d["0"]["maxwh"]  for i in range(5,47)])
linearP23, parm_cov = sp.optimize.curve_fit(model_funcLinear, d["23"]["Ys"][5:47],
      [(d["23"]["maxwh"]-d["23"]["Xs"][i]*d["23"]["Ys"][i]/1000)/d["23"]["maxwh"] for i in range(5,47)])
linearP45, parm_cov = sp.optimize.curve_fit(model_funcLinear, d["45"]["Ys"][5:47],
      [(d["45"]["maxwh"]-d["45"]["Xs"][i]*d["45"]["Ys"][i]/1000)/d["45"]["maxwh"] for i in range(5,47)])


   
def returnSOCValsLinear(temp, Vs): 
   Xss = []
   if temp == -20:
      tl = linearN20
   if temp == -10:
      tl = linearN10      
   if temp == 0:
      tl = linear0            
   if temp == 23:
      tl = linearP23            
   if temp == 45:
      tl = linearP45            
   (m,b) = tl
   for i in Vs:
      Xss.append(model_funcLinear([i],m,b))
   return([clip(i[0]) for i in Xss])







"""The below is the 3 line model code"""


def model_func3Line(x,m1,b1,m2,b2,m3,b3):
   ans = []
   for i in range(0,len(x)):
      if i < 5:
         ans.append(m1*x[i]+b1)
      elif i < 46:
         ans.append(m2*x[i]+b2)
      else:
         ans.append(m3*x[i]+b3)
   return ans

def model_func2_3Line(x,m1,b1,m2,b2,m3,b3,m):
   if m == 1:
      return m1*x+b1
   elif m == 2:
      return m2*x+b2
   else:
      return m3*x+b3
  
threeLineN20, parm_cov = sp.optimize.curve_fit(model_func3Line, d["-20"]["Ys"],
      [(d["-20"]["maxwh"]-d["-20"]["Xs"][i]*d["-20"]["Ys"][i]/1000)/d["-20"]["maxwh"]  for i in range(0,len(d["-20"]["Xs"]))])
threeLineN10, parm_cov = sp.optimize.curve_fit(model_func3Line, d["-10"]["Ys"],
      [(d["-10"]["maxwh"] -d["-10"]["Xs"][i]*d["-10"]["Ys"][i]/1000)/d["-10"]["maxwh"]  for i in range(0,len(d["-10"]["Xs"]))])
threeLine0,   parm_cov = sp.optimize.curve_fit(model_func3Line, d["0"]["Ys"],
      [(d["0"]["maxwh"]-d["0"]["Xs"][i]*d["0"]["Ys"][i]/1000)/d["0"]["maxwh"]  for i in range(0,len(d["0"]["Xs"]))])
threeLineP23, parm_cov = sp.optimize.curve_fit(model_func3Line, d["23"]["Ys"],
      [(d["23"]["maxwh"]-d["23"]["Xs"][i]*d["23"]["Ys"][i]/1000)/d["23"]["maxwh"] for i in range(0,len(d["23"]["Xs"]))])
threeLineP45, parm_cov = sp.optimize.curve_fit(model_func3Line, d["45"]["Ys"],
      [(d["45"]["maxwh"]-d["45"]["Xs"][i]*d["45"]["Ys"][i]/1000)/d["45"]["maxwh"] for i in range(0,len(d["45"]["Xs"]))])

 
def returnSOCVals3Line(temp, Vs):

   Xss = []

   if temp == -20:
      tl = threeLineN20
      Xs = d["-20"]["Xs"] 
      Ys = d["-20"]["Ys"]
   if temp == -10:
      tl = threeLineN10      
      Xs = d["-10"]["Xs"] 
      Ys = d["-10"]["Ys"]
   if temp == 0:
      tl = threeLine0            
      Xs = d["0"]["Xs"] 
      Ys = d["0"]["Ys"]
   if temp == 23:
      tl = threeLineP23            
      Xs = d["23"]["Xs"] 
      Ys = d["23"]["Ys"]
   if temp == 45:
      tl = threeLineP45            
      Xs = d["45"]["Xs"] 
      Ys = d["45"]["Ys"]

   (m1,b1,m2,b2,m3,b3) = tl
   
   
   for i in Vs:
      #print(i)
      #these 3 are functions; no ambiguity as to which mode we are in
      if temp == 0 or temp == 23 or temp == 45:
         if i > Ys[5]:
            Xss.append(model_func2_3Line(i, m1,b1,m2,b2,m3,b3, 1))
            #print("1")
         elif i > Ys[46]:
            Xss.append(model_func2_3Line(i, m1,b1,m2,b2,m3,b3, 2))
            #print("2")
         else:
            #mode 3 is invalid, dont use it
            Xss.append(model_func2_3Line(i, m1,b1,m2,b2,m3,b3, 3))
            #print("3 but using 2")
      else:
         #UNTIL SOMETHING BETTER PUT INTO PLACE, ALWAYS JUST USE 2 FOR THESE
         #future work: select mode 1 or 3 for ambiguous voltages based on prior histrpy
         
         """this will be bad, and produce strange graphs, when the voltage is outside the model 2 range."""
         Xss.append(model_func2_3Line(i, m1,b1,m2,b2,m3,b3, 2))
    
   return [clip(i) for i in Xss]
    









