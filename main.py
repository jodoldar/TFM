#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from tkinter import Tk, StringVar, Frame, Text, END
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import multiprocessing as mp
from functools import partial
import asyncio

import time
import json
import scipy
import numpy as np
from random import shuffle
from copy import deepcopy
from haversine import haversine, Unit

import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

from chunk import Chunk
from par_lib import v2_create_subjects_par, v2_create_subject_par, v2_score_par, v2_check_valid_par

class TFM_Application():
    vehicles_db = {"Tesla Model X LR": {"Capacity": 100, "Cons": [14.5, 28.8]},
                   "Tesla Model S LR": {"Capacity": 100, "Cons": [12.7, 25.9]},
                   "Tesla Model 3 LR4": {"Capacity":75, "Cons": [10.8, 21.8]},
                   "Hyundai Kona": {"Capacity": 67, "Cons": [10.8, 22.9]},
                   "Jaguar I-Pace": {"Capacity": 90, "Cons": [15.3, 31.4]}}
    
    bestScore = -1; bestElem = None

    def __init__(self, width=600, height=400):
        self.root = Tk()

        self.origin = StringVar(); self.origin.set("39.462160,-0.324177")
        self.destination = StringVar(); self.destination.set("39.441699,-0.595555")
        self.figure = Figure(figsize= ((width-190)/100, 3.3), dpi=100)
        # self.figure2 = Figure(figsize= ((width-190)/100, 0.15), dpi=100)
        self.axis0 = self.figure.add_axes((0.01, 0.02, 0.98, 0.98), frameon=True)
        # self.axis1 = self.figure.add_axes((0.01, 0.24, 0.08, 0.95), frameon=True)
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        # self.axis1.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        # self.axis1.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        
        # Initialization of the window
        self.root.geometry("{}x{}".format(width, height))
        self.root.resizable(width=True, height=False)
        self.root.title('Route calculator')

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Left Column
        self.leftFrame = Frame(self.root, bg='beige', width=80, height=400)
        self.leftFrame.grid(row=0, column=0, sticky="nsew")

        # Center Zone
        self.centerFrame = Frame(self.root, bg='beige', width=450, height=400)
        self.centerFrame.grid(row=0, column=1, sticky="nsew")

        # Origin point
        self.origin_p_lab = ttk.Label(self.leftFrame, text='Origen:')
        self.origin_p = ttk.Entry(self.leftFrame, textvariable=self.origin, width=20)
        self.origin_p_lab.grid(column=0, row=0)
        self.origin_p.grid(column=0, row=1, sticky="we")

        # Detination point
        self.dest_p_lab = ttk.Label(self.leftFrame, text='Destino: ')
        self.dest_p = ttk.Entry(self.leftFrame, textvariable=self.destination, width=15)
        self.dest_p_lab.grid(column=0, row=2)
        self.dest_p.grid(column=0, row=3, sticky="we")

        # Obtain route from API
        self.calc_button = ttk.Button(self.leftFrame, text='Obtener ruta', command=self.getRouteProfile)
        self.calc_button.grid(column=0, row=5, sticky="we")

        # Calculate optimum profile
        self.profile_button = ttk.Button(self.leftFrame, text='Cálculo', command=self.getOptimumProfile)
        self.profile_button.grid(column=0, row=6, sticky="we")

        # Get Window Information
        self.button_getInfo = ttk.Button(self.centerFrame, text='Informame',
            command=self.verInfo)
        self.button_getInfo.grid(column=0, row=0, sticky="ns")

        # Exit application
        self.button_exit = ttk.Button(self.centerFrame, text='Salir',
            command=self.root.destroy)
        self.button_exit.grid(column=0, row=1, sticky="ns")

        # TextBox
        self.text_info = Text(self.centerFrame, width=40, height=5)
        self.text_info.grid(column=0, row=3, sticky="ns")

        # Canvas 1
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.centerFrame)
        self.canvas.get_tk_widget().grid(column=0, row=4,sticky="nsew")
        self.canvas.draw()

        # Canvas 2
        # self.canvas2 = FigureCanvasTkAgg(self.figure2, master=self.centerFrame)
        # self.canvas2.get_tk_widget().grid(column=0, row=5, sticky="nsew")
        # self.canvas2.draw()

        toolbarFrame = Frame(self.centerFrame)
        toolbarFrame.grid()
        #self.toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        #self.toolbar.grid()
        #self.toolbar.update()

        self.button_getInfo.focus_set()

        self.root.mainloop()

    def verInfo(self):
        self.text_info.delete("1.0", END)

        text_info = "Clase de 'raiz': " + self.root.winfo_class() + "\n"
        text_info += "Resolución y posición: " + self.root.winfo_geometry() + "\n"
        text_info += "Anchura de ventana: " + str(self.root.winfo_width()) + "\n"
        text_info += "Altura de ventana: " + str(self.root.winfo_height()) + "\n"
        text_info += "Pos. Ventanta X: " + str(self.root.winfo_rootx()) + "\n"
        text_info += "Pos. Ventana Y: " + str(self.root.winfo_rooty()) + "\n"
        text_info += "Id. de 'raiz': " + str(self.root.winfo_id()) + "\n"
        text_info += "Nombre objeto: " + self.root.winfo_name() + "\n"
        text_info += "Gestor ventanas: " + self.root.winfo_manager() + "\n"

        self.text_info.insert("1.0", text_info)
        
    def calculateRoute(self):
        print("I'm calculating route from {} to {}...".format(self.origin.get(), self.destination.get()))

    def getRouteProfile(self):
        api_instance = swagger_client.RoutingApi()
        key = '6b48ad3a-d56f-4fa5-8320-d62e01fca263'
        pointA = self.origin.get()
        pointB = self.destination.get()
        locale = 'es'
        vehicle = 'car'
        elevation = True
        instructions = False
        details = ['road_class']

        coordinates = []
        altitudes = []
        inclination = []

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
        for i in range(0, len(altitudes)-1):
            if (altitudes[i+1]-altitudes[i]) > 1.0:
                inclination.append(1)
            elif (altitudes[i+1]-altitudes[i]) < -1.0:
                inclination.append(-1)
            else:
                inclination.append(0)
        inclination.append(0)
        self.neutro = scipy.zeros(len(inclination))

        self.x_axis = np.arange(0,len(altitudes),1)
        np_alts = np.array(inclination)
        self.alts = np.array(altitudes)
        self.chunk_size = api_response.paths[0].distance / len(api_response.paths[0].points.coordinates)

        self.real_chunk_sizes = []
        for i in range(0, len(coordinates)-1):
            self.real_chunk_sizes.append(haversine(coordinates[i], coordinates[i+1], unit=Unit.METERS))
        

        # Calculate divisor for reshepe
        ######################################################
        divisor = 4; MAX_SUBSAMPLE = 15
        full_len = len(np_alts)

        while (divisor < MAX_SUBSAMPLE):
            if (full_len%divisor == 0):
                break
            divisor += 1
        
        if (divisor == MAX_SUBSAMPLE):
            if (full_len%2 == 0):
                divisor = 2
            else:
                divisor = 1
        text_info += "Subsampling set to {}\n".format(divisor)
        ###################################################

        new_inc = np.sum(np_alts.reshape(-1,divisor), axis=1)
        #print(new_inc)
        self.sampled_inc = np.repeat(new_inc, divisor)
        #print(sampled_inc)

        #self.axis0.plot(altitudes, 'gx')
        self.axis0.fill_between(self.x_axis, altitudes, color='blue')
        self.axis0.fill_between(self.x_axis, altitudes, where=self.sampled_inc<self.neutro, color='green')
        self.axis0.fill_between(self.x_axis, altitudes, where=self.sampled_inc>self.neutro, color='red')
        self.axis0.set_xlim(0, len(altitudes)); self.axis0.set_ylim(0,max(altitudes))
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        self.canvas.draw()

        self.text_info.delete("1.0", END)
        self.text_info.insert("1.0", text_info)

        ###################################################
        # Pre-check for the route validity
        print("{} is greater than {}?".format(self.vehicles_db['Tesla Model X LR']["Capacity"] / self.vehicles_db["Tesla Model X LR"]["Cons"][0], api_response.paths[0].time/3600000))
        if(self.vehicles_db['Tesla Model X LR']["Capacity"] / self.vehicles_db["Tesla Model X LR"]["Cons"][0] >= api_response.paths[0].time/3600000):
            print("Calculating optimum map...")
        else:
            print("The route is not suitable for the selected car.")
            return
        ###################################################

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
            else:
                max_speed = 120
            
            for i in range(road_block[0], road_block[1]-1):
                self.road_speeds[i] = max_speed

    def getOptimumProfile(self):
        ###################################################
        # Creating population
        population = self.createParallelPopulation(len(self.alts))
        #print(population)

        # Obtain initial scores
        scores = self.v2_obtainScores(population, self.vehicles_db["Tesla Model X LR"]["Cons"])

        print(scores)
        minScores = float(min([n for n in scores if n>0], default=1000000))
        self.bestScore = minScores
        self.bestElem = deepcopy(population[scores.index(minScores)])
        print("Best score before start is {}.".format(self.bestScore))

        num_iterations = 50
        is_even = len(population)%2 == 0
        print("Is the population even? {}".format(is_even))

        self.newPopulation = []
        for it in range(0, num_iterations):
            shuffle(population)
            if (is_even):
                for internal_it in range(0,len(population), 2):
                    self.mixPopulation(internal_it, population)
            else:
                for internal_it in range(0, len(population)-1, 2):
                    self.mixPopulation(internal_it, population)
                self.newPopulation.append(population[-1])

            # self.mutate_v2(int(np.random.rand()*len(self.newPopulation)), self.newPopulation)
            for i in range(0, len(self.newPopulation)):
                if (np.random.rand() > 0.1):
                    self.mutate_v2(i, self.newPopulation)

            population = deepcopy(self.newPopulation)
            self.newPopulation = []

            scores = self.v2_obtainScores(population, self.vehicles_db["Tesla Model X LR"]["Cons"])
            print(scores, end='')
            minScores = min([n for n in scores if n>0], default=1000000)
            print(" {} ¿{} < {}?".format(minScores, minScores, self.bestScore))
            if (minScores < self.bestScore):
                print("Update: {}, pos of. {}".format(minScores.all(), scores.index(minScores)))
                self.bestScore = minScores
                self.bestElem = deepcopy(population[scores.index(minScores)])
            print("{}, {}".format(self.bestScore, sum(self.bestElem)))


            # Replot each iteration the original graphic w/ the best elem, scaled to adapt in the Y axis.
            self.axis0.clear()


            self.axis0.fill_between(self.x_axis, self.alts, color='blue')
            self.axis0.fill_between(self.x_axis, self.alts, where=self.sampled_inc<self.neutro, color='green')
            self.axis0.fill_between(self.x_axis, self.alts, where=self.sampled_inc>self.neutro, color='red')
            self.axis0.set_xlim(0, len(self.alts)); self.axis0.set_ylim(0,max(self.alts))
            self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
            self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

            #self.axis1.clear()
            y_avg = (max(self.alts) - min(self.alts)) / 2
            self.axis0.plot(self.x_axis, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem)), 'y')
            self.axis0.hlines(y_avg, min(self.x_axis), max(self.x_axis),'k')
            #self.axis1.set_xlim(0, len(self.bestElem)); self.axis1.set_ylim(0,1)
            self.canvas.draw()

        #print(scores)



    def createPopulation(self, shape):
        pops = []
        print("Creating population...", end='', flush=True)
        while (len(pops) < 15):
            candidate = self.createSubject(shape)
            if (self.v2_score(candidate[0], self.vehicles_db["Tesla Model X LR"]["Cons"]) != -1):
                pops.append(candidate[0])
                print(" {}".format(len(pops)), end='', flush=True)
        print("")
        return pops
    
    def createParallelPopulation(self, shape):
        pops = []
        self.pool = mp.Pool(mp.cpu_count()-1)
        print("Creating population...", end='', flush=True)
        while (len(pops) < 30):
            createSubjectsS=partial(v2_create_subjects_par, shape=shape, alts=self.alts, consumption=self.vehicles_db["Tesla Model X LR"]["Cons"], real_chunk_sizes=self.real_chunk_sizes, cruise=self.cruise, road_speeds=self.road_speeds)
            candidates = self.pool.map(createSubjectsS,list(range(30*mp.cpu_count()-1)))
            for elem in candidates:
                if (elem[0] != -1):
                    pops.append(elem[1])
                    print(" {}".format(len(pops)), end='', flush=True)
        print("")
        self.pool.close()
        return pops

    def createSubject(self, shape):
        # Creation of individual between [0.5, 0.5]
        return np.random.rand(1, shape) - 0.5

    def obtainScores(self, population, consumptions):
        scores = []
        #print("Current consumptions: {}".format(consumptions))
        for elem in population:
            calc = 0
            for acc in elem:
                calc += np.interp(acc, [0.0, 1.0], consumptions)
            scores.append(calc)
        
        return scores

    def v2_obtainScores(self, population, consumptions):
        scores = []
        for elem in population:
            scores.append(self.v2_score(elem, consumptions))
        
        return scores
    
    def v2_score(self, profile, consumptions):
        chunks = []
        cons = 0
        for i in range(0, len(self.alts)-1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/self.real_chunk_sizes[i]) * 100
            #print("Alt1: {}, Alt2: {}, Dist: {}, Slope:{}".format(self.alts[i], self.alts[i+1], self.real_chunk_sizes[i], lcl_slope))
            if (i == 0):
                chunks.append(Chunk(0, profile[i], lcl_slope))
                #print("Initial slope is {}".format(lcl_slope))
            else:
                chunks.append(Chunk(chunks[-1].v1, profile[i], lcl_slope))

            # Once the chunk is created, the v1 speed is calculated
            adapt_cruise_accel = 0
            initial_spd = chunks[-1].v0
            if initial_spd < 20:
                adapt_cruise_accel = self.cruise['A']
            elif initial_spd < 40:
                adapt_cruise_accel = self.cruise['B']
            elif initial_spd < 70:
                adapt_cruise_accel = self.cruise['C']
            elif initial_spd < 100:
                adapt_cruise_accel = self.cruise['D']
            else:
                adapt_cruise_accel = self.cruise['E']
            
            adapt_cruise_accel = np.interp(adapt_cruise_accel, consumptions, [0,1])

            chunks[-1].calculate_v1(self.real_chunk_sizes[i], adapt_cruise_accel, self.road_speeds[i])

            # In the case there is a negative acceleration (i.e the car is braking), there is no consumption
            if (chunks[-1].accel > 0):
                cons += np.interp(chunks[-1].accel, [0,1], consumptions) / chunks[-1].est_time_s

            #print("Chunk {}. v0-> {}, v1-> {}, accel-> {}[{}], slp: {}[{}]".format(i, chunks[-1].v0, chunks[-1].v1, chunks[-1].accel, adapt_cruise_accel, chunks[-1].slope, self.real_chunk_sizes[i]))
        
        if (not self.v2_checkValid(chunks)):
            #print(profile)
            return -1

        return cons[0]
    
    # In this function, it has to be checked different facts:
    #   - In any moment the v1 speed is higher than the road limit.
    def v2_checkValid(self, chunks):
        for i in range(len(chunks)):
            if (chunks[i].v1 > self.road_speeds[i]):
                #print("Profile not valid. {} is greater than {}. (v0: {}, v1: {}, accel: {}, slp:{}, dist: {}".format(chunks[i].v1, self.road_speeds[i], chunks[i].v0, chunks[i].v1, chunks[i].accel, chunks[i].slope, self.real_chunk_sizes[i]))
                return False
        return True

    def mixPopulation(self, pos, population):
        #print("Mix population of pos {} & {}".format(pos, pos+1))
        l1 = population[pos]
        l2 = population[pos+1]

        for i in range(0, len(l1)):
            if (np.random.rand() > 0.9):
                aux = l1[i]
                l1[i] = l2[i]
                l2[i] = aux

        self.newPopulation.append(l1)
        self.newPopulation.append(l2)

    def mutate(self, pos, population):
        for i in range(0, len(population[pos])):
            if (np.random.rand() > 0.4):
                population[pos][i] = np.random.rand()

    def mutate_v2(self, pos, population):
        for i in range(0, len(population[pos])):
            # First decide if we increase or decrease the accel.
            if (np.random.rand() > 0.5):
                fFactor = 1 # Increase accel.
            else:
                fFactor = -1 # Decrease accel.

            # Apply the mutation if applies.
            if (np.random.rand() > 0.6):
                population[pos][i] = clamp(population[pos][i] + (0.1*fFactor), -1, 1)

def clamp(n, minn, maxn): return min(max(n, minn), maxn) 

def main():
    my_app = TFM_Application(width=800, height=512)
    return 0


if __name__ == "__main__":
    main()
