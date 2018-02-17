#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1
    visor de impulsos IR wav
    
"""
import sys
import numpy as np
from scipy.io import wavfile
from scipy import signal
from matplotlib import pyplot as plt

if __name__ == "__main__":

    files  = sys.argv[1:]
    
    for file in files:

        fs, imp = wavfile.read(file)
        fny = fs/2.0
    
        # el .wav es int16 normalized 
        imp = imp.astype('float32') / 32768.0

        # bins de frecs logspaciadas que resolverá freqz
        w1 = 1 / fny * (2 * np.pi)
        w2 = 2 * np.pi
        bins = np.geomspace(w1, w2, 500)

        # whole=False hasta Nyquist
        w, h = signal.freqz(imp, worN=bins, whole=False)
        # frecuencias trasladadas a Fs
        freqs = w / np.pi * fny
        magdB = 20 * np.log10(abs(h))
        plt.plot(freqs, magdB)

    plt.xscale('log')  
    plt.xlim(10,20000)
    plt.ylim(-30,5)  
    plt.show()

   
