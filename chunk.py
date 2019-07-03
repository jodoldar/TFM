class Chunk:    
    def __init__(self, v0=0, accel=0, slope=0):
        self.v0 = v0
        self.v1 = 0
        self.accel = accel
        self.slope = slope
        self.est_time_s = 0
    
    def calculate_v1(self, space, cruise_accel, max_speed=120):
        if (self.v0 == 0):
            est_time = space / (max_speed / 4)
            self.est_time_s = space / ((max_speed / 3.6) / 4)
        else:
            est_time = space / self.v0
            self.est_time_s = space / (self.v0 / 3.6)
        
        self.v1 = max(self.v0 + (self.accel - cruise_accel) * est_time, 0)