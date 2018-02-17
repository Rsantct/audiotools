#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1
    visor de impulsos IR wav o raw (.pcm)
    
    Si se pasan impulsos raw (.pcm) se precisa pasar también la Fs
    
    Ejemplo de uso:
    
    visor_IR.py drcREW_test1.wav drcREW_test1.pcm 44100
    
"""
import sys
import numpy as np
from scipy.io import wavfile
from scipy import signal
from matplotlib import pyplot as plt

def readPCM32(fname):
    """ lee un archivo pcm float32
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype='float32', mode='r')

def readWAV16(fname):
    fs, imp = wavfile.read(fname)
    return fs, imp.astype('float32') / 32768.0
    
def lee_commandline(opcs):

    # impulsos que devolverá esta función
    IRs = []
    # archivos que leeremos
    fnames = []
    fs = 0

    for opc in opcs:
        if opc in ("-h", "-help", "--help"):
            print __doc__
            sys.exit()
            
        elif opc.isdigit():
            fs = float(opc)

        else:
            fnames.append(opc)

    # si no hay fnames
    if not fnames:
        print __doc__
        sys.exit()

    for fname in fnames:
    
        if fname.endswith('.wav'):
            fswav, imp = readWAV16(fname)
            IRs.append( (fswav, imp, fname) )
            
        else:
            if fs:
                imp = readPCM32(fname)
                IRs.append( (fs, imp, fname) )
            else:
                print __doc__
                sys.exit()
            
    return IRs
    
if __name__ == "__main__":

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()
    else:
        IRs = lee_commandline(sys.argv[1:])


    for IR in IRs:
    
        fs, imp, info = IR
        fny = fs/2.0
        l = imp.shape[0]
        info += " " + str(l)
        
        # bins de frecs logspaciadas que resolverá freqz
        w1 = 1 / fny * (2 * np.pi)
        w2 = 2 * np.pi
        bins = np.geomspace(w1, w2, 500)

        # whole=False hasta Nyquist
        w, h = signal.freqz(imp, worN=bins, whole=False)
        # frecuencias trasladadas a Fs
        freqs = w / np.pi * fny
        magdB = 20 * np.log10(abs(h))
        plt.plot(freqs, magdB,label=info)

    plt.xscale('log')  
    plt.xlim(10,20000)
    plt.ylim(-20,5)
    plt.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})
    plt.show()
