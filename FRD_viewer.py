#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.2 BETA
    Visor de archivos de respuesta en frecuencia .FRD
    Se muestra la fase si existe una tercera columna.

    Uso:
    FRD_viewer.py   file1.frd  file2.frd ... [-opciones]
    
    -normaliza      Dibuja el máx de la curva en 0 dB
    -nomask         Muestra la phase también en las regiones de magnitud
                    muy baja respecto a la banda de paso.
    -autobalance    Dibuja las curvas niveladas en su banda de paso.

    -f300-3000      Eje de frecuencias de 300 a 3000 Hz
    -m25-5          Eje de magnitudes desde -25 hasta 5 dBs

    -Xoct           Suaviza la curva a 1/X oct

"""
import sys
import numpy as np
from scipy import signal, interpolate
from scipy.stats import mode
from matplotlib import pyplot as plt
from matplotlib import gridspec
from matplotlib import ticker
import utils
from smoothSpectrum import smoothSpectrum as smooth

def prepara_eje_frecuencias(ax):
    freq_ticks=[20, 100, 1000, 10000, 20000]
    ax.grid(True)
    ax.set_xscale("log")
    fmin2 = 20; fmax2 = 20000
    if fmin:
        fmin2 = fmin
    if fmax:
        fmax2 = fmax
    ax.set_xticks(freq_ticks)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.set_xlim([fmin2, fmax2])

def prepara_graf():
    fig = plt.figure()
    grid = gridspec.GridSpec(nrows=2, ncols=1)

    axMag = fig.add_subplot(grid[0,0])
    axMag.set_ylim(ymin,ymax)
    prepara_eje_frecuencias(axMag)
    axMag.set_ylabel("magnitude (dB)")

    axPha = fig.add_subplot(grid[1,0])
    prepara_eje_frecuencias(axPha)
    axPha.set_ylim([-180.0,180.0])
    #axPha.set_yticks(range(-135, 180, 45))
    axPha.set_yticks(range(-180, 225, 45))
    axPha.grid(linestyle=":")
    axPha.set_ylabel("phase")

    return axMag, axPha

def lee_command_line():
    global frdnames, fmin, fmax, ymin, ymax
    global autobalance, normalize, maskPhaseIfLow, Noct

    frdnames = []

    if len(sys.argv) == 1:
        print __doc__
        sys.exit()
    else:
        for opc in sys.argv[1:]:

            if opc in ("-h", "-help", "--help"):
                print __doc__
                sys.exit()

            elif "-f" in opc and opc[2].isdigit() and opc[-1].isdigit:
                fmin, fmax = opc[2:].split("-")
                fmin = float(fmin)
                fmax = float(fmax)

            elif "-m" in opc and opc[2].isdigit() and opc[-1].isdigit:
                ymin, ymax = opc[2:].split("-")
                ymin = -float(ymin)
                ymax = float(ymax)

            elif "-" in opc and opc[0].isdigit() and opc[-1].isdigit:
                fmin, fmax = opc.split("-")
                fmin = float(fmin)
                fmax = float(fmax)

            elif "-auto" in opc:
                autobalance = True

            elif "-norm" in opc:
                normalize = True
                
            elif "-nomask" in opc:
                maskPhaseIfLow = False

            elif opc[0] == "-" and opc[-3:] == "oct":
                Noct = int(opc.replace("-", "").replace("oct", "").strip())

            elif not "-" in opc:
                frdnames.append(opc)

    # si no hay pcms o si no hay (Fs xor ini)
    if not frdnames:
        print __doc__
        sys.exit()

def BPavg(curve):
    """ cutre estimación del promedio de una curva de magnitudes dB en la banda de paso
    """
    # Suponemos que la curva es de tipo band-pass maomeno plana
    # Elegimos los bins que están a poca distancia del máximo de la curva
    bandpass_locations = np.where( curve > max(curve) - 12)
    bandpass = np.take( curve, bandpass_locations)
    # Buscamos los valores más frecuentes de la zona plana 'bandpass' redondeada a .1 dB
    avg = mode(np.round(bandpass,1), axis=None)[0][0]
    return avg

def limpia(curva, curvaRef, th):
    # Eliminamos (np.nan) los valores del array 'curva' cuando los valores del
    # array 'curvaRef' estén por debajo de el umbral 'th'.
    curvaClean  = np.full((len(curva)), np.nan)
    mask = (curvaRef > th)
    np.copyto(curvaClean, curva, where=mask)
    return curvaClean

if __name__ == "__main__":

    # Por defecto
    fmin = 20;  fmax = 20000    # Hz
    ymin = -40; ymax = 10       # dB
    autobalance = False
    normalize = False
    maskPhaseIfLow = True
    Noct = 0                    # Sin suavizado

    # Umbral de descarte para pintar la fase
    magThr = -40.0


    # Lee archivos .frd y limites de frecuencias
    lee_command_line()

    # Prepara graficas
    axMag, axPha = prepara_graf()

    # Usaremos un nuevo vector de frecuencias comun sobre el que interpolaremos
    # las FRDs de los archivos leidos que pueden diferir
    #freq = np.linspace(fmin, fmax, 500)
    # (i) Preferimos un vector logespaciado porque con uno linespaciado
    #     la interpolación resulta en una resolución escasa en graves.
    freq = np.logspace(np.log10(fmin), np.log10(fmax), num=500)

    for frdname in frdnames:
        curvename = frdname.split("/")[-1].split(".")[:-1][0]

        # Leemos el contenido del archivo .frd. NOTA: np.loadtxt() no admite
        # los .frd de ARTA por que tienen cabecera sin comentar '#'
        frd = utils.readFRD(frdname)

        # Vemos si hay columna de phase
        frd_con_fase = (frd.shape[1] == 3)

        # arrays de freq, mag y pha
        freq0 = frd[:, 0]
        mag0  = frd[:, 1]

        # Funcion de interpolación con los datos leidos. (!) OjO 'cubic' puede fallar.
        Imag = interpolate.interp1d(freq0, mag0, kind="linear", bounds_error=False)

        # Hallamos la interpolación proyectada sobre nuestro eje 'freq'
        mag = Imag(freq)
        # Opcionalmente la bajamos por debajo de 0
        if normalize:
            mag -= np.max(mag)
        if autobalance and len(frdnames) > 1:
            mag -= BPavg(mag)
            axMag.set_title("(!) Curves level have an automatic offset")

        # Plot de la magnitud
        ls = "-"        # linestyle solid
        if Noct <> 0:
            ls = ":"    # linestyle dotted
        axMag.plot(freq, mag, ls=ls, label=curvename)
        color = axMag.lines[-1].get_color() # anotamos el color

        # Fase mínima (BETA pendiente)
        H = signal.hilbert(mag)
        mpha = np.angle(H, deg=True)
        mpha = limpia(curva=mpha, curvaRef=mag, th=magThr)

        # Plot de la minPhase
        # axPha.plot(freq, mpha, "--", linewidth=1.0, color=color)

        if frd_con_fase:

            # La interpolamos sobre nuestro vector de frecuencias 
            pha0  = frd[:, 2]
            Ipha = interpolate.interp1d(freq0, pha0, kind="linear", bounds_error=False)
            pha = Ipha(freq)
            # Limpieza opcional dejamos de pintar la phase si la amplitud es muy baja.
            if maskPhaseIfLow:
                pha = limpia(curva=pha, curvaRef=mag, th=magThr)

            # Plot de la phase
            axPha.set_ylabel("pha")
            axPha.plot(freq, pha, "-", linewidth=1.0, color=color)

        # Plot de la curva suavizada
        if Noct <> 0:
            smoothed = smooth(mag, freq, Noct=Noct)
            axMag.plot(freq, smoothed, color=color)


    axMag.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})
    axPha.legend(loc='lower left', prop={'size':'small', 'family':'monospace'})
    plt.show()



