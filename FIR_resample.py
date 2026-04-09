#!/usr/bin/env python3
"""
    Resamples an FIR filter for a new sample rate

    Usage:

        Float 32 raw mode:  FIR_resample.py  filename  fs  new_fs   [options...]

        Wavefile mode:      FIR_resample.py  filename  new_fs       [options...]

        options:

            -plot
            -reco           full FFT reconstruction (default)
            -poly           polyphase resampling
            -upfirdn        up-fir-down method
"""

import  sys
import  tools
import  numpy             as     np
from    scipy             import signal
import  matplotlib.pyplot as     plt
from    math              import gcd

# Don't worry if Mac OS will show something like that garbage, after plt.show()
# 2025-01-29 23:10:26.477 Python[13014:1202800] +[IMKClient subclass]: chose IMKClient_Modern
# 2025-01-29 23:10:26.477 Python[13014:1202800] +[IMKInputSession subclass]: chose IMKInputSession_Modern


def resample_fir_upfirdn(taps, f_in, f_out, correct_DC_gain=True):
    """
    Remuestrea un FIR usando upfirdn con un filtro de interpolación
    de alta atenuación (Kaiser) para evitar leakage en graves.
    """
    # 1. Calcular los factores de upsampling (L) y downsampling (M)
    common_gcd = gcd(int(f_in), int(f_out))
    L = int(f_out // common_gcd)  # Para 48k -> 44.1k, L = 147
    M = int(f_in // common_gcd)   # Para 48k -> 44.1k, M = 160

    # 2. Diseñar el filtro de interpolación (LPF antialiasing)
    # El ancho de banda debe ser el mínimo entre las dos frecuencias de Nyquist
    nyquist_min = min(f_in / 2, f_out / 2)
    cutoff = nyquist_min / (max(L, M) * (f_in / (2 * M))) # Normalizado

    # Usamos una ventana de Kaiser para obtener >100dB de rechazo
    # beta=14 es excelente para evitar el "suelo" de ruido que viste
    num_taps_interp = 20 * max(L, M) # Longitud del filtro de interpolación
    interp_filter = signal.firwin(num_taps_interp, 1/max(L, M),
                                 window=('kaiser', 14))

    # 3. Aplicar upfirdn
    # upfirdn escala la amplitud, multiplicamos por L para compensar la ganancia de inserción
    resampled_taps = signal.upfirdn(interp_filter, taps, up=L, down=M) * L

    # 4. Gestión del retardo (Compensación de fase)
    # El filtro de interpolación introduce un retraso de (len - 1) / 2
    delay = (num_taps_interp - 1) / 2
    # Ajustamos para que el pico del impulso coincida con el original proporcionalmente
    start_idx = int(np.round(delay / M))
    end_idx = start_idx + int(len(taps) * L / M)

    final_fir = resampled_taps[start_idx:end_idx]

    # 5. Ajuste final de precisión para HPF (Garantizar DC = 0)
    # Esto elimina cualquier residuo plano en los graves profundos
    if correct_DC_gain:
        final_fir -= np.mean(final_fir)

    return final_fir


def resample_fir_polyphase(taps, f_in, f_out, correct_DC_gain=True):
    """
        What resample_poly does:
            - interpolates (freq up) x Num
            - low-pass filter, to eliminate unwanted spectral images
            - decimate (freq down) ÷ Den

            The low pass filter will attenuate the resulted FIR in a few tenths of a dB
    """

    print('\nComputing polyphase ...')

    up, down = tools.get_samplerate_ratio(f_in, f_out)

    #new_taps = signal.resample_poly(taps, up, down, window=('kaiser', 14))
    new_taps = signal.resample_poly(taps, up, down, window=('blackman',))

    if correct_DC_gain:
        new_taps -= np.mean(new_taps)

    print(f'original {len(taps)} taps fs={f_in}')
    print(f'new      {len(new_taps)} taps fs={f_out}')

    return new_taps


def resample_fir_reconstruction(fir, fs, fs_new):
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

    print('\nComputing reconstruction ...')


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
    new_fir = new_fir[:M] * tools.pydsd.semiblackmanharris(M)

    print(f'original {len(fir)} taps fs={fs}')
    print(f'new      {len(new_fir)} taps fs={fs_new}')

    return new_fir


def filter_analyze(frd, N=1, threshold_dB=-3, normalize=False):
    """
    frd:        stack array [freq, dB]
    N:          Octave fraction to detect passband (0.5, 1, 2, 3, 12, etc.)
    threshold_dB:  Relative level to the maximum to consider the passband.
    """
    freqs   = frd[:, 0]
    mags_db = frd[:, 1]

    # Avoid the log(0) error by ensuring the minimum frequency is > 0
    # We use 1 Hz as the absolute minimum for octave calculations
    f_min_safe = max(np.min(freqs), 1.0)
    f_max_safe = np.max(freqs)

    if normalize:
        mags_db = mags_db - np.max(mags_db)

    # oct/N center freqs
    f_ref = 1000
    k_min = int(np.floor(N * np.log2(f_min_safe / f_ref)))
    k_max = int(np.ceil(N * np.log2(f_max_safe / f_ref)))

    f_centers = f_ref * (2 ** (np.arange(k_min, k_max + 1) / N))

    # Filter centers existing in our data range
    f_centers = f_centers[(f_centers >= f_min_safe) & (f_centers <= f_max_safe)]

    # Filter centers out of our data range
    f_centers = f_centers[(f_centers >= np.min(freqs)) & (f_centers <= np.max(freqs))]

    step = 2 ** (1 / (2 * N))
    active_bands = []

    # Classify by bands
    for fc in f_centers:
        f_inf, f_sup = fc / step, fc * step
        indices = np.where((freqs >= f_inf) & (freqs < f_sup))[0]

        if len(indices) > 0:
            mean_band = np.mean(mags_db[indices])
            active_bands.append(mean_band >= threshold_dB)
        else:
            active_bands.append(False)

    active_bands = np.array(active_bands)
    idx_on = np.where(active_bands)[0]

    if len(idx_on) == 0:
        return "Total Reject", (None, None)

    # Evaluate filter type
    first, last = idx_on[0], idx_on[-1]
    n_bands = len(active_bands)
    continuous = np.all(active_bands[first:last+1])

    if continuous:

        if first <= 1 and last >= n_bands - 2: # margin of error in a band
            tipo = "All Pass"
        elif first <= 1:
            tipo = "Low Pass"
        elif last >= n_bands - 2:
            tipo = "High Pass"
        else:
            tipo = "Band Pass"
    else:
        tipo = "Multi-Band or Notch"

    # estimated cut freq
    f_low_cut = f_centers[first] / step
    f_hi_cut = f_centers[last] * step

    return tipo, (f_low_cut, f_hi_cut)


def do_plot(ir1, ir2):
    """ ir_packs is a tuple of 2 tuples (ir, fs)
    """

    flat_avgs = []

    plt.figure(figsize=(8, 5))

    for irX in (ir1, ir2):

        ir, fs = irX
        label = f'fs_{fs}'

        print( f'computing magnitude to plot {label} ...')
        freqs, dB, _ = tools.fir_response( ir, fs )

        frd = tools.np.column_stack( (freqs, dB) )

        curve_type, band = filter_analyze( frd, threshold_dB=-12 )
        f_ini, f_end = band

        print(f'curve type: {curve_type}')

        flat_avgs.append( tools.get_avg_flat_region( frd, f_ini, f_end ) )

        plt.plot( freqs, dB, label=label )

    drop_info = ''
    drop_dB = round(flat_avgs[0] - flat_avgs[1], 2)
    if abs(drop_dB) > 0.09:
        drop_info = f'(i) FIR resampled to {fs} drops {drop_dB} dB'
        print(drop_info)

    plt.xscale('log')
    plt.xlim([20, 20000])
    plt.ylim(-48, 12)
    plt.yticks( range(-48, 18, 6) )
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    if drop_info:
        drop_info = '\n' + drop_info
    plt.title(f"Freq. response ({method}) {drop_info}")
    plt.grid(True)
    plt.legend()
    plt.show()


def read_cmd_line():
    """
        Wavefile mode:      FIR_resample.py  filename  fs_new
        Float 32 raw mode:  FIR_resample.py  filename  fs  fs_new

        returns:

            fname, fir, fs , fs_new

    """

    global method, plot, fname, fir, fs , fs_new

    for arg in sys.argv[1:]:

        if '-h' in arg:
            print(__doc__)
            sys.exit()

        elif '-plot' in arg:
            plot = True

        elif arg.startswith('-poly'):
             method = 'polyphase'

        elif arg.startswith('-reco'):
             method = 'reconstruction'

        elif arg.startswith('-upfir'):
             method = 'upfirdn'

    try:

        fname = sys.argv[1]

        # WAV file
        if fname.endswith('wav'):
            fs, fir = tools.readWAV( fname )
            fs_new  = int(sys.argv[2])

        # RAW float-32 file
        else:
            fs      = int(sys.argv[2])
            fir     = tools.readPCM32( fname )
            fs_new  = int(sys.argv[3])

    except Exception as e:
        print(f'ERROR: {str(e)}')
        print(__doc__)
        sys.exit()


if __name__ == "__main__":

    method = 'reconstruction'
    plot = False

    read_cmd_line()

    # Compute the new FIR
    print(f'\nResampling method: {method}')

    if method == 'polyphase':
        new_fir = resample_fir_polyphase(fir, fs, fs_new)

    elif method == 'reconstruction':
        new_fir = resample_fir_reconstruction(fir, fs, fs_new)

    elif method == 'upfirdn':
        new_fir = resample_fir_upfirdn(fir, fs, fs_new)

    # Saving to file
    new_fname = f'{fname[:-4]}_{fs_new}_Hz_{method}'

    print('Saving to:', new_fname)
    tools.savePCM32(new_fir, f'{new_fname}.f32')
    tools.saveWAV(f'{new_fname}.wav', fs_new, new_fir, wav_dtype='int32')

    # Plot the frequency responses
    print('Preparing plot ...')
    if plot:
        do_plot( (fir, fs), (new_fir, fs_new) )
