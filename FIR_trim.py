#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
    v0.1b

    Recorta un FIR .pcm float32 o .wav int16
    El recorte se efectúa aplicando Blackmann-Harris
    El resultado se guarda en formato .pcm float 32

    Uso y opciones:

      python FIR_trim.py  file.pcm[.wav] -tM [-pP] [-asym[R]] [-o] [-lp|-mp]

      -tM       M taps de salida potencia de 2 (sin espacios)

      -lp       Equivale a enventanado simétrico en el peak (autolocalizado),
                o sea, a no poner más opciones que los taps de salida.

      -mp       Equivale a -p0 sirve para FIRs minimum phase sin delay añadido,
                como los proporcionados por DSD.

      -pP       Posición en P taps del peak en el FIR de entrada (no se buscará).
                Si se omite -p, se buscará el peak automáticamente.

      -asym[R]  Enventanado asimétrico respecto del peak,
                R es el ratio % que ocupará la semiventana de la izquierda.
                Si se omite R se aplicará un ratio del 0.1 %
                Si se omite -asym[R] se aplicará enventanado simétrico.

      -o        Sobreescribe el archivo original.
                Si se omite se le añade un prefijo 'Mtaps_'

    Notas de aplicación:

    Tipo de FIR:                  Ventana:    PeakPos:
    -----------------             -------     -------
    minimum phase (no delayed)    asym 0%     userdef=0
    minimum phase (delayed)       asym        auto / userdef
    linear phase                  sym         auto / userdef
    mixed phase (*)               asym X%     auto / userdef

      (*) ajustar X% según la longitud de la componente lp del FIR.

"""

# v0.1b
#   Por defecto enventanado simétrico
#   Ratio ajustable para la semiventana por la izq del pico vs el ancho total (wizq+wder)

import sys
import numpy as np
import pydsd as dsd
import utils

def lee_opciones():
    global f_in, f_out, m, phasetype
    global pkPos, sym, wratio, overwriteFile
    f_in = ''
    m = 0
    phaseType= ''
    pkPos = -1 # fuerza la búsqueda del peak
    overwriteFile = False
    sym = True
    wratio = 0.001
    
    if len(sys.argv) == 1:
        print __doc__
        sys.exit()
    for opc in sys.argv[1:]:

        if opc.startswith('-t'):
            m = int(opc.replace('-t', ''))
            if not utils.isPowerOf2(m):
                print __doc__
                sys.exit()
                
        elif opc.startswith('-p'):
            pkPos = int(opc.replace('-p', ''))
            
        elif opc == '-h' or opc == '--help':
            print __doc__
            sys.exit()
            
        elif opc == '-o':
            overwriteFile = True
            
        elif opc.startswith('-asym'):
            sym = False
            if opc[5:]:
                wpercent = float(opc[5:])
                wratio = wpercent / 100.0
            
        elif opc == '-lp':
            phaseType = 'lp'
            
        elif opc == '-mp':
            phaseType = 'mp'
            
        else:
            if not f_in:
                f_in = opc
                
    if not m:
        print __doc__
        sys.exit()

    if phaseType == 'lp':
        sym = True
        pkPos = -1 # pkPos autodiscovered
    if phaseType == 'mp':
        sym = False
        pkPos = 0

        
    # El nombre de archivo de salida depende de si se pide sobreescribir
    if not overwriteFile:
        f_out = str(m) + "taps_" + f_in.replace('.wav', '.pcm')
    else:
        f_out = f_in.replace('.wav', '.pcm')


if __name__ == "__main__":

    # Leemos opciones
    lee_opciones()

    # Leemos el impulso de entrada imp1
    if   f_in[-4:] == '.pcm':
        imp1 = utils.readPCM32(f_in)
    elif f_in[-4:] == '.wav':
        fs, imp1 = utils.readWAV16(f_in)
    else:
        print "(i) trimFIR.py '" + f_in + "' no se reconoce :-/"
        sys.exit()

    # Buscamos el pico si no se ha indicado una posición predefinida:
    if pkPos == -1:
        pkPos = abs(imp1).argmax()

    # Enventanado NO simétrico
    if not sym:
        # Hacemos dos semiventanas, una muy corta por delante para pillar bien el impulso
        # y otra larga por detrás hasta completar los taps finales deseados:
        nleft  = int(wratio * m)
        if nleft <= pkPos:
            nright = m - nleft
            imp2L = imp1[pkPos-nleft:pkPos]  * dsd.semiblackmanharris(nleft)[::-1]
            imp2R = imp1[pkPos:pkPos+nright] * dsd.semiblackmanharris(nright)
            imp2 = np.concatenate([imp2L, imp2R])
        else:
            imp2 = imp1[0:m] * dsd.semiblackmanharris(m)

    # Enventanado simétrico
    else:
        # Aplicamos la ventana centrada en el pico
        imp2 = imp1[pkPos-m/2 : pkPos+m/2] * dsd.blackmanharris(m)

    # Informativo
    pkPos2 = abs(imp2).argmax()

    # Y lo guardamos en formato pcm float 32
    utils.savePCM32(imp2, f_out)
    print "FIR recortado en: " + f_out + " (peak:" + str(pkPos) + " peak_" + str(m) + ":" + str(pkPos2) + ")"
