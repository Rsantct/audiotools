#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

def q2bw(Q):
    """
        convierte un valor de Q a BW en octavas
        http://www.rane.com/note167.html#qformula
        http://www.rane.com/note170.html
    """
    bw = 2.0 / np.log10(2.0) * np.log10( 0.5 * (1/Q + np.sqrt(1/Q**2 + 4)))
    return bw

if __name__ == '__main__':
    pass

