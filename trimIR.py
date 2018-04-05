#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1beta
    
    Recorta un IR mediante una reconstrucción completa 
         time domain > spectrum > time domain
    
"""

import sys
import numpy as np
import pydsd as dsd
import utils

if __name__ == "__main__":

    m = 16384 # por defecto
    mK = int(np.log2(m))

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()

    for opc in sys.argv[1:]:

        if "-t" in opc:
            m = int(opc.replace('-t', ''))
            mK = int(np.log2(m))
            if mK - int(mK) <> 0:
                print __doc__
            sys.exit()

        else:
            fin = opc

    fout = str(mK) + "K_" + fin

    # Leemos el impulso de entrada imp1
    imp1 = utils.readPCM32(fin)
    
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
   
