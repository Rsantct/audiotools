#!/usr/bin/env python3
"""
    Prepare loudness compensation curves for listening levels referred
    to a given reference phon (dBSPL), to be used on Brutefir eq coeff.

    Curves follows the ISO 226:2003 normal equal-loudness-level contours

    Usage:

    loudness_compensation.py   -RXX  -ref=X  -fs=X  --save  --plot

        -RXX    R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -ref=X  0 ... 90 phon ~ dBSPL listening reference level (default: 83)

        -fs=X   44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

        --save  save curves to disk

"""

import sys
import os
import numpy as np
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

HOME = os.path.expanduser("~")
sys.path.append(f'{HOME}/audiotools')
import iso226
from iso_R import get_iso_R
from tools import extrap1d, min_phase_from_real_mag
from smoothSpectrum import smoothSpectrum as smooth

def doplot():

    # Prepare axes
    fig, (ax1, ax2) = plt.subplots(2,1)
    fig.set_size_inches(7,10)
    ax1.set_xlim(10, 30000)
    ax1.set_title("iso226")
    ax1.set_ylabel('phon')
    ax2.set_xlim(10, 30000)
    ax2.set_title(f'loudness compensation for listening levels referred to '
                  f'{refSPL} dBSPL\n'
                  f'--- extended values for {Rseries} series')
    fig.subplots_adjust(hspace = 0.5)

    # ax1: plot equal loudness contour curves (10 dB stepped samples)
    for i in np.arange(0, iso226.EQ_LD_CURVES.shape[0], 10):
        ax1.semilogx(iso226.FREQS, iso226.EQ_LD_CURVES[i], label=i)

    # ax2: plot loudness compensation curves referred to refSPL (10dB stepped)
    for i in np.arange(refSPL % 10, lcurves_RXX.shape[0], 10):
        ax2.semilogx(freqs_isoR, lcurves_RXX[i],
                                 '--',
                                 color='black')
        ax2.semilogx(iso226.FREQS, lcurves_iso226[i],
                                   linewidth=1.2,
                                   label=f'{i-refSPL} dBr')

    # reverse the order in ax1 legend
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles[::-1], labels[::-1])
    ax2.legend()
    plt.show()


def phase_from_mag(freqs, curves):
    phases = np.zeros( curves.shape )
    for i, curve in enumerate(curves):
        _,_,pha = min_phase_from_real_mag( freqs, curve)
        phases[i] = pha
    return phases


def save_FIRtro_curves(curves):
    """ FIRtro manages Matlab/Octave arrays kind of, so
        transpose() will save them with a column vector form factor.
    """

    # Let's move curves to easily compensate around the flat one (refSPL curve)
    # Now, the curve at index refSPL is the flat one,
    # the curves at upper index are for EQ at listening levels above refSPL,
    # and the curves at lower index are for EQ at listening below refSPL.
    for level, _ in enumerate(curves):
        curves[level] = curves[level] - level + refSPL

    # (i) Will flipud because FIRtro computes compensation curves in
    # reverse order from the one found inside the _mag.dat and _pha.dat files.
    # So the flat curve index changes from natural flatIdx => refSPL (e.g.: 83)
    # to flatIdx => (90-refSPL) (e.g.: 7)
    curves = np.flipud(curves)

    # Retrieving phase from mag will be done only when saving to disk
    print( 'retrieving phase from curves, will take a while ...' )

    folder=f'{HOME}/tmp/audiotools/eq'
    if not os.path.isdir(folder):
        os.makedirs(folder)

    fname = f'{folder}/freq.dat'
    mname = f'{folder}/ref_{refSPL}_loudness_mag.dat'
    pname = f'{folder}/ref_{refSPL}_loudness_pha.dat'
    np.savetxt( fname, freqs_isoR.transpose() )
    np.savetxt( mname, curves.transpose() )
    np.savetxt( pname, phase_from_mag( freqs_isoR, curves).transpose() )
    print(f'freqs saved to:  {fname}')
    print(f'curves saved to: {mname}')
    print(f'                 {pname}')


def extend_curves(freqs, curves, new_freqs, Noct=0):
    """ Extrapolates (freqs,curves) by using  a new frequency bands 'new_freqs'.
        Noct will smooth the resulting curves in 1/Noct, Noct=0 will not.
    """
    new_curves = np.zeros( (curves.shape[0], len(new_freqs)) )
    for i, curve in enumerate(curves):
        I = interp1d(freqs, curve)
        X = extrap1d( I )
        if Noct:
            new_curves[i] = smooth(new_freqs, X(new_freqs), Noct)
        else:
            new_curves[i] = X(new_freqs)
    return new_curves


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

        elif opc[:5] == '-ref=':
            refSPL = int(opc[5:])

        elif opc[:2] == '-R':
            Rseries = opc[1:]

        elif opc[:4] == '-fs=':
            value = int(opc[4:])
            if value in (44100, 48000, 96000):
                fs = value

        elif '-p' in opc:
            plot = True

        elif '-s' in opc:
            save = True

    freqs_isoR = get_iso_R(Rseries, fmin=fmin, fs=fs)

    # Initial curves set with 29 iso226 bands (20 ~ 12500 Hz).
    # These are differential curves referred to the curve of phons
    # equal to the defined reference SPL in our sound system.
    lcurves_iso226 = iso226.EQ_LD_CURVES - iso226.EQ_LD_CURVES[refSPL]

    # Extended version with iso RXX frequency bands (usually 20 ~ 20000 Hz)
    lcurves_RXX = extend_curves(iso226.FREQS, lcurves_iso226, freqs_isoR, Noct=2)

    print(f'Using {Rseries} from {freqs_isoR[0]} Hz to {freqs_isoR[-1]} Hz')
    print(f'Ref: {refSPL} phon ~ dBSPL listening reference level')
    print(f'flat curve index: {refSPL}, but in disk will flip to index: {90-refSPL}')

    if save:
        save_FIRtro_curves(lcurves_RXX)

    if plot:
        doplot()
