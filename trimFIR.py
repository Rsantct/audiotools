#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1 wip
    
    Recorta un FIR .pcm float32 o .wav int16 aplicando una ventana
    Uso:
        python trimPCM.py  file.pcm  -tN [-s] [-o]
        -tN: N taps de salida potencia de 2 (sin espacios)
        -s:  ventana simétrica centrada en el pico
        -o:  sobreescribe el original
        
    Notas:
        -s  permite procesar FIR linear phase 
            con el pico en cualquier localización.

        El resultado se guarda en formato .pcm float 32
"""

# ----------   config   -------------------
# En enventanado asimétrico, fracción de m 
# que se tomará por delante del pico
frac = 0.001
# -----------------------------------------

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
        f_out = str(m) + "taps_" + f_in.replace('.wav', '.pcm')
    else:
        f_out = f_in.replace('.wav', '.pcm')
        

if __name__ == "__main__":
    
    print "WORK IN PROGRESS"
    sys.exit()

    # Leemos opciones
    lee_opciones()
   
    # Leemos el impulso de entrada imp1
    if   f_in[-3:] == '.pcm'
        imp1 = utils.readPCM32(f_in)
    elif f_in[-3:] == '.wav'
        fs, imp1 = utils.readWAV16(f_in)

    # Buscamos el pico:
    pkpos = abs(imp1).argmax()

    # Enventanado NO simétrico
    if not sym:
        # Hacemos dos ventanas, una muy corta por delante para pillar bien el impulso
        # y otra larga por detrás hasta completar los taps finales deseados:
        nleft  = int(frac * m)
        nright = m - nleft
        imp2L = imp1[pkpos-nleft:pkpos]  * dsd.semiblackman(nleft)[::-1]
        imp2R = imp1[pkpos:pkpos+nright] * dsd.semiblackman(nright)
        imp2 = np.concatenate([imp2L, imp2R])

    # Enventanado simétrico
    else:
        imp2 = imp1[pkpos-m/2 : pkpos+m/2+ 1]  * dsd.blackman(m)
    
    # Y lo guardamos en formato pcm float 32
    utils.savePCM32(imp2, f_out)
    print "pcm recortado a " + str(m) + " taps en: " + f_out

