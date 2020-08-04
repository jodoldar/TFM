import math

class Chunk:    
    def __init__(self, v0=0, accel=0, slope=0, space=1):
        self.v0 = v0
        self.v1 = 0
        self.accel = accel
        self.slope = slope
        self.est_time_s = 0
        self.est_cons = 0
        self.space = space
    
    def calculate_v1(self, space, cruise_accel, max_speed=120):
        if (self.v0 == 0):
            est_time = space / (max_speed / 4)
            self.est_time_s = space / ((max_speed / 3.6) / 4)
        else:
            est_time = space / self.v0
            self.est_time_s = space / (self.v0 / 3.6)
        
        if (self.slope > 2):
            if (self.accel > (cruise_accel + 0.1)):
                # La velocidad sube
                self.v1 = self.v0 + (self.accel - (cruise_accel + 0.1)) * est_time
            else:
                # La velocidad baja
                self.v1 = max(0, self.v0 - (self.accel - (cruise_accel + 0.1)) * est_time)
        elif (self.slope > 5):
            if (self.accel > (cruise_accel + 0.2)):
                # La velocidad sube
                self.v1 = self.v0 + (self.accel - (cruise_accel + 0.2)) * est_time
            else:
                # La velocidad baja
                self.v1 = max(0, self.v0 - (self.accel - (cruise_accel + 0.2)) * est_time)
        elif (self.slope > 10):
            if (self.accel > (cruise_accel + 0.25)):
                # La velocidad sube
                self.v1 = self.v0 + (self.accel - (cruise_accel + 0.25)) * est_time
            else:
                # La velocidad baja
                self.v1 = max(0, self.v0 - (self.accel - (cruise_accel + 0.25)) * est_time)
        elif (self.slope < -2):
            if (self.accel > (cruise_accel - 0.1)):
                # La velocidad sube
                self.v1 = self.v0 + (self.accel - max(0,(cruise_accel - 0.1))) * est_time
            else:
                # La velocidad baja
                self.v1 = max(0, self.v0 - (self.accel - max(0,(cruise_accel - 0.1))) * est_time)
        elif (self.slope < -5):
            if (self.accel > (cruise_accel - 0.2)):
                # La velocidad sube
                self.v1 = self.v0 + (self.accel - max(0,(cruise_accel - 0.2))) * est_time
            else:
                # La velocidad baja
                self.v1 = max(0, self.v0 - (self.accel - max(0,(cruise_accel - 0.2))) * est_time)
        elif (self.slope < -10):
            if (self.accel > (cruise_accel - 0.25)):
                # La velocidad sube
                self.v1 = self.v0 + (self.accel - max(0,(cruise_accel - 0.25))) * est_time
            else:
                # La velocidad baja
                self.v1 = max(0, self.v0 - (self.accel - max(0,(cruise_accel - 0.25))) * est_time)
        else:
            self.v1 = max(0, self.v0 + (self.accel - cruise_accel) * est_time)

    def calculate_CPEM_kwh(self, veh_info):
        p_wheel = veh_info["Weight"] * self.accel

        r_roll = veh_info["Weight"] * 9.8066 * math.cos(math.radians(self.slope)) * (1.75 / 1000)*(0.0328 * self.v1 + 4.575)

        r_aer = 0.5 * 1.2256 * 2.3316 * 0.28 * math.pow(self.v1,2)

        r_gr = veh_info["Weight"] * 9.8066 * math.sin(math.radians(self.slope))

        force = (p_wheel + r_roll + r_aer + r_gr) * self.v1

        self.est_cons = (force / 3600) * self.est_time_s