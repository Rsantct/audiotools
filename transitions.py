#!/usr/env/python
# -*- coding: utf-8 -*-

import numpy as np
from matplotlib import pyplot as plt

def logTransition(f, f0, speed="medium"):
    """
    +1  _______
               \
                \
     0           \______
               f0        
        <-- semilog f -->

    Proporciona una transición, con la apariencia del esquema de arriba, útil para 
    aplicar un efecto sobre la representación logarítmica de un semiespectro DFT.
    
    'speed' (slow, mid, fast) define la velocidad de la transición.
    
    Ejecutando la función ejemplo_logTransition() se muestra un gráfica ilustrativa.
    
    """
    speeds = { "slow":0.5, "medium":1.2, "fast":3.0}
    speed = speeds[speed]
    if f0 < min(f) or f0 <= 0:
        return np.zeros(len(f))
    if f0 > max(f):
        return np.ones(len(f))
    return 1 / ( 1 + (f/f0)**(2**speed) )

def ejemplo_logTransition():

    frecs = np.linspace(0, 20000, 2**12)
    mags  = np.ones( len(frecs) )
    print "Creamos un semiespectro de frecuencias plano, de 4K bins"

    f0 = 100
    print "Frecuencia de transición f0: ", f0, "Hz"

    # Gráficas de la transición del efecto
    for speed in ["slow", "medium", "fast"]:
        efecto = logTransition(frecs, f0, speed)
        plt.semilogx( frecs, efecto , label="speed " + str(speed) )

    plt.xlim(20,20000)
    plt.legend()
    plt.title("transition.logTransition at f0 = " + str(f0))
    plt.show()
