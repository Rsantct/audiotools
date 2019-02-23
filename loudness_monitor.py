#!/usr/bin/env python3
"""
    Measures EBU R128 (I)ntegrated Loudness on runtime from an audio 
    sound device.

    Will write it to an --output_file
    
    You can reset the current (I) by writing 'reset' into --input-file
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

    parser = argparse.ArgumentParser(description=__doc__,
              formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-l', '--list-devices', action='store_true',
            help='list audio devices and exit')

    parser.add_argument('-id', '--input_device', type=int_or_str,
            help='input device (numeric ID or substring, see -l)')

    parser.add_argument('-od', '--output_device', type=int_or_str,
            help='output device (numeric ID or substring, see -l)')

    parser.add_argument('-of', '--output_file', type=str, default='.loudness_events',
            help='output file')

    parser.add_argument('-cf', '--control_file', type=str, default='.loudness_control',
            help='control file')

    parser.add_argument('-p', '--print', action="store_true", default=False,
            help='console print out measured loudness')

    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    return args

def callback(indata, frames, time, status):
    """ The handler for input stream audio chunks """
    if status:
        print( f'----- {status} -----' )
    qIn.put( indata )

def amplify( x, gain_dB ):
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
    # coeffs includes 'b', 'a' and initial condition 'zi' for lfilter
    b, a, zi = coeffs
    y = np.copy( x )
    y[:,0], _ = signal.lfilter( b, a, x[:,0], zi=zi*x[:,0][0] )
    y[:,1], _ = signal.lfilter( b, a, x[:,1], zi=zi*x[:,1][0] )
    return y

    
if __name__ == '__main__':

    # FIFO queue
    qIn    = queue.Queue()

    # Reading command line args
    args = parse_cmdline()
    
    # Setting parameters
    fs = sd.query_devices(args.input_device, 'input')['default_samplerate']
    # 100ms block size
    BS = int( fs * 0.100 )
    
    # precalculating coeffs for scipy.lfilter
    hpf_coeffs =    get_coeffs(fs, 100,  .707, 'hpf'            )
    hshelf_coeffs = get_coeffs(fs, 1000, .707, 'highshelf', 4.0 )

    # Initialize 400ms stereo block window
    w400 = np.zeros( (4*BS, 2) , dtype='float32')

    # Intialize (I)ntegrated Loudness and gates to -23.0 dBFS => 0 LU
    M = -23.0
    I = -23.0
    G1mean = -23.0
    G1 = 0          # gate counters to calculate the accu mean
    G2 = 0

    # Reset the accumulated (I) on the fly by reading the control_file
    reset = False
    
    # Main loop: open a capturing stream processing 100ms audio blocks
    with sd.InputStream( device=args.input_device, 
                          callback=callback,
                          blocksize  = BS,
                          samplerate = fs,
                          channels   = 2,
                          dither_off = True):

        while True:
            
            # Reading captured 100 ms (b)locks:
            b100 = qIn.get()

            # “K” weight (f)iltering the 100ms chunks
            f100 = lfilter( b100, hpf_coeffs )      # 100Hz HPF
            f100 = lfilter( f100, hshelf_coeffs )   # 1000Hz High Shelf +4dB

            # Sliding the 400ms (w)indow
            w400[ : BS*3 ] = w400[ BS : ]
            w400[ BS*3 : ] = f100
        
            # Mean square calculation for 400ms audio blocks
            msqL = np.sum( np.square( w400[:,0] ) ) / (fs * 0.4)
            msqR = np.sum( np.square( w400[:,1] ) ) / (fs * 0.4)
            
            # Stereo (M)omentary Loudness
            if msqL or msqR: # avoid log10(0)
                M = -0.691 + 10 * np.log10 (msqL + msqR)
            
            # Dual gatting to compute (I)ntegrated Loudness.
            if M > -70.0:
                # cumulative moving average
                G1 += 1
                G1mean = G1mean + (M - G1mean) / G1
                
            if M > (G1mean - 10.0):
                G2 += 1
                I = G1mean + (M - G1mean) / G2
            
            # Converting FS (Full Scale) to LU (Loudness Units) ref to -23dBFS
            M_LU = M - -23.0
            I_LU = I - -23.0

            # Updating the output file with the accumulated
            # (I)ntegrated loudness in LU units.
            with open( args.output_file, 'w') as fout:
                fout.write( str( round(I_LU,1) ) )
                fout.close()

            # Reading the control file waiting for a 'reset' command
            with open( args.control_file, 'r') as fin:
                cmd = fin.read()
                if cmd:
                    with open( args.control_file, 'w') as fin:
                        fin.write('')
                    if cmd.startswith('reset'):
                        reset = True
            if reset:
                # RESET the accumulated
                I = -23.0
                G1mean = -23.0
                G1 = 0
                G2 = 0
                # and zeroes the output file
                with open( args.output_file, 'w') as fout:
                    fout.write( '0.0' )
                    fout.close()
                reset = False

            # Optionally prints to console
            if args.print:
                print( f'LUFS: {round(M,1):6.1f}(M) {round(I,1):6.1f}(I)       ' +
                        f'LU: {round(M_LU,1):6.1f}(M) {round(I_LU,1):6.1f}(I)   ')
                    
