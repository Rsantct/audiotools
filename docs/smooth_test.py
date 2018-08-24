#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Ejemplo de uso de la función utils/smooth.py
    de suavizado de respuestas en frecuencia
    obternidas con ARTA.
    
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

# array de frecuencias
frec = FR[:, 0]
# array de magnitudes
mag  = FR[:, 1]

# Ploteo sin suavizar
plt.semilogx(frec, mag , label="raw")

aten = -10
for Noct in 12, 6, 3:
    print "suavizando 1/" + str(Noct) + " oct ... .. ."
    # Ploteo de la magnitud SUAVIZADA (se pinta desplazada -10 dBs)
    plt.semilogx(frec, aten + smooth(mag, frec, Noct), label="1/"+str(Noct)+" oct" )
    aten -= 10

plt.xlim(20, 20000)
plt.ylim(-60, 10)
plt.grid()
plt.legend()
plt.show()

