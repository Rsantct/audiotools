#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1

    Adaptación del original trimwav2pcm.m del paquete DSD
    https://github.com/rripio/DSD

    Utilidad para recortar un IR .wav  y 
    convertirlo a formato raw float 32 (.pcm)
    
    Uso:  trimwav2pcm.py  file.wav -tM
          -tM: M taps de salida potencia de 2 (sin espacios)

    NOTA:
        Para el caso de un impulso wav de 128 Ktaps proporcionado
        por REW, el pico está desplazado 44100 muestras, por tanto
        buscaremos el pico para hacer el trim, en lugar de asumir que
        el pico se localiza en el principio del IR.
        
"""
import sys
import numpy as np
import pydsd as dsd
import utils

# ------------------------   config   -----------------------------
# Fracción de m que se tomará para enventanar por delante del pico
frac = 0.001
# -----------------------------------------------------------------

if __name__ == "__main__":

    # Leemos opciones
    f_in=''
    m = 0
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
        else:
            f_in = opc
    if not m or not f_in:
        print __doc__
        sys.exit()

    # Leemos el archivo que se pasa
    fs, imp1 = utils.readWAV16(f_in)

    # Buscamos el pico:
    pkpos = abs(imp1).argmax()

    # Hacemos dos ventanas, una muy corta por delante para pillar bien el impulso
    # y otra larga por detrás hasta completar los taps finales deseados:
    nleft  = int(frac * m)
    nright = m - nleft
    imp2L = imp1[pkpos-nleft:pkpos]  * dsd.semiblackman(nleft)[::-1]
    imp2R = imp1[pkpos:pkpos+nright] * dsd.semiblackman(nright)

    # Guardamos el resultado
    f_out = f_in.replace(".wav", ".pcm")
    utils.savePCM32(np.concatenate([imp2L, imp2R]), f_out)
    print "recortado y guardado en:", f_out
