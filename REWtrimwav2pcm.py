#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    v0.1
    Utilidad para recortar un IR .wav de DRC exportado
    desde REW Room EQ Wizard.

    Adaptación del original trimwav2pcm.m del paquete DSD
    https://github.com/rripio/DSD

    Se observa que el impulso wav de 128 Ktaps que proporciona REW, 
    tiene el pico desplazado 44100 muestras, por tanto el mecanismo 
    de trim desde el principio resulta en todo a cero.
        
"""
# https://github.com/rripio/DSD
# Copyright (C) 2012 Roberto Ripio
#    
#    function trimwav2pcm(filename)
#    
#    m=2^15; % longitud del impulso
#    filenamewav = [filename '.wav'];
#    [imp, FS, BITS] = wavread (filenamewav);
#    w = semiblackman(m);
#    imp = imp(1:m) .* w;
#    savepcm(imp,[filename '.pcm']);
#    
#    end

import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import blackmanharris
import pydsd as dsd

def readWAV16(fname):
    fs, imp = wavfile.read(fname)
    return fs, imp.astype('float32') / 32768.0
    
def savePCM32(raw, fout):
    # guardamos en raw binary float32
    f = open(fout, 'wb')
    raw.astype('float32').tofile(f)
    f.close()

# ------------------------   config   -----------------------------
# Longitud total deseada
m = 2 ** 15 
#
# Fracción de m que se tomará para enventanar por delante del pico
frac = 0.001
# -----------------------------------------------------------------

# Leemos el archivo que se pasa
f_in = sys.argv[1]
fs, imp1 = readWAV16(f_in)

# Buscamos el pico:
pkpos = abs(imp1).argmax()

# Hacemos dos ventanas, una muy corta por delante para pillar bien el impulso
# y otra larga por detrás hasta completar los taps finales deseados:
nleft  = int(frac * m)
nright = m - nleft

imp2L = imp1[pkpos-nleft:pkpos]  * dsd.semiblackman(nleft)[::-1]
imp2R = imp1[pkpos:pkpos+nright] * dsd.semiblackman(nright)


# Guardamos el resultado
f_out = f_in.replace(".wav", ".pcm")
savePCM32(np.concatenate([imp2L, imp2R]), f_out)
print "recortado y guardado en:", f_out




