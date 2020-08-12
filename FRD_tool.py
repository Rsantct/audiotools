#!/usr/bin/env python3

"""
    v0.5
    Visor de archivos de respuesta en frecuencia .frd .txt

    Uso:
     FRD_tool.py   file1.frd  file2.txt .. [-opciones ..]

    -dBXX           Rango XX dBs del eje de magnitudes
    -norm           Ajusta el máx de la curva en 0 dB
    -autobal        Presenta las curvas niveladas con su banda de paso en 0 dB
                    De utilidad para estimar la combinación de curvas,
                    por ejemplo de un woofer campo cercano + campo libre

    -phase          Incluye gráfico de la phase si la hubiera.
    -nomask         Muestra la phase también en las regiones de magnitud
                    muy baja respecto a la banda de paso.

    -f300-3000      Eje de frecuencias p.ej: 300 a 3000 Hz

    -Noct           Suaviza la curva a 1/N oct, ejemplo de uso: -6oct
    -f0=xx          Frecuencia en la que deja de suavizar 1/N oct
                    hasta alcanzar 1/1 oct en Nyquist
    -saveNoct       Guarda la curva suavizada en un archivo 'fileX_Noct.frd'

"""
# v0.2
#   - Mejoras en la estimación del promedio de la curva en la banda de paso
#   - Nuevas opciones de presentación
# v0.3
#   - La gráfica de phase queda como opcional
#   - Permite guardar la versión suavizada de una curva:
#   - Cambio de nombre FRD_viewer.py --> FRD_tool.py
# v0.3b
#   - Se deja de pintar la curva sin suavizar junto con la suavizada por ser poco legible
#     sobre todo con varias curvas.
#   - Se revisa el encuadre en el eje Y
# v0.4
#   - muestra los offset aplicados para la opción '-autobal'
# v0.5
#   - Python 2 --> 3

import sys
import numpy as np
from scipy import signal, interpolate
from scipy.stats import mode
from matplotlib import pyplot as plt
from matplotlib import gridspec
from matplotlib import ticker
import tools
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
    plt.rcParams.update({'font.size': 8})

    if subplotPha:
        grid = gridspec.GridSpec(nrows=3, ncols=1)
    else:
        grid = gridspec.GridSpec(nrows=1, ncols=1)

    axMag = fig.add_subplot(grid[0:2,0])
    axMag.set_ylim(ymax-dBrange, ymax)
    prepara_eje_frecuencias(axMag)
    axMag.set_ylabel("magnitude (dB)")

    if subplotPha:
        axPha = fig.add_subplot(grid[2,0])
        prepara_eje_frecuencias(axPha)
        axPha.set_ylim([-180.0,180.0])
        #axPha.set_yticks(range(-135, 180, 45))
        axPha.set_yticks(range(-180, 225, 45))
        axPha.grid(linestyle=":")
        axPha.set_ylabel("phase")

        return axMag, axPha

    else:
        return axMag, None

def BPavg(curve):
    """ Estimación del promedio de una curva de magnitudes dB en la banda de paso
    """
    # Suponemos que la curva es de tipo band-pass maomeno plana
    # En todo caso la suavizamos para aplanarla.
    smoothed = smooth(freq, curve, Noct=3)

    # Elegimos los bins que distan poco del máximo de la curva suavizada 1/1oct
    bandpass_locations = np.where( curve > max(smoothed) - 12)
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

def lee_command_line():
    global frdnames, fmin, fmax, dBrange, subplotPha, saveNoct
    global autobalance, normalize, maskPhaseIfLow, Noct, f0

    frdnames = []

    if len(sys.argv) == 1:
        print (__doc__)
        sys.exit()
    else:
        for opc in sys.argv[1:]:

            if opc in ('-h', '-help', '--help'):
                print (__doc__)
                sys.exit()

            elif opc[:2] == '-f' and opc[2].isdigit() and opc[-1].isdigit and '-' in opc[1:]:
                fmin, fmax = opc[2:].split('-')
                fmin = float(fmin)
                fmax = float(fmax)

            elif '-auto' in opc:
                autobalance = True

            elif '-norm' in opc:
                normalize = True

            elif opc.lower()[:3] == '-db':
                dBrange = round(float(opc[3:].strip()))

            elif '-pha' in opc:
                subplotPha = True

            elif '-nomask' in opc:
                maskPhaseIfLow = False

            elif opc[0] == '-' and opc[-3:] == 'oct':
                Noct = int(opc.replace('-', '').replace('oct', '').strip())

            elif opc[:4] == '-f0=':
                f0 = int(opc[4:])

            elif opc[:5] == '-save':
                saveNoct = True

            elif opc[-4:].lower() in ['.txt', '.frd']:
                frdnames.append(opc)

    # si no hay frdname
    if not frdnames:
        print (__doc__)
        sys.exit()

if __name__ == "__main__":

    # Por defecto
    fmin = 20;     fmax = 20000     # Hz
    dBrange             = 100        # dB
    ymax                = 10
    autobalance         = False
    normalize           = False
    subplotPha          = False
    maskPhaseIfLow      = True
    Noct                = 0         # Sin suavizado
    f0                  = None      # f0 para transicion del suavizado hasta 1/1 oct en Nyq
    saveNoct            = False     # guarda una versión de la curva suavizada.

    # Umbral dB de descarte para pintar la fase
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

    # We can add info from each curve
    graph_title = []

    # We'll collect the avg magnitude of each curve, just for display fitting
    BPavgs = []

    for frdname in frdnames:

        curvename = frdname.split("/")[-1].split(".")[:-1][0]

        # Leemos el contenido del archivo .frd. NOTA: np.loadtxt() no admite
        # los .frd de ARTA por que tienen cabecera sin comentar '#'
        frd, _ = tools.readFRD(frdname)

        # Vemos si hay columna de phase
        frd_con_fase = (frd.shape[1] == 3)

        # arrays de freq, mag y pha
        freq0 = frd[:, 0]
        mag0  = frd[:, 1]

        # Funcion de interpolación con los datos leidos. (!) OjO 'cubic' puede fallar.
        Imag = interpolate.interp1d(freq0, mag0, kind='linear',
                                    bounds_error=False, fill_value='extrapolate')

        # Hallamos la interpolación proyectada sobre nuestro eje 'freq'
        mag = Imag(freq)
        BPavg_mag = round(BPavg(mag), 2)
        BPavgs.append( BPavg_mag )

        # Opcionalmente la bajamos por debajo de 0
        if normalize:
            mag -= np.max(mag)

        # Opcionalmente la nivela a 0dB en su banda de paso
        if autobalance:
            mag -= BPavg_mag
            if len(frdnames) > 1:
                graph_title.append( curvename + ' offset: ' + str(-BPavg_mag) )

        # Plot de la magnitud
        if not Noct:
            axMag.plot(freq, mag, label=curvename)
        else:
            if f0:
                smoothed = smooth(freq, mag, Noct=Noct, f0=f0)
            else:
                smoothed = smooth(freq, mag, Noct=Noct)
            # Ploteo
            axMag.plot(freq, smoothed, label=curvename)
            # Opcionalmente guarda la versión suavizada:
            if saveNoct:
                tools.saveFRD(curvename + '_' + str(Noct) + 'oct.frd',
                              freq, smoothed, fs=None)

        color = axMag.lines[-1].get_color() # anotamos el color

        if subplotPha:
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

            axPha.legend(loc='lower left', prop={'size':'small', 'family':'monospace'})


    # Encuadre vertical
    if normalize or autobalance:
        centerY = 0
    else:
        avg_mags = np.average(BPavgs)
        centerY = ( avg_mags // 10 ) * 10

    # centerY is actually placed 1/4 below upper limit
    axMag.set_ylim( centerY - dBrange * 3.0/4.0, centerY + dBrange * 1.0/4.0 )

    axMag.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})

    axMag.set_title( '\n'.join(graph_title) )

    plt.show()
