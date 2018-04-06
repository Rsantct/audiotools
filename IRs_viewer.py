#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    v0.2d
    visor de impulsos IR wav o raw (.pcm)
    
    Si se pasan impulsos raw (.pcm) se precisa pasar también la Fs
    
    Ejemplo de uso:
    
    IR_viewer.py  drcREW_test1.wav  drcREW_test2.pcm   44100  fmin-fmax
    
    fmin-fmax:  es opcional y permite visualizar un rango en Hz, útil para ver graves.

"""
# v0.2
#   Se añade un visor de la fase y otro pequeño visor de los impulsos
# v0.2b 
#   Opción del rango de frecuencias a visualizar
# v0.2c
#   Opcion -pha (oculta beta) para pintar la phase. ESTO NO ESTÁ CLARO PTE INVESTIGARLO DEEPER
# v0.2d
#   Dejamos de pintar phases o gd fuera de la banda de paso, 
#   con nuevo umbral a -50dB parece más conveniente para FIRs cortos con rizado alto.
#   Se aumenta el rango de magnitudes hasta -60 dB
#   Muestra el pkOffset en ms
#   RR: El GD debería recoger en la gráfica el delay del filtro.
#       Ok, se muestra el GD real que incluye el retardo del impulso si es de linear phase
#   Autoescala magnitudes.
#   Se dejan de mostrar los taps en Ktaps

import sys
import numpy as np, math
from scipy import signal
from matplotlib import pyplot as plt
from matplotlib import ticker   # Para rotular a medida
from matplotlib import gridspec # Para ajustar disposición de los subplots
import utils

def lee_commandline(opcs):
    global fmin, fmax, plotPha
    
    # impulsos que devolverá esta función
    IRs = []
    # archivos que leeremos
    fnames = []
    fs = 0
    plotPha = False

    for opc in opcs:
        if opc in ("-h", "-help", "--help"):
            print __doc__
            sys.exit()
            
        elif opc.isdigit():
            fs = float(opc)

        elif "-" in opc and opc[0].isdigit() and opc[-1].isdigit():
            fmin, fmax = opc.split("-")
            fmin = float(fmin)
            fmax = float(fmax)
            
        elif "-ph" in opc:
            plotPha = True

        else:
            fnames.append(opc)

    # si no hay fnames
    if not fnames:
        print __doc__
        sys.exit()

    for fname in fnames:
    
        if fname.endswith('.wav'):
            fswav, imp = utils.readWAV16(fname)
            IRs.append( (fswav, imp, fname) )
            
        else:
            if fs:
                imp = utils.readPCM32(fname)
                IRs.append( (fs, imp, fname) )
            else:
                print __doc__
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
    columnas = len(IRs)
    
    global fig, grid, axMag, axDrv, axPha, axGD, axIR
    #-------------------------------------------------------------------------------
    # Preparamos el área de las gráficas 'fig'
    #-------------------------------------------------------------------------------
    fig = plt.figure(figsize=(10,7))
    # Para que no se solapen los rótulos
    fig.set_tight_layout(True)

    # Preparamos una matriz de Axes (gráficas).
    # Usamos GridSpec que permite construir un array chachi.
    # Las gráficas de MAG ocupan 3 filas, la de PHA ocupa 2 filas,
    # y la de IR será de altura simple, por tanto declaramos 6 filas.
    grid = gridspec.GridSpec(nrows=6, ncols=columnas)

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
    # umbral de magnitud en dB para dejar de pintar phases o gd
    magThr = -50.0 

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()

    IRs = lee_commandline(sys.argv[1:])
        
    preparaGraficas()
    
    GDavgs = [] # los promedios de GD de cada impulso, para mostrarlos por separado
    columnaIR = 0
    for IR in IRs:
    
        fs, imp, info = IR
        fny = fs/2.0
        limp = imp.shape[0]
        peakOffsetms = np.round(abs(imp).argmax() / fs * 1000, 1) # en ms

        # 500 bins de frecs logspaciadas para que las resuelva freqz
        w1 = 1 / fny * (2 * np.pi)
        w2 = 2 * np.pi
        #bins = np.geomspace(w1, w2, 500) # np.geomspace needs numpy >= 1.12
        bins = np.logspace(np.log10(w1), np.log10(w2), num=500)

        # Semiespectro
        # whole=False --> hasta Nyquist
        w, h = signal.freqz(imp, worN=bins, whole=False)
        
        # frecuencias trasladadas a Fs
        freqs = w / np.pi * fny
        
        # Magnitud:
        magdB = 20 * np.log10(abs(h))

        # Wrapped Phase:
        phase = np.angle(h, deg=True)
        # Eliminamos (np.nan) los valores fuera de la banda de paso,
        # por ejemplo de magnitud por debajo de un umbral
        phaseClean  = np.full((len(phase)), np.nan)
        mask = (magdB > magThr)
        np.copyto(phaseClean, phase, where=mask)

        # Group Delay:
        wgd, gd = signal.group_delay((imp, 1), w=bins, whole=False)
        # Eliminamos (np.nan) los valores fuera de la banda de paso,
        # por ejemplo de magnitud por debajo de un umbral
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

        # ploteo de la Magnitud con autoajuste del top
        tmp = np.max(magdB)
        tmp = math.ceil(tmp/5.0) * 5.0 + 5.0
        if tmp > top_dBs:
            top_dBs = tmp
        axMag.set_ylim(bottom = top_dBs - range_dBs, top = top_dBs)
        axMag.plot(freqs, magdB, label=info)
        color = axMag.lines[-1].get_color() # anotamos el color de la última línea  

        if plotPha:
            axPha.plot(freqs, phaseClean, "-", linewidth=1.0, color=color)

        # ploteo del GD con autoajuste del top
        ymin = peakOffsetms - 25
        ymax = peakOffsetms + 75
        axGD.set_ylim(bottom = ymin, top = ymax)
        axGD.plot(freqs, gdms, "--", linewidth=1.0, color=color)
    
        # plot del IR. Nota: separamos los impulsos en columnas
        axIR = fig.add_subplot(grid[5, columnaIR])
        axIR.set_title(str(limp) + " taps - pk offset " + str(peakOffsetms) + " ms")
        axIR.set_xticks(range(0,len(imp),10000))
        axIR.ticklabel_format(style="sci", axis="x", scilimits=(0,0))
        axIR.plot(imp, "-", linewidth=1.0, color=color)
        columnaIR += 1

    GDtitle = 'GD avg: ' + ', '.join([str(x) for x in GDavgs]) + ' ms'
    axGD.set_title(GDtitle)
    
    axMag.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})
    plt.show()

   
