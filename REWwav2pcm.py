#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    v0.1beta
    
    Convierte una IR de DRC originada en REW Room EQ Wizard
    en un archivo raw float32 (.pcm) adecuado para un convolver
    como Brutefir

    NOTA:   Los impulsos IR .wav de REW vienen con el pico desplazado
            tantas muestras como el valor de la Fs del wav.
            Aquí haremos una reconstrucción completa:
            time domain > spectrum > time domain, tomando la 
            minimum phase descartamos el exceso de phase si lo hubiera, 
            resultando en un impulso con el pico al inicio.
"""

import sys
import numpy as np
import pydsd as dsd
import tools

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
    fs, imp1 = tools.readWAV16(fin)
    
    # Espectro completo
    h = np.fft.fft(imp1)
    # Réplica del espectro completo en fase mínima
    hmp = dsd.minphsp(h)

    # Convertimos el espectro completo mp en un IR, se toma la parte real.
    imp2 = np.fft.ifft( hmp )
    imp2 = np.real(imp2)

    # Lo cortamos a la longitud deseada y aplicamos una ventana:
    imp2 = dsd.semiblackmanharris(m) * imp2[:m]

    # Y lo guardamos en formato pcm float 32
    tools.savePCM32(raw=imp2, fout=fout)
    print "Guardado en:", fout
