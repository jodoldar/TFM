db = {
    
    "Tesla Model X LR": {
        "Capacity": 100, #KWh
        "Cons": [14.5, 28.8], #KWh/100km
        "ColdCons": [20.9, 24.4, 28.8], #KWh/100km
        "MildCons": [14.5, 18.3, 22.6], #KWh/100km
        "Range": 460, #km
        "Power": 350, #kW
        "Accel": 4.6, #sec 0-100km/h
        "Weight": 2459 #Kg
    },
    
    
    "Tesla Model S LR": {
        "Capacity": 100, #KWh
        "Cons": [12.7, 25.9], #KWh/100km
        "ColdCons": [18.8, 21.6, 25.0], #KWh/100km
        "MildCons": [12.7, 15.8, 19.4], #KWh/100km
        "Range": 525, #km
        "Power": 350, #kW
        "Accel": 3.8, #sec 0-100km/h
        "Weight": 2215 #Kg
    },
    
    
    "Tesla Model 3 LR4": {
        "Capacity":75, #KWh
        "Cons": [10.8, 21.8], #KWh/100km
        "ColdCons": [16.4, 18.7, 21.8], #KWh/100km
        "MildCons": [10.8, 13.5, 16.6], #KWh/100km
        "Range": 475, #km
        "Power": 258, #kW
        "Accel": 4.6, #sec 0-100km/h
        "Weight": 1847 #Kg
    },
    
    
    "Hyundai Kona": {
        "Capacity": 67, #KWh
        "Cons": [10.8, 22.9], #KWh/100km
        "ColdCons": [16.4, 19.1, 22.9], #KWh/100km
        "MildCons": [10.8, 13.9, 17.5], #KWh/100km
        "Range": 400, #km
        "Power": 150, #kW
        "Accel": 7.6, #sec 0-100km/h
        "Weight": 1685 #Kg
    },
    
    
    "Jaguar I-Pace": {
        "Capacity": 90, #KWh
        "Cons": [15.3, 31.4], #KWh/100km
        "ColdCons": [21.7, 26.1, 31.4], #KWh/100km
        "MildCons": [15.3, 19.7, 24.9], #KWh/100km
        "Range": 380, #km
        "Power": 294, #kW
        "Accel": 4.8, #sec 0-100km/h
        "Weight": 2133 #Kg
    }


}


point_bias = {
    "5": 5,
    "10": 10,
    "15": 15,
    "20": 20,
    "50": 50,
    "100" : 100
}

ga_method = {
    "+ Consumos": 0,
    "+ Tiempo": 1,
    "Ambos": 2
}