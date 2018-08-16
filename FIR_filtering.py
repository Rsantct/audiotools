#!/usr/bin/python

# https://scipy-cookbook.readthedocs.io/items/ApplyFIRFilter.html#

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
from matplotlib import pyplot as plt
import sys
import os
import utils

xfile = sys.argv[1]
x = utils.readPCM32(xfile)

yfile = sys.argv[1]
y = utils.readPCM32(xfile)


z = signal.lfilter(y, [1.0], x)#[:, len(x) - 1:]
# Creo que lo suyo seria aplicar una ventana al corte de arriba, ejem

uti.savePCM32(z, "filtered.pcm")
