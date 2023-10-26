#!/usr/bin/env python3
"""
    Prepare loudness compensation curves for listening levels referred
    to a given reference phon (dBSPL), to be used on Brutefir eq coeff.

    The curves follows the ISO 226:2003 normal equal-loudness-level contours


    Usage:

    loudness_compensation_curves.py   -RXX  -ref=X,Y,...  -fs=X     --save  --plot

        -RXX            R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -ref=X,Y,..     comma separated values for desired listening reference SPLs
                        0 ... 90 phon ~ dBSPL (default: 83)

        -fs=X           44100 | 48000 | 96000  sampling frequency Hz
                        (default: 44100, upper limits RXX to 20000 Hz)

        --save          save curves to disk

"""

import sys
import os
import json
import numpy as np
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

HOME = os.path.expanduser("~")
sys.path.append(f'{HOME}/audiotools')
import iso226
from iso_R import get_iso_R
from tools import extrap1d, min_phase_from_real_mag, make_linspaced_freq
from smoothSpectrum import smoothSpectrum as smooth

# Default parameters
refSPL  = 83
Rseries = 'R20'
plot    = False
save    = False
fmin    = 10
fs      = 44100


def doplot():

    # Prepare axes
    fig, (axISO, axMAG, axPHA) = plt.subplots(3, 1)
    fig.set_size_inches(7,12)
    fig.suptitle(f'refSPL={refSPL}')

    # iso226 equal loudness contour curves
    axISO.set_xlim(10, 20000)
    axISO.set_title(f'iso226 equal loudness curves (20 Hz ~ 12.5 Khz)' )
    axISO.set_ylabel('phon')
    for phon, curve in enumerate( iso226.EQ_LD_CURVES ):
        if phon % 10 != 0:
            continue
        axISO.semilogx( iso226.FREQS, curve, label=f'{phon} phon' )
    axISO.legend(fontsize='small')

    # loudness compensation curves referred to refSPL (10dB stepped)
    axMAG.set_xlim(10, 20000)
    axMAG.set_ylabel('dB')
    axMAG.set_title(f'loudness contour compensation for listening levels\n'
                    f'referred to {refSPL} dBSPL (extended to {Rseries} bands)')
    for i, curve in enumerate( loudcomp_mag ):
        if i % 10 != 0:
            continue
        # Derive the relative level for each curve
        dBr =  i - refSPL
        axMAG.semilogx( freqs,        curve, label=f'#{i}: {dBr} dBr' )
    axMAG.legend(fontsize='small', title='#curve: gain', loc='upper center')

    # the phase of loudness compensation curves
    axPHA.set_xlim(10, 20000)
    axPHA.set_ylabel('deg')
    axPHA.set_title(f'loudness contour compensation (phase)')
    for i, curve in enumerate( loudcomp_pha ):
        if i % 10 != 0:
            continue
        # Derive the relative level for each curve
        dBr =  i - refSPL
        axPHA.semilogx( freqs,        curve, label=f'#{i}: {dBr} dBr' )


    fig.subplots_adjust(hspace = 0.5)


def phase_from_mag(freqs, curves):
    phases = np.zeros( curves.shape )
    for i, curve in enumerate(curves):
        _,_,pha = min_phase_from_real_mag( freqs, curve)
        phases[i] = pha
    return phases


def save_curves():

    if not os.path.isdir(CFOLDER):
        os.makedirs(CFOLDER)

    np.savetxt(f'{CFOLDER}/freq.dat',                      freqs)
    np.savetxt(f'{CFOLDER}/ref_{refSPL}_loudness_mag.dat', loudcomp_mag)
    np.savetxt(f'{CFOLDER}/ref_{refSPL}_loudness_pha.dat', loudcomp_pha)

    print(f'loudness curves for refSPL={refSPL} saved to: {CFOLDER}')


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


def make_curves():

    global freqs, loudcomp_mag, loudcomp_pha


    if Rseries[0]== 'R':
        freqs = get_iso_R(Rseries, fmin=fmin, fs=fs)

    elif Rseries[0]== 'N':
        N = int(Rseries[1:])
        freqs = make_linspaced_freq(fs, 2**N+1)

    else:
        print('Error in -Nxx / -Rxx parameter')
        sys.exit()

    # (i) iso226.EQ_LD_CURVES have a limited 29 bands (20 ~ 12500 Hz).
    #     Extended version with iso RXX frequency bands (usually 20 ~ 20000 Hz)
    eqloud_mag = extend_curves(iso226.FREQS, iso226.EQ_LD_CURVES, freqs, Noct=2)

    # Differential curves referred to the equal loudness curve whose phons
    # corresponds to the defined reference SPL in our sound system.
    loudcomp_mag = eqloud_mag - eqloud_mag[refSPL]

    # Let's move curves so that can compensate around the flat one (refSPL)
    # Now, the curve at index refSPL is the flat one,
    # Curves at upper index used to compensate at listening levels above refSPL,
    # curves at lower index used to compensate at listening levels below refSPL.
    for phon, _ in enumerate( loudcomp_mag ):
        loudcomp_mag[phon] = loudcomp_mag[phon] - phon + refSPL

    # Retrieving phase from mag
    print( '(equal_loudness) retrieving phase from relative magnitudes, will take a while ...' )
    loudcomp_pha = phase_from_mag( freqs, loudcomp_mag)
    print( '(equal_loudness) done.' )


if __name__ == '__main__':

    # Read command line options
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()
    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        elif '-ref=' in opc:
            refSPL = opc.split('=')[-1]

        elif opc[:2] == '-R' or opc[:2] == '-N':
            Rseries = opc[1:]

        elif opc[:4] == '-fs=':
            value = int(opc[4:])
            if value in (44100, 48000, 96000):
                fs = value

        elif '-p' in opc:
            plot = True

        elif '-s' in opc:
            save = True

    if type(refSPL) == str:
        refSPLs = json.loads(f'[{refSPL}]')
    else:
        refSPLs = [refSPL]


    if Rseries[0] == 'R':
        print(f'Using {Rseries} iso frequencies')
    elif Rseries[0] == 'N':
        print(f'Using 2**{Rseries[1:]} ({2**int(Rseries[1:])}) frequency bins')
    else:
        print('ERROR with freq series')
        sys.exit()

    # Save folder
    CFOLDER = f'curves_{Rseries}'

    for refSPL in refSPLs:
        make_curves()
        if save:
            save_curves()
        if plot:
            doplot()

    if plot:
        if save:
            plt.savefig(f'{CFOLDER}/loudness_compensation_curves.png')
        plt.show()
