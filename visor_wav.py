#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
from scipy.io import wavfile
from scipy import signal
from matplotlib import pyplot as plt

if __name__ == "__main__":

    fin  = sys.argv[1]

    fs, x = wavfile.read(fin)
    
    x = x.astype('float32') / 32768.0

    w, h = signal.freqz(x, worN=2**13, whole=False) 

    freqs = w / np.pi * fs/2.0
    magdB = 20 * np.log10(abs(h))
    plt.plot(freqs, magdB)
    plt.xscale('log')  
    plt.xlim(20,20000)
    #plt.xticks(x, [20, 100, 1000, 10000])  
    plt.ylim(-30,5)  
    plt.show()

   
