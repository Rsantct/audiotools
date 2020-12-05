#!/usr/bin/env python3
""" A portable module to compute eq curves to be loaded into the Brutefir's
    run time EQ module:
        - tone (bass & treble) curves
        - loudness compensation curves
        - room psycho acoustic curve
"""
import sys
import os

HOME = os.path.expanduser("~")

sys.path.append(f'{HOME}/audiotools')
from iso_R import get_iso_R
import iso226
from brutefir_eq import tones as tone
from brutefir_eq import loudness_compensation as loud
from brutefir_eq import room_curves as room


# USER's CONFIG PARAMETERS:
fs          = 44100
refSPL      = 83  # default reference SPL for flat loudness contour curve


# Factory default parameters (usually not changed)
# - Common:
Rseries     = 'R20'
fmin        = 10
# - Tones:
# (i) FIRtro original bass low shelf was at 160 Hz and 2nd order slope
#     but we want to align this with the new House Curve centered at
#     120 Hz and 1st order slope
tone.shelf_order   = 1             # (i) order 1 overlaps bass and treble
tone.fc_bass       = 120           #
tone.fc_treble     = 2500
tone.span          = 12            # tone control span in dB
tone.step          = 1             # tone curves step in dB
tone.Rseries       = Rseries
tone.fs            = fs
tone.fmin          = fmin
# - Loudness contour:
loud.refSPL         = refSPL
loud.Rseries        = Rseries
loud.fmin           = fmin
loud.fs             = fs
# - Room curves
#   (i) Lets use bass low shelf 1st order slope and centered at 120 Hz,
#       in coherence with default settings in tone curves.
room.shelf_order    = 1         # <1>st or <2>nd low shelf order (slope)
room.fc_low         = 120       # low shelf center frequency
room.fc_high        = 500       # high roll-off corner frecuency
room.Rseries        = Rseries
room.fmin           = fmin
room.fs             = fs


# FREQS
freqs = get_iso_R(Rseries, fmin=fmin, fs=fs)


def plotall():

    from matplotlib import pyplot as plt

    fig, (axLOUD, axTONE, axROOM) = plt.subplots(3)
    fig.set_size_inches(8,12)
    axTONE.set_ylim(-15, 15)
    axROOM.set_ylim(-15, 15)

    # - Bass
    for i, _ in enumerate(bass_mag):
        axTONE.semilogx(freqs, bass_mag[i])

    # - Treble
    for i, _ in enumerate(treble_mag):
        axTONE.semilogx(freqs, treble_mag[i])

    # - Loudness
    for level in range(0, lcurves_mag.shape[0], 10):
        axLOUD.semilogx(freqs, lcurves_mag[level], label=f'{level - refSPL}')
    axLOUD.legend()

    # - Room
    axROOM.semilogx(freqs, room_mag)

    plt.show()


def do_loudness_curves():
    global  lcurves_mag, lcurves_pha

    # Initial curves set with 29 iso226 bands (20 ~ 12500 Hz).
    # These are differential curves referred to the curve of phons
    # equal to the defined reference SPL in our sound system.
    lcurves_iso226 = iso226.EQ_LD_CURVES - iso226.EQ_LD_CURVES[refSPL]

    # Extended version with iso RXX frequency bands (usually 20 ~ 20000 Hz)
    lcurves_mag = loud.extend_curves( iso226.FREQS, lcurves_iso226, freqs,
                                          Noct=2 )
    print(f'(bf_eq.py) computing phase from {lcurves_mag.shape[0]}'
          f' equal loudness magnitude curves, will take a while ...')
    lcurves_pha = loud.phase_from_mag(freqs, lcurves_mag)
    print(f'(bf_eq.py) done')


def do_tone_curves():
    global  bass_mag,   bass_pha,  \
            treble_mag, treble_pha

    tone.freqs  = freqs
    tone.make_curves()
    bass_mag    = tone.bass_mag
    bass_pha    = tone.bass_pha
    treble_mag  = tone.treble_mag
    treble_pha  = tone.treble_pha


def do_room_curve(lo_gain, hi_gain):
    global  room_mag, room_pha

    room.f       = freqs
    c_lo = room.make_low (fc=room.fc_low,  gain=lo_gain)
    c_hi = room.make_high(fc=room.fc_high, gain=hi_gain)
    room_mag     = c_lo + c_hi
    _,_,room_pha = room.min_phase_from_real_mag( freqs, room_mag)


if __name__ == '__main__':

    doplot = False
    if sys.argv[1:]:
        if '-p' in sys.argv[1]:
            doplot = True

    # DO CURVES
    room_lo_gain = +4.0
    room_hi_gain = -1.0
    do_loudness_curves()
    do_tone_curves()
    do_room_curve(room_lo_gain, room_hi_gain)

    # PLOT
    if doplot:
        plotall()
