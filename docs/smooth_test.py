#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Ejemplo de uso de la función audiotools/smoothSpectrum.py
    para el suavizado de respuestas en frecuencia.
    
    Uso:  python smooth_test.py altavoz.frd
"""

# Para que este script pueda estar fuera de ~/audiotools
import os
import sys
HOME = os.path.expanduser("~")
sys.path.append(HOME + "/audiotools")
# modulos de audiotools:
try:
    import utils
    import pydsd
except:
    raise ValueError("rew2fir.py necesita https://githum.com/AudioHumLab/audiotools")
    sys.exit()

from matplotlib import pyplot as plt
from smoothSpectrum import smoothSpectrum as smooth
import numpy as np

# Lee el nombre de archivo .frd
if len(sys.argv) == 1:
    print __doc__
    sys.exit() 
try:
    fname = sys.argv[1]
    # Lee el contenido del archivo .frd
    FR = utils.readFRD(fname)
except:
    print "No se puede leer " + fname
    sys.exit()

frec = FR[:, 0]     # array de frecuencias
mag  = FR[:, 1]     # array de magnitudes

# Ploteo sin suavizar
plt.semilogx(frec, mag , label="raw")

# Ploteos de la magnitud SUAVIZADA 1/9 1/24 (se pintan desplazados -10 dBs)
gainStep = -10
for Noct in [24]:

    print "suavizando 1/" + str(Noct) + " oct ... .. ."
    plt.semilogx(frec, gainStep + smooth(mag, frec, Noct),
                 label="1/"+str(Noct)+" oct" )
    gainStep -= 10

    print "suavizado variable 1/" + str(Noct) + " oct ... .. ."
    plt.semilogx(frec, gainStep + smooth(mag, frec, Noct, f0=250, Tspeed="slow"),
                 label="1/"+str(Noct)+" oct variable" )
    gainStep -= 10

# Ajustes de la gráfica
promedio = np.average(mag)
plt.ylim(promedio-50, promedio+10)
plt.xlim(20, 20000)
plt.grid()
plt.legend()
plt.show()
