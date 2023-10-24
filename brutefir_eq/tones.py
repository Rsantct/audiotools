#!/usr/bin/env python3
"""
    Prepare tone EQ curves to be used on Brutefir eq coeff.

    First or second order shelving filters are available.

    Usage:

    tones.py    -RXX  -fs=X  -o=X -b=X -t=X  --save  --plot

        -RXX:   R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -NXX:   overrides iso R series, then using 2**XX linspaced freq values

        -fs=X   44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

        -o=X    1 | 2  low shelf order (default: 1, 1st order 6 dB/oct)

        -b=X    set bass   center frequency at X Hz (default 120 Hz)

        -t=X    set treble center frequency at X Hz (default 2500 Hz)

        --save  save curves to disk

        --plot

"""
import sys
import os
import numpy as np
from scipy.signal import freqz
from matplotlib import pyplot as plt

HOME = os.path.expanduser("~")
sys.path.append(f'{HOME}/audiotools')
from iso_R import get_iso_R
from tools import shelf1low, shelf2low, shelf1high, shelf2high, \
                  make_linspaced_freq


def plot_all():

    fig, (axmag, axpha) = plt.subplots(2,1)

    axmag.set_ylim(-span-3, +span+3)
    axmag.set_title(f'bass@{fc_bass} Hz, treble@{fc_treble} Hz, slope {slopeInfo}')
    axmag.set_ylabel('gain dB')

    axpha.set_ylim(-50, +50)
    axpha.set_ylabel('phase deg')

    for i, _ in enumerate(bass_mag):
        if not i%3 == 0:
            continue
        gain = i - (bass_mag.shape[0] - 1) / 2
        axmag.semilogx( freqs, bass_mag[i]   , label=f'{gain} dB')
        axmag.semilogx( freqs, treble_mag[i] )

    for i, _ in enumerate(bass_pha):
        if not i%3 == 0:
            continue
        axpha.semilogx( freqs, bass_pha[i]   )
        axpha.semilogx( freqs, treble_pha[i] )

    axmag.legend(loc='upper right', bbox_to_anchor=(1.25, 1.0),
                 fontsize='x-small', title='(bass)')
    plt.tight_layout()
    plt.show()


def save_curves():

    if not os.path.isdir(CFOLDER):
        os.makedirs(CFOLDER)

    np.savetxt( f'{CFOLDER}/freq.dat',       freqs      )
    np.savetxt( f'{CFOLDER}/bass_mag.dat',   bass_mag   )
    np.savetxt( f'{CFOLDER}/bass_pha.dat',   bass_pha   )
    np.savetxt( f'{CFOLDER}/treble_mag.dat', treble_mag )
    np.savetxt( f'{CFOLDER}/treble_pha.dat', treble_pha )

    print(f'freqs saved to:  {CFOLDER}')


def make_curves():

    global  freqs,                  \
            bass_mag,   bass_pha,   \
            treble_mag, treble_pha

    if Rseries[0]== 'R':
        freqs = get_iso_R(Rseries, fmin=fmin, fs=fs)

    elif Rseries[0]== 'N':
        N = int(Rseries[1:])
        freqs = make_linspaced_freq(fs, N)

    else:
        print('Error in -Nxx / -Rxx parameter')
        sys.exit()

    # Prepare curves collection arrays
    dB_steps = np.arange(-span, span+step ,step)
    bass_mag    = np.zeros( (len(dB_steps), len(freqs)) )
    bass_pha    = np.zeros( (len(dB_steps), len(freqs)) )
    treble_mag  = np.zeros( (len(dB_steps), len(freqs)) )
    treble_pha  = np.zeros( (len(dB_steps), len(freqs)) )

    for i, dB in enumerate(dB_steps):

        G = 10 ** (dB / 20.0)

        # Compute bass
        wc = 2 * np.pi * fc_bass / fs
        b, a = {1: shelf1low, 2:shelf2low}[shelf_order](G, wc)
        # for compatibility with scipy < v2.x do not use worN= and fs=
        _, h = freqz( b, a, freqs * 2*np.pi / fs )
        mag_dB = 20 * np.log10(abs(h))
        pha_deg = np.angle(h, deg=True)
        bass_mag[i] = mag_dB
        bass_pha[i] = pha_deg

        # Compute treble
        wc = 2 * np.pi * fc_treble / fs
        b, a = {1: shelf1high, 2:shelf2high}[shelf_order](G, wc)
        _, h = freqz( b, a, freqs * 2*np.pi / fs )
        mag_dB = 20 * np.log10(abs(h))
        pha_deg = np.angle(h, deg=True)
        treble_mag[i] = mag_dB
        treble_pha[i] = pha_deg


if __name__ == '__main__':

    # Default parameters

    # (i) FIRtro original bass low shelf was at 160 Hz and 2nd order slope
    #     but we want to align this with the new House Curve centered at
    #     120 Hz and 1st order slope
    shelf_order = 1             # (i) order 1 overlaps bass and treble
    fc_bass     = 120           #
    fc_treble   = 2500
    span        = 12            # tone control span in dB
    step        = 1             # tone curves step in dB

    Rseries     = 'R20'
    fs          = 44100
    fmin        = 10

    plot        = False
    save        = False

    # Read command line options
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()
    for opc in sys.argv[1:]:

        if '-h' in opc:
            print(__doc__)
            sys.exit()

        elif opc[:2] == '-R' or opc[:2] == '-N':
            Rseries = opc[1:]

        elif opc[:4] == '-fs=':
            value = int(opc[4:])
            if value in (44100, 48000, 96000):
                fs = value

        elif opc[:3] == '-o=':
            shelf_order = int(opc[3:])

        elif opc[:3] == '-b=':
            fc_bass = float(opc[3:])

        elif opc[:3] == '-t=':
            fc_treble = float(opc[3:])

        elif '-p' in opc:
            plot = True

        elif '-s' in opc:
            save = True

    slopeInfo = {1:"6 dB/oct", 2:"12 dB/oct"}[shelf_order]

    if Rseries[0] == 'R':
        print(f'Using {Rseries} iso frequencies')
    elif Rseries[0] == 'N':
        print(f'Using 2**{Rseries[1:]} ({2**int(Rseries[1:])}) frequency bins')
    else:
        print('ERROR with freq series')
        sys.exit()

    print(f'bass @{fc_bass} Hz, treble @{fc_treble} Hz, slope {slopeInfo}')

    # Save folder
    CFOLDER = f'curves_{Rseries}'

    make_curves()

    if save:
        save_curves()

    if plot:
        plot_all()
