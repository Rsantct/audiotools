#!/usr/bin/env python3
""" A simple tool to convert multicurve '.dat' files from FIRtro / pre.di.c

    Former FIRtro curves array files xxx.dat were stored in the Matlab way,
    so when reading them with numpy.loadtxt() it is needed to transpose
    and flipud in order to access to the curves data in a natural way.

    Currently the curves are stored in a Pythonic way, so the loaded data
    with numpy.loadtxt() will be indexed in a natural order.
"""

import numpy as np
import os
import sys


# Put here the filenames you want yo convert:

tone_fnames = [ 'R20_ext-bass_mag.dat',
                'R20_ext-bass_pha.dat',
                'R20_ext-treble_mag.dat',
                'R20_ext-treble_pha.dat' ]

loudness_fnames = [ 'R20_ext-loudness_mag.dat',
                    'R20_ext-loudness_pha.dat' ]


if __name__ == '__main__':

    os.mkdir('converted')

    for f1 in tone_dat_fnames:

        x = np.loadtxt(f1)

        y = x.transpose()
        y = np.flipud(y)

        f2 = f'converted/{f1[8:]}'
        print(y.shape, f2, y[6])
        np.savetxt(f2, y)


    for f1 in loudness_fnames:

        x = np.loadtxt(f1)

        y = x.transpose()
        y = np.flipud(y)

        y = np.concatenate( (np.zeros((70,y.shape[1])), y) )

        f2 = f'converted/ref_83_{f1[8:]}'
        print(y.shape, f2, y[83])
        np.savetxt(f2, y)

