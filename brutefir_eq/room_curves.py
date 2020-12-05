#!/usr/bin/env python3
"""
    Generates psycho acoustic set of curves as target room equalization
    to be used on the FIRtro's Brutefir eq coeff.

    Usage:

    room_curves.py  -RXX -fs=X -loS=X -loG=X -loF=X -hiA=X -hiF=X --save --plot

        -RXX    R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -fs=X   44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

        -loS=X  6 | 12  low shelf slope (default: X=6, 1st order 6 dB/oct)

        -loG=X  Low shelf gain (default: from 0 to +6.0 dB, 1 dB step)

        -loF=X  Low shelf center frequency (default: X=120 Hz)

        -hiA=X  High roll-off end atten (default: from 0 to -6.0 dB, 1 dB step)

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


def make_low(fc, gain):
    wc = 2 * np.pi * fc / fs
    b, a = {1: shelf1low, 2: shelf2low}[shelf_order](10**(gain/20.0), wc)
    w, h = freqz( b, a, f, fs=fs )
    return 20 * np.log10( np.abs(h) )


def make_high(fc, gain):
    curve = np.zeros( len(f) )
    i0 = len(curve[ f < fc ])
    for i, g in enumerate(curve):
        if i > i0:
            curve[i] = (i-i0) * gain / (len(curve)-i0)
    return smoothSpectrum(f, curve, Noct=2)


def doplotexample():

    # Getting the last generated curve
    hc = curves[list(curves.keys())[-1]]

    fig, (axMag, axPha) = plt.subplots(2,1)
    fig.set_size_inches(12, 6)
    fig.suptitle('house curve vs syseq, DSS')
    axMag.set_ylim(-8, 8)
    axPha.set_ylim(-45, 45)

    axMag.semilogx(f, hc["mag"], label='hc', color='blue')
    axPha.semilogx(f, hc["pha"], label='hc', color='blue')

    samples_f = f'{HOME}/audiotools/brutefir_eq/eq_samples/'
    f2       = np.loadtxt(f'{samples_f}/R20-freq.dat').transpose()
    DSS      = np.loadtxt(f'{samples_f}/R20-DSS_mag.dat').transpose()
    DSSpha   = np.loadtxt(f'{samples_f}/R20-DSS_mag.dat').transpose()
    SYSEQ    = np.loadtxt(f'{samples_f}/R20-syseq_mag.dat').transpose()
    SYSEQpha = np.loadtxt(f'{samples_f}/R20-syseq_pha.dat').transpose()
    axMag.semilogx(f2, DSS,         '--', label='DSS', color='red')
    axPha.semilogx(f2, DSSpha,      '--', label='DSS', color='red')
    axMag.semilogx(f2, SYSEQ + 6.0, '--', label='syseq', color='green')
    axPha.semilogx(f2, SYSEQpha,    '--', label='syseq', color='green')

    axMag.legend()
    plt.show()


def doplotall():

    fig, (axMag, axPha) = plt.subplots(2,1)
    fig.set_size_inches(9, 6)
    axMag.set_ylim(-8, 8)
    axPha.set_ylim(-45, 45)

    for curve in curves:
        mag = curves[curve]['mag']
        pha = curves[curve]['pha']
        axMag.semilogx(f, mag)
        axPha.semilogx(f, pha)

    plt.show()


def make_curves():
    """
    curves stored in a dictionary
    """
    curves = {}
    for lo_gain in lo_gains:
        clo = make_low( fc=fc_low, gain=lo_gain )
        for hi_gain in hi_gains:
            chi = make_high( fc=fc_high, gain=hi_gain )
            hc_mag = clo + chi
            _,_,hc_pha = min_phase_from_real_mag( f, hc_mag)
            lo_str = str(round(float(lo_gain), 1))
            hi_str = str(round(float(hi_gain), 1))
            hi_str = f'-{hi_str}'.replace('--', '-')
            curves[f'+{lo_str}{hi_str}'] = {'mag': hc_mag, 'pha': hc_pha}
    return curves


def save_curves():
    """ FIRtro manages Matlab/Octave arrays kind of, so
        transpose() will save them with a column vector form factor.
    """
    folder=f'{HOME}/tmp/audiotools/eq/target_sets'
    if not os.path.isdir(folder):
        os.makedirs(folder)

    fname = f'{folder}/freq.dat'
    np.savetxt( fname, f.transpose() )

    for curve in curves:
        mag = curves[curve]['mag']
        pha = curves[curve]['pha']
        mname = f'{folder}/{curve}_target_mag.dat'
        pname = f'{folder}/{curve}_target_pha.dat'
        np.savetxt( mname, mag )
        np.savetxt( pname, pha )

    print(f'freqs saved to:  {folder}/freq.dat')
    print(f'curves saved to: {folder}/L-H_target_mag.dat')
    print(f'                 {folder}/L-H_target_pha.dat')


if __name__ == '__main__':

    # Defaults

    # (i) Lets use bass low shelf 1st order slope and centered at 120 Hz,
    #     in coherence with default settings in tone curves.
    shelf_order = 1     # <1>st or <2>nd low shelf order (slope)
    fc_low  = 120       # low shelf center frequency
    fc_high = 500       # high roll-off corner frecuency

    # Will generate a set of curves by combining low shelf and house ranges
    dB_range  = 6       # use integer
    dB_step   = 1       # use integer
    lo_gains  = []      # the wanted gains for low shelf
    hi_gains  = []      # the wanted gaings for high roll-off

    # Frequency bins
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

        elif '-loG=' in opc:
            value = float(opc[5:])
            if value >= 0.0 and value <= 12.0:
                lo_gains = [value]
            else:
                raise ValueError('Low self gain between 0 ... 12 dB')

        elif '-loF=' in opc:
            value = int(opc[5:])
            if value >= 20 and value <= 250:
                fc_low = float(value)
            else:
                raise ValueError('Low self center freq 20 ... 250 Hz')

        elif '-hiA=' in opc:
            value = float(opc[5:])
            if value >= 0.0 and value <= 12.0:
                hi_gains = [-value]
            else:
                raise ValueError('Hi roll-off between 0 ... 12 dB')

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


    f = get_iso_R(Rseries, fmin=fmin, fs=fs)
    shelf_slope_info = {1:'6 dB/oct', 2:'12 dB/oct'}[shelf_order]

    print(f'Using {Rseries} iso frequencies'
          f' from {int(f[0])} Hz to {int(f[-1])} Hz (fs: {fs})')
    print(f'Low shelf center freq: {fc_low} Hz, slope: {shelf_slope_info}')
    print(f'High roll-off corner: {fc_high} Hz')

    # If not a gain is selected, will make set of curves (i.e 0...6 dB)
    if not lo_gains:
        lo_gains = np.arange(0, dB_range + dB_step, dB_step)
    if not hi_gains:
        hi_gains = np.arange(0, dB_range + dB_step, dB_step) * -1

    print('cumputing curves...')
    curves   = make_curves()

    if plot:
        doplotexample()
        #doplotall()

    if savetodisk:
        save_curves()
