#!/usr/env/python
# -*- coding: utf-8 -*-

# This is a Python translation from the original written in Matlab:
#
# https://github.com/IoSR-Surrey/MatlabToolbox
# Institute of Sound Recording
# University of Surrey
# Home of the Tonmeister course and research into psychoacoustic engineering
# Copyright 2016 University of Surrey.

#   Example (original code)
# 
#       % Calculate the 1/3-octave-smoothed power spectral density of the
#       % Handel example.
# 
#       % load signal
#       load handel.mat
#       
#       % take fft
#       Y = fft(y);
#       
#       % keep only meaningful frequencies
#       NFFT = length(y);
#       if mod(NFFT,2)==0
#           Nout = (NFFT/2)+1;
#       else
#           Nout = (NFFT+1)/2;
#       end
#       Y = Y(1:Nout);
#       f = ((0:Nout-1)'./NFFT).*Fs;
#       
#       % put into dB
#       Y = 20*log10(abs(Y)./NFFT);
#       
#       % smooth
#       Noct = 3;
#       Z = iosr.dsp.smoothSpectrum(Y,f,Noct);
#       
#       % plot
#       figure
#       semilogx(f,Y,f,Z)
#       grid on
# 

import numpy as np
from utils import logTransition # used for variable smoothing feature

def smoothSpectrum(X, f, Noct, f0=0, Tspeed="medium"):
    """
    Applies 1/NOCT-octave smoothing to the frequency spectrum contained 
    in vector 'X' sampled at frequencies in vector 'f'. 
    
    'X' can be a log-, magnitude-, or power-spectrum.
    
    Setting Noct to 0 results in no smoothing.

    Algorithm:

    The function calculates the i-th smoothed spectral coefficient sX(i)
    as the sum of the windowed spectrum. The window is a Gaussian whose
    centre frequency is f(i), and whose standard deviation is proportional
    to f(i)/Noct.

    See also IOSR.DSP.LTAS, FFT.

    Copyright 2016 University of Surrey.
    
    This translation to Python adds a VARIABLE SMOOTHING feature:
    
        'f0'    indicates the frequency for transit from 1/N oct smoothing towards
                1/1 smoothing at the spectrum high end.
                If f0 = 0, then CONSTANT 1/N smoothing will be applied.
        
        'Tspeed' (slow, medium, fast) indicates the speed of the transition at f0
    """

    #%% Input checking

    # assert(isvector(X), 'iosr:smoothSpectrum:invalidX', 'X must be a vector.');
    # assert(isvector(f), 'iosr:smoothSpectrum:invalidF', 'F must be a vector.');
    # assert(isscalar(Noct), 'iosr:smoothSpectrum:invalidNoct', 'NOCT must be a scalar.');
    # assert(isreal(X), 'iosr:smoothSpectrum:invalidX', 'X must be real.');
    # assert(all(f>=0), 'iosr:smoothSpectrum:invalidF', 'F must contain positive values.');
    # assert(Noct>=0, 'iosr:smoothSpectrum:invalidNoct', 'NOCT must be greater than or equal to 0.');
    # assert(isequal(size(X),size(f)), 'iosr:smoothSpectrum:invalidInput', 'X and F must be the same size.');

    assert(type(X) is np.ndarray),  "Mag must be an array"
    assert(type(f) is np.ndarray),  "Frec must be an array"
    assert(type(Noct) is int),      "Noct must be an integer '1/Noct octaves'"
    assert(np.all(np.isreal(X))),   "Mag must be real values"
    assert(np.all( f >= 0 )),       "Frec must contain positive values" 
    assert(Noct >= 0),              "Noct must be greater than or equal to 0"
    assert(len(X) == len(f)),       "Mag and Frec must be the same size"
    assert( f0 > 0 or f0 < max(f) ), "f0 must be in the range of Frec"
    assert( Tspeed in ["slow", "medium", "fast"]), "Tspeed mut be 'slow', 'medium' or 'fast'"
    
    #%% Smoothing
    #% calculates a Gaussian function for each frequency,
    #% deriving a bandwidth for that frequency.

    x_oct = np.copy(X)  # initial spectrum (OjO numpy requiere hacer una copia)

    ##################################################################
    # En esta adaptación, Noct pasa a ser un vector de la longitud del 
    # vector 'f' de las frecuencias.
    # Si se pide un smooth variable (f0 <> 0), Noct empezará valiendo N, 
    # y cambiará hacia 1 a partir de la f0 (ver utils/logTransition)
    if f0:
        Noct = (Noct-1) * logTransition(f, f0, speed=Tspeed) + 1
    else:
        Noct = Noct * np.ones( len(f) )
    # print Noct # DEBUG
    ##################################################################
    
    # INICIO DEL SUAVIZADO:
    
    if Noct[0] == 0:                                # Return if no smoothing
        return x_oct

    # Matlab:
    # for i = find(f>0, 1, 'first') : length(f)     # first index for non zero element
    #     g = gauss_f(f, f(i), Noct);
    #     x_oct(i) = sum(g.*X);                     % calculate smoothed spectral coefficient
    # end

    # Numpy:
    start = np.flatnonzero(f)[0]
    for i in range( start, len(f) ):
        g = gauss_f(f, f[i], Noct[i])               # 'Noct[i]' is for variable smoothing
        x_oct[i] = np.sum(g * X)

    # remove undershoot when Mag is positive
    # if all( X >= 0 )                              # Matlab
    #    x_oct( x_oct < 0 ) = 0;
    if np.all( X >= 0 ):                            # Numpy
        x_oct[ x_oct < 0 ] = 0

    return x_oct

def gauss_f(f_x, F , Noct):
    """
    GAUSS_F calculate frequency-domain Gaussian with unity gain
 
    Calculates a frequency-domain Gaussian function
    for frequencies f_x, with centre frequency f and bandwidth f/Noct.
    """
    # Matlab:
    # sigma = (F/Noct)/pi;                                      % standard deviation
    # g = exp(-(((f_x-F).^2)./(2.*(sigma^2))));                 % Gaussian
    # g = g./sum(g);                                            % normalise magnitude
    
    # Numpy:
    sigma = (F/Noct) / np.pi                                    # standard deviation
    g = np.exp( -( ( (f_x-F) ** 2) / (2 * (sigma ** 2) ) ) )    # Gaussian
    g = g / np.sum(g)                                           # normalise magnitude

    return g
