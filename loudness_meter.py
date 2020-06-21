#!/usr/bin/env python3

# Copyright (c) 2019 Rafael Sánchez
# This file is part of 'audiotools'
#
# 'audiotools' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'audiotools' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'pe.audio.sys'.  If not, see <https://www.gnu.org/licenses/>.

"""
    Measures EBU R128 [M]omentary & [I]ntegrated loudness of
    an audio stream from a system sound device.

    To view suported devices use '-l' option

"""
import sys
import os
import argparse
import numpy as np
from scipy.signal import lfilter, lfilter_zi
import queue
import threading
# Thanks to https://python-sounddevice.readthedocs.io
import sounddevice as sd


def biquad(fs, f0, Q, ftype, dBgain=0.0):
    """
    INPUTS:

        fs:         sampling rate
        f0:         filter central frequency
        Q:          quality factor as per "peakingEQ" at "DSP EQ cookbook",
                    stands for the BW from -6 dB points arounf f0.
        ftype:      lpf, hpf, notch, peakingEQ, lowshelf, highshelf (string)
        dBgain:     used for peakingEQ, lowshelf, highshelf kind of filters.

    OUTPUT:

        (b,a):      coeffs of the IIR filter associated to a biquad

    CREDITS:
        #############################################################
        ###  http://www.musicdsp.org/files/Audio-EQ-Cookbook.txt  ###
        #############################################################
    """

    if (Q <= 0):
        raise ValueError("Q must be positive");

    if (f0 <= 0) or (fs <= 0):
        raise ValueError("f must be positive");


    A     = np.sqrt(10 ** (dBgain / 20.0))
    w0    = 2.0 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2.0 * Q)

    if ftype.lower() == "lpf":
        b0 =  (1 - np.cos(w0)) / 2
        b1 =   1 - np.cos(w0)
        b2 =  (1 - np.cos(w0)) / 2
        a0 =   1 + alpha
        a1 =  -2 * np.cos(w0)
        a2 =   1 - alpha

    elif ftype.lower() == "hpf":
        b0 =  (1 + np.cos(w0)) / 2
        b1 = -(1 + np.cos(w0))
        b2 =  (1 + np.cos(w0)) / 2
        a0 =   1 + alpha
        a1 =  -2 * np.cos(w0)
        a2 =   1 - alpha

    elif ftype.lower() == "notch":
        b0 =   1
        b1 =  -2 * np.cos(w0)
        b2 =   1
        a0 =   1 + alpha
        a1 =  -2 * np.cos(w0)
        a2 =   1 - alpha

    elif ftype.lower() == "peakingeq":
        b0 =   1 + alpha * A
        b1 =  -2 * np.cos(w0)
        b2 =   1 - alpha * A
        a0 =   1 + alpha / A
        a1 =  -2 * np.cos(w0)
        a2 =   1 - alpha / A

    elif ftype.lower() == "lowshelf":
        b0 =      A * ( (A+1) - (A-1)*np.cos(w0) + 2*np.sqrt(A)*alpha )
        b1 =  2 * A * ( (A-1) - (A+1)*np.cos(w0)                      )
        b2 =      A * ( (A+1) - (A-1)*np.cos(w0) - 2*np.sqrt(A)*alpha )
        a0 =            (A+1) + (A-1)*np.cos(w0) + 2*np.sqrt(A)*alpha
        a1 = -2 *     ( (A-1) + (A+1)*np.cos(w0)                      )
        a2 =            (A+1) + (A-1)*np.cos(w0) - 2*np.sqrt(A)*alpha

    elif ftype.lower() == "highshelf":
        b0 =      A * ( (A+1) + (A-1)*np.cos(w0) + 2*np.sqrt(A)*alpha )
        b1 = -2 * A * ( (A-1) + (A+1)*np.cos(w0)                      )
        b2 =      A * ( (A+1) + (A-1)*np.cos(w0) - 2*np.sqrt(A)*alpha )
        a0 =            (A+1) - (A-1)*np.cos(w0) + 2*np.sqrt(A)*alpha
        a1 =  2 *     ( (A-1) - (A+1)*np.cos(w0)                      )
        a2 =            (A+1) - (A-1)*np.cos(w0) - 2*np.sqrt(A)*alpha

    else:
        raise ValueError("Wrong biquad type")

    a = np.array([a0, a1, a2])
    b = np.array([b0, b1, b2])
    return b, a


def parse_cmdline():

    def int_or_str(text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text

    parser = argparse.ArgumentParser(description=__doc__,
              formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-l', '--list-devices', action='store_true',
            help='list audio devices and exit')

    parser.add_argument('-id', '--input_device', type=int_or_str,
            help='input device (numeric ID or substring, see -l)')

    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    return args


class LU_meter(object):
    """
        Measures EBU R128 [M]omentary & [I]ntegrated loudness of
        an audio stream from a system sound device.


        .start()        Start to measure

        .reset()        Reset current measurement

        .device         The sound device identifier (see -l command line option)

        .display        On console use, will display measurements (boolean)

        .M              [M]omentary loudness measurement

        .I              [I]ntegrated loudness measurement (cummulated)

        .M_event        Event object to notify the user for changes in [M]

        .M_threshold    Threshold in dB to trigger M_event

        .I_event        Event object to notify the user for changes in [I]

        .I_threshold    Threshold in dB to trigger I_event

    """


    def __init__(self, device, display=False,
                       M_threshold = 1.0,
                       I_threshold = 1.0 ):
        # The sound device
        self.device  = device
        # Boolean for console display measurements
        self.display = display
        # Events to notify the user when M or I
        # changes are greater than a given threshold
        self.M_event = threading.Event()
        self.I_event = threading.Event()
        # Thresholds for levels changes notifications
        # default to 1 dB to avoid stress on triggering events.
        self.M_threshold = M_threshold
        self.I_threshold = I_threshold
        # A flag to RESET measures on the fly:
        self.meas_reset  = False
        # Measured (M)omentary Loudness  dBFS
        self.M = -100.0
        # Measured (I)ntegrated Loudness dBFS
        self.I = -100.0


    def reset(self):
        self.meas_reset = True


    def start(self):
        """ Starts metering forever """


        def display_header():
            print(f'    -------- dBFS --------      --- dBLU @ -23dBFS ---')
            print(f'    Momentary   Integrated      Momentary   Integrated')


        def display_measurements():
            # A header must be already displayed
            M_FS = round(self.M, 1)
            I_FS = round(self.I, 1)
            M_LU = M_FS - -23.0        # from dBFS to dBLU ( 0 dBLU = -23dBFS )
            I_LU = I_FS - -23.0
            print( f'    {M_FS:6.1f}      {I_FS:6.1f}      '
                   f'    {M_LU:6.1f}      {I_LU:6.1f}', end='\r' )


        def get_coeffs(fs, f0, Q, ftype, dBgain=0.0):
            """ this calculates coeffs and initial conditions
                for signal.lfilter
            """
            b, a = biquad( fs, f0, Q, ftype, dBgain )
            zi   = lfilter_zi(b, a)
            return b, a, zi


        def k_filter(x):
            """ input:  stereo audio block: x[:, channel]
                output: x K-filtered, 100Hz HPF + 1000Hz High Shelf +4dB
            """
            y = np.copy( x )
            # coeffs includes 'b', 'a' and initial condition 'zi' for lfilter
            # hpf_coeffs     -->  100Hz HPF
            # hshelf_coeffs  -->  1000Hz High Shelf +4dB
            for coeffs in (hpf_coeffs, hshelf_coeffs):
                b, a, zi = coeffs
                y[:, 0], _ = lfilter( b, a, x[:,0], zi = zi * x[:, 0][0] )
                y[:, 1], _ = lfilter( b, a, x[:,1], zi = zi * x[:, 1][0] )
            return y


        def callback(indata, frames, time, status):
            """ The handler for input stream audio chunks,
                simply puts data into the input-queue
            """
            if status:
                print( f'----- {status} -----' )
            qIn.put( indata )


        def loop_forever():
            """ loop capturing stream and processing audio blocks """

            # Initialize cummulative mean and gates
            G1mean  = -100.0
            G1      = 0
            G2      = 0
            # Memorize last measurements used for evaluate if threshold exceeded
            M_last = -100.0
            I_last = -100.0

            with sd.InputStream(  device=self.device,
                                  callback=callback,
                                  blocksize=bs,
                                  samplerate=fs,
                                  channels= 2,
                                  dither_off=True):
                while True:

                    # Reading captured blocks of 100 ms from the input-queue
                    b100 = qIn.get()

                    # “K” weight filtering the 100ms chunks
                    k100 = k_filter(b100)

                    # Sliding the 400ms (w)indow and filling it with k100 chunks
                    w400[ : bs * 3 ] = w400[ bs : ]
                    w400[ bs * 3 : ] = k100

                    # Mean square calculation for 400ms audio blocks
                    msqL = np.sum( np.square( w400[:,0] ) ) / (fs * 0.4)
                    msqR = np.sum( np.square( w400[:,1] ) ) / (fs * 0.4)

                    # Stereo (M)omentary Loudness (divided by 2 channels)
                    if msqL or msqR:    # avoid log10(0)
                        self.M = -0.691 + 20 * np.log10(msqL + msqR) / 2
                    else:
                        self.M = -100.0

                    # Dual gatting to compute (I)ntegrated Loudness.
                    if self.M > -70.0:
                        # cumulative moving average
                        G1 += 1
                        G1mean = G1mean + (self.M - G1mean) / G1

                    if self.M > (G1mean - 10.0):
                        G2 += 1
                        self.I = G1mean + (self.M - G1mean) / G2

                    # End of measurements, let's manage events:

                    # Reseting on the fly.
                    if self.meas_reset:
                        print('(lu_meter) restarting measurement')
                        self.M  = -100.0
                        self.I  = -100.0
                        G1mean  = -100.0
                        G1 = 0
                        G2 = 0
                        self.meas_reset = False  # releasing the flag

                    # Prints to console
                    if self.display:
                        display_measurements()

                    # Notify an event if changes greater than a given threshold
                    if abs(M_last - self.M) > self.M_threshold:
                        self.M_event.set()
                        M_last = self.M
                    if abs(I_last - self.I) > self.I_threshold:
                        self.I_event.set()
                        I_last = self.I


        # Prepare an internal FIFO queue for the callback process
        qIn = queue.Queue()

        # Getting current Fs from the PortAudio device
        fs = sd.query_devices(self.device, 'input')['default_samplerate']

        # Block size in samples for 100 msec of audio at Fs
        bs  = int( fs * 0.100 )

        # Initialize a 400ms stereo block window
        w400 = np.zeros( (4 * bs, 2) , dtype='float32')

        # Prepare the needed coeffs for 'K' filtering audio blocks
        hpf_coeffs =    get_coeffs(fs, 100,  .707, 'hpf'            )
        hshelf_coeffs = get_coeffs(fs, 1000, .707, 'highshelf', 4.0 )

        # Prepare display header
        if self.display:
            display_header()

        # Launch a thread that loops metering audio blocks forever
        jloop = threading.Thread( target=loop_forever, args=() )
        jloop.start()


if __name__ == '__main__':

    # Reading command line args
    args = parse_cmdline()

    # Prepare a meter instance
    meter = LU_meter(device=args.input_device, display=True)

    # Do start metering
    meter.start()

    # TODO
    # A reset keystroke for console usage
