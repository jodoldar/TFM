#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from chunk import Chunk
from par_lib import *
from veh_db import *

import swagger_client
from swagger_client.rest import ApiException
from vincenty import vincenty

from tkinter import Tk, StringVar, Frame, Text, END, Scrollbar

class TestResult():
    vehicles_db = db

    def __init__(self):
        self.root = Tk()

        self.origin = StringVar(); self.origin.set("39.462160,-0.324177")
        self.destination = StringVar(); self.destination.set("39.441699,-0.595555")
        self.ngr_val = 0.1
        self.ga_iterations = StringVar(); self.ga_iterations.set(20)

    def getRouteProfile(self):
        api_instance = swagger_client.RoutingApi()
        key = 'e8a518c2-0c42-4102-9ad2-2f8a79bdb744'
        pointA = self.origin.get()
        pointB = self.destination.get()
        locale = 'es'
        vehicle = 'car'
        elevation = True
        instructions = False
        details = ['road_class']

        coordinates = []
        altitudes = []

        print("Getting route from {} to {}\n".format(pointA, pointB))

        try:
            api_response = api_instance.route_get([pointA,pointB], False, key, locale=locale, vehicle=vehicle, elevation=elevation, instructions=instructions, details=details)
            
            print("Info received: {}".format(api_response.info))
            text_info = "Nº of paths: {}\n".format(len(api_response.paths))
            text_info += "Distance: {:.2f} km.\nTime: {:.2f} min.\nTotal points: {}\n".format(api_response.paths[0].distance/1000, api_response.paths[0].time/60000,len(api_response.paths[0].points.coordinates))
            text_info += "Types of roads: {}\n".format(len(api_response.paths[0].details['road_class']))
            for coordinate in api_response.paths[0].points.coordinates:
                coordinates.append([coordinate[0], coordinate[1]])
                altitudes.append(coordinate[2])
        except ApiException as e:
            print("Exception when calling GeocodignApi->geocode_get: %s\n" % e)

        text_info += "Nº of alt. coordinates: {}\n".format(len(altitudes))

        print("Processing surface...")
        print("Initial number of points: {}".format(len(coordinates)))


        # PRE-FILTERING BY BIAS
        filt_ids = []; filt_ids.append(0)
        filt_coords = []; filt_coords.append(coordinates[0])
        filt_alts = []; filt_alts.append(altitudes[0])
        inclination = []; inclination.append(0)

        bias_dist = point_bias["100"]

        for i in range(1,len(coordinates)-1):
            #print(vincenty(filt_coords[-1], coordinates[i])*1000)
            if vincenty(filt_coords[-1], coordinates[i])*1000 > bias_dist:
            #if haversine(filt_coords[-1], coordinates[i], unit=Unit.METERS) > bias_dist :
                filt_ids.append(i)
                filt_coords.append(coordinates[i])
                filt_alts.append(altitudes[i])
                inclination.append(altitudes[i]-filt_alts[-2]) # Check that new altitude is already introduced at this point
        filt_coords.append(coordinates[-1]); filt_alts.append(altitudes[-1]); inclination.append(altitudes[-1]-filt_alts[-2])
        print("Pre-Process 1. Points reduced to {}. Bias is {}".format(len(filt_coords), bias_dist))

        self.x_axis = np.arange(0,len(filt_alts),1)
        self.np_alts = np.array(inclination)
        self.alts = np.array(filt_alts)
        self.chunk_size = api_response.paths[0].distance / len(api_response.paths[0].points.coordinates)

        self.real_chunk_sizes = []
        self.real_chunk_sizes.append(0)
        for i in range(0, len(filt_coords)-1):
            #print(vincenty(filt_coords[i], filt_coords[i+1]))
            self.real_chunk_sizes.append(self.real_chunk_sizes[-1] + vincenty(filt_coords[i], filt_coords[i+1])*1000)
            #self.real_chunk_sizes.append(self.real_chunk_sizes[-1] + haversine(filt_coords[i], filt_coords[i+1], unit=Unit.METERS))
        
        ###################################################
        # Calculate cruise accelerations
        # Cruise[A,B,C,D,E] -> A:[0-20], B:[21-40], C:[41-70], D:[71-100], E:[101-120]
        self.cruise = {}
        self.cruise['A'] = np.interp(0.15, [0, 1], self.vehicles_db["Tesla Model X LR"]["Cons"])
        self.cruise['B'] = np.interp(0.20, [0, 1], self.vehicles_db["Tesla Model X LR"]["Cons"])
        self.cruise['C'] = np.interp(0.25, [0, 1], self.vehicles_db["Tesla Model X LR"]["Cons"])
        self.cruise['D'] = np.interp(0.35, [0, 1], self.vehicles_db["Tesla Model X LR"]["Cons"])
        self.cruise['E'] = np.interp(0.50, [0, 1], self.vehicles_db["Tesla Model X LR"]["Cons"])

        print("Accl. Profile: {}".format(self.cruise.items()))
        print("Roads: {}".format(api_response.paths[0].details['road_class']))
        self.road_speeds = np.full((len(self.alts),1), 50)
        for road_block in api_response.paths[0].details['road_class']:
            if road_block[2] == 'residential':
                max_speed = 30
            elif road_block[2] == 'tertiary':
                max_speed = 50
            elif road_block[2] == 'secondary':
                max_speed = 80
            elif road_block[2] == 'primary':
                max_speed = 100
            elif road_block[2] == 'unclassified':
                max_speed = 75
            else:
                max_speed = 120
            
            for i in range(road_block[0], road_block[1]):
                if i in filt_ids:
                    self.road_speeds[filt_ids.index(i)] = max_speed

        print(text_info)

        ###################################################
        # Pre-check for the route validity
        avg_cons = (self.vehicles_db["Tesla Model X LR"]["Cons"][0] + self.vehicles_db["Tesla Model X LR"]["Cons"][1])/2
        print("{}h is greater than {}h?".format(self.vehicles_db["Tesla Model X LR"]["Capacity"] / avg_cons, api_response.paths[0].time/3600000))
        if(self.vehicles_db["Tesla Model X LR"]["Capacity"] / avg_cons >= api_response.paths[0].time/3600000):
            print("Calculating optimum map...")
        else:
            print("The route is not suitable for the selected car.")
            return
        ###################################################

        

        self.route_info_available = True

    def v3_score(self, candidate):
        chunks = []; cons = 0

        for i in range(0, len(self.alts) - 1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/(self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])) * 100

            if i==0:
                chunks.append(Chunk(0, candidate[0], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))
            else:
                chunks.append(Chunk(chunks[-1].v1, candidate[i], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))

            d = (chunks[-1].v0**2) - (2*chunks[-1].accel*chunks[-1].space)
            time1 = ((-1 * chunks[-1].v0) - cmath.sqrt(d)) / chunks[-1].accel
            time2 = ((-1 * chunks[-1].v0) + cmath.sqrt(d)) / chunks[-1].accel

            #print("{},{},{} ".format(chunks[-1].v0, chunks[-1].accel, chunks[-1].space), end='')
            chunks[-1].v1 = math.sqrt(max(0,(chunks[-1].v0**2) + (2*chunks[-1].accel*chunks[-1].space)))
            chunks[-1].est_time_s = abs((chunks[-1].v1 - chunks[-1].v0) / chunks[-1].accel)

            chunks[-1].calculate_CPEM_kwh_pro(self.vehicles_db["Tesla Model X LR"])
            #if chunks[-1].est_cons[0] > 0:
            cons += chunks[-1].est_cons[0]
        
        return (cons, chunks)

def main():
    my_app = TestResult()    

    elem = [9.23804948e-01,-4.92857123e-01,4.05488224e-01,4.83062941e-01
,-6.55466716e-01,-4.09103612e-01,9.90132771e-01,-3.98701844e-01
,7.61368685e-01,5.55998174e-01,3.70929029e-01,-1.22577200e-01
,-2.86682308e-01,7.65913677e-01,-3.76025505e-01,4.97837921e-01
,2.40089215e-01,-9.31515963e-01,-1.42403361e-02,9.60459745e-01
,-7.07629406e-01,3.47281865e-01,-1.14721099e-01,8.30949335e-01
,9.73305497e-02,-2.56853242e-01,1.29526991e-01,3.09330415e-01
,-8.98944419e-01,-3.01405476e-01,4.27493723e-02,5.76925214e-01
,-7.08005519e-01,-3.91340493e-01,-5.30915233e-01,1.63901658e-01
,6.22075501e-01,2.83157102e-01,2.20229541e-02,6.30201217e-01
,-3.00269898e-01,-1.47001943e-01,2.47552802e-01,2.01119927e-02
,1.30081006e-01,1.16594942e-02,-1.46305513e-02,4.28960696e-01
,1.46723442e-01,6.82973810e-01,-5.26204542e-01,6.43025623e-01
,2.77462904e-04,9.16878202e-01,9.01311016e-01,-6.95547134e-01
,-1.38820471e-01,1.43321035e-01,1.65402128e-01,2.09673223e-01
,4.94639280e-01,-3.37486962e-01,-2.88604502e-01,2.52252842e-01
,-4.22075047e-01,-6.06115462e-01,-6.56440617e-02,7.28612545e-01
,3.47023446e-01,-3.54628861e-01,-7.50767541e-01,5.97182077e-01
,1.73434826e-01,-8.76209737e-01,-6.71016511e-01,2.29943884e-01
,-5.30559279e-01,5.88616770e-01,-9.75567339e-01,-9.47799495e-01
,6.10619164e-01,-8.22244073e-01,5.80488060e-01,-7.72149844e-01
,2.05688647e-01,-9.37424826e-01,1.21867587e-01,9.36886434e-02
,6.83176557e-01,8.51348116e-01,-6.05478723e-01,-5.69968267e-01
,-4.87382151e-01,7.65911934e-01,7.39949368e-01,8.07983796e-01
,4.71330727e-01,-1.38651863e-01,-3.28791263e-01,9.73125379e-01
,8.12108919e-02,9.17051819e-01,-8.73888770e-01,-7.96623641e-01
,-9.81804283e-01,-3.59159031e-01,2.43641112e-01,-2.93279198e-01
,-8.80520187e-01,3.11919409e-01,8.52917315e-01,-7.62846507e-01
,2.41828648e-02,-9.38377321e-01,-4.02928202e-01,-7.09179609e-01
,-2.73848880e-01,8.73809222e-02,-7.43785874e-01,-3.82462939e-01
,-1.30057005e-01,-9.92684022e-01,-9.46969088e-02,-8.21743543e-01
,-6.20516629e-01,-1.66740173e-01,2.58491058e-01,-1.23215892e-01
,-4.81429811e-01,-4.06253180e-01,7.78759337e-01,7.98484810e-01
,8.03791423e-01]

    my_app.getRouteProfile()

    cons,chunks = my_app.v3_score(elem)

    print("Consumption is {}".format(cons/3600))

    return 0


if __name__ == "__main__":
    main()
