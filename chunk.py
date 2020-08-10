import math
import scipy.integrate as integrate

class Chunk:    
    def __init__(self, v0=0, accel=0, slope=0, space=1):
        self.v0 = v0
        self.v1 = 0
        self.accel = accel
        self.slope = slope
        self.est_time_s = 0
        self.est_cons = 0
        self.space = space

        self.driveline_eff = 0.92
        self.elec_motor_eff = 0.91
    
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
        rad_slope = math.atan(self.slope / 100)
        avg_spd = (self.v0 + self.v1) / 2

        p_wheel = veh_info["Weight"] * self.accel

        r_roll = veh_info["Weight"] * 9.8066 * math.cos(rad_slope) * (1.75 / 1000)*(0.0328 * avg_spd + 4.575)

        r_aer = 0.5 * 1.2256 * 2.3316 * 0.28 * math.pow(avg_spd,2)

        r_gr = veh_info["Weight"] * 9.8066 * math.sin(rad_slope)

        force = (p_wheel + r_roll + r_aer + r_gr) * avg_spd

        self.est_cons = force * self.est_time_s * (1/0.9)

    def internal_CPEM_kw(self, s, veh_info):
        rad_slope = math.atan(self.slope / 100)
        avg_spd = (self.v0 + self.v1) / 2

        p_wheel = veh_info["Weight"] * self.accel

        r_roll = veh_info["Weight"] * 9.8066 * math.cos(rad_slope) * (1.75 / 1000)*(0.0328 * avg_spd + 4.575)

        r_aer = 0.5 * 1.2256 * 2.3316 * 0.28 * math.pow(avg_spd,2)

        r_gr = veh_info["Weight"] * 9.8066 * math.sin(rad_slope)

        force = (p_wheel + r_roll + r_aer + r_gr) * avg_spd

        em_est_cons = force  * (1/self.driveline_eff) * (1/self.elec_motor_eff)

        if em_est_cons < 0 and self.accel < 0:
            regen_brk_eff = 1 / math.exp(0.0411/self.accel)
            em_est_cons = em_est_cons * (1/regen_brk_eff)

        return em_est_cons


    def calculate_CPEM_kwh_pro(self, veh_info):
        self.est_cons = integrate.quad(self.internal_CPEM_kw, 0, self.est_time_s, args=veh_info)
        return self.est_cons[0]