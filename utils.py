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
