#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scipy import signal

# Para que este script pueda estar fuera de ~/audiotools
import os
import sys
HOME = os.path.expanduser("~")
sys.path.append(HOME + "/audiotools")
import utils
import pydsd


# PARAMETROS GLOBALES:
fs = 44100   # Frecuencia de muestreo
m  = 16386   # Longitud del impulso FIR

# 0. Partimos de una delta (espectro plano)
delta = pydsd.delta(m)

# 1. Aplicamos una curva Room Gain +6dB
gain = 6.0
imp = utils.RoomGain2impulse(delta, fs, gain)

# 2. Encadenamos filtros 'peakingEQ' ~ 'paramétricos' 
# NOTA: para filtros de alto Q > 5  y baja frecuencia <50Hz
#       usar m >= 8192 para un FIR largo.
#       (i) Observar los resultados con 'IRs_viewer.py biquads.pcm 44100'

for param in [(50,  10, -20), 
              (100, 10, -15), 
              (120, 10, -20)]:
    f0  = param[0]
    Q   = param[1]
    gdB = param[2]
    b, a = pydsd.biquad(fs=fs, f0=f0, Q=Q, type="peakingEQ", dBgain=gdB)
    imp = signal.lfilter(b, a, imp)

# 4. Guardamos el resultado
utils.savePCM32(imp, "biquads.pcm")

# 3. Convertimos a LP linear phase :-| ejem...
imp = utils.MP2LP(imp, windowed=False)

# 4. Guardamos el resultado LP
utils.savePCM32(imp, "biquads_lp.pcm")

print "(i) Observar los resultados con"
print "    'IRs_viewer.py biquads.pcm 44100'"


