#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.01beta
    
    Recorta un IR aplicando una ventana

    Uso:
        python trimIR.py IRfile.pcm -tN
        N: taps de salida potencia de 2 (sin espacios)
    
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
            if not utils.isPowerOf2(m):
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
    
    # Lo cortamos a la longitud deseada aplicando una ventana:
    imp2 = dsd.semiblackman(m) * imp1[:m]

    # Y lo guardamos en formato pcm float 32
    utils.savePCM32(raw=imp2, fout=fout)
    print "Guardado en:", fout
