#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.01beta
    
    Recorta un IR mediante una reconstrucción completa 
         time domain > spectrum > time domain
    
    Uso:
        python trimIR.py IRfile.pcm -tX
        X: taps de salida (sin espacios)
    
"""

import sys
import numpy as np
import pydsd as dsd
import utils

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()

    m = 0

    for opc in sys.argv[1:]:

        if "-t" in opc:
            m = int(opc.replace('-t', ''))
            mExp = int(np.log2(m))
            if mExp - int(mExp) <> 0:
                print __doc__
                sys.exit()

        else:
            fin = opc

    if not m:
        print __doc__
        sys.exit()

    fout = str(m) + "taps_" + fin

    # Leemos el impulso de entrada imp1
    imp1 = utils.readPCM32(fin)
    
    ## Espectro completo en dominio de f
    #h = np.fft.fft(imp1)
    #
    ## Volvemos al dominio de t: convertimos el espectro completo en un IR,
    ## y se toma la parte real.
    #imp2 = np.fft.ifft(h)
    #imp2 = np.real(imp2)

    # Lo cortamos a la longitud deseada aplicando una ventana:
    imp2 = dsd.semiblackman(m) * imp1[:m]

    # Y lo guardamos en formato pcm float 32
    utils.savePCM32(raw=imp2, fout=fout)
    print "Guardado en:", fout
