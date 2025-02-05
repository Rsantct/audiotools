#!/usr/bin/env python3
"""
    Resamples an FIR filter for a new sample rate

    Usage:

        Float 32 raw mode:  FIR_resample.py  filename  fs  new_fs   [--plot]

        Wavefile mode:      FIR_resample.py  filename  new_fs       [--plot]


        --plot              display frequency responses (can be slow)

"""

import  sys
from    tools               import *
import  matplotlib.pyplot   as plt

# Don't worry if Mac OS will show something like that garbage, after plt.show()
# 2025-01-29 23:10:26.477 Python[13014:1202800] +[IMKClient subclass]: chose IMKClient_Modern
# 2025-01-29 23:10:26.477 Python[13014:1202800] +[IMKInputSession subclass]: chose IMKInputSession_Modern


def resample_fir(fir, fs, fs_new):
    """
        Resamples an FIR filter for a new sample rate.
        (helped by Google Gemini AI)

        Args:
            fir:    The FIR filter coefficients (numpy array).
            fs:     The original sample rate (Hz).
            fs_new: The desired new sample rate (Hz).

        Returns:
            The resampled FIR filter coefficients (numpy array)
            or
            None if the rate change is not feasible.


        NOTICE:

        Interpolation of Magnitude and Phase:
        The code interpolates both the magnitude and phase of the frequency response.
        Interpolating the magnitude alone can lead to poor results.
        This version interpolates the unwrapped phase and then reconstructs the complex frequency response.
        This is a more accurate approach.

        Handling Phase:
        The code unwraps the phase using np.unwrap() before interpolation.
        This prevents issues with phase wrapping, which can cause significant distortion.

        Length Adjustment:
        The np.fft.irfft function can sometimes return an array that is slightly longer than expected.
        The code takes the first M coefficients to ensure the correct length of the resampled filter.

    """

    N = len(fir)

    rate_ratio = fs_new / fs

    if rate_ratio == 1.0:
        pass
        #return fir

    if rate_ratio < 0.01 or rate_ratio > 100:
        print("Warning: Extreme resampling ratio, results may be inaccurate or inefficient. Consider multi-stage resampling.")
        return None

    # New number of taps (M)
    M = int(np.ceil(N * rate_ratio))

    # Frequency response of the original filter
    w, h = signal.freqz(fir, worN=2**15) #len(fir))

    # Interpolate the frequency response to the new frequency range:

    # 1. Frequencies for the new rate
    w_new = np.linspace(0, np.pi, M, endpoint=True)

    # 2. Preparing x_points to interpolate into
    xpoints_old = w / rate_ratio
    xpoints_new = w_new

    # 3. Interpolated magnitude, by now without phase info.
    h_new     = np.interp(xpoints_new, xpoints_old, np.abs(h))

    # 4. Interpolate phase.  A simple approach (often sufficient) is to assume linear phase.
    #    Will use a more sophisticated approach by involving phase unwrapping.
    phase     = np.unwrap( np.angle(h) )
    phase_new = np.interp(xpoints_new, xpoints_old, phase)

    # 5. Reconstruct the transfer function with phase contents
    h_new     = h_new * np.exp( 1j * phase_new )

    # Convert the interpolated frequency response back to time-domain coefficients
    new_fir = np.fft.irfft(h_new)

    # Ensure the correct length (important due to irfft). Take the first M coefficients
    new_fir = new_fir[:M] * pydsd.semiblackmanharris(M)

    return new_fir


def impulse_2_fr(imp, fs, oversampling=1, dB=True):
    """
        Calculate the frequency response of an impulse response

        Oversampling (e.g. 4)  will smooth out the low frequency curve
    """

    N = len(imp) * oversampling

    w, h = signal.freqz(imp, worN=N)

    freqs = w * fs / (2 * np.pi)

    mag = np.abs(h)

    if dB:
        mag = 20 * np.log10( mag )

    return freqs, mag


def read_cmd_line():
    """
        Wavefile mode:      FIR_resample.py  filename  new_fs
        Float 32 raw mode:  FIR_resample.py  filename  fs  new_fs

        returns:

            fname, fir, fs , new_fs

    """

    global plot

    for arg in sys.argv[1:]:

        if '-h' in arg:
            print(__doc__)
            sys.exit()

        if '-plot' in arg:
            plot = True

    try:

        fname = sys.argv[1]

        # WAV file
        if fname.endswith('wav'):
            fs, fir = readWAV( fname )
            new_fs  = int(sys.argv[2])

        # RAW float-32 file
        else:
            fs      = int(sys.argv[2])
            fir     = readPCM32( fname )
            new_fs  = int(sys.argv[3])

        return fname, fir, fs , new_fs

    except:
        print(__doc__)
        sys.exit()


def do_plot(ir_packs):
    """ each ir_pack must be a tuple of: (fir, fs, plot_label)
    """

    plt.figure(figsize=(8, 5))

    for ir_pack in ir_packs:

        _fir, _fs, _label = ir_pack

        print( f'computing magnitude to plot {_label} ...')

        freqs, mag_dB = impulse_2_fr(_fir, _fs)

        plt.plot(freqs, mag_dB, label=_label)

    plt.xscale('log')
    plt.xlim([20, 20000])
    plt.ylim(-48, 12)
    plt.yticks( range(-48, 18, 6) )
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.title("Frequency Response")
    plt.grid(True)
    plt.legend()
    plt.show()


if __name__ == "__main__":

    plot = False

    fname, fir, fs , new_fs = read_cmd_line()

    # Compute the new FIR
    new_fir = resample_fir(fir, fs, new_fs)

    # Saving to file
    new_fname = f'{fname[:-4]}_{new_fs}_Hz'
    print('Saving to:', new_fname)
    savePCM32(new_fir, f'{new_fname}.f32')
    saveWAV(f'{new_fname}.wav', new_fs, new_fir, wav_dtype='int32')

    # Plot the frequency responses
    if plot:
        ir_packs = (
            (fir,       fs,     f'{    fs} Hz'),
            (new_fir,   new_fs, f'{new_fs} Hz')

        )
        do_plot( ir_packs )
