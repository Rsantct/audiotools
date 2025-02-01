#!/usr/bin/env python3
"""
    v0.1c

    Recorta un FIR .pcm float32 o .wav int16
    El recorte se efectúa aplicando Blackmann-Harris
    El resultado se guarda en formato .pcm float 32

    Uso y opciones:

      FIR_trim.py  file.pcm[.wav] -tM [-pP] [-asym[R]] [-o] [-lp|-mp]

      -tM       M taps de salida (sin espacios)

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
# v0.1c
#   Python3

import sys
import numpy as np
import tools

#VENTANA = tools.dsd.blackmanharris
#SEMIVENTANA = tools.dsd.semiblackmanharris
VENTANA = tools.hann
SEMIVENTANA = tools.semihann

def lee_opciones():

    global f_in, m, phasetype
    global pkPos, sym, wratio, overwriteFile

    f_in = ''
    m = 0
    phaseType= ''
    pkPos = -1 # fuerza la búsqueda del peak
    overwriteFile = False
    sym = True
    wratio = 0.001

    if len(sys.argv) == 1:
        print (__doc__)
        sys.exit()

    for opc in sys.argv[1:]:

        if opc.startswith('-t'):
            m = int(opc.replace('-t', ''))

        elif opc.startswith('-p'):
            pkPos = int(opc.replace('-p', ''))

        elif opc == '-h' or opc == '--help':
            print (__doc__)
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
        print (__doc__)
        sys.exit()

    if phaseType == 'lp':
        sym = True
        pkPos = -1 # pkPos autodiscovered
    if phaseType == 'mp':
        sym = False
        pkPos = 0



if __name__ == "__main__":

    # Leemos opciones
    lee_opciones()

    # Leemos el impulso de entrada imp1
    try:

        if   f_in[-4:] in ('.pcm', '.f32'):
            imp1 = tools.readPCM32(f_in)
            fs = 0

        elif f_in[-4:] == '.wav':
            fs, imp1 = tools.readWAV(f_in)

        else:
            print( f"'{f_in}' debe ser .pcm, .f32 o .wav" )
            sys.exit()

    except Exception as e:
        print( f"Error leyendo '{f_in}'" )
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
            imp2L = imp1[pkPos-nleft:pkPos]  * SEMIVENTANA(nleft)[::-1]
            imp2R = imp1[pkPos:pkPos+nright] * SEMIVENTANA(nright)
            imp2 = np.concatenate([imp2L, imp2R])
        else:
            imp2 = imp1[0:m] * SEMIVENTANA(m)

    # Enventanado simétrico
    else:
        # Aplicamos la ventana centrada en el pico
        imp2 = imp1[int(pkPos-m/2) : int(pkPos+m/2)] * VENTANA(m)

    # Informativo
    pkPos2 = abs(imp2).argmax()


    # Y lo guardamos
    fname_woext = f_in[:-4]

    if not overwriteFile:
        f_out_pcm = f'{fname_woext}_{m}_taps.f32'
        f_out_wav = f'{fname_woext}_{m}_taps.wav'

    else:
        f_out_pcm = f'{fname_woext}.f32'
        f_out_wav = f'{fname_woext}.wav'


    print(f'FIR recortado (peak original en tap: {pkPos}, peak {m} taps en tap: {pkPos2})')
    tools.savePCM32(imp2, f_out_pcm)
    print(f_out_pcm)
    if fs:
        tools.saveWAV(f_out_wav, fs, imp2, 'int32')
        print(f_out_wav)


