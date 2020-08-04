import numpy as np
from chunk import Chunk

def v2_create_subjects_par(it, shape, alts, consumption, real_chunk_sizes, cruise, road_speeds):
        candidate = v2_create_subject_par(shape)
        return (v2_score_par(alts, candidate[0], consumption, real_chunk_sizes, cruise, road_speeds), candidate[0])

def v2_create_subject_par(shape):
    # Creation of individual between [0.5, 0.5]
    return np.random.rand(1, shape) - 0.5

def v2_score_par(alts, profile, consumptions, real_chunk_sizes, cruise, road_speeds):
    chunks = []
    cons = 0
    for i in range(0, len(alts)-1):
        lcl_slope = ((alts[i+1] - alts[i])/(real_chunk_sizes[i+1]-real_chunk_sizes[i])) * 100
        #print("Alt1: {}, Alt2: {}, Dist: {}, Slope:{}".format(self.alts[i], self.alts[i+1], self.real_chunk_sizes[i], lcl_slope))
        if (i == 0):
            chunks.append(Chunk(0, profile[i], lcl_slope, (real_chunk_sizes[i+1]-real_chunk_sizes[i])))
            #print("Initial slope is {}".format(lcl_slope))
        else:
            chunks.append(Chunk(chunks[-1].v1, profile[i], lcl_slope, (real_chunk_sizes[i+1]-real_chunk_sizes[i])))

        # Once the chunk is created, the v1 speed is calculated
        adapt_cruise_accel = 0
        initial_spd = chunks[-1].v0
        if initial_spd < 20:
            adapt_cruise_accel = cruise['A']
        elif initial_spd < 40:
            adapt_cruise_accel = cruise['B']
        elif initial_spd < 70:
            adapt_cruise_accel = cruise['C']
        elif initial_spd < 100:
            adapt_cruise_accel = cruise['D']
        else:
            adapt_cruise_accel = cruise['E']
        
        adapt_cruise_accel = np.interp(adapt_cruise_accel, consumptions["Cons"], [0,1])

        chunks[-1].calculate_v1(real_chunk_sizes[i], adapt_cruise_accel, road_speeds[i])
        #chunks[-1].calculate_CPEM_kwh(consumptions)

        # In the case there is a negative acceleration (i.e the car is braking), there is no consumption
        if (chunks[-1].accel > 0):
            cons += np.interp(chunks[-1].accel, [0,1], consumptions["Cons"]) / chunks[-1].est_time_s
            #cons += chunks[-1].est_cons

        #print("Chunk {}. v0-> {}, v1-> {}, accel-> {}[{}], slp: {}[{}]".format(i, chunks[-1].v0, chunks[-1].v1, chunks[-1].accel, adapt_cruise_accel, chunks[-1].slope, self.real_chunk_sizes[i]))
    
    if (not v2_check_valid_par(chunks, road_speeds)):
        #print(profile)
        return -1

    return cons[0]
    
# In this function, it has to be checked different facts:
#   - In any moment the v1 speed is higher than the road limit.
def v2_check_valid_par(chunks, road_speeds):
    for i in range(len(chunks)):
        if (chunks[i].v1 > road_speeds[i]):
            #print("Profile not valid. {} is greater than {}. (v0: {}, v1: {}, accel: {}, slp:{}, dist: {}".format(chunks[i].v1, self.road_speeds[i], chunks[i].v0, chunks[i].v1, chunks[i].accel, chunks[i].slope, self.real_chunk_sizes[i]))
            return False
    return True