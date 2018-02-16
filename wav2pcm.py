#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    OjO: Los impulsos IR .wav de REW vienen con el pico desplazado
         tantas muestras como el valor de la Fs del wav.
         por tanto haremos una doble conversion time > spectrum > time
"""

import sys
import numpy as np
from scipy.io import wavfile
from scipy import signal
from matplotlib import pyplot as plt
import pydsd as dsd

def savepcm32(a):
    # guardamos en raw binary float32
    f = open(fout, 'wb')
    a.astype('float32').tofile(f)
    f.close()

if __name__ == "__main__":

    # taps de salida deseados
    m = 2 ** 15 

    # Archivos de entrada y de salida
    fin  = sys.argv[1]
    fout = fin.replace(".wav", ".pcm")

    # Leemos el impulso de entrada imp1
    fs, imp1 = wavfile.read(fin)
    
    # normalizamos el impulso ya que REW lo ha normalizado a +- 32768
    imp1 = imp1.astype('float32') / 32768.0

    # Espectro completo
    h = np.fft.fft(imp1)
    # Réplica del espectro completo en fase mínima
    hmp = dsd.minphsp(h)

    # Convertimos el espectro completo mp en un IR, se toma la parte real.
    imp2 = np.fft.ifft( hmp )
    imp2 = np.real(imp2)

    # Lo cortamos a la longitud deseada y aplicamos una ventana:
    imp2 = dsd.semiblackman(m) * imp2[:m]

    # Y lo guardamos en formato pcm float 32
    savepcm32(imp2)
   
