#!/usr/bin/env python3

"""
    A prototype for runtime dsp using Python
"""

# Thanks to https://python-sounddevice.readthedocs.io

import argparse
import numpy as np
from scipy import signal
import sounddevice as sd
import queue
import pydsd 

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def parse_cmdline():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='list audio devices and exit')

    parser.add_argument('-b', '--block-duration', type=float,
                        metavar='DURATION', default=50,
                        help='block size (default %(default)s milliseconds)')

    parser.add_argument('-id', '--input_device', type=int_or_str,
                        help='input device (numeric ID or substring)')

    parser.add_argument('-od', '--output_device', type=int_or_str,
                        help='output device (numeric ID or substring)')

    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    return args

def callback(indata, outdata, frames, time, status):
    """ The handler for full duplex Stream audio chunks """
    if status:
        print( f'----- {status} -----' )
    qIn.put( indata )
    outdata[:] = qOut.get()

# Some example dsp functions to be applied

def amplify( x, gain_dB ):
    # x is a stereo audio block
    gain = 10**(gain_dB/20)
    return x * gain

def get_coeffs(fs, f0, Q, ftype, dBgain=0.0):
    """ this calculates coeffs and initial conditions
        for signal.lfilter to filter audio blocks
    """
    b, a = pydsd.biquad( fs, f0, Q, ftype, dBgain )
    zi   = signal.lfilter_zi(b, a)
    return b, a, zi

def lfilter( x, coeffs):
    # x is a stereo audio block: x[:,0] -> ch0, x[:,1] -> ch1 
    b, a, zi = coeffs
    y = np.copy( x )
    y[:,0], _ = signal.lfilter( b, a, x[:,0], zi=zi*x[:,0][0] )
    y[:,1], _ = signal.lfilter( b, a, x[:,1], zi=zi*x[:,1][0] )
    return y

if __name__ == '__main__':

    # FIFO queues
    qIn    = queue.Queue()
    qOut   = queue.Queue()

    # Reading command line args
    args = parse_cmdline()
    fs = sd.query_devices(args.input_device, 'input')['default_samplerate']
    channels   = sd.query_devices(args.input_device, 'input')['max_input_channels']
    bs  = int(fs * args.block_duration / 1000)

    # precalculating coeffs for scipy.lfilter
    hpf_coeffs =    get_coeffs(fs, 100,  .707, 'hpf'            )
    hshelf_coeffs = get_coeffs(fs, 1000, .707, 'highshelf', 4.0 )

    # Main loop: open a fullduplex audio stream for processing the audio blocks
    with sd.Stream(device=(args.input_device, args.output_device), 
                    callback=callback,
                    blocksize  = bs,
                    samplerate = fs,
                    channels   = channels,
                    dither_off = True):

        while True:
            
            # Reading captured audio blocks
            indata = qIn.get()
            
            # DSP: aplying some filters
            filtered = lfilter( indata,   hpf_coeffs)
            filtered = lfilter( filtered, hshelf_coeffs)

            # Putting filtered audio blocks into the output queue
            qOut.put( filtered )

