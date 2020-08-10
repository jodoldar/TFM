#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from tkinter import Tk, StringVar, Frame, Text, END, Scrollbar
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import matplotlib.pyplot as pyp

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
import cmath, math

import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

from chunk import Chunk
from par_lib import *
from veh_db import *

class TFM_Application():
    vehicles_db = db
    
    bestScore = -1; bestElem = None

    def __init__(self, width=600, height=400):
        self.root = Tk()

        # Default values for UI
        self.origin = StringVar(); self.origin.set("39.462160,-0.324177")
        self.destination = StringVar(); self.destination.set("39.441699,-0.595555")
        

        self.figure = Figure(figsize= ((width-190)/100, 3.3), dpi=100)
        self.axis0 = self.figure.add_axes((0.00, 0.01, 0.999, 0.99), frameon=True)
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        
        # Initialization of the window
        self.root.geometry("{}x{}".format(width, height))
        self.root.resizable(width=False, height=False)
        self.root.title('Route calculator')

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # Left Column
        self.leftFrame = Frame(self.root, width=80, height=400)
        self.leftFrame.grid(row=0, column=0, padx=(10,10), sticky='NS', pady=(10,0))

        # Center Zone
        self.centerFrame = Frame(self.root, width=500, height=400)
        self.centerFrame.grid(row=0, column=1, padx=(10,10), pady=(10,0), sticky='NS')

        # Left Column > Origin point
        self.origin_p_lab = ttk.Label(self.leftFrame, text='Origen:')
        self.origin_p = ttk.Entry(self.leftFrame, textvariable=self.origin, width=20)
        self.origin_p_lab.grid(column=0, row=0)
        self.origin_p.grid(column=0, row=1, sticky="we", pady=(0,5))

        # Left Column > Destination point
        self.dest_p_lab = ttk.Label(self.leftFrame, text='Destino: ')
        self.dest_p = ttk.Entry(self.leftFrame, textvariable=self.destination, width=15)
        self.dest_p_lab.grid(column=0, row=2)
        self.dest_p.grid(column=0, row=3, sticky="we", pady=(0,5))

        # Left Column > Vehicle
        self.vehicle_used_lab = ttk.Label(self.leftFrame, text='Vehículo: ')
        self.vehicle_used = ttk.Combobox(self.leftFrame, values=list(db.keys()), state='readonly')
        self.vehicle_used.set(list(db.keys())[0])
        self.vehicle_used_lab.grid(column=0, row=4)
        self.vehicle_used.grid(column=0, row=5, pady=(0,5))

        #Left Column > Point Bias
        self.point_bias_lab = ttk.Label(self.leftFrame, text='Márgen de puntos: ')
        self.point_bias_cb = ttk.Combobox(self.leftFrame, values=list(point_bias.keys()), state='readonly')
        self.point_bias_cb.set(list(point_bias.keys())[1])
        self.point_bias_lab.grid(column=0, row=6)
        self.point_bias_cb.grid(column=0, row=7, pady=(0,5))

        # Left Column > Obtain route from API
        self.calc_button = ttk.Button(self.leftFrame, text='Obtener ruta', command=self.getRouteProfile)
        self.calc_button.grid(column=0, row=8, sticky="we")

        # Left Column > Calculate optimum profile
        self.profile_button = ttk.Button(self.leftFrame, text='Cálculo', command=self.getOptimumProfile)
        self.profile_button.grid(column=0, row=9, sticky="we")

        # Center Zone > Get Window Information
        self.button_getInfo = ttk.Button(self.centerFrame, text='Informame',
            command=self.verInfo)
        self.button_getInfo.grid(column=0, row=0, sticky="ns", pady=(0,5))

        # Center Zone > Exit application
        self.button_exit = ttk.Button(self.centerFrame, text='Salir',
            command=self.root.destroy)
        self.button_exit.grid(column=0, row=1, sticky="ns", pady=(0,5))

        # Center Zone > TextBox
        self.tb_Frame = Frame(self.centerFrame, bg='beige', width=70, height=5)
        self.tb_Frame.grid(row=3, column=0, padx=(10,10), pady=(0,0), sticky='NS')

        self.tb_scrollbar = Scrollbar(self.tb_Frame)
        self.tb_scrollbar.grid(row=0, column=1, sticky='NS')
        self.text_info = Text(self.tb_Frame, width=70, height=5)
        self.text_info.grid(column=0, row=0, sticky="ns")
        self.text_info.config(yscrollcommand=self.tb_scrollbar.set)
        self.tb_scrollbar.config(command=self.text_info.yview)

        # Center Zone > Canvas 1
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.centerFrame)
        self.canvas.get_tk_widget().grid(column=0, row=4,sticky="nsew")
        self.canvas.draw()

        self.calc_button.focus_set()

        self.root.mainloop()

    def verInfo(self):
        self.text_info.yview(END)

    def addInfo(self, text):
        self.text_info.insert(END, text)
        self.text_info.yview(END)

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

        self.addInfo("Getting route from {} to {}\n".format(pointA, pointB))

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

        bias_dist = point_bias[self.point_bias_cb.get()]

        for i in range(1,len(coordinates)-1):
            if haversine(filt_coords[-1], coordinates[i], unit=Unit.METERS) > bias_dist :
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
            self.real_chunk_sizes.append(self.real_chunk_sizes[-1] + haversine(filt_coords[i], filt_coords[i+1], unit=Unit.METERS))
        

        self.axis0.clear()
        self.axis0.fill_between(self.real_chunk_sizes, filt_alts, color='blue')
        self.axis0.fill_between(self.real_chunk_sizes, filt_alts, where=self.np_alts < -5, color='green')
        self.axis0.fill_between(self.real_chunk_sizes, filt_alts, where=self.np_alts > 5, color='red')
        self.axis0.set_xlim(0, self.real_chunk_sizes[-1]); self.axis0.set_ylim(0,max(filt_alts))
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        self.canvas.draw()

        self.addInfo(text_info)

        ###################################################
        # Pre-check for the route validity
        print("{} is greater than {}?".format(self.vehicles_db[self.vehicle_used.get()]["Capacity"] / self.vehicles_db[self.vehicle_used.get()]["Cons"][0], api_response.paths[0].time/3600000))
        if(self.vehicles_db[self.vehicle_used.get()]["Capacity"] / self.vehicles_db[self.vehicle_used.get()]["Cons"][0] >= api_response.paths[0].time/3600000):
            print("Calculating optimum map...")
        else:
            print("The route is not suitable for the selected car.")
            return
        ###################################################

        ###################################################
        # Calculate cruise accelerations
        # Cruise[A,B,C,D,E] -> A:[0-20], B:[21-40], C:[41-70], D:[71-100], E:[101-120]
        self.cruise = {}
        self.cruise['A'] = np.interp(0.15, [0, 1], self.vehicles_db[self.vehicle_used.get()]["Cons"])
        self.cruise['B'] = np.interp(0.20, [0, 1], self.vehicles_db[self.vehicle_used.get()]["Cons"])
        self.cruise['C'] = np.interp(0.25, [0, 1], self.vehicles_db[self.vehicle_used.get()]["Cons"])
        self.cruise['D'] = np.interp(0.35, [0, 1], self.vehicles_db[self.vehicle_used.get()]["Cons"])
        self.cruise['E'] = np.interp(0.50, [0, 1], self.vehicles_db[self.vehicle_used.get()]["Cons"])

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
                if i in filt_ids:
                    self.road_speeds[filt_ids.index(i)] = max_speed

    def getOptimumProfile(self):
        ###################################################
        # Creating population
        population = self.createParallelPopulation(len(self.alts))
        #print(population)

        # Obtain initial scores
        scores = self.v3_obtainScores(population)
        #scores = self.v3_score(self.alts, population[0])
        #scores = self.v2_obtainScores(population, self.vehicles_db["Tesla Model X LR"]["Cons"])

        print(scores)
        minScores = float(min([n for n in scores if n>0], default=1000000))
        self.bestScore = minScores
        self.bestElem = deepcopy(population[scores.index(minScores)])
        print("Best score before start is {} W.".format(self.bestScore))

        num_iterations = 100
        is_even = len(population)%2 == 0
        print("Is the population even? {}".format(is_even))

        self.newPopulation = []
        for it in range(0, num_iterations):

            ###################################################################
            ##                      MIX POPULATION                           ##
            ###################################################################

            shuffle(population)
            #if (is_even):
            #    for internal_it in range(0,len(population), 2):
            #        self.mixPopulation(internal_it, population)
            #else:
            #    for internal_it in range(0, len(population)-1, 2):
            #        self.mixPopulation(internal_it, population)
            #    self.newPopulation.append(population[-1])
            self.newPopulation[:] = population

            ###################################################################
            ##                          APPLY MUTATION                       ##
            ###################################################################

            # self.mutate_v2(int(np.random.rand()*len(self.newPopulation)), self.newPopulation)
            for i in range(0, len(self.newPopulation)):
                if (np.random.rand() > 0.75):
                    self.mutate_v2(i, self.newPopulation)

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (REPLACE)          ##
            ###################################################################
            #print("Positions ", end="")
            #for i in range(0, len(self.newPopulation)):
            #    if self.v2_score(self.newPopulation[i], self.vehicles_db["Tesla Model X LR"]["Cons"]) < 0:
            #        # Correction time
            #        temp_pop = self.createParallelPopulation(len(self.alts), 1, False)
            #        self.newPopulation[i] = temp_pop[0]
            #        print("{} ".format(i), end="")
            #print(" corrected.")

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (CORRECT)          ##
            ###################################################################
            #print("Positions ", end="")
            #for i in range(0, len(self.newPopulation)):
            #    if self.v2_score(self.newPopulation[i], self.vehicles_db["Tesla Model X LR"]["Cons"]) < 0:
            #        # Correction time
            #        temp_pop = self.v2_correction(self.newPopulation[i],self.vehicles_db["Tesla Model X LR"]["Cons"])
            #        self.newPopulation[i] = temp_pop
            #        print("{} ".format(i), end="")
            #print(" corrected.")

            ###################################################################
            ##                         GET BEST SCORE                        ##
            ###################################################################

            population[:] = self.newPopulation
            self.newPopulation = []

            scores = self.v3_obtainScores(population)
            print(scores, end='')
            minScores = min([n for n in scores if n>0], default=1000000)
            print(" {} ¿{} < {}?".format(minScores, minScores, self.bestScore))
            if (minScores < self.bestScore):
                print("Update: {}, pos of. {}".format(minScores, scores.index(minScores)))
                self.bestScore = minScores
                self.bestElem = deepcopy(population[scores.index(minScores)])
            print("{}, {}".format(self.bestScore, sum(self.bestElem)))

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (REPLACE)          ##
            ###################################################################
            print("Positions ", end="")
            for i in range(0, len(population)):
                if scores[i] < 0:
                    # Correction time
                    temp_pop = self.createParallelPopulation(len(self.alts), 1, False)
                    population[i] = temp_pop[0]
                    print("{} ".format(i), end="")
            print(" corrected.")

            ###################################################################
            ##                      REDRAW EACH ITERATION                    ##
            ###################################################################

            # Replot each iteration the original graphic w/ the best elem, scaled to adapt in the Y axis.
            self.axis0.clear()
            self.axis0.fill_between(self.real_chunk_sizes, self.alts, color='blue')
            self.axis0.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts < -5, color='green')
            self.axis0.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts > 5, color='red')
            self.axis0.set_xlim(0, self.real_chunk_sizes[-1]); self.axis0.set_ylim(0,max(self.alts))
            self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
            self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

            #self.axis1.clear()
            y_avg = (max(self.alts) - min(self.alts)) / 2
            self.axis0.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            self.axis0.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            #self.axis1.set_xlim(0, len(self.bestElem)); self.axis1.set_ylim(0,1)
            self.canvas.draw()

            ###################################################################

        #print(scores)
        self.addInfo("Best score: {}".format(self.bestScore/1000))


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

    def createParallelPopulation(self, shape, num_of_elems=30, verbose=True):
        pops = []
        self.pool = mp.Pool(mp.cpu_count()-1)
        if verbose:
            print("Creating population...", end='', flush=True)
        while (len(pops) < num_of_elems):
            createSubjectsS=partial(v3_create_subjects_par, profile=self.alts, real_chunk_sizes=self.real_chunk_sizes, vehicle_used=self.vehicles_db[self.vehicle_used.get()], roads=self.road_speeds)
            candidates = self.pool.map(createSubjectsS,list(range(30)))
            for elem in candidates:
                if (elem[0] != -1):
                    pops.append(elem[1])
                    if verbose:
                        print(" {}".format(len(pops)), end='', flush=True)
                else:
                    print(" A", end='')
        if verbose:
            print("")

        self.pool.close()

        return pops


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

    def v3_obtainScores(self, population):
        scores = []
        for elem in population:
            scores.append(self.v3_score(elem))
        
        return scores

    def v3_score(self, candidate):

        chunks = []
        cons = 0

        for i in range(0, len(self.alts) - 1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/(self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])) * 100
            #print("{:0.1f}-".format(lcl_slope), end='', flush=True)

            if i==0:
                chunks.append(Chunk(0, candidate[0][0], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))
            else:
                chunks.append(Chunk(chunks[-1].v1, candidate[0][i], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))

            d = (chunks[-1].v0**2) - (2*chunks[-1].accel*chunks[-1].space)
            time1 = ((-1 * chunks[-1].v0) - cmath.sqrt(d)) / chunks[-1].accel
            time2 = ((-1 * chunks[-1].v0) + cmath.sqrt(d)) / chunks[-1].accel

            #print("{},{},{} ".format(chunks[-1].v0, chunks[-1].accel, chunks[-1].space), end='')
            chunks[-1].v1 = math.sqrt(max(0,(chunks[-1].v0**2) + (2*chunks[-1].accel*chunks[-1].space)))
            chunks[-1].est_time_s = abs((chunks[-1].v1 - chunks[-1].v0) / chunks[-1].accel)

            chunks[-1].calculate_CPEM_kwh_pro(self.vehicles_db[self.vehicle_used.get()])
            if chunks[-1].est_cons[0] > 0:
                cons += chunks[-1].est_cons[0]
            #print(" --> {}".format(chunks[-1].est_cons))

        #print("Cons (kWh): {}".format(cons/1000))

        if (not self.v3_checkValid(chunks)):
            return -1
        return cons

    def v2_score(self, profile, consumptions):
        chunks = []
        cons = 0
        for i in range(0, len(self.alts)-1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/self.real_chunk_sizes[i]) * 100
            #print("Alt1: {}, Alt2: {}, Dist: {}, Slope:{}".format(self.alts[i], self.alts[i+1], self.real_chunk_sizes[i], lcl_slope))
            if (i == 0):
                chunks.append(Chunk(0, profile[i], lcl_slope, self.real_chunk_sizes[i]))
                #print("Initial slope is {}".format(lcl_slope))
            else:
                chunks.append(Chunk(chunks[-1].v1, profile[i], lcl_slope, self.real_chunk_sizes[i]))

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
            chunks[-1].calculate_CPEM_kwh(self.vehicles_db["Tesla Model X LR"])

            # In the case there is a negative acceleration (i.e the car is braking), there is no consumption
            if (chunks[-1].accel > 0):
                #v2 cons += np.interp(chunks[-1].accel, [0,1], consumptions) / chunks[-1].est_time_s
                cons += chunks[-1].est_cons

            #print("Chunk {}. v0-> {}, v1-> {}, accel-> {}[{}], slp: {}[{}]".format(i, chunks[-1].v0, chunks[-1].v1, chunks[-1].accel, adapt_cruise_accel, chunks[-1].slope, self.real_chunk_sizes[i]))
        
        if (not self.v2_checkValid(chunks)):
            #print(profile)
            return -1

        return cons[0]

    def v2_correction(self, profile, consumptions):
        
        attempts = 0
        new_profile = deepcopy(profile)

        while attempts < 50:
            chunks = []
            temp_profile = deepcopy(new_profile)
            
            for i in range(0, len(self.alts)-1):
                lcl_slope = ((self.alts[i+1] - self.alts[i])/self.real_chunk_sizes[i]) * 100
                
                if (i == 0):
                    chunks.append(Chunk(0, temp_profile[i], lcl_slope, self.real_chunk_sizes[i]))
                else:
                    chunks.append(Chunk(chunks[-1].v1, temp_profile[i], lcl_slope, self.real_chunk_sizes[i]))

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

                if (chunks[-1].v1 > self.road_speeds[i]):
                    new_profile[i] = temp_profile[i] - 0.1


            if (self.v2_checkValid(chunks)):
                break

            attempts += 1

        return new_profile

    # In this function, it has to be checked different facts:
    #   - In any moment the v1 speed is higher than the road limit.
    def v3_checkValid(self, chunks):
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
            if (np.random.rand() > 0.95):
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
        for i in range(0, len(population[pos][0])):
            # First decide if we increase or decrease the accel.
            if (np.random.rand() > 0.5):
                fFactor = 1 # Increase accel.
            else:
                fFactor = -1 # Decrease accel.

            # Apply the mutation if applies.
            if (np.random.rand() > 0.8):
                population[pos][0][i] = clamp(population[pos][0][i] + (0.1*fFactor), -1, 1)

def clamp(n, minn, maxn): return min(max(n, minn), maxn) 

def main():
    my_app = TFM_Application(width=800, height=512)
    return 0


if __name__ == "__main__":
    main()
