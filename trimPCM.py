#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.02beta
    
    Recorta un FIR pcm float 32 aplicando una ventana

    Uso:
        python trimPCM.py  file.pcm  -tN  [-o]
        -tN: N taps de salida potencia de 2 (sin espacios)
        -o:  sobreescribe el original
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
    overwriteFile = False

    # Leemos opciones
    for opc in sys.argv[1:]:

        if opc.startswith('-t'):
            m = int(opc.replace('-t', ''))
            if not utils.isPowerOf2(m):
                print __doc__
                sys.exit()

        elif opc == '-h' or opc == '--help':
            print __doc__
            sys.exit()

        elif opc == '-o':
            overwriteFile = True
            
        else:
            fin = opc

    if not m:
        print __doc__
        sys.exit()


    if not overwriteFile:
        fout = str(m) + "taps_" + fin
    else:
        fout = fin
        
    # Leemos el impulso de entrada imp1
    imp1 = utils.readPCM32(fin)
    
    # Lo cortamos a la longitud deseada aplicando una ventana:
    imp2 = dsd.semiblackman(m) * imp1[:m]

    # Y lo guardamos en formato pcm float 32
    utils.savePCM32(raw=imp2, fout=fout)
    print "Guardado en:", fout
