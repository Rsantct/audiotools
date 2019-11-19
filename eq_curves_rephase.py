#!/usr/bin/env python3
"""
    WORK IN PROGRESS

    An experimental purpose tool to remake the phase of
    a set of curves from those used in the EQ stage of
    FIRtro / pre.di.c

    usage:   eq_curves_rephase.py  pattern  /path/to/your/eq_folder

        pattern: loudness | bass | treble | xxxxtarget

        It is expected to found a UNIQUE set of curves, so
        if you have several sets please preprare a dedicated folder.

"""

import sys, os
import numpy as np
from scipy.signal import hilbert

def get_curve_files(fpattern):

    try:
        freq_files = [x for x in EQ_FILES if 'freq.dat' in x ]
        if len(freq_files) > 1:
            raise
        else:
            freq_file = freq_files[0]
    except:
        print( f'\n(!) Problems reading a unique \'xxxfreq.dat\' '
               f'at \'{EQ_FOLDER}\'' )
        exit()

    try:
        mag_files = [x for x in EQ_FILES if f'{fpattern}_mag.dat' in x ]
        if len(mag_files) > 1:
            raise
        else:
            mag_file = mag_files[0]
    except:
        print( f'\n(!) problems reading a unique \'***{fpattern}_mag.dat\' '
               f'at \'{EQ_FOLDER}\'' )
        exit()

    pha_file = mag_file.replace('_mag', '_pha')

    return freq_file, mag_file, pha_file


if __name__ == '__main__':

    HOME = os.path.expanduser("~")


    print(  '\n(!) WORK IN PROGRESS, the calculated phase '
            'is NOT correct' )

    # Try to read the optional /path/to/eq_files_folder
    pha = False
    if sys.argv[2:]:
        for opc in sys.argv[2:]:
            if '-h' in opc[0:]:
                print(__doc__)
                exit()
            else:
                EQ_FOLDER = opc
                EQ_FILES = os.listdir(EQ_FOLDER)
    else:
        EQ_FOLDER = f'{HOME}/pe.audio.sys/share/eq'
        EQ_FILES = os.listdir(EQ_FOLDER)


    try:
        pattern = sys.argv[1]
        freq_fname, mag_fname, pha_fname = get_curve_files( pattern )
    except:
        print(__doc__)
        sys.exit()

    freq = np.loadtxt( f'{EQ_FOLDER}/{freq_fname}' )
    mags = np.loadtxt( f'{EQ_FOLDER}/{mag_fname}' )
    phas = np.loadtxt( f'{EQ_FOLDER}/{pha_fname}' )

    if 'target' in mag_fname:
        mags = mags.transpose()
        phas = phas.transpose()

    # Derive the phase ( notice mag is in dB )

    # target curves have only one dimension
    if len( mags.shape ) == 1:

        dphas = np.angle( ( hilbert( np.abs( 10**(mags/20) ) ) ) )
        dphas = dphas * 180.0 / np.pi

    # loudness and tone have severals inside
    else:

        dphas = np.ndarray( mags.shape )
        i = 0
        for mag in mags:
            dpha = np.angle( ( hilbert( np.abs( 10**(mag/20) ) ) ) )
            dpha = dpha * 180.0 / np.pi
            dphas[i,:] = dpha
            i += 1

    freq_fname_new = 'repha_' + freq_fname
    mag_fname_new  = 'repha_' + mag_fname
    pha_fname_new  = 'repha_' + pha_fname

    # Saving new set under an underlying directory ./repha/
    try:
        os.mkdir('repha')
    except:
        pass
    np.savetxt( f'./repha/{freq_fname_new}', freq)
    np.savetxt( f'./repha/{mag_fname_new}',  mags)
    np.savetxt( f'./repha/{pha_fname_new}', dphas)


