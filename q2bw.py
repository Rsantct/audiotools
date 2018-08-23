#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

# Fórmulas copiadas de:
# http://www.sengpielaudio.com/calculator-bandwidth.htm
# N == BW_octaves
# N = log(1 + 1 / (2 × Q^2) + sqr(((2 + 1 / (Q^2))^2) / 4 − 1)) / log(2)
# Q = sqr(2^N) / (2^N − 1)
#
# Los resultados coinciden con los de la siguiente TABLA
# http://www.doctorproaudio.com/content.php?7-q-bw-anchodebanda

# Otras fuentes:
#
# http://www.rane.com/note167.html#qformula
# http://www.rane.com/note170.html
# BWoct = 2.0 / np.log10(2.0) * np.log10( 0.5 * (1/Q + np.sqrt(1/Q**2 + 4)))
#
# http://www.musicdsp.org/files/Audio-EQ-Cookbook.txt
# http://shepazu.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html

def q2bw(Q):
    """ Convierte un valor de Q a BW_octavas
    """
    Q = float(Q)
    BWoct = np.log10( 1 + 1 / (2*Q*Q) + np.sqrt(((2 + 1/(Q*Q))**2) / 4 - 1 )) / np.log10(2)
    return BWoct

def bw2q(N):
    """ Convierte un valor BW_octavas a Q
    """
    N = float(N)
    Q = np.sqrt(2**N) / (2**N -1)
    return Q

if __name__ == '__main__':
    pass

