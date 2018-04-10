#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1 wip
    
    Recorta un FIR pcm float 32 aplicando una ventana
    Uso:
        python trimPCM.py  file.pcm  -tN [-s] [-o]
        -tN: N taps de salida potencia de 2 (sin espacios)
        -s:  ventana simétrica en el pico
        -o:  sobreescribe el original
        
    Nota:
        -s  permite procesar FIR linear phase 
            con el pico en cualquier localización.
"""

# ------------------------   config   -----------------------------
# Fracción de m que se tomará para enventanar por delante del pico
frac = 0.001
# -----------------------------------------------------------------

import sys
import numpy as np
import pydsd as dsd
import utils

def lee_opciones():
    global m, overwriteFile, sym
    m = 0
    overwriteFile = False
    sym = False
    if len(sys.argv) == 1:
        print __doc__
        sys.exit()
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
        elif opc == '-s':
            sym = True
        else:
            f_in = opc
    if not m:
        print __doc__
        sys.exit()

    # El nombre de archivo de salida depende de si se pide sobreescribir
    if not overwriteFile:
        f_out = str(m) + "taps_" + f_in
    else:
        f_out = f_in
        

if __name__ == "__main__":
    
    print "WORK IN PROGRESS"
    sys.exit()

    # Leemos opciones
    lee_opciones()
   
    # Leemos el impulso de entrada imp1
    imp1 = utils.readPCM32(f_in)
    
    # Lo cortamos a la longitud deseada aplicando una ventana:
    imp2 = dsd.semiblackman(m) * imp1[:m]

    # Y lo guardamos en formato pcm float 32
    utils.savePCM32(raw=imp2, fout=f_out)
    print "pcm recortado a " + str(m) + " taps en: " + f_out

