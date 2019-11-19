#!/usr/bin/env python3
"""
    WORK IN PROGRESS

    An experimental purpose tool to remake the phase of
    a set of curves from those used in the EQ stage of
    FIRtro / pre.di.c

    usage:   eq_curves_rephase.py  pattern  /path/to/your/eq_folder

        pattern: loudness | bass | treble | xxxxtarget

        It is expected to found a UNIQUE set of curves, so
        if you have several sets please prepare a dedicated folder.

"""
print( '(!) WORK IN PROGRESS: ANALYTICAL PHASE CURVES HAVE A STRANGE SHIFT' )

import sys, os
import numpy as np
from scipy.signal import hilbert
from matplotlib import pyplot as plt

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

    fig, axes = plt.subplots(2)

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

    # Load the frequency vector
    freq = np.loadtxt( f'{EQ_FOLDER}/{freq_fname}' )
    # Load the set of magnitude curves
    magSet = np.loadtxt( f'{EQ_FOLDER}/{mag_fname}' )
    # Load the set of phase curves
    phaSet = np.loadtxt( f'{EQ_FOLDER}/{pha_fname}' )

    if 'target' in mag_fname:
        magSet = magSet.transpose()
        phaSet = phaSet.transpose()

    # (i) Loudness and tone have severals inside, in a shape (63,x)
    #     where x is the curve selector index, each having 63 freq bands


    # Derive the phase ( notice mag is in dB )

    # Prepare a new <D>erivated set of phase curves
    DphaSet = np.ndarray( magSet.shape )

    # Iterate each magnitude curve
    for i in range(magSet.shape[1]):

        mag = magSet[:,i]

        # Derivate the analytic signal from the bare magnitude
        # (foa make a whole spectrum and adding bins for 0 Hz)
        whole_mag = np.concatenate( (   mag[::-1],
                                        [ mag[0], mag[0] ],
                                        mag    ) )
        analytic = np.conj( hilbert( np.abs(10**(whole_mag/20.0)) ) )

        # <D>erivated phase
        Dpha = np.angle( analytic )

        # rad -> deg
        Dpha = Dpha * 180.0 / np.pi

        # Take only the semi spectrum and skip the bin 0
        semi_Dpha = Dpha[ Dpha.shape[0]//2 + 1  : ]

        # Adding the curve to the set of phase curves
        DphaSet[:,i] = semi_Dpha

        # Plot
        axes[0].plot(mag)
        axes[1].plot(semi_Dpha)


    # Plotting the mags and the result phase curves
    plt.show()

    # Saving the new set under an underlying directory ./rephased
    freq_fname_new = 'repha_' + freq_fname
    mag_fname_new  = 'repha_' + mag_fname
    pha_fname_new  = 'repha_' + pha_fname
    try:
        os.mkdir('rephased')
    except:
        pass
    np.savetxt( f'./rephased/{freq_fname_new}', freq   )
    np.savetxt( f'./rephased/{mag_fname_new}',  magSet )
    np.savetxt( f'./rephased/{pha_fname_new}', DphaSet )


