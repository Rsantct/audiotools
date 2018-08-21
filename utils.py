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

def ba2LP(b, a, m, windowed=True):
    """
    audiotools/utils/ba2LP(b, a, m, windowed=True)

    Esta función pretende obtener un impulso linear phase de longitud m
    cuyo espectro se corresponde en magnitud con la de la función de 
    transferencia de los coeff b,a proporcionados.

    Está inspirada en el mecanismo usado en la función Octave DSD/crossButterworthLP.m
    que aquí aparece traducida a Python/Scipy en audiotools/pydsd.py

    b, a:   Coeffs numerador y denominador de la func de transferencia a procesar
    m:      Longitud del impulso resultante
    w:      Boolean para aplicar una ventana al impulso resultante (*)

    (*) Parece conveniente no aplicar ventana si procesamos coeffs b,a 
        resultantes de un biquad type='peakingEQ' estrecho.

    !!!!!!!
    ACHTUNG: estás usando una función en pruebas, tu sabrás lo que haces
    !!!!!!!
    """

    # MUESTRA UN AVISO:
    print ba2LP.__doc__

    # Obtenemos el espectro correspondiente a los 
    # coeff b,a de la func de transferencia indicada
    Nbins = m
    w, h = signal.freqz(b, a, Nbins, whole=True)
    mag = np.abs(h)

    # tomamos la parte real de IFFT para descartar la phase
    imp = np.real( np.fft.ifft( mag ) )
    # shifteamos la IFFT
    imp = np.roll(imp, Nbins/2)

    if windowed:
        imp = pydsd.blackmanharris(Nbins) * imp

    return imp


def RoomGain2impulse(imp, fs, gaindB):
    """
    Aplica ecualización Room Gain a un impulso
    (Adaptación de DSD/RoomGain.m que se aplica a un espectro)

    fs       = Frecuencia de muestreo.
    imp      = Impulso al que se aplica la ecualización.
    gaindBS  = Ganancia total a DC sobre la respuesta plana.
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
