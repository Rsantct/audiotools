#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1beta
    
    Recorta un FIR mediante una reconstrucción completa 
         time domain > spectrum > time domain
    
"""

import sys
import numpy as np
import pydsd as dsd
import utils

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()

    # taps de salida deseados (PDTE PASAR COMO ARGUMENTO)
    m = 2 ** 15 

    # Archivos de entrada y de salida
    fin  = sys.argv[1]
    fout = fin.replace(".wav", ".pcm")

    # Leemos el impulso de entrada imp1
    fs, imp1 = utils.readWAV16(fin)
    
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
    utils.savePCM32(raw=imp2, fout=fout)
    print "Guardado en:", fout
   
