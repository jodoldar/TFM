#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from tkinter import *
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


import time
import json
import scipy
import numpy as np
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


class TFM_Application():
    def __init__(self, width=600, height=400):
        self.root = Tk()

        self.origin = StringVar(); self.origin.set("39.462160,-0.324177")
        self.destination = StringVar(); self.destination.set("39.441699,-0.595555")
        self.figure = Figure(figsize= ((width-160)/100, 3.45), dpi=100)
        self.axis0 = self.figure.add_axes((0.01, 0.01, 0.98, 0.99), frameon=True)
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        
        # Initialization of the window
        self.root.geometry("{}x{}".format(width, height))
        self.root.resizable(width=False, height=False)
        self.root.title('Route calculator')

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Left Column
        self.leftFrame = Frame(self.root, bg='beige', width=150, height=400)
        self.leftFrame.grid(row=0, column=0, sticky="ns")

        # Center Zone
        self.centerFrame = Frame(self.root, bg='beige', width=450, height=400)
        self.centerFrame.grid(row=0, column=1, sticky="nsew")

        # Origin point
        self.origin_p_lab = ttk.Label(self.leftFrame, text='Origen:')
        self.origin_p = ttk.Entry(self.leftFrame, textvariable=self.origin, width=25)
        self.origin_p_lab.grid(column=0, row=0)
        self.origin_p.grid(column=0, row=1, sticky="we")

        # Detination point
        self.dest_p_lab = ttk.Label(self.leftFrame, text='Destino: ')
        self.dest_p = ttk.Entry(self.leftFrame, textvariable=self.destination, width=15)
        self.dest_p_lab.grid(column=0, row=2)
        self.dest_p.grid(column=0, row=3, sticky="we")

        # Calculation button
        self.calc_button = ttk.Button(self.leftFrame, text='Cálculo', command=self.getRouteProfile)
        self.calc_button.grid(column=0, row=5, sticky="we")

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

        # Canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.centerFrame)
        self.canvas.get_tk_widget().grid(column=0, row=4,sticky="nsew")
        self.canvas.draw()

        toolbarFrame = Frame(self.centerFrame)
        toolbarFrame.grid()
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbarFrame)
        self.toolbar.grid()
        self.toolbar.update()

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

        altitudes = []
        inclination = []

        try:
            api_response = api_instance.route_get([pointA,pointB], False, key, locale=locale, vehicle=vehicle, elevation=elevation, instructions=instructions)
            
            print("Info received: {}".format(api_response.info))
            text_info = "Nº of paths: {}\n".format(len(api_response.paths))
            text_info += "Distance: {:.2f} km.\nTime: {:.2f} min.\nTotal points: {}\n".format(api_response.paths[0].distance/1000, api_response.paths[0].time/60000,len(api_response.paths[0].points.coordinates))
            for coordinate in api_response.paths[0].points.coordinates:
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
        neutro = scipy.zeros(len(inclination))

        x_axis = np.arange(0,len(altitudes),1)
        np_alts = np.array(inclination)
        new_inc = np.sum(np_alts.reshape(-1,4), axis=1)
        #print(new_inc)
        sampled_inc = np.repeat(new_inc, 4)
        #print(sampled_inc)

        self.axis0.plot(altitudes, 'gx')
        self.axis0.fill_between(x_axis, altitudes, color='blue')
        self.axis0.fill_between(x_axis, altitudes, where=sampled_inc<neutro, color='green')
        self.axis0.fill_between(x_axis, altitudes, where=sampled_inc>neutro, color='red')
        self.axis0.set_xlim(0, len(altitudes)); self.axis0.set_ylim(0,max(altitudes))
        self.axis0.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        self.axis0.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        self.canvas.draw()

        self.text_info.delete("1.0", END)
        self.text_info.insert("1.0", text_info)

def main():
    my_app = TFM_Application(width=800, height=512)
    return 0


if __name__ == "__main__":
    main()
