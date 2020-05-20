#!/usr/bin/env python3

"""
    visor de impulsos IR wav o raw (.pcm, .txt)

    Si se pasan impulsos raw (.pcm) se precisa pasar también la Fs

    Ejemplo de uso:

    IR_viewer.py  drc_test1.wav  drc_test2.pcm   44100  [ -pha fmin-fmax -1 -eq ]

    Opciones:

        -pha        Muestra la fase

        fmin-fmax   Permite visualizar un rango en Hz, útil para ver graves.

        -1          Muestra las gráficas de los impulsos en una fila única.

        -pdf        Guarda la gráfica en archivo PDF, incluyendo el zoom
                    que se hiciese durante la visualización.

        -eq         Para ver curvas de un FIR de EQ (abcisas de -15 a +5 dB)

"""
# version = 'v0.2'
#   Se añade un visor de la fase y otro pequeño visor de los impulsos
# version = 'v0.2b'
#   Opción del rango de frecuencias a visualizar
# version = 'v0.2c'
#   Opcion -pha (oculta beta) para pintar la phase.
# version = 'v0.2d'
#   Dejamos de pintar phases o gd fuera de la banda de paso,
#   con nuevo umbral a -50dB parece más conveniente para FIRs cortos con rizado alto.
#   Se aumenta el rango de magnitudes hasta -60 dB
#   Muestra el pkOffset en ms
#   El GD recoge en la gráfica el delay del pico del filtro.
#   Autoescala magnitudes.
#   Se deja de mostrar los taps en 'Ktaps'
# version = 'v0.2f'
#   Axes de impulsos en una fila opcinalmente
#   Se muestra la versión del programa al pie de las gráficas.
#   Se guarda la gráfica en un pdf
# version = 'v0.2g'
#   La impresión a PDF se deja opcional
# version = 'v0.2h'
#   Opción -eq para ver FIRs de ecualización.
#version = 'v0.2i'
#   Admite IRs en archivos de texto.
# TO DO:
#   Revisar la información mostrada "GD avg" que pretende ser la moda de los valores
# version = 'v0.2ip3'
#   Python3
version = 'v0.2j'
#   opción -pha visible

import sys
import numpy as np, math
from scipy import signal
from matplotlib import pyplot as plt
from matplotlib import ticker   # Para rotular a medida
from matplotlib import gridspec # Para ajustar disposición de los subplots
import tools

def lee_commandline(opcs):
    global fmin, fmax, plotPha, IRtype
    global plotIRsInOneRow, generaPDF
    plotIRsInOneRow = False
    generaPDF = False
    IRtype = "normal"

    # impulsos que devolverá esta función
    IRs = []
    # archivos que leeremos
    fnames = []
    fs = 0
    plotPha = False

    for opc in opcs:
        if opc in ("-h", "-help", "--help"):
            print (__doc__)
            sys.exit()

        elif opc.isdigit():
            fs = float(opc)

        elif "-" in opc and opc[0].isdigit() and opc[-1].isdigit():
            fmin, fmax = opc.split("-")
            fmin = float(fmin)
            fmax = float(fmax)

        elif opc == "-eq":
            IRtype = 'eq'

        elif "-ph" in opc:
            plotPha = True

        elif opc == "-1":
            plotIRsInOneRow = True

        elif opc == "-pdf":
            generaPDF = True

        else:
            fnames.append(opc)

    # si no hay fnames
    if not fnames:
        print (__doc__)
        sys.exit()

    for fname in fnames:

        if fname.endswith('.wav'):
            fswav, imp = tools.readWAV16(fname)
            IRs.append( (fswav, imp, fname) )

        elif fname.endswith('.txt'):
            if fs:
                imp = np.loadtxt(fname)
                IRs.append( (fs, imp, fname) )
            else:
                print (__doc__)
                sys.exit()

        elif fname.endswith('.pcm'):
            if fs:
                imp = tools.readPCM32(fname)
                IRs.append( (fs, imp, fname) )
            else:
                print (__doc__)
                sys.exit()
        else:
            print (__doc__)
            sys.exit()

    return IRs

def prepara_eje_frecuencias(ax):
    """ según las opciones fmin, fmax, frec_ticks """
    frec_ticks = 20, 100, 1000, 10000
    ax.set_xscale("log")
    fmin2 = 10; fmax2 = 20000
    if fmin:
        fmin2 = fmin
    if fmax:
        fmax2 = fmax
    ax.set_xticks(frec_ticks)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.set_xlim([fmin2, fmax2])

def preparaGraficas():
    numIRs = len(IRs)
    global fig, grid, axMag, axDrv, axPha, axGD, axIR

    #-------------------------------------------------------------------------------
    # Preparamos el tamaño de las gráficas 'fig'
    #-------------------------------------------------------------------------------
    if plotIRsInOneRow:
        fig = plt.figure(figsize=(9, 6))
    else:
        fig = plt.figure(figsize=(9, 8 + numIRs))

    # Tamaño de la fuente usada en los títulos de los axes
    plt.rcParams.update({'axes.titlesize': 'medium'})

    # Para que no se solapen los rótulos
    fig.set_tight_layout(True)

    #-------------------------------------------------------------------------------
    # Preparamos una matriz de Axes (gráficas).
    # Usamos GridSpec que permite construir un array chachi.
    # Las gráficas de MAG ocupan 3 filas, la de PHA ocupa 2 filas,
    # y gráfica de IR según la opcion elegida:
    #   - en una fila única simple declaramos 6 filas y numIRs columnas
    #   - en filas independientes de altura doble declaramos 5 + 2*numIRs filas.
    #-------------------------------------------------------------------------------

    if plotIRsInOneRow:
        grid = gridspec.GridSpec(nrows = 6, ncols = numIRs)
    else:
        grid = gridspec.GridSpec(nrows = 5 + 2*numIRs, ncols = 1)

    # --- SUBPLOT para pintar las FRs (alto 3 filas, ancho todas las columnas)
    axMag = fig.add_subplot(grid[0:3, :])
    axMag.grid(linestyle=":")
    prepara_eje_frecuencias(axMag)
    # axMag.set_ylim([top_dBs - range_dBs, top_dBs]) # dejamos esto para cuando conozcamos la mag
    axMag.set_ylabel("filter magnitude dB")

    # --- SUBPLOT para pintar el GD (alto 2 filas, ancho todas las columnas)
    # comparte el eje X (twinx) con el de la phase
    # https://matplotlib.org/gallery/api/two_scales.html
    axGD = fig.add_subplot(grid[3:5, :])
    axGD.grid(False)
    prepara_eje_frecuencias(axGD)
    #axGD.set_ylim(-25, 75) # dejamos los límites del eje y para cuando conozcamos el GD
    axGD.set_ylabel(u"--- filter GD (ms)")

    # --- SUBPLOT para pintar las PHASEs (común con el de GD)
    if plotPha:
        axPha = axGD.twinx()
        axPha.grid(linestyle=":")
        prepara_eje_frecuencias(axPha)
        axPha.set_ylim([-180.0,180.0])
        axPha.set_yticks(range(-135, 180, 45))
        axPha.set_ylabel(u"filter phase")

if __name__ == "__main__":

    top_dBs   = 5  # inicial lugo se reajustará
    range_dBs = 65
    fmin = 10
    fmax = 20000
    # Umbral de la magnitud en dB para dejar de pintar phases o gd
    magThr = -50.0

    if len(sys.argv) == 1:
        print (__doc__)
        sys.exit()

    IRs = lee_commandline(sys.argv[1:])

    preparaGraficas()

    GDavgs = [] # los promedios de GD de cada impulso, para mostrarlos por separado

    IRnum = 0

    for IR in IRs:

        fs, imp, info = IR
        fny = fs/2.0
        limp = len(imp)
        peakOffsetms = np.round(abs(imp).argmax() / fs * 1000, 1) # en ms

        # Semiespectro
        # whole=False --> hasta Nyquist
        w, h = signal.freqz(imp, worN=int(len(imp)/2), whole=False)

        # frecuencias trasladadas a Fs
        freqs = w / np.pi * fny

        # Magnitud:
        magdB = 20 * np.log10(abs(h))

        # Phase:
        phase = np.unwrap( np.angle(h, deg=True) )
        # Eliminamos (np.nan) los valores de phase fuera de
        # la banda de paso, por debajo de un umbral configurable.
        phaseClean  = np.full((len(phase)), np.nan)
        mask = (magdB > magThr)
        np.copyto(phaseClean, phase, where=mask)

        # Group Delay:
        wgd, gd = signal.group_delay((imp, 1), w=int(len(imp)/2), whole=False)
        # Eliminamos (np.nan) los valores fuera de
        # la banda de paso, por debajo de un umbral configurable.
        gdClean  = np.full((len(gd)), np.nan)
        mask = (magdB < magThr)
        np.copyto(gd, gdClean, where=mask)
        # GD es en radianes los convertimos a milisegundos
        gdms = gd / fs * 1000
        # Computamos el GD promedio (en ms) para mostrarlo en la gráfica
        #   1. Vemos un primer promedio
        gdmsAvg = np.round(np.nanmean(gdms), 1)
        #   2. limpiamos las desviaciones > 5 ms respecto del promedio (wod: without deviations)
        gdmswod = np.full((len(gdms)), np.nan)
        mask = (gdms < (gdmsAvg + 5.0) ) # nota: se muestra un Warning porque se evalúan valores np.nan
        np.copyto(gdmswod, gdms, where=mask)
        #   3. Promedio recalculado sobre los valores without deviations
        gdmsAvg = np.round(np.nanmean(gdms), 1)
        GDavgs.append(gdmsAvg)

        # ---- PLOTEOS ----

        # Ploteo de la Magnitud con autoajuste del top
        tmp = np.max(magdB)
        tmp = math.ceil(tmp/5.0) * 5.0 + 5.0
        if tmp > top_dBs:
            top_dBs = tmp
        axMag.set_ylim(bottom = top_dBs - range_dBs, top = top_dBs)
        if IRtype == 'eq':
            axMag.set_ylim(-15.0, 5.0)
        axMag.plot(freqs, magdB, label=info)
        color = axMag.lines[-1].get_color() # anotamos el color de la última línea

        if plotPha:
            axPha.plot(freqs, phaseClean, "-", linewidth=1.0, color=color)

        # Ploteo del GD con autoajuste del top
        ymin = peakOffsetms - 25
        ymax = peakOffsetms + 75
        axGD.set_ylim(bottom = ymin, top = ymax)
        axGD.plot(freqs, gdms, "--", linewidth=1.0, color=color)

        # Plot del IR
        # (i) Opcionalmente podemos pintar los impulsos en una sola fila
        rotuloIR = str(limp) + " taps - pk offset " + str(peakOffsetms) + " ms"
        if plotIRsInOneRow:
            # Todos los IRs en una fila de altura simple, en columnas separadas:
            axIR = fig.add_subplot(grid[5, IRnum]) # (i) grid[rangoVocupado, rangoHocupado]
            # Rotulamos en el espacio de título:
            axIR.set_title(rotuloIR)
        else:
            # Cada IR en una fila de altura doble:
            axIR = fig.add_subplot(grid[5+2*IRnum:5+2*IRnum+2, :])
            # Rotulamos dentro del axe:
            axIR.annotate(rotuloIR, xy=(.6,.8), xycoords='axes fraction') # coords referidas al area gráfica
        IRnum += 1
        axIR.set_xticks(range(0,len(imp),10000))
        axIR.ticklabel_format(style="sci", axis="x", scilimits=(0,0))
        axIR.plot(imp, "-", linewidth=1.0, color=color)

    # Mostramos los valores de GD avg de cada impulso:
    GDtitle = 'GD avg:    ' + '    '.join([str(x) for x in GDavgs]) + ' (ms)'
    axGD.set_title(GDtitle)

    # Leyenda con los nombres de los impulsos en el gráfico de magnitudes
    axMag.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})

    # Y un footer con la versión:
    progname = sys.argv[0].split("/")[-1]
    footer = "AudioHumLab " + progname + " " + version
    plt.gcf().text(0.01, 0.01, footer, size='smaller')

    # Finalmente mostramos las gráficas por pantalla.
    plt.show()

    if generaPDF:
        # Y guardamos las gráficas en un PDF:
        pdfName = ",".join([x for x in sys.argv[1:] if '.' in x]) + '.pdf'
        print ( f'\nGuardando en el archivo: {pdfName}' )
        # evitamos los warnings del pdf
        # C:\Python27\lib\site-packages\matplotlib\figure.py:1742: UserWarning:
        # This figure includes Axes that are not compatible with tight_layout, so
        # its results might be incorrect.
        import warnings
        warnings.filterwarnings("ignore")
        fig.savefig(pdfName, bbox_inches='tight')

    print ("Bye!")
