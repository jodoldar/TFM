#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import math
import numpy as np
import matplotlib.pyplot as plt


# Calculate max. acceleration from the 0-100 seconds
#max_accel_time = 3.8; vehicle_mass = 2215 # Tesla Model S LR
max_accel_time = 4.6; vehicle_mass = 2459 # Tesla Model X LR
#max_accel_time = 4.6; vehicle_mass = 1847 # Tesla Model 3 LR
#max_accel_time = 4.8; vehicle_mass = 2133 # Jaguar I-Pace
#max_accel_time = 7.6; vehicle_mass = 1685 # Hyundai Kona

g_const = 9.8066


ground = math.radians(20.0)

accel = 27.7778 / max_accel_time
print("Max accel is {}".format(accel))

plt.xlabel('Acceleration ($m/s^2$)')
plt.ylabel('Power (kW)')
plt.title('Power consumption depending on the acceleration')
plt.grid(True)

plt.hlines(258, 0, accel, linestyles='dashed')

for velocity in [1,5,10,15,20,25,30]: # Velocity in m/s

    values_x = []
    values_y = []

    s_plot1 = "Vel: {} m/s".format(velocity)

    for i in np.arange(0, accel, 0.1):
        p_wheel = vehicle_mass * i

        r_roll = vehicle_mass * g_const * math.cos(ground) * (1.75 / 1000)*(0.0328 * velocity * 4.575)

        r_aer = 0.5 * 1.2256 * 2.3316 * 0.28 * math.pow(velocity,2)

        r_gr = vehicle_mass * g_const * math.sin(ground)

        force = (p_wheel + r_roll + r_aer + r_gr) * velocity

        print("Acc: {}, Power: {}".format(i, force/1000))
        values_x.append(i)
        values_y.append(force/1000)

    plt.plot(values_x, values_y, label=s_plot1)

plt.legend()
plt.show()