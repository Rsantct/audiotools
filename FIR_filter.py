#!/usr/bin/env python3

"""
v0.1
Script para combinar dos filtros FIR en formato '.pcm' 32 bits.

Mediante convolución obtenemos el FIR resultado.

Uso:

    FIR_filter.py   path/to/fir_1.pcm   path/to/fir_2.pcm

"""

# (i) Como es de esperar, el resultado es el mismo si cambiamos el
#     orden de los pcm proporcionados. La convolución es conmutativa.

# https://scipy-cookbook.readthedocs.io/items/ApplyFIRFilter.html

# From scipy.signal, lfilter() is designed to apply a discrete IIR filter to a signal,
# so by simply setting the array of denominator coefficients to [1.0],
# it can be used to apply a FIR filter.

# signal.lfilter is designed to filter one-dimensional data. It can take a two-dimensional
# array (or, in general, an n-dimensional array) and filter the data in any given axis.
# It can also be used for IIR filters, so in our case, we'll pass in [1.0] for the
# denominator coefficients. In python, this looks like:
# y = lfilter(b, [1.0], x)
#
# To obtain exactly the same array as computed by convolve or fftconvolve (i.e. to get
# the equivalent of the 'valid' mode), we must discard the beginning of the array computed
# by lfilter. We can do this by slicing the array immediately after the call to filter:
# y = lfilter(b, [1.0], x)[:, len(b) - 1:]

import numpy as np
from scipy import signal
import sys
import tools
import pydsd

try:
    xfile = sys.argv[1]
    yfile = sys.argv[2]
    #zfile = "result.pcm"
    zfile = xfile.replace('.pcm','') + '+' + yfile.replace('.pcm','') + '.pcm'
except:
    print (__doc__)
    sys.exit()


# Leemos los FIR desde los archivos
x = tools.readPCM32(xfile)
y = tools.readPCM32(yfile)

# Ventana que aplicaremos
m = max([len(x), len(y)])
w = pydsd.semiblackmanharris(m)

# Filtramos (aplicando ventana)
z = w * signal.lfilter(y, [1.0], x)#[:, len(x) - 1:] # este slice no lo entiendo

# Guardamos el resultado en el archivo de salida
tools.savePCM32(z, zfile)
print( f'saved: {zfile}' )
