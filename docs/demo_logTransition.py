#!/usr/env/python2
# -*- coding: utf-8 -*-

# Para que este script pueda estar fuera de ~/audiotools
import os
import sys
HOME = os.path.expanduser("~")
sys.path.append(HOME + "/audiotools")
# modulos de audiotools:
try:
    import tools
    import pydsd
except:
    raise ValueError("rew2fir.py necesita https://githum.com/AudioHumLab/audiotools")
    sys.exit()

from tools import logTransition
import numpy as np
from matplotlib import pyplot as plt

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
