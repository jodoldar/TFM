#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import chunk

from tkinter import Tk, StringVar, Frame, Text, END, Scrollbar
from tkinter import ttk

import matplotlib
from numpy.lib.function_base import interp
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
from vincenty import vincenty
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
        self.ngr_val = 0.1
        self.ga_iterations = StringVar(); self.ga_iterations.set(20)

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
        self.calc_button.grid(column=0, row=12, pady=(10,5), sticky="we")

        # Left Column > Calculate optimum profile
        self.profile_button = ttk.Button(self.leftFrame, text='Cálculo', command=self.getIOptimumProfile)
        self.profile_button.grid(column=0, row=13, sticky="we")

        # Left Column > GA Iterations
        self.ga_iterations_lab = ttk.Label(self.leftFrame, text='Iteraciones: ')
        self.ga_iterations_p = ttk.Entry(self.leftFrame, textvariable=self.ga_iterations)
        self.ga_iterations_lab.grid(column=0, row=8)
        self.ga_iterations_p.grid(column=0, row=9, pady=(0,5), sticky="we")

        # Left Column > Method
        self.ga_method_lab = ttk.Label(self.leftFrame, text='Método Opt.:')
        self.ga_method_cb = ttk.Combobox(self.leftFrame, values=list(ga_method.keys()), state='readonly')
        self.ga_method_cb.set(list(ga_method.keys())[0])
        self.ga_method_lab.grid(column=0, row=10)
        self.ga_method_cb.grid(column=0, row=11, pady=(0,5))

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

        self.route_info_available = False
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
            elif road_block[2] == 'unclassified':
                max_speed = 75
            else:
                max_speed = 120
            
            for i in range(road_block[0], road_block[1]):
                if i in filt_ids:
                    self.road_speeds[filt_ids.index(i)] = max_speed

        self.axis0.clear()
        self.axis0.fill_between(self.real_chunk_sizes, filt_alts, color='blue')
        self.axis0.fill_between(self.real_chunk_sizes, filt_alts, where=self.np_alts < -5, color='green')
        self.axis0.fill_between(self.real_chunk_sizes, filt_alts, where=self.np_alts > 5, color='red')
        self.axis0.plot(self.real_chunk_sizes, self.road_speeds)
        self.axis0.set_xlim(0, self.real_chunk_sizes[-1]); self.axis0.set_ylim(0,max(filt_alts))
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        self.canvas.draw()

        self.addInfo(text_info)

        ###################################################
        # Pre-check for the route validity
        avg_cons = (self.vehicles_db[self.vehicle_used.get()]["Cons"][0] + self.vehicles_db[self.vehicle_used.get()]["Cons"][1])/2
        print("{}h is greater than {}h?".format(self.vehicles_db[self.vehicle_used.get()]["Capacity"] / avg_cons, api_response.paths[0].time/3600000))
        if(self.vehicles_db[self.vehicle_used.get()]["Capacity"] / avg_cons >= api_response.paths[0].time/3600000):
            print("Calculating optimum map...")
        else:
            print("The route is not suitable for the selected car.")
            return
        ###################################################

        

        self.route_info_available = True

    def getIOptimumProfile(self, num_elems=30):
        print("Info? {}, Profile? {}".format(self.route_info_available, self.ga_method_cb.current()))

        if (self.route_info_available == False):
            self.getRouteProfile()

        if self.route_info_available: #Second filter
            if self.ga_method_cb.current() == 0:
                self.getOptimumProfile(num_elems)
            elif self.ga_method_cb.current() == 1:
                self.getOptimumProfileTime(num_elems)
            else:
                self.getOptimumProfileMixed(num_elems)
        else:
            print("Mala suerte amigo")



    def getOptimumProfile(self, num_elems):
        file_out = open("tfm.out", "w")
        pyp.ion()
        ###################################################
        # Creating population
        population = self.createParallelPopulation(len(self.alts), num_elems)

        # Obtain initial scores
        all_chunks = []
        scores, all_chunks = self.v3_obtainScores(population)

        print(scores)
        minScores = float(min([n for n in scores if n>0], default=1000000))
        self.bestScore = minScores
        self.bestElem = deepcopy(population[scores.index(minScores)])
        print("Best score before start is {} W.".format(self.bestScore))
        iNumOfConsecutiveStuck = 0
        iPrevScore = self.bestScore

        y_avg = (max(self.alts) - min(self.alts)) / 4
        bestChunk = all_chunks[scores.index(minScores)]
        self.axis0.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
        self.axis0.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
        self.axis0.plot(self.real_chunk_sizes, self.road_speeds)
        self.axis0.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
        self.canvas.draw()
        self.centerFrame.update_idletasks()

        num_iterations = int(self.ga_iterations.get())
        is_even = len(population)%2 == 0
        print("Is the population even? {}".format(is_even))

        self.newPopulation = []
        for it in range(0, num_iterations):

            ###################################################################
            ##                      MIX POPULATION                           ##
            ###################################################################

            # Apply normalized NGR
            q0 = self.ngr_val / (1 - (1 - self.ngr_val)**len(population))
            
            sort_scores = sorted(scores)
            sort_positions = sorted(range(len(scores)), key=lambda k: scores[k])
            ngr = []

            for sor_it in range(0, len(sort_scores)):
                ngr.append(self.ngr_val * (1 - self.ngr_val)**(sor_it))

            #print("For mixing: q0 = {}, scores:\n{}".format(q0, ngr))
            #print("{}\n{}".format(sort_scores, sort_positions))
            
            max_candidates = round(0.4 * len(population))
            if (max_candidates % 2) != 0:
                max_candidates = max_candidates - 1
            candidates = []; children = []

            # Get best candidates
            for sor_it in range(0, len(ngr)):
                if ((ngr[sor_it] > (self.ngr_val * 0.4)) or (len(candidates) < max_candidates)):
                    candidates.append(population[sort_positions[sor_it]])
                    #print("Added position: {} -> {}".format(sort_positions[sor_it], ngr[sor_it]))

            # Get new children
            for pos in range(0, max_candidates, 2):
                dist = np.random.uniform()
                childA = []; childB = []

                for pair in list(zip(candidates[pos], candidates[pos+1])):
                    childA.append(dist*pair[0] + (1-dist)*pair[1])
                    childB.append((1-dist)*pair[0] + dist*pair[1])
                    children.append(childA); children.append(childB)

            # Replace worst population
            for pos in range(0, max_candidates):
                population[sort_positions[-1-pos]] = children[pos]

            ###################################################################
            ##                          APPLY MUTATION                       ##
            ###################################################################

            # self.mutate_v2(int(np.random.rand()*len(self.newPopulation)), self.newPopulation)
            for i in range(0, len(population)):
                if (np.random.rand() > 0.9):
                    self.mutate_v3(i, population)
            
            #self.newPopulation[:] = population

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

            #population[:] = self.newPopulation
            #self.newPopulation = []

            scores, all_chunks = self.v3_obtainScores(population)
            #print(scores, end='')
            minScores = min([n for n in scores if n>0], default=1000000)
            print(" {} ¿{} < {}?".format(minScores, minScores, self.bestScore))
            if (minScores < self.bestScore):
                print("Update: {}, pos of. {}".format(minScores, scores.index(minScores)))
                self.bestScore = minScores
                self.bestElem = deepcopy(population[scores.index(minScores)])
            
            window= np.ones(int(10))/float(10)
            rl_avg = np.convolve(self.bestElem[0], window, 'same')

            pyp.close('all')
            pyp.figure()
            
            pyp.subplot(211)
            pyp.plot(self.real_chunk_sizes, self.bestElem[0], lw=0.5, color='black')
            pyp.plot(self.real_chunk_sizes, rl_avg, lw=2.0, color='blue')
            pyp.hlines(0, 0, self.real_chunk_sizes[-1], colors='black', linestyles='--')
            pyp.xlim(0, self.real_chunk_sizes[-1])
            pyp.ylabel('Accel.')
            pyp.xlabel('Dist (m)')
            
            pyp.subplot(212)

            pyp.fill_between(self.real_chunk_sizes, self.alts, color='blue')
            pyp.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts < -5, color='green')
            pyp.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts > 5, color='red')
            y_avg = (max(self.alts) - min(self.alts)) / 2
            bestChunk = all_chunks[scores.index(minScores)]
            pyp.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            pyp.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
            pyp.plot(self.real_chunk_sizes, self.road_speeds)
            pyp.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            pyp.xlabel('Dist (m)')
            pyp.xlim(0, self.real_chunk_sizes[-1]); pyp.ylim(0,max(self.alts))
            
            pyp.show()

            #print("{}, {}".format(self.bestScore, sum(self.bestElem)))
            file_out.write("{},{},{}\n".format(it,self.bestScore, minScores))

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (REPLACE)          ##
            ###################################################################
            print("{} - Positions ".format(it), end="")
            invalid_count = len([x for x in scores if x<0])
            good_elems = []
            for i in range(0, len(population)):
                if scores[i] >= 0:
                    good_elems.append(population[i])
            
            # Correction time
            temp_pop = self.createParallelPopulation(len(self.alts), invalid_count, False)
            for i in range(invalid_count):
                good_elems.append(temp_pop[i])
                print("{} ".format(i), end="")
            
            population = good_elems[:]
            print(" corrected.")

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (CORRECT)          ##
            ###################################################################
            #print("{} - Positions ".format(it), end="")
            #for i in range(0, len(population)):
            #    if scores[i] < 0:
            #        # Correction time
            #        temp_pop = self.v3_correction(population[i], all_chunks[i])
            ##        temp_pop = self.v2_correction(self.newPopulation[i],self.vehicles_db["Tesla Model X LR"]["Cons"])
            #        population[i] = temp_pop
            #        print("{} ".format(i), end="")
            #print(" corrected.")


            ###################################################################
            ##                              DOOMSDAY                         ##
            ###################################################################
            if (iPrevScore == self.bestScore):
                iNumOfConsecutiveStuck += 1
            else:
                iNumOfConsecutiveStuck = 0

            if (iNumOfConsecutiveStuck >= math.floor(0.3*num_iterations)):
                print("15 Stuck iterations. Resetting population.", end="")
                
                good_elems2 = []
                good_elems2.append(self.bestElem)

                new_pops = self.createParallelPopulation(len(self.alts), num_elems - 1, False)
                for i in range(len(new_pops)):
                    good_elems2.append(new_pops[i])

                population = good_elems2[:]
                iNumOfConsecutiveStuck = 0

                print(" DONE.")

            iPrevScore = self.bestScore


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
            bestChunk = all_chunks[scores.index(minScores)]
            self.axis0.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            self.axis0.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
            self.axis0.plot(self.real_chunk_sizes, self.road_speeds)
            self.axis0.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            self.canvas.draw()
            self.root.update()

            file_out.flush()

            ###################################################################

        #print(scores)
        self.addInfo("Best score: {} kWh".format(round(self.bestScore/3600,2)))
        file_out.close()

    def getOptimumProfileMixed(self, num_elems):
        file_out = open("tfm.out", "w")
        ###################################################
        # Creating population
        population = self.createParallelPopulation(len(self.alts), num_elems)

        # Obtain initial scores
        all_chunks = []; scoreKwhNorm = []; scoreTNorm = []
        scoreKwh, scoreSec, all_chunks = self.v3_obtainScoresByMix(population)

        # Normalize different scores before compare them
        max_kwh = max(scoreKwh); max_sec = max(scoreSec)
        for it_sc in range(0, len(scoreKwh)-1):
            if (scoreKwh[it_sc] >= 0 and scoreSec[it_sc] >= 0):
                scoreKwhNorm.append(interp(scoreKwh[it_sc],[0,max_kwh],[0,10]))
                scoreTNorm.append(interp(scoreSec[it_sc],[0,max_sec],[0,10]))
            else:
                scoreKwhNorm.append(-1)
                scoreTNorm.append(-1)

        scores = list((np.array(scoreKwhNorm)+np.array(scoreTNorm))/2)

        print(scores)
        minScores = float(min([n for n in scores if n>0], default=1000000))
        self.bestScore = minScores
        self.bestElem = deepcopy(population[scores.index(minScores)])
        print("Best score before start is {} Sec.".format(self.bestScore))
        iNumOfConsecutiveStuck = 0
        iPrevScore = self.bestScore

        num_iterations = int(self.ga_iterations.get())
        is_even = len(population)%2 == 0
        print("Is the population even? {}".format(is_even))

        self.newPopulation = []
        for it in range(0, num_iterations):

            ###################################################################
            ##                      MIX POPULATION                           ##
            ###################################################################

            # Apply normalized NGR
            q0 = self.ngr_val / (1 - (1 - self.ngr_val)**len(population))
            
            sort_scores = sorted(scores)
            sort_positions = sorted(range(len(scores)), key=lambda k: scores[k])
            ngr = []

            for sor_it in range(0, len(sort_scores)):
                ngr.append(self.ngr_val * (1 - self.ngr_val)**(sor_it))

            #print("For mixing: q0 = {}, scores:\n{}".format(q0, ngr))
            #print("{}\n{}".format(sort_scores, sort_positions))
            
            max_candidates = round(0.4 * len(population))
            if (max_candidates % 2) != 0:
                max_candidates = max_candidates - 1
            candidates = []; children = []

            # Get best candidates
            for sor_it in range(0, len(ngr)):
                if ((ngr[sor_it] > (self.ngr_val * 0.4)) or (len(candidates) < max_candidates)):
                    candidates.append(population[sort_positions[sor_it]])
                    #print("Added position: {} -> {}".format(sort_positions[sor_it], ngr[sor_it]))

            # Get new children
            for pos in range(0, max_candidates, 2):
                dist = np.random.uniform()
                childA = []; childB = []

                for pair in list(zip(candidates[pos], candidates[pos+1])):
                    childA.append(dist*pair[0] + (1-dist)*pair[1])
                    childB.append((1-dist)*pair[0] + dist*pair[1])
                    children.append(childA); children.append(childB)

            # Replace worst population
            for pos in range(0, max_candidates):
                population[len(ngr) - 1 - pos] = children[pos]

            self.newPopulation[:] = population

            ###################################################################
            ##                          APPLY MUTATION                       ##
            ###################################################################

            # self.mutate_v2(int(np.random.rand()*len(self.newPopulation)), self.newPopulation)
            for i in range(0, len(population)):
                if (np.random.rand() > 0.9):
                    self.mutate_v3(i, population)

            ###################################################################
            ##                         GET BEST SCORE                        ##
            ###################################################################

            population[:] = self.newPopulation
            self.newPopulation = []
            all_chunks = []; scoreKwhNorm = []; scoreTNorm = []
            scoreKwh, scoreSec, all_chunks = self.v3_obtainScoresByMix(population)

            # Normalize different scores before compare them
            max_kwh = max(scoreKwh); max_sec = max(scoreSec)
            for it_sc in range(0, len(population)):
                if (scoreKwh[it_sc] >= 0 and scoreSec[it_sc] >= 0):
                    scoreKwhNorm.append(interp(scoreKwh[it_sc],[0,max_kwh],[0,10]))
                    scoreTNorm.append(interp(scoreSec[it_sc],[0,max_sec],[0,10]))
                else:
                    scoreKwhNorm.append(-1)
                    scoreTNorm.append(-1)

            scores = list((np.array(scoreKwhNorm)+np.array(scoreTNorm))/2)
            #scores, all_chunks = self.v3_obtainScoresByTime(population)
            print(scores, end='')
            minScores = min([n for n in scores if n>0], default=1000000)
            min_index = scores.index(minScores)
            print(" {} ¿{} < {}?".format(minScores, minScores, self.bestScore))
            if (minScores < self.bestScore):
                print("Update: {}, pos of. {}".format(minScores, scores.index(minScores)))
                self.bestScore = minScores
                self.bestElem = deepcopy(population[scores.index(minScores)])

            window= np.ones(int(10))/float(10)
            rl_avg = np.convolve(self.bestElem[0], window, 'same')

            pyp.close('all')
            pyp.figure()
            
            pyp.subplot(211)
            pyp.plot(self.real_chunk_sizes, self.bestElem[0], lw=0.5, color='black')
            pyp.plot(self.real_chunk_sizes, rl_avg, lw=2.0, color='blue')
            pyp.hlines(0, 0, self.real_chunk_sizes[-1], colors='black', linestyles='--')
            pyp.xlim(0, self.real_chunk_sizes[-1])
            pyp.ylabel('Accel.')
            pyp.xlabel('Dist (m)')
            
            pyp.subplot(212)

            pyp.fill_between(self.real_chunk_sizes, self.alts, color='blue')
            pyp.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts < -5, color='green')
            pyp.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts > 5, color='red')
            y_avg = (max(self.alts) - min(self.alts)) / 2
            bestChunk = all_chunks[scores.index(minScores)]
            pyp.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            pyp.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
            pyp.plot(self.real_chunk_sizes, self.road_speeds)
            pyp.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            pyp.xlabel('Dist (m)')
            pyp.xlim(0, self.real_chunk_sizes[-1]); pyp.ylim(0,max(self.alts))
            
            pyp.show(False)

            #print("{}, {}".format(self.bestScore, sum(self.bestElem)))
            file_out.write("{},{},{}\n".format(it,self.bestScore, minScores))

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (REPLACE)          ##
            ###################################################################
            print("{} - Positions ".format(it), end="")
            invalid_count = len([x for x in scores if x<0])
            good_elems = []
            for i in range(0, len(population)):
                if scores[i] >= 0:
                    good_elems.append(population[i])
            
            # Correction time
            temp_pop = self.createParallelPopulation(len(self.alts), invalid_count, False)
            for i in range(invalid_count):
                good_elems.append(temp_pop[i])
                print("{} ".format(i), end="")
            
            population = good_elems[:]
            print(" corrected.")

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (CORRECT)          ##
            ###################################################################
            #print("{} - Positions ".format(it), end="")
            #for i in range(0, len(population)):
            #    if scores[i] < 0:
                    # Correction time
            #        temp_pop = self.v3_correction(population[i], all_chunks[i])
            #        temp_pop = self.v2_correction(self.newPopulation[i],self.vehicles_db["Tesla Model X LR"]["Cons"])
            #        population[i] = temp_pop
            #        print("{} ".format(i), end="")
            #print(" corrected.")


            ###################################################################
            ##                              DOOMSDAY                         ##
            ###################################################################
            if (iPrevScore == self.bestScore):
                iNumOfConsecutiveStuck += 1
            else:
                iNumOfConsecutiveStuck = 0

            if (iNumOfConsecutiveStuck >= math.floor(0.3*num_iterations)):
                print("15 Stuck iterations. Resetting population.", end="")
                
                good_elems2 = []
                good_elems2.append(self.bestElem)

                new_pops = self.createParallelPopulation(len(self.alts), num_elems-1,False)
                for i in range(len(new_pops)):
                    good_elems2.append(new_pops[i])

                population = good_elems2[:]
                iNumOfConsecutiveStuck = 0

                print(" DONE.")

            iPrevScore = self.bestScore

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
            bestChunk = all_chunks[scores.index(minScores)]
            self.axis0.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            self.axis0.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
            self.axis0.plot(self.real_chunk_sizes, self.road_speeds)
            self.axis0.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            self.canvas.draw()
            self.root.update()

            file_out.flush()

            ###################################################################

        #print(scores)
        self.addInfo("Best score: {}/10 ({} kWh, {} Min.).".format(self.bestScore,round(scoreKwh[min_index]/360000), round(scoreSec[min_index]/60)))
        file_out.close()

        print("Best option: {}/{}".format(self.real_chunk_sizes, self.bestElem))
        print("Speeds: {}".format([0]+list(x.v1 for x in bestChunk)))

    def getOptimumProfileTime(self, num_elems):
        file_out = open("tfm.out", "w")
        ###################################################
        # Creating population
        population = self.createParallelPopulation(len(self.alts), num_elems)

        # Obtain initial scores
        all_chunks = []
        scores, all_chunks = self.v3_obtainScoresByTime(population)

        print(scores)
        minScores = float(min([n for n in scores if n>0], default=1000000))
        self.bestScore = minScores
        self.bestElem = deepcopy(population[scores.index(minScores)])
        print("Best score before start is {} Sec.".format(self.bestScore))
        iNumOfConsecutiveStuck = 0
        iPrevScore = self.bestScore

        y_avg = (max(self.alts) - min(self.alts)) / 4
        bestChunk = all_chunks[scores.index(minScores)]
        self.axis0.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
        self.axis0.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
        self.axis0.plot(self.real_chunk_sizes, self.road_speeds)
        self.axis0.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
        self.canvas.draw()

        num_iterations = int(self.ga_iterations.get())
        is_even = len(population)%2 == 0
        print("Is the population even? {}".format(is_even))

        self.newPopulation = []
        for it in range(0, num_iterations):

            ###################################################################
            ##                      MIX POPULATION                           ##
            ###################################################################

            # Apply normalized NGR
            q0 = self.ngr_val / (1 - (1 - self.ngr_val)**len(population))
            
            sort_scores = sorted(scores)
            sort_positions = sorted(range(len(scores)), key=lambda k: scores[k])
            ngr = []

            for sor_it in range(0, len(sort_scores)):
                ngr.append(self.ngr_val * (1 - self.ngr_val)**(sor_it))

            #print("For mixing: q0 = {}, scores:\n{}".format(q0, ngr))
            #print("{}\n{}".format(sort_scores, sort_positions))
            
            max_candidates = round(0.4 * len(population))
            if (max_candidates % 2) != 0:
                max_candidates = max_candidates - 1
            candidates = []; children = []

            # Get best candidates
            for sor_it in range(0, len(ngr)):
                if ((ngr[sor_it] > (self.ngr_val * 0.4)) or (len(candidates) < max_candidates)):
                    candidates.append(population[sort_positions[sor_it]])
                    #print("Added position: {} -> {}".format(sort_positions[sor_it], ngr[sor_it]))

            # Get new children
            for pos in range(0, max_candidates, 2):
                dist = np.random.uniform()
                childA = []; childB = []

                for pair in list(zip(candidates[pos], candidates[pos+1])):
                    childA.append(dist*pair[0] + (1-dist)*pair[1])
                    childB.append((1-dist)*pair[0] + dist*pair[1])
                    children.append(childA); children.append(childB)

            # Replace worst population
            for pos in range(0, max_candidates):
                population[len(ngr) - 1 - pos] = children[pos]

            self.newPopulation[:] = population

            ###################################################################
            ##                          APPLY MUTATION                       ##
            ###################################################################

            # self.mutate_v2(int(np.random.rand()*len(self.newPopulation)), self.newPopulation)
            for i in range(0, len(population)):
                if (np.random.rand() > 0.9):
                    self.mutate_v3(i, population)

            ###################################################################
            ##                         GET BEST SCORE                        ##
            ###################################################################

            population[:] = self.newPopulation
            self.newPopulation = []

            scores, all_chunks = self.v3_obtainScoresByTime(population)
            print(scores, end='')
            minScores = min([n for n in scores if n>0], default=1000000)
            print(" {} ¿{} < {}?".format(minScores, minScores, self.bestScore))
            if (minScores < self.bestScore):
                print("Update: {}, pos of. {}".format(minScores, scores.index(minScores)))
                self.bestScore = minScores
                self.bestElem = deepcopy(population[scores.index(minScores)])

            window= np.ones(int(10))/float(10)
            rl_avg = np.convolve(self.bestElem[0], window, 'same')

            pyp.close('all')
            pyp.figure()
            
            pyp.subplot(211)
            pyp.plot(self.real_chunk_sizes, self.bestElem[0], lw=0.5, color='black')
            pyp.plot(self.real_chunk_sizes, rl_avg, lw=2.0, color='blue')
            pyp.hlines(0, 0, self.real_chunk_sizes[-1], colors='black', linestyles='--')
            pyp.xlim(0, self.real_chunk_sizes[-1])
            pyp.ylabel('Accel.')
            pyp.xlabel('Dist (m)')
            
            pyp.subplot(212)

            pyp.fill_between(self.real_chunk_sizes, self.alts, color='blue')
            pyp.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts < -5, color='green')
            pyp.fill_between(self.real_chunk_sizes, self.alts, where=self.np_alts > 5, color='red')
            y_avg = (max(self.alts) - min(self.alts)) / 2
            bestChunk = all_chunks[scores.index(minScores)]
            pyp.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            pyp.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
            pyp.plot(self.real_chunk_sizes, self.road_speeds)
            pyp.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            pyp.xlabel('Dist (m)')
            pyp.xlim(0, self.real_chunk_sizes[-1]); pyp.ylim(0,max(self.alts))
            
            pyp.show(False)

            #print("{}, {}".format(self.bestScore, sum(self.bestElem)))
            file_out.write("{},{},{}\n".format(it,self.bestScore, minScores))

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (REPLACE)          ##
            ###################################################################
            print("{} - Positions ".format(it), end="")
            invalid_count = len([x for x in scores if x<0])
            good_elems = []
            for i in range(0, len(population)):
                if scores[i] >= 0:
                    good_elems.append(population[i])

            # Correction time
            temp_pop = self.createParallelPopulation(len(self.alts), invalid_count, False)
            for i in range(invalid_count):
                good_elems.append(temp_pop[i])
                print("{} ".format(i), end="")

            population = good_elems[:]
            print(" corrected.")

            ###################################################################
            ##                  CORRECTION OF INDIVIDUALS (CORRECT)          ##
            ###################################################################
            #print("{} - Positions ".format(it), end="")
            #for i in range(0, len(population)):
            #    if scores[i] < 0:
            #        # Correction time
            #        temp_pop = self.v3_correction(population[i], all_chunks[i])
            #        temp_pop = self.v2_correction(self.newPopulation[i],self.vehicles_db["Tesla Model X LR"]["Cons"])
            #        population[i] = temp_pop
            #        print("{} ".format(i), end="")
            #print(" corrected.")


            ###################################################################
            ##                              DOOMSDAY                         ##
            ###################################################################
            if (iPrevScore == self.bestScore):
                iNumOfConsecutiveStuck += 1
            else:
                iNumOfConsecutiveStuck = 0

            if (iNumOfConsecutiveStuck >= math.floor(0.3*num_iterations)):
                print("15 Stuck iterations. Resetting population.", end="")
                
                good_elems2 = []
                good_elems2.append(self.bestElem)

                new_pops = self.createParallelPopulation(len(self.alts), num_elems-1,False)
                for i in range(len(new_pops)):
                    good_elems2.append(new_pops[i])

                population = good_elems2[:]
                iNumOfConsecutiveStuck = 0

                print(" DONE.")

            iPrevScore = self.bestScore


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
            y_avg = (max(self.alts) - min(self.alts)) / 4
            bestChunk = all_chunks[scores.index(minScores)]
            self.axis0.plot(self.real_chunk_sizes, list(map(lambda x: x * (y_avg/2) + y_avg, self.bestElem))[0], 'y')
            self.axis0.plot(self.real_chunk_sizes, [0]+list(x.v1 for x in bestChunk))
            self.axis0.plot(self.real_chunk_sizes, self.road_speeds)
            self.axis0.hlines(y_avg, min(self.real_chunk_sizes), max(self.real_chunk_sizes),'k')
            #self.axis1.set_xlim(0, len(self.bestElem)); self.axis1.set_ylim(0,1)
            self.canvas.draw()
            #print([0]+list(x.v1 for x in bestChunk))

            file_out.flush()

            ###################################################################

        #print(scores)
        self.addInfo("Best score: {} M.".format(round(self.bestScore/60,2)))
        file_out.close()

    #def createPopulation(self, shape):
    #    pops = []
    #    print("Creating population...", end='', flush=True)
    #    while (len(pops) < 15):
    #        candidate = self.createSubject(shape)
    #        if (self.v2_score(candidate[0], self.vehicles_db["Tesla Model X LR"]["Cons"]) != -1):
    #            pops.append(candidate[0])
    #            print(" {}".format(len(pops)), end='', flush=True)
    #    print("")
    #    return pops

    def createParallelPopulation(self, shape, num_of_elems=30, verbose=True):
        pops = []
        self.pool = mp.Pool(mp.cpu_count()-1)
        if verbose:
            print("Creating population...", end='', flush=True)
        while (len(pops) < num_of_elems):
            createSubjectsS=partial(v3_create_subjects_par, profile=self.alts, real_chunk_sizes=self.real_chunk_sizes, vehicle_used=self.vehicles_db[self.vehicle_used.get()], roads=self.road_speeds)
            candidates = self.pool.map(createSubjectsS,list(range(30)))
            for elem in candidates:
                if (elem[0] > 0):
                    pops.append(elem[1])
                    if verbose:
                        print(" {}-{}".format(len(pops), elem[0]), end='', flush=True)
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
        scores = []; chunks = []
        

        for elem in population:
            lcl_score, lcl_chunk = self.v3_score(elem)
            scores.append(lcl_score)
            chunks.append(lcl_chunk)
        
        return scores, chunks

    def v3_obtainScoresByTime(self, population):
        scores = []; chunks = []

        for elem in population:
            lcl_score, lcl_chunk = self.v3_scoreByTime(elem)
            scores.append(lcl_score)
            chunks.append(lcl_chunk)

        return scores, chunks

    def v3_obtainScoresByMix(self, population):
        scoresEle = []; scoresT = []; chunks = []

        for elem in population:
            lcl_scoreEle, lcl_scoreT, lcl_chunk = self.v3_scoreByMix(elem)
            scoresEle.append(lcl_scoreEle)
            scoresT.append(lcl_scoreT)
            chunks.append(lcl_chunk)
        
        return scoresEle, scoresT, chunks

    def v3_score(self, candidate):
        chunks = []; cons = 0

        for i in range(0, len(self.alts) - 1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/(self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])) * 100

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
            #if chunks[-1].est_cons[0] > 0:
            cons += chunks[-1].est_cons[0]

        if (not self.v3_checkValid(chunks)):
            return (-1, chunks)
        
        return (cons, chunks)

    def v3_scoreByTime(self, candidate):
        chunks = []; cons = 0

        for i in range(0, len(self.alts)-1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/(self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])) * 100

            if i==0:
                chunks.append(Chunk(0, candidate[0][0], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))
            else:
                chunks.append(Chunk(chunks[-1].v1, candidate[0][i], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))
            
            d = (chunks[-1].v0**2) + (2*chunks[-1].accel*chunks[-1].space)
            time1 = ((-1 * chunks[-1].v0) - cmath.sqrt(d)) / chunks[-1].accel
            time2 = ((-1 * chunks[-1].v0) + cmath.sqrt(d)) / chunks[-1].accel

            chunks[-1].v1 = math.sqrt(max(0,d))
            chunks[-1].est_time_s = abs((chunks[-1].v1 - chunks[-1].v0) / chunks[-1].accel)

            cons += chunks[-1].est_time_s

        if (not self.v3_checkValid(chunks)):
            #print("Check correctness failed")
            return (-1, chunks)

        return (cons, chunks)

    def v3_scoreByMix(self, candidate):
        chunks = []; consEle = 0; consT = 0

        for i in range(0, len(self.alts)-1):
            lcl_slope = ((self.alts[i+1] - self.alts[i])/(self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])) * 100

            if i==0:
                chunks.append(Chunk(0, candidate[0][0], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))
            else:
                chunks.append(Chunk(chunks[-1].v1, candidate[0][i], lcl_slope, (self.real_chunk_sizes[i+1] - self.real_chunk_sizes[i])))
            
            chunks[-1].v1 = math.sqrt(max(0,(chunks[-1].v0**2) + (2*chunks[-1].accel*chunks[-1].space)))
            chunks[-1].est_time_s = abs((chunks[-1].v1 - chunks[-1].v0) / chunks[-1].accel)
            chunks[-1].calculate_CPEM_kwh_pro(self.vehicles_db[self.vehicle_used.get()])

            consEle += chunks[-1].est_cons[0]
            consT += chunks[-1].est_time_s

        if (not self.v3_checkValid(chunks)):
            return(-1, -1, chunks)

        return (consEle, consT, chunks)


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
        
        #if (not self.v2_checkValid(chunks)):
            #print(profile)
        #    return -1

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


            #if (self.v2_checkValid(chunks)):
            #    break

            attempts += 1

        return new_profile

    def v3_correction(self, profile, chunks):
        """Corrects an element of the population

        Args:
            profile ([ndarray]): Profile of the element to be corrected.
            chunks([list]): Chunks where the correction should be made.

        The correction will be made in those chunks where the computed v1
        speed is greater than the road limit.

        Return:
            ([list]): Corrected element
        """

        new_profile = profile[:]

        for i in range(len(chunks) - 1):
            if (chunks[i].v1 > self.road_speeds[i]):
                # Moment to try the recovery. Soften the acceleration performed
                new_profile[0][i] = new_profile[0][i]*0.9
                tmp_score, tmp_chunks = self.v3_score(new_profile)
                
                while (tmp_chunks[i].v1 > self.road_speeds[i]):
                    new_profile[0][i] = new_profile[0][i]-0.05
                    tmp_score, tmp_chunks = self.v3_score(new_profile)
                
                if (tmp_score > 0):
                    # Element corrected
                    return new_profile

        # In case we end here, then best-effort has been made ¿without success?
        return new_profile

    # In this function, it has to be checked different facts:
    #   - In any moment the v1 speed is higher than the road limit.
    #   - The vehicle is at least at half of the speed limit.
    def v3_checkValid(self, chunks):
        for i in range(len(chunks)):
            if (chunks[i].v1 > self.road_speeds[i][0]):
                return False
            elif (i > 10 and self.road_speeds[i][0] > 80 and self.road_speeds[i-1][0] > 80 and chunks[i].v1 < self.road_speeds[i][0]/4):
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

    def mutate_v3(self, pos, population):
        mut_pos = round(np.random.uniform(0, len(population)-1))
        population[pos][0][mut_pos] = np.random.uniform()

def clamp(n, minn, maxn): return min(max(n, minn), maxn) 

def main():
    my_app = TFM_Application(width=800, height=512)
    return 0


if __name__ == "__main__":
    main()
