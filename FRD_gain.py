#!/usr/bin/env python3

"""
    v0.1
    Aplica ganacia a un archivo .frd y lo guarda en otro archivo.

    Uso:
     FRD_gain.py   file.frd  GAIN (dB)

"""

import sys
import numpy as np
import tools

def lee_command_line():
    global frdname, gainStr, gain

    frdname = ''

    if len(sys.argv) == 1:
        print (__doc__)
        sys.exit()
    else:
        for opc in sys.argv[1:]:

            if opc in ('-h', '-help', '--help'):
                print (__doc__)
                sys.exit()

            elif opc[-4:].lower() in ['.txt', '.frd']:
                frdname = opc

            elif opc.replace('.','').replace('-','').replace('+','').isdigit():
                gainStr = opc
                gain    = float(opc)

            else:
                print (__doc__)
                sys.exit()

    # si no hay frdname
    if not frdname:
        print (__doc__)
        sys.exit()

if __name__ == "__main__":

    lee_command_line()

    # Leemos los datos de la respuesta en frecuencia
    frd, fs = tools.readFRD(frdname)

    # Vemos si hay columna de phase
    tiene_phase = (frd.shape[1] == 3)

    # arrays de freq, mag y pha
    freq = frd[:, 0]
    mag  = frd[:, 1]
    if tiene_phase:
        pha = frd[:, 2]

    # Aplicamos la ganancia:
    mag2 = mag + gain

    tmp = frdname.replace('.frd','_'+gainStr+'dB.frd').replace('.txt','_'+gainStr+'.txt')

    if tiene_phase:
        tools.saveFRD(tmp, freq, mag2, pha, fs=fs)
    else:
        tools.saveFRD(tmp, freq, mag2, fs=fs)
