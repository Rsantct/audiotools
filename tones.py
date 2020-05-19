#!/usr/bin/env python3
"""
    Prepare tone EQ curves to be used on Brutefir eq coeff

    Usage:

    tones.py    -RXX  -fsXX  -oX -bX -tX   --save  --plot

        -RXX:   R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -fsXX:  44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

        -oN:    1 | 2  low shelf order (default: 1, 1st order 6 dB/oct)

        -bX:    set bass   center frequency at X Hz (default 120 Hz)

        -tX:    set treble center frequency at X Hz (default 2500 Hz)

        --save  save curves to disk

        --plot

"""

import sys
import numpy as np
from scipy import signal
from matplotlib import pyplot as plt
from iso_R import get_iso_R
from utils import shelf1low, shelf2low, shelf1high, shelf2high
import os
HOME = os.path.expanduser("~")


def make_curves():
    global curves_bass_mag,   curves_bass_pha
    global curves_treble_mag, curves_treble_pha

    # Prepare curves collection arrays
    dB_steps = np.arange(-span, span+step ,step)
    curves_bass_mag    = np.zeros( (len(dB_steps), len(freqs)) )
    curves_bass_pha    = np.zeros( (len(dB_steps), len(freqs)) )
    curves_treble_mag  = np.zeros( (len(dB_steps), len(freqs)) )
    curves_treble_pha  = np.zeros( (len(dB_steps), len(freqs)) )

    for i, dB in enumerate(dB_steps):

        G = 10 ** (dB / 20.0)

        # Compute bass
        wc = 2 * np.pi * fc_bass / fs
        b, a = {1: shelf1low, 2:shelf2low}[shelf_order](G, wc)
        w, h = signal.freqz( b, a, freqs, fs=fs )
        mag_dB = 20 * np.log10(abs(h))
        pha_deg = np.angle(h, deg=True)
        curves_bass_mag[i] = mag_dB
        curves_bass_pha[i] = pha_deg

        # Compute treble
        wc = 2 * np.pi * fc_treble / fs
        b, a = {1: shelf1high, 2:shelf2high}[shelf_order](G, wc)
        w, h = signal.freqz( b, a, freqs, fs=fs )
        mag_dB = 20 * np.log10(abs(h))
        pha_deg = np.angle(h, deg=True)
        curves_treble_mag[i] = mag_dB
        curves_treble_pha[i] = pha_deg


def prepare_plot():
    fig, (axMag, axPha) = plt.subplots(2,1)
    axMag.set_ylim(-span, +span)
    axMag.set_title(f'bass@{fc_bass} Hz, treble@{fc_treble} Hz, slope {slopeInfo}')
    axMag.set_ylabel('gain dB')
    axPha.set_ylim(-50, +50)
    axPha.set_ylabel('phase deg')
    return fig, (axMag, axPha)


def plot_all():
    global curves_bass_mag,   curves_bass_pha
    global curves_treble_mag, curves_treble_pha

    fig, (axMag, axPha) = prepare_plot()
    for mag in curves_bass_mag:
        axMag.semilogx(freqs, mag)
    for mag in curves_treble_mag:
        axMag.semilogx(freqs, mag)
    for pha in curves_bass_pha:
        axPha.semilogx(freqs, pha)
    for pha in curves_treble_pha:
        axPha.semilogx(freqs, pha)
    plt.show()


def plot_single_settings(*pairs):

    fig, (axMag, axPha) = prepare_plot()

    for dB_bass, dB_treble in pairs:

        G_bass   = 10 ** (dB_bass   / 20.0)
        G_treble = 10 ** (dB_treble / 20.0)

        # Compute bass
        wc = 2 * np.pi * fc_bass / fs
        b, a = {1: shelf1low, 2:shelf2low}[shelf_order](G_bass, wc)
        w, h_lo = signal.freqz( b, a, freqs, fs=fs )

        # Compute treble
        wc = 2 * np.pi * fc_treble / fs
        b, a = {1: shelf1high, 2:shelf2high}[shelf_order](G_treble, wc)
        w, h_hi = signal.freqz( b, a, freqs, fs=fs )

        mag_dB = 20 * np.log10(abs(h_lo * h_hi)) # product equals summ in dB
        pha_deg = np.angle(h_lo * h_hi, deg=True)
        line = axMag.semilogx(w, mag_dB, label=f'b:{dB_bass} t:{dB_treble}')
        color = line[0].get_color()
        axPha.semilogx(w, pha_deg, color=color)

    axMag.legend()
    plt.show()


def save_dat():
    """ FIRtro manages Matlab/Octave arrays kind of, so
        transpose() will save them with a column vector form factor.
    """
    folder=f'{HOME}/tmp/audiotools/eq'
    if not os.path.isdir(folder):
        os.makedirs(folder)

    np.savetxt( f'{folder}/freq.dat', freqs.transpose(), fmt='%.4e' )
    np.savetxt( f'{folder}/bass_mag.dat',   curves_bass_mag.transpose(),
                                            fmt='%.4e' )
    np.savetxt( f'{folder}/bass_pha.dat',   curves_bass_pha.transpose(),
                                            fmt='%.4e' )
    np.savetxt( f'{folder}/treble_mag.dat', curves_treble_mag.transpose(),
                                            fmt='%.4e' )
    np.savetxt( f'{folder}/treble_pha.dat', curves_treble_pha.transpose(),
                                            fmt='%.4e' )

    print(f'freqs saved to:  {folder}/freq.dat')
    print(f'curves saved to: {folder}/<bass|treble>_mag.dat')
    print(f'                 {folder}/<bass|treble>_pha.dat')

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
        elif opc[:2] == '-R':
            Rseries = opc[1:]
        elif opc[:3] == '-fs':
            value = int(opc[3:])
            if value in (44100, 48000, 96000):
                fs = value
        elif opc[:2] == '-o':
            shelf_order = int(opc[2:])
        elif opc[:2] == '-b':
            fc_bass = float(opc[2:])
        elif opc[:2] == '-t':
            fc_treble = float(opc[2:])
        elif '-p' in opc:
            plot = True
        elif '-s' in opc:
            save = True

    freqs     = get_iso_R(Rseries, fmin=fmin, fs=fs)
    slopeInfo = {1:"6 dB/oct", 2:"12 dB/oct"}[shelf_order]

    # Compute curves
    make_curves()

    print(f'Using {Rseries} from {freqs[0]} Hz to {freqs[-1]} Hz (fs: {fs})')
    print(f'bass @{fc_bass} Hz, treble @{fc_treble} Hz, slope {slopeInfo}')

    if save:
        save_dat()

    if plot:
        #plot_all()
        plot_single_settings( [6, 0], [0, 6], [-4, -2] )


