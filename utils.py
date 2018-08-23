#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    common use tools
"""
import os.path
import sys
from ConfigParser import ConfigParser
import numpy as np
from scipy.io import wavfile
from scipy import signal
import pydsd
from q2bw import *

def read_REW_EQ_txt(rew_eq_fname):
    """
     Lee un archivo .txt de filtros paramétricos de RoomEqWizard
     y devuelve un diccionario con los parámetros de los filtros
 
     (i) Se precisa que en REW se utilice [Equaliser: Generic]
    """
    f = open(rew_eq_fname, 'r')
    txt = f.read()
    f.close()
 
    PEQs = {}   # Diccionario con el resultado de paramétricos leidos
 
    i = 0
    for linea in txt.split("\n"):
        if "Filter" in linea and (not "Settings" in linea) and ("Fc") in linea:
            active  = ( linea[11:14].strip() == "ON" )
            fc      = float( linea[28:34].strip().replace(",",".") )
            gain    = float( linea[44:49].strip().replace(",",".") )
            Q       = float( linea[56:61].strip().replace(",",".") )
            BW = round( q2bw(float(Q)), 4)  # convertimos Q en BW(oct)
            # Añadimos el filtro
            PEQs[i] = {'active':active, 'fc':fc, 'gain':gain, 'Q':Q, 'BW':BW}
            i += 1
 
    return PEQs

def MP2LP(imp, windowed=True, kaiserBeta=8):
    """
    audiotools/utils/MP2LP(imp, windowed=True, kaiserBeta=8)
 
    Obtiene un impulso linear phase cuyo espectro se corresponde
    en magnitud con la del impulso causal proporcionado.
 
    imp:      Impulso a procesar
    windowed: Boolean para aplicar una ventana al impulso resultante, True por defecto (*)
 
    (*) El enventado afectará a la resolución en IRs con espectro en magnitud muy accidentado.
        Por contra suaviza los microartifactos de retardo de grupo del impulso resultante,
        que son visibles haciendo zoom con 'IRs_viewer.py'. El GD debe ser constante.
     """
    # MUESTRA LA DOC DE ESTA FUNCIÓN:
    # print MP2LP.__doc__
 
    # Obtenemos el espectro completo del impulso dado
    Nbins = len(imp)
    _, h = signal.freqz(imp, worN=Nbins, whole=True)
    wholemag = np.abs(h)
 
    # Obtenemos el impulso equivalente en linear phase
    return wholemag2LP(wholemag , windowed=windowed, kaiserBeta=kaiserBeta)
 
def ba2LP(b, a, m, windowed=True, kaiserBeta=3):
    """
    audiotools/utils/ba2LP(b, a, m, windowed=True, kaiserBeta=4)
 
    Obtiene un impulso linear phase de longitud m cuyo espectro
    se corresponde en magnitud con la de la función de
    transferencia definida por los coeff 'b,a' proporcionados.
 
    b, a:     Coeffs numerador y denominador de la func de transferencia a procesar
    m:        Longitud del impulso resultante
    windowed: Boolean para aplicar una ventana al impulso resultante, True por defecto (*)
 
    (*) El enventanado afecta a la resolución final y se nota sustancialmente
        si procesamos coeffs 'b,a' correspondientes a un biquad type='peakingEQ' estrecho.
        Por contra suaviza los microartifactos de retardo de grupo del impulso resultante
        que son visibles haciendo zoom con 'IRs_viewer.py'. El GD debe ser constante.
    """
    # MUESTRA LA DOC DE ESTA FUNCIÓN:
    # print ba2LP.__doc__
 
    # Obtenemos el espectro completo correspondiente
    # a los coeff b,a de func de transferencia
    Nbins = m
    _, h = signal.freqz(b, a, worN=Nbins, whole=True)
    wholemag = np.abs(h)
 
    # Obtenemos el impulso equivalente en linear phase
    return wholemag2LP(wholemag , windowed=windowed, kaiserBeta=kaiserBeta)
 
def wholemag2LP(wholemag, windowed=True, kaiserBeta=3):
    """
    Obtiene un impulso linear phase cuyo espectro se corresponde 
    en magnitud con el espectro fft proporcionado 'wholemag',
    que debe ser un espectro fft completo y causal.
 
    La longitud del impulso resultante ifft se corresponde con la longitud del espectro de entrada.
 
    Se le aplica una ventana kaiser con 'beta' ajustable.
    """
 
    # Volvemos al dom de t, tomamos la parte real de IFFT
    imp = np.real( np.fft.ifft( wholemag ) )
    # y shifteamos la IFFT para conformar el IR con el impulso centrado:
    imp = np.roll(imp, len(wholemag)/2)
 
    # Enventanado simétrico
    if windowed:
        # imp = pydsd.blackmanharris(len(imp)) * imp
        # Experimentamos con valores 'beta' de kaiser:
        return signal.windows.kaiser(len(imp), beta=kaiserBeta) * imp
    else:
        return imp

def RoomGain2impulse(imp, fs, gaindB):
    """
    Aplica ecualización Room Gain a un impulso
    (Adaptación de DSD/RoomGain.m que se aplica a un espectro)

    fs       = Frecuencia de muestreo.
    imp      = Impulso al que se aplica la ecualización.
    gaindB   = Ganancia total a DC sobre la respuesta plana.
    """
    # Parámetros convencionales para una curva Room Gain
    f1 = 120
    Q  = 0.707
    # Obtenemos los coeff de la curva y la aplicamos al impulso
    b, a = pydsd.biquad(fs, f1, Q, "lowShelf", gaindB)
    return signal.lfilter(b, a, imp)

def maxdB(imp, fs):
    """ busca el máximo en el espectro de un impulso
    """
    # Obtenemos el espectro 'mag' con cierta resolución 1024 bins
    Nbins = 1024
    w, h = signal.freqz(imp, worN=Nbins, whole=False)
    mag  = np.abs(h)
    # buscamos el máximo
    amax = np.amax(mag)             # magnitud máx
    wmax = w[ np.argmax(mag) ]      # frec máx
    fmax = wmax * fs/len(imp)
    return fmax, 20*np.log10(amax)  # frec y mag en dBs

def isPowerOf2(n):
    return np.floor(np.log2(n)) == np.ceil(np.log2(n))

def Ktaps(x):
    """ cutre conversor para mostrar la longitud de un FIR """
    if x >= 1024:
        return str(x / 1024) + " Ktaps"
    else:
        return str(x) + " taps"
    
def KHz(f):
    """ cutre formateo de frecuencias en Hz o KHz """
    f = int(round(f, 0))
    if f in range(1000):
        f = str(f) + "Hz"
    else:
        f = round(f/1000.0, 1)
        f = str(f) + "KHz"
    return f.ljust(8)

def readWAV16(fname):
    fs, imp = wavfile.read(fname)
    return fs, imp.astype('float32') / 32768.0

def readPCM32(fname):
    """ lee un archivo pcm float32
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype='float32', mode='r')
    
def savePCM32(raw, fout):
    # guardamos en raw binary float32
    f = open(fout, 'wb')
    raw.astype('float32').tofile(f)
    f.close()

def readFRD(fname):
    """ devuelve la FR leida en .frd en tuplas (freq, mag, phase)
    """
    f = open(fname, 'r')
    lineas = f.read().split("\n")
    f.close()
    fr = []
    for linea in [x[:-1].replace("\t", " ").strip() for x in lineas if x]:
        if linea[0].isdigit():
            linea = linea.split()
            f = []
            for col in range(len(linea)):
                dato = float(linea[col])
                if col == 2: # hay columna de phases en deg
                    dato = round(dato / 180.0 * np.pi, 4)
                f.append(dato)
            fr.append(f)
    return np.array(fr)

def readPCMini(f):
    """ lee el .ini asociado a un filtro .pcm de FIRtro
    """
    iniPcm = ConfigParser()
    fs = 0
    gain = 0.0
    gainext = 0.0
    if os.path.isfile(f):
        iniPcm.read(f)
        fs      = float(iniPcm.get("miscel", "fs"))
        gain    = float(iniPcm.get("miscel", "gain"))
        gainext = float(iniPcm.get("miscel", "gainext"))
    else:
        print "(!) no se puede accecer a " + f
        sys.exit()
    return fs, gain, gainext
