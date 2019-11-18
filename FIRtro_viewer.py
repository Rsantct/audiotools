#!/usr/bin/env python3

"""
    Visor de archivos FIR xover y de archivos FRD (freq. response).
    Se muestra la magnitud y fase de los FIR.

    Este visor está orientado al proyecto FIRtro
        https://github.com/AudioHumLab/FIRtro

    Cada 'viaX.pcm' puede tener asociado un archivo 'viaX.cfg'
    que especifica la Fs y la ganacia aplicada en el convolver.

    Además, si se proporcionan archivos 'viaX.frd' con la FRD del altavoz usado
    en cada via, se visualizará el resultado estimado al aplicar los filtros.

    También se pueden visualizar archivos FIR .pcm o .bin sueltos,
    indicando la Fs en la linea de comandos.

    Acepta archivos FIR en formato PCM float32. Los archivos FRD de la respuesta
    del altavoz pueden tener hasta tres columnas (frecuencia, magnitud  y fase).

    Archivo de configuración del ploteo: FIRtro_viewer.cfg

    Uso:

    FIRtro_viewer.py [-cfg|xxx] path/to/filtro1.pcm  [path/to/filtro2.pcm ... ] [flow-fhigh] [-1]

          -cfg:       Lee Fs y Gain en los archivos '.cfg' asociados a '.pcm'
          xxx:        Toma xxxx como Fs y se ignoran los '.ini'
          flow-fhigh: Rango de frecuencias de la gráfica (opcional, util para un solo fir)
          -1:         Para mostrar las gráficas de los impulsos en una fila única.

    Ejemplo de archivo 'viaX.cfg' (La sintaxis es YAML):

        fs      : 44100
        gain    : -6.8     # Ganancia ajustada en el convolver.
        gainext : 8.0      # Resto de ganancia incluyendo la potencia final
                             radiada en el eje de escucha.

    See also: FRD_tool.py, IRs_viewer.py

"""
#
# v0.1
#   Límites de ploteo en .cfg
#   Lee 'filterN.cfg' asociado a 'filterN.pcm'
#   Fs opcional en command line
# v0.2
#   Uso de scipy.signal.freqz
#   Gráficas de magnitud y phase de los fltros xover '.pcm'
# v0.3
#   Descartar el ploteo de la phase fuera de la banda de paso de los filtros.
# v0.4
#   Si están disponibles las FRDs de los altavoces se muestra el resultado del filtrado.
#   Detecta clips en los FIR de xover
#   Rango de frecuencias en linea de comandos opcional, útil para representar una sola vía.
# v0.4b
#   El semiespectro se computa sobre frecuecias logespaciadas
#   para mejor resolución gráfica en graves.
# v0.4c
#   Umbral para dejar de pintar la phase configurable, se entrega a -50dB
#   ya que parece más conveniente para FIRs cortos con rizado alto.
#   PkOffset en ms
#   El GD recoge en la gráfica el delay del pico del filtro.
#   Se deja de mostrar los taps en 'Ktaps'
#   Se deja opcional pintar la phase
#version = 'v0.4d'
#   Axes de impulsos en una fila opcinalmente
#   Se muestra la versión del programa al pie de las gráficas.
version = 'v0.4e'
#   Python3

# TO DO:
#   Revisar la gráfica de fases
#   Revisar la información mostrada "GD avg" que pretende ser la moda de los valores

import sys
import os.path
import numpy as np
from scipy import signal, interpolate
from scipy.stats import mode    # Usada en la función BPavg
from matplotlib import pyplot as plt
from matplotlib import ticker   # Para rotular a medida
from matplotlib import gridspec # Para ajustar disposición de los subplots
import yaml
import utils

def readConfig():
    """ lee la gonfiguracion del ploteo desde FIRtro_viewer.cfg"""
    global DFTresol
    global frec_ticks, fig_size
    global phaVsMagThr, top_dBs, range_dBs, fmin, fmax

    cfgfile = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/") + "/FIRtro_viewer.cfg"
    with open(cfgfile, 'r') as f:
        config = yaml.load(f)

    phaVsMagThr     = config["plot"]["phaVsMagThr"]
    top_dBs         = config["plot"]["top_dBs"]
    range_dBs       = config["plot"]["range_dBs"]
    fmin            = config["plot"]["fmin"]
    fmax            = config["plot"]["fmax"]
    fig_width       = config["plot"]["fig_width"]
    fig_height      = config["plot"]["fig_height"]
    tmp             = config["plot"]["frec_ticks"]
    frec_ticks      = [ float(x) for x in tmp.split(',') ]
    fig_size        = (fig_width, fig_height)


def prepara_eje_frecuencias(ax):
    """ según las opciones fmin, fmax, frec_ticks de fir_viewer.cgf """
    ax.set_xscale("log")
    fmin2 = 20; fmax2 = 20000
    if fmin:
        fmin2 = fmin
    if fmax:
        fmax2 = fmax
    ax.set_xticks(frec_ticks)
    ax.get_xaxis().set_major_formatter(ticker.ScalarFormatter())
    ax.set_xlim([fmin2, fmax2])

def lee_command_line():

    global fs_commandline, lee_cfgs, pcmnames, fmin, fmax, plotPha
    global plotIRsInOneRow

    plotIRsInOneRow = False
    plotPha = False
    fs_commandline = ""
    lee_cfgs = False
    pcmnames = []

    if len(sys.argv) == 1:
        print (__doc__)
        sys.exit()
    else:
        for opc in sys.argv[1:]:
            if opc in ("-h", "-help", "--help"):
                print (__doc__)
                sys.exit()
            elif opc.isdigit():
                fs_commandline = float(opc)
            elif opc == "-cfg":
                lee_cfgs = True
            elif "-" in opc and opc[0].isdigit() and opc[-1].isdigit():
                fmin, fmax = opc.split("-")
                fmin = float(fmin)
                fmax = float(fmax)
            elif "-ph" in opc:
                plotPha = True
            elif opc == "-1":
                plotIRsInOneRow = True
            else:
                pcmnames.append(opc)

    # si no hay pcms o si no hay (Fs xor cfgs)
    if not pcmnames or not (bool(fs_commandline) ^ lee_cfgs):  # '^' = 'xor'
        print (__doc__)
        sys.exit()

def lee_params(pcmname):
    """ Lee ganancias y Fs indicadas el el .cfg asociado al filtro .pcm """
    gain    = 0.0
    gainext = 0.0

    if fs_commandline:      # no se lee el .cfg
        fs = fs_commandline
    else:                   # se lee el .cfg
        fcfg = pcmname[:-4] + ".cfg"
        fs, gain, gainext = utils.readPCMcfg(fcfg)

    return fs, gain, gainext

def frd_of_pcm(f):
    """ devuelve el nombre del .frd asociado al filtro .pcm (o .bin)
    """
    f = f.replace("\\", "/")
    if "/" in f:
        path = "/".join(f.split("/")[:-1]) + "/"
        f = f.split("/")[-1]
    else:
        path = "./"
    return path + f[3:].replace(".pcm", ".frd").replace(".bin", ".frd")

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

def hroomInfo(magdB, via):
    gmax = np.amax(magdB)
    fgmax = freqs[np.argmax(magdB)]
    tmp1 = str(round(gmax, 1)).rjust(5) + "dBFS"   # dBs maquillados
    tmp2 = utils.KHz(fgmax)                              # frec en Hz o KHz
    info = via[:12].ljust(12) + " max:" + tmp1 + "@ " + tmp2
    # Tenemos en cuenta la gain del .INI si se hubiera facilitado
    if gmax + gain > 0:
        print( f'(!) Warning CLIP: {info}' )
    return info

def prepararaGraficas():
    global fig, grid, axMag, axDrv, axPha, axGD, axIR
    numIRs = len(pcmnames)

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
    axMag.set_ylim([top_dBs - range_dBs, top_dBs])
    axMag.set_ylabel("filter magnitude dB")

    # --- SUBPLOT compartido para pintar los .FRD de los altavoces
    axDrv = axMag.twinx()
    axDrv.grid(linestyle=":")
    axDrv.set_ylabel("--- driver magnitude dB")
    # Lo reubicamos 10 dB abajo para claridad de lectura
    axDrv.set_ylim([top_dBs - range_dBs + 10, top_dBs + 10])
    prepara_eje_frecuencias(axDrv)

    # --- SUBPLOT para pintar el GD
    # comparte el eje X (twinx) con el de la phase
    # https://matplotlib.org/gallery/api/two_scales.html
    axGD = fig.add_subplot(grid[3:5, :])
    axGD.grid(False)
    prepara_eje_frecuencias(axGD)
    # axGD.set_ylim(-25, 75) # dejamos los límites del eje 'y' para cuando conozcamos el GD
    axGD.set_ylabel(u"--- filter GD (ms)")

    # --- SUBPLOT para pintar las PHASEs (alto 2 filas, ancho todas las columnas)
    #     (común con el del GD)
    if plotPha:
        axPha = axGD.twinx()
        axPha.grid(linestyle=":")
        prepara_eje_frecuencias(axPha)
        axPha.set_ylim([-180.0,180.0])
        axPha.set_yticks(range(-135, 180, 45))
        axPha.set_ylabel(u"filter phase")

if __name__ == "__main__":

    # Lee la configuración de ploteo
    readConfig()

    # Lee opciones command line: fs_commandline, lee_cfgs, pcmnames, fmin, fmax
    lee_command_line()

    # Prepara la parrilla de gráficas
    prepararaGraficas()

    # Aquí guardaremos las curvas de cada via
    vias = []

    hay_FRDs = False

    for pcmname in pcmnames:

        #--- Nombre de la vía
        tmp = pcmname.replace("\\", "/") # windows
        via = tmp.split("/")[-1].replace(".pcm", "").replace(".bin", "")

        #--- Leemos el impulso IR y sus parámetros (Fs, gain)
        IR = utils.readPCM32(pcmname)
        fs, gain, gainext = lee_params(pcmname)
        fny = fs / 2.0 # Nyquist

        #   Semiespectro, whole=False para computar hasta pi (Nyquist)
        #   devuelve: h - la FT  y w - las frec normalizadas hasta Nyquist
        w, h = signal.freqz(IR, worN=int(len(IR)/2), whole=False)
        # convertimos las frecuencias normalizadas en reales según la Fs
        freqs = (w / np.pi) * fny

        #--- Extraemos la MAG de la FR 'h'
        #    tomamos en cuenta la 'gain' del .cfg que se aplicará como coeff del convolver
        firMagdB = 20 * np.log10(abs(h)) + gain

        #--- Extraemos la wrapped PHASE de la FR 'h'
        firPhase = np.angle(h, deg=True)
        # Eliminamos (np.nan) los valores de phase fuera de
        # la banda de paso, por debajo de un umbral configurable.
        firPhaseClean  = np.full((len(firPhase)), np.nan)
        mask = (firMagdB > phaVsMagThr)
        np.copyto(firPhaseClean, firPhase, where=mask)

        #--- Obtenemos el GD 'gd' en N bins:
        wgd, gd = signal.group_delay((IR, 1), w=int(len(IR)/2), whole=False)
        # GD es en radianes los convertimos a en milisegundos
        firGDms = gd / fs * 1000
        # Limpiamos con la misma mask de valores fuera de la banda de paso usada arriba
        firGDmsClean  = np.full((len(firGDms)), np.nan)
        np.copyto(firGDmsClean, firGDms, where=mask)
        # Computamos el GD promedio (en ms) para mostrarlo en la gráfica
        #   1. Vemos un primer promedio
        gdmsAvg = np.round(np.nanmean(firGDmsClean), 1)
        #   2. limpiamos las desviaciones > 5 ms respecto del promedio (wod: without deviations)
        gdmswod = np.full((len(firGDmsClean)), np.nan)
        mask = (firGDmsClean < (gdmsAvg + 5.0) ) # nota: se muestra un Warning porque se evalúan valores np.nan
        np.copyto(gdmswod, firGDmsClean, where=mask)
        #   3. Promedio recalculado sobre los valores without deviations
        gdmsAvg = np.round(np.nanmean(firGDmsClean), 1)

        #--- Info del headroom dBFs en la convolución de este filtro pcm
        ihroom = hroomInfo(magdB = firMagdB, via=via)

        curva = {'via':via, 'IR':IR, 'mag':firMagdB, 'pha':firPhaseClean,
                           'gd':firGDmsClean, 'gdAvg':gdmsAvg, 'hroomInfo':ihroom}

        #--- Curvas de los .FRD de los altavoces (si existieran)
        frdname = frd_of_pcm(pcmname)
        if os.path.isfile(frdname):
            hay_FRDs = True
            frd, _ = utils.readFRD(frdname)
            frdFreqs = frd[::, 0]
            frdMag = frd[::, 1]

            # Como las frecuencias del FRD no van a coincidir con las 'freqs' de nuestra FFT,
            # hay que interpolar. Usamos los valores del FRD para definir la función de
            # interpolación. Y eludimos errores si se pidieran valores fuera de rango.
            I = interpolate.interp1d(frdFreqs, frdMag, kind="linear", bounds_error=False,
                                     fill_value="extrapolate")
            # Obtenemos las magnitudes interpoladas en nuestras 'freqs':
            frdMagIpol = I(freqs)
            # Y la reubicamos maomeno en 0 dBs
            frdMagIpol -= BPavg(frdMagIpol)

            # Curva FR resultado de aplicar el filtro PCM a la FR del altavoz
            resMag = firMagdB + frdMagIpol
            # La reubicamos en 0 dB maomeno
            resMag -= BPavg(resMag)

            # Añadimos la curva del driver y el resultado del filtrado
            curva['driver']    = frdMagIpol
            curva['resultado'] = resMag

        else:
            print( f'(i) No se localiza la FR del driver: {frdname}' )

        vias.append( curva )

    if hay_FRDs:
        #----------------------------------------------------------------
        # Curva mezcla de los resultados de filtrado de todas las vias:
        #----------------------------------------------------------------
        # Inicializamos una curva a -1000 dB ;-)
        mezclaTot = np.zeros(len(freqs)) - 1000
        # Y le vamos sumando las curvas resultado de cada via:
        for via in vias:
            resultado = via['resultado']
            mezclaTot = 20.0 * np.log10(10**(resultado/20.0) + 10**(mezclaTot/20.0))
        # La reubicamos en 0 dB
        mezclaTot -= BPavg(mezclaTot)

    #----------------------------------------------------------------
    # PLOTEOS
    #----------------------------------------------------------------
    GDavgs = [] # los promedios de GD de cada impulso, para mostrarlos por separado
    IRnum  = 0
    for curva in vias:

        imp         = curva['IR']
        magdB       = curva['mag']
        phase       = curva['pha']
        gd          = curva['gd']
        gdAvg       = curva['gdAvg']
        info        = curva['hroomInfo']

        limp = imp.shape[0]
        peakOffsetms = np.round(abs(imp).argmax() / fs * 1000, 1) # en ms

        #--- MAG
        axMag.plot(freqs, magdB, "-", linewidth=1.0, label=info)
        color = axMag.lines[-1].get_color() # anotamos el color de la última línea

        #--- PHA
        if plotPha:
            axPha.plot(freqs, phase, "-", linewidth=1.0, color=color)

        #--- GD con autoajuste del top
        ymin = peakOffsetms - 25
        ymax = peakOffsetms + 75
        axGD.set_ylim(bottom = ymin, top = ymax)
        axGD.plot(freqs, gd, "--", linewidth=1.0, color=color)
        GDavgs.append(gdAvg)

        #--- IR (opcionalmente podremos pintar los impulsos en una sola fila)
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

        if 'driver' in curva.keys():
            driver      = curva['driver']
            resultado   = curva['resultado']
            #--- FR del driver
            axDrv.plot(freqs, driver, "--", linewidth=1.0, color=color)
            #--- FR resultado del filtrado
            axMag.plot(freqs, resultado, color="grey", linewidth=1.0)

    if hay_FRDs:
        axMag.plot(freqs, mezclaTot, color="black", linewidth=1.0, label="estimated")

    # La leyenda mostrará las label indicadas en el ploteo de cada curva en 'axMag'
    axMag.legend(loc='lower right', prop={'size':'small', 'family':'monospace'})

    # Y los GDs de cada impulso
    GDtitle = 'GD avg:    ' + '    '.join([str(x) for x in GDavgs]) + ' (ms)'
    axGD.set_title(GDtitle)

    # Y un footer con la versión:
    progname = sys.argv[0].split("/")[-1]
    footer = "AudioHumLab " + progname + " " + version
    plt.gcf().text(0.01, 0.01, footer, size='smaller')

    # Finalmente mostramos las gráficas por pantalla.
    plt.show()

    #----------------------------------------------------------------
    # Y guardamos la gráficas en un PDF:
    #----------------------------------------------------------------
    print( "\nGuardando en el archivo 'filters.pdf'" )
    # evitamos los warnings del pdf
    # C:\Python27\lib\site-packages\matplotlib\figure.py:1742: UserWarning:
    # This figure includes Axes that are not compatible with tight_layout, so
    # its results might be incorrect.
    import warnings
    warnings.filterwarnings("ignore")
    fig.savefig("filters.pdf", bbox_inches='tight')

    print("Bye!")
