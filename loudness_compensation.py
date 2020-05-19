#!/usr/bin/env python3
"""
    Prepare loudness compensation curves for listening levels referred
    to a given reference phon (dBSPL), to be used on Brutefir eq coeff.

    Usage:

    loudness_compensation.py   -refXX -RXX  -fsXX  --save  --plot

        -refXX: 0 ... 90 phon (default: 83)

        -RXX:   R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -fsXX:  44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

        --save  save curves to disk

"""

import sys
import numpy as np
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt
import iso226
from iso_R import get_iso_R
from utils import extrap1d, min_phase_from_real_mag
import os
HOME = os.path.expanduser("~")

def doplot():

    # Prepare axes
    fig, (ax1, ax2) = plt.subplots(2,1)
    fig.set_size_inches(7,10)
    ax1.set_xlim(10, 30000)
    ax1.set_title("iso226")
    ax1.set_ylabel('phon')
    ax2.set_xlim(10, 30000)
    ax2.set_title(f'loudness compensation for listening levels referred to {refSPL} dBSPL\n'
                  f'--- extrapolated values for {Rseries} from {freqs_isoR[0]} Hz to {freqs_isoR[-1]} Hz')
    fig.subplots_adjust(hspace = 0.5)

    # ax1: plot equal loudness contour curves (10 dB stepped samples)
    for i in np.arange(0, iso226.EQ_LD_CURVES.shape[0], 10):
        ax1.semilogx(iso226.FREQS, iso226.EQ_LD_CURVES[i], label=i)

    # ax2: plot loudness compensation curves referred to refSPL (10dB stepped)
    for i in np.arange(refSPL % 10, ld_compens_curves_RXX.shape[0], 10):
        ax2.semilogx(freqs_isoR, ld_compens_curves_RXX[i],
                                 '--',
                                 color='black')
        ax2.semilogx(iso226.FREQS, ld_compens_curves_iso226[i],
                                   linewidth=1.2,
                                   label=i-refSPL)

    # reverse the order in ax1 legend
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles[::-1], labels[::-1])
    ax2.legend()
    plt.show()


def phase_from_mag(curves):
    phases = np.zeros( curves.shape )
    for i, curve in enumerate(curves):
        _,_,pha = min_phase_from_real_mag( freqs_isoR, curve)
        phases[i] = pha
    return phases


def save_curves():
    """ FIRtro manages Matlab/Octave arrays kind of, so
        transpose() will save them with a column vector form factor.
    """
    folder=f'{HOME}/tmp/audiotools/eq'
    if not os.path.isdir(folder):
        os.makedirs(folder)


    fname = f'{folder}/freq.dat'
    mname = f'{folder}/ref_{refSPL}_loudness_mag.dat'
    pname = f'{folder}/ref_{refSPL}_loudness_pha.dat'
    np.savetxt( fname, freqs_isoR.transpose(),                  fmt='%.4e' )
    np.savetxt( mname, ld_compens_curves_RXX.transpose(),       fmt='%.4e' )
    np.savetxt( pname, phase_from_mag(ld_compens_curves_RXX).transpose(),
                                                                fmt='%.4e' )
    print(f'freqs saved to:  {fname}')
    print(f'curves saved to: {mname}')
    print(f'                 {pname}')


def extrapolate_curves(freqs):
    """ Interpolates iso226 loudness compensation curves by using
        a new array of frequency bands 'freqs', and extrapolates them
        beyond iso226 bands limits.
    """
    curves = np.zeros( (ld_compens_curves_iso226.shape[0], len(freqs)) )
    for i, curve in enumerate(ld_compens_curves_iso226):
        I = interp1d(iso226.FREQS, curve)
        X = extrap1d( I )
        curves[i] = X(freqs)
    return curves


if __name__ == '__main__':

    # Default parameters
    refSPL  = 83
    Rseries = 'R20'
    plot    = False
    save    = False
    fmin    = 10
    fs      = 44100

    # Read command line options
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()
    for opc in sys.argv[1:]:
        if '-h' in opc:
            print(__doc__)
            sys.exit()
        elif opc[:4] == '-ref':
            refSPL = int(opc[4:])
        elif opc[:2] == '-R':
            Rseries = opc[1:]
        elif opc[:3] == '-fs':
            value = int(opc[3:])
            if value in (44100, 48000, 96000):
                fs = value
        elif '-p' in opc:
            plot = True
        elif '-s' in opc:
            save = True

    freqs_isoR = get_iso_R(Rseries, fmin=fmin, fs=fs)

    # Initial version for iso226 29 bands (20 ~ 12500 Hz)
    ld_compens_curves_iso226 = iso226.EQ_LD_CURVES - iso226.EQ_LD_CURVES[refSPL]

    # Let's move curves to easily compensate around the flat one (refSPL curve)
    # Now, the curve at index refSPL is the flat one,
    # the curves at upper index are for EQ at listening levels above refSPL,
    # and the curves at lower index are for EQ at listening below refSPL.
    for level, _ in enumerate(ld_compens_curves_iso226):
        ld_compens_curves_iso226[level] = ld_compens_curves_iso226[level] \
                                          - level + refSPL

    # Extrapolated version for iso RXX frequency bands (usually 20 ~ 20000 Hz)
    ld_compens_curves_RXX = extrapolate_curves(freqs_isoR)

    print(f'Using {Rseries} from {freqs_isoR[0]} Hz to {freqs_isoR[-1]} Hz')
    print(f'Ref dBSPL: {refSPL} (flat curve index)')

    if save:
        save_curves()

    if plot:
        doplot()

