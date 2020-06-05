#!/usr/bin/env python3

# Copyright (c) 2020 Rafael Sánchez
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
    A simple audio meter

    To view suported devices use '-l' option
    
    For options available use '-h'

"""
import sys
import argparse
import numpy as np
import queue
import threading
# Thanks to https://python-sounddevice.readthedocs.io
import sounddevice as sd


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def parse_cmdline():

    parser = argparse.ArgumentParser(description=__doc__,
              formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-l', '--list-devices', action='store_true',
            help='list audio devices and exit')

    parser.add_argument('-id', '--input_device', type=int_or_str,
            default='pre_in_loop',
            help='input device (numeric ID or substring, see -l)')

    parser.add_argument('-m', '--mode', type=str,
            default='rms',
            help='\'rms\' or \'peak\'')

    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    return args


class Meter(object):


    def __init__(self, device, mode='rms', bar=True):
        self.device = device
        self.mode   = mode
        self.bar    = bar
        self.L      = -100.0


    def start(self):
        """ Starts metering forever """

        def callback(indata, frames, time, status):
            """ The handler for input stream audio chunks """
            if status:
                print( f'----- {status} -----' )
            qIn.put( indata )


        def measure(block, duration, mode):
            """ Compute the measured level for each audio block"""
            if mode == 'rms':
                # Mean square calculation for audio blocks
                msqL = np.sum( np.square( block[:,0] ) ) / (fs * dur)
                msqR = np.sum( np.square( block[:,1] ) ) / (fs * dur)
                # Combine 2 channels
                if msqL or msqR:    # avoid log10(0+0)
                    M = 20 * np.log10(msqL + msqR) / 2
                else:
                    M = -100.0

            elif mode == 'peak':
                ML, MR = np.max(block[:,0]), np.max(block[:,1])
                M = max(ML, MR)
                if M:
                    M = 20 * np.log10(M)
                else:
                    M = -100.0

            else:
                print('bad mode')
                sys.exit()

            return round(M, 1)


        def loop_forever():
            """ loop capturing stream and processing audio blocks """

            with sd.InputStream(  device=self.device,
                                  callback=callback,
                                  blocksize=bs,
                                  samplerate=fs,
                                  channels= 2,
                                  dither_off=True):
                while True:
                    # Reading captured (b)locks:
                    b = qIn.get()
                    # Compute the measured level
                    self.L = measure(block=b, duration=dur, mode=self.mode)
                    # Print a nice bar meter
                    if self.bar:
                        I = max(-60, int(self.L))
                        print( f' {"#" * (60 + I + 1)}{" " * (-I - 1)}  {self.L}',
                               end='\r')


        h1 = f'-60       -50       -40       -30       -20       -10        0' + \
             f'  {self.mode.upper()}'
        h2 =  ' |    |    |    |    |    |    |    |    |    |    |    |    |'
        if self.bar:
            print(h1)
            print(h2)

        # Prepare an internal FIFO queue for the callback function
        qIn    = queue.Queue()

        # Getting current Fs
        fs = sd.query_devices(self.device, 'input')['default_samplerate']

        # Audio block duration in seconds
        dur = 0.100
        # lenght in samples of the audio block
        bs  = int( fs * dur )

        # Launch a thread that loops metering audio blocks
        jloop = threading.Thread( target=loop_forever, args=() )
        jloop.start()


if __name__ == '__main__':

    # Reading command line args
    args = parse_cmdline()

    # Prepare a meter instance
    meter = Meter(device=args.input_device, mode=args.mode, bar=True)

    # Do start metering
    meter.start()
