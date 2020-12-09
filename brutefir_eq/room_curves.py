#!/usr/bin/env python3
"""
    Generates psycho acoustic set of curves as target room equalization
    to be used on the Brutefir's run time EQ module.

    Usage:

    room_curves.py   -RXX  -fs=X  -loS=X  -loF=X  -hiF=X   --save  --plot

        -RXX    R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -fs=X   44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

        -loS=X  6 | 12  low shelf slope (default: X=6, 1st order 6 dB/oct)

        -loF=X  Low shelf center frequency (default: X=120 Hz)

        -hiF=X  High roll-off corner frequency (default: X=500 Hz)

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
from smoothSpectrum import smoothSpectrum
from tools import shelf1low, shelf2low, min_phase_from_real_mag

cfolder=f'{HOME}/audiotools/brutefir_eq/curves/room'


def make_low(fc, gain):
    wc = 2 * np.pi * fc / fs
    b, a = {1: shelf1low, 2: shelf2low}[shelf_order](10**(gain/20.0), wc)
    # for compatibility with scipy < v2.x do not use worN= and fs=
    _, h = freqz( b, a, freqs * 2*np.pi / fs )
    return 20 * np.log10( np.abs(h) )


def make_high(fc, gain):
    curve = np.zeros( len(freqs) )
    i0 = len(curve[ freqs < fc ])
    for i, g in enumerate(curve):
        if i > i0:
            curve[i] = (i-i0) * gain / (len(curve)-i0)
    return smoothSpectrum(freqs, curve, Noct=2)


def plotsamples():

    fig, (axMag, axPha) = plt.subplots(2,1)
    fig.set_size_inches(9, 6)
    axMag.set_ylim(-15, 15)
    axPha.set_ylim(-45, 45)

    samples = ('+4.0-1.0', '+3.0-2.0', '+0.0-3.0')
    for curve in samples:
        mag = curves[curve]['mag']
        pha = curves[curve]['pha']
        axMag.semilogx(freqs, mag, label=curve)
        axPha.semilogx(freqs, pha)

    axMag.set_title('psycho acoustic curves for room equalization\n'
                    '(some samples)')
    axMag.legend()
    axMag.set_ylabel('dB')
    axPha.set_ylabel('phase deg')

    plt.show()


def make_curves():
    """
    curves stored in a dictionary
    """

    print(f'cumputing a full set of curves, will take a while ...')

    global freqs, curves

    freqs = get_iso_R(Rseries, fmin=fmin, fs=fs)

    curves = {}
    for lo_gain in lo_gains:
        clo = make_low( fc=fc_low, gain=lo_gain )
        for hi_gain in hi_gains:
            chi = make_high( fc=fc_high, gain=hi_gain )
            hc_mag = clo + chi
            _,_,hc_pha = min_phase_from_real_mag( freqs, hc_mag)
            lo_str = str(round(float(lo_gain), 1))
            hi_str = str(round(float(hi_gain), 1))
            hi_str = f'-{hi_str}'.replace('--', '-')
            curves[f'+{lo_str}{hi_str}'] = {'mag': hc_mag, 'pha': hc_pha}
    return curves


def save_curves():

    if not os.path.isdir(cfolder):
        os.makedirs(cfolder)

    np.savetxt( f'{cfolder}/freq.dat', freqs)

    for curve in curves:
        mag = curves[curve]['mag']
        pha = curves[curve]['pha']
        mname = f'{cfolder}/{curve}_target_mag.dat'
        pname = f'{cfolder}/{curve}_target_pha.dat'
        np.savetxt( mname, mag )
        np.savetxt( pname, pha )

    print(f'freqs saved to:  {cfolder}')


if __name__ == '__main__':

    # Defaults

    # (i) Lets use bass low shelf 1st order slope and centered at 120 Hz,
    #     in coherence with default settings in tone curves.
    shelf_order = 1     # <1>st or <2>nd low shelf order (slope)
    fc_low  = 120       # low shelf center frequency
    fc_high = 500       # high roll-off corner frecuency

    # Will generate a set of curves by combining low shelf and house ranges
    lo_range = 6; lo_step = 1.0
    hi_range = 3; hi_step = 0.5
    lo_gains    = np.arange(0, lo_range + lo_step, lo_step)
    hi_gains    = np.arange(0, hi_range + hi_step, hi_step)

    # Frequency points
    fmin    = 10
    Rseries = 'R20'
    fs      = 44100

    plot = False
    savetodisk = False

    # Read command line options
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()
    for opc in sys.argv[1:]:

        if opc == '-h' or opc == '--help':
            print(__doc__)
            sys.exit()

        elif opc[:2] == '-R':
            Rseries = opc[1:]

        elif opc[:4] == '-fs=':
            value = int(opc[4:])
            if value in (44100, 48000, 96000):
                fs = value

        elif '-loS=' in opc:
            value = int(opc[5:])
            if value in (6, 12):
                shelf_order = {6:1, 12:2}[value]
            else:
                raise ValueError('Low self slope choose 6 or 12 (dB/oct)')

        elif '-loF=' in opc:
            value = int(opc[5:])
            if value >= 20 and value <= 250:
                fc_low = float(value)
            else:
                raise ValueError('Low self center freq 20 ... 250 Hz')

        elif '-hiF=' in opc:
            value = int(opc[5:])
            if value >= 250 and value <= 10000:
                fc_low = float(value)
            else:
                raise ValueError('Hi roll-off corner 250 ... 10000 Hz')

        elif opc == '--save' or opc == '-s':
            savetodisk = True

        elif '-p' in opc:
            plot = True


    shelf_slope_info = {1:'6 dB/oct', 2:'12 dB/oct'}[shelf_order]

    print(f'Using {Rseries} iso frequencies')
    print(f'Low shelf center freq: {fc_low} Hz, slope: {shelf_slope_info}')
    print(f'High roll-off corner:  {fc_high} Hz')


    make_curves()

    if savetodisk:
        save_curves()

    if plot:
        plotsamples()
