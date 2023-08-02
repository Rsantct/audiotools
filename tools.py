#!/usr/bin/env python3
"""
    common use tools
"""
import os.path
import numpy as np
from scipy.io import wavfile
from scipy import signal
from scipy.interpolate import interp1d
from scipy.fftpack import fftfreq, fft, ifft
import yaml

# audiotools imports:
import pydsd
from q2bw import *


def octaves(f1, f2):
    """ octaves from f2 to f1
    """
    return np.log2(f2/f1)


def freq_octaves(f, N):
    """ freq at N octaves from f
    """
    return 2 ** N * f


def decades(f1, f2):
    """ decades from f1 to f2
    """
    return np.log10(f1/f2)


def freq_decades(f, N):
    """ freq at N decades from f
    """
    return 10 ** N * f


def center_logspaced(f1, f2):
    """ logspaced center frequency between f1 and f2
    """
    return freq_octaves( f1, octaves(f1, f2)/2.0)


def logspaced_gauss( fc=1000, wideOct=10, freq=np.geomspace(20, 20000, 2**10) ):
    """ A logspaced gaussian curve rendered over a given freq array
        (the frequencies array can have an arbitrary freq point spacing)

                        ____
                     /        \
                   /            \
                /                  \
        ------           fc           -------

                <------ wideOct ---->

        <-------------- freq --------------->


        Useful to ponderate a spectral magnitudes curve, e.g. to limit a positive
        eq curve at extremes, when obtained from inverting an in-room response curve.
    """
    # The logspaced gaussian curve
    N       = 100   # 100 points is enough because the soft gaussian slope
    sigma   = 7     # standard gaussian shape
    f1      = freq_octaves(fc,  wideOct/2.0)
    f2      = freq_octaves(fc, -wideOct/2.0)
    # The frequencies where the gaussian exists:
    GaussFreq   = np.geomspace( f1, f2, N )
    # The gaussian itself:
    GaussMag    = signal.windows.gaussian(N, N/sigma)
    # Finally, we render our gaussian curve over the given full freq array
    Ipol  = interp1d(GaussFreq, GaussMag)   # interpolator
    Xpol  = extrap1d( Ipol )                # extrapolator
    wholeGaussMag = Xpol(freq)
    return wholeGaussMag


def shelf1low(G, wc):
    # CREDITS:
    # A python-ported version of:
    # shelf1low.m
    #  first order low-frequency shelving filter derived in the review article:
    #  V. Valimaki and J. D. Reiss, "All About Audio Equalization: Solutions
    #  and Frontiers", Applied Sciences, 2016
    #
    #  INPUTS % OUTPUTS
    #  G = Gain at low frequencies (linear, not dB)
    #  wc = crossover frequency
    #  num = numerator coefficients b0 and b1
    #  den = denominator coefficients a0 and a1
    #
    #  Written by Vesa Valimaki, Nov. 5, 2015.

    # Transfer function coefficients
    a0 = np.tan(wc/2.0) + np.sqrt(G)
    a1 = np.tan(wc/2.0) - np.sqrt(G)
    b0 = G * np.tan(wc/2.0) + np.sqrt(G)
    b1 = G * np.tan(wc/2.0) - np.sqrt(G)

    # Transfer function polynomials
    den = np.array( [a0, a1] )
    num = np.array( [b0, b1] )

    return num, den


def shelf2low(G, wc):
    # CREDITS:
    # A python-ported version of:
    # shelf2low
    #  Second- rder low shelving filter based on the design based on the
    #  review paper:
    #  V. Valimaki and J. D. Reiss, "All About Audio Equalization: Solutions
    #  and Frontiers", Applied Sciences, 2016.
    #
    #  INPUTS % OUTPUTS
    #  G = Gain at low frequencies (linear, not dB)
    #  wc = crossover frequency (radians)
    #  num = numerator coefficients b0, b1, and b2
    #  den = denominator coefficients a0=1, a1, and a2
    #
    #  Written by Vesa Valimaki, 7 April 2016
    #  Modified by Vesa Valimaki, 29 April 2016

    # Filter coefficients
    Omega = np.tan(wc/2)
    a0 = np.sqrt(1/G) * Omega**2 + np.sqrt(2) * Omega * G**(-1/4) + 1
    a1 = 2 * (np.sqrt(1/G) * Omega**2 - 1)
    a2 = np.sqrt(1/G) * Omega**2 - np.sqrt(2) * Omega * G**(-1/4) + 1
    b0 = np.sqrt(G) * Omega**2 + np.sqrt(2) * Omega * G**(1/4) + 1
    b1 = 2 * (np.sqrt(G) * Omega**2 - 1)
    b2 = np.sqrt(G) * Omega**2 - np.sqrt(2) * Omega * G**(1/4) + 1

    # Transfer function
    den = np.array( [a0, a1, a2] )
    num = np.array( [b0, b1, b2] )

    return num, den


def shelf1high(G, wc):
    # CREDITS:
    # A python-ported version of:
    # shelf1high.m
    #  first order HIGH-frequency shelving filter derived in the review article:
    #  V. Valimaki and J. D. Reiss, "All About Audio Equalization: Solutions
    #  and Frontiers", Applied Sciences, 2016
    #
    #  INPUTS % OUTPUTS
    #  G = Gain at high frequencies (linear, not dB)
    #  wc = crossover frequency
    #  num = numerator coefficients b0 and b1
    #  den = denominator coefficients a0 and a1
    #
    #  Written by Vesa Valimaki, Nov. 5, 2015.
    #  Modified by Vesa Valimaki, April 29, 2016.

    # Transfer function coefficients
    pi = np.pi
    a0 = np.tan(pi/2-wc/2) + np.sqrt(G)      # tan -> -tan
    a1 = -np.tan(pi/2-wc/2) + np.sqrt(G)     # Inverted, also tan -> -tan
    b0 = G * np.tan(pi/2-wc/2) + np.sqrt(G)  # also tan -> -tan
    b1 = -G * np.tan(pi/2-wc/2) + np.sqrt(G) # Inverted, tan -> -tan

    # Transfer function polynomials
    den = np.array( [a0, a1] )
    num = np.array( [b0, b1] )

    return num, den


def shelf2high(G, wc):
    # CREDITS:
    # A python-ported version of:
    # shelf2high.m
    #  Second order HIGH-frequency shelving filter derived in the review article:
    #  V. Valimaki and J. D. Reiss, "All About Audio Equalization: Solutions
    #  and Frontiers", Applied Sciences, 2016
    #
    #  INPUTS % OUTPUTS
    #
    #  G = Gain at high frequencies (linear, not dB)
    #  wc = crossover frequency (radians)
    #  num = numerator coefficients b0, b1, and b2
    #  den = denominator coefficients a0, a1, and a2
    #
    #  Written by Vesa Valimaki, April 7, 2016.
    #  Modified April 29, 2016.

    # Filter coefficients
    Omega = np.tan(wc/2);
    a0 = np.sqrt(G) * Omega**2 + np.sqrt(2) * Omega * G**(1/4) + 1
                                               # Normalize by 1/a0
    a1 = 2 * (np.sqrt(G) * Omega**2 - 1)
    a2 = np.sqrt(G) * Omega**2 - np.sqrt(2) * Omega * G**(1/4) + 1
    b0 = np.sqrt(G) * (np.sqrt(G) + np.sqrt(2) * Omega * G**(1/4) + Omega**2)
    b1 = np.sqrt(G) * (2 * (-np.sqrt(G) + Omega**2))
    b2 = np.sqrt(G) * (np.sqrt(G) - np.sqrt(2) * Omega * G**(1/4) + Omega**2)

    # Transfer function
    den = np.array( [a0, a1, a2] )
    num = np.array( [b0, b1, b2] )

    return num, den


def min_phase_from_real_mag(f, sp_real, dB=True, deg=True):
    """
    Input:

        f, sp_real:     An arbitrary spectrum of positive frequency bands
                        and their corresponding real valued magnitudes.
                        No matter the spectral distribution of the input bins,
                        it works for linear spaced or log spaced flawors,
                        even for arbitrary spaced bins.

        dB:             Input and output magnitudes given in dB

        deg:            Output phase given in deg instead of rad

    Output:

        f:              Same frecuency bands as input

        sp_mp_mag:      The computed min-phase magnitude ( error ~ 1e-4 dB typ.)

        sp_mp_pha:      The computed min-phase phase

    """

    # From dB to linear
    if dB:
        sp_real = 10 ** (sp_real / 20.0)

    # From our custom spectrum to a full extended one by using
    # even spaced bins from 0 Hz to Nyquist.
    f_ext, sp_real_ext = fft_spectrum(f, sp_real, fs=44100)

    # Obtains the whole minimum phase spectrum
    # from our real valued specimen.
    sp_mp = min_phase_wsp( whole_spectrum(sp_real_ext) )

    # Getting magnitude and phase from the positive frequencies half
    # of the obtained minimum phase:
    N = len(f_ext)
    sp_mp_mag = np.abs(sp_mp[:N])
    sp_mp_pha = np.unwrap( np.angle( sp_mp[:N] ) )

    # Remapping to the original 'f' frequencies
    I_mag = interp1d(f_ext, sp_mp_mag)
    I_pha = interp1d(f_ext, sp_mp_pha)
    sp_mp_mag = I_mag(f)
    sp_mp_pha = I_pha(f)

    # From linear to dB
    if dB:
        sp_mp_mag = 20 * np.log10( sp_mp_mag )

    # From rad to deg
    if deg:
        sp_mp_pha = sp_mp_pha * 180 / np.pi

    return f, sp_mp_mag, sp_mp_pha


def min_phase_wsp(wsp):
    """
    input:  wps is a whole 'fft' kind of spectrum (real values, linear scaled).
    output: The corresponding minimum phase spectrum (complex values).

    CREDITS: https://github.com/rripio/DSD
    """

    if not wsp.ndim == 1:
        raise ValueError("wsp must be a 1-d array")

    mpwsp =  np.exp( np.conj( signal.hilbert( np.log(wsp) ) ) )

    return mpwsp


def whole_spectrum(semi):
    """
    input:  semispectrum of positive freqs from 0 Hz to Nyq, must be ODD,
    output: the whole spectrum as needed to FFT computation, will be EVEN.
    """
    n = len(semi)

    if (semi.ndim != 1) or (n % 2 == 0):
        raise ValueError("whole_spectrum needs an ODD lenght 1-d array")

    return np.concatenate(  ( semi, np.flipud( semi[1:n-1] )  )  )


def fft_spectrum(freq, mag, fs=44100, wsize=2**12, make_whole=False):
    """
    Input:

        freq, mag:  An arbitrary spectrum of positive frequency bands
                    and their corresponding real valued magnitudes.
                    No matter the spectral distribution of the input bins,
                    it works for linear spaced or log spaced flawors,
                    even for arbitrary spaced bins.

        fs:         Fs will limit the Nyq of the output spectrum.

        wsize:      The window size to compute the output spectrum.
                    If lower than number of input bins, it will be auto raised
                    to a suitable power of 2 value.

                    Notice that a useful FFT audio spectrum needs a sufficient
                    bin resolution, so be careful to use a suitable window size.

        make_whole: returns a whole FFT kind of frequencies and magnitude spectrum.


    Output:

        freq_new:   A new even spaced frequency bands from 0 Hz to Nyquist,
                    or a whole FFT kind of version: [0....nyq, -nyq-1....-1]

        mag_new:    The new spectrum magnitudes corrensponding to freq_new

    """
    if wsize < len(freq):
        wsize = nearest_pow2(len(freq))

    if wsize % 2 != 0:
        print(wsize)
        raise ValueError(f'fft_semi_spectrum wsize must be EVEN')

    I = interp1d(freq, mag)
    Xtra = extrap1d( I )

    ftmp = fftfreq(wsize)
    ftmp = np.concatenate( ([ftmp[0]], -ftmp[wsize//2:][::-1]) )
    freq_new = fs * ftmp
    mag_new  = Xtra(freq_new)

    if make_whole:
        freq_new = np.concatenate( (freq_new, np.flipud(freq_new[1:-1]) ) )
        mag_new  = whole_spectrum(mag_new)

    return freq_new, mag_new


def logspaced_semispectrum(freq, mag, Npoints):
    """ Interpolates a given magnitude/freq semi-spectrum into
        a new one with <Npoints> length logspaced freq points.

        Note: for fft compliance see tools.fft_spectrum()
    """
    freqNew  = np.geomspace(1, freq[-1], Npoints)

    funcI = interp1d(   freq,
                        mag,
                        kind         = "linear",
                        bounds_error = False,
                        fill_value   = "extrapolate"
                    )

    return freqNew, funcI(freqNew)


def nearest_pow2(x):
    """ returns the nearest power of 2 greater or equal than x
    """
    n=1
    while True:
        if (2 ** n) >= x:
            break
        n +=1
    return 2 ** n


def extrap1d(interpolator):
    """ input:  interpolator (an user defined scipy interpo1d class)
        output: a simple and convenient linear extrapolation FUNCTION.

        example:

            from scipy.interpolate import interp1d
            freqs = np.array( [10, 20 , 30, 40 ] )
            mags  = np.array( [ 1,  2 ,  2,  1 ] )
            I     = interp1d(freqs, mags)
            Xtra  = extrap1d( I )
            Xtra([5, 45])   ----->  array([0.5, 0.5])

    """
    # https://stackoverflow.com/questions/2745329/how-to-make-scipy-interpolate-
    # give-an-extrapolated-result-beyond-the-input-range

    xs = interpolator.x
    ys = interpolator.y

    # linear extrapolation
    def pointwise(x):
        # below iso226.FREQS lower limit 20 Hz
        if x < xs[0]:
            return ys[0] + (x-xs[0]) * (ys[1]-ys[0]) / (xs[1]-xs[0])
        # beyond iso226.FREQS upper limit 12.5 KHz
        elif x > xs[-1]:
            return ys[-1] + (x-xs[-1]) * (ys[-1]-ys[-2]) / (xs[-1]-xs[-2])
        else:
            return interpolator(x)

    def ufunclike(xs):
        return np.array(list(map(pointwise, np.array(xs))))

    return ufunclike


def logTransition(f, f0, speed="medium"):
    """
    +1  _______
               \
                \
     0           \______
               f0
        <-- semilog f -->

    Proporciona una transición, con la apariencia del esquema de arriba,
    útil para aplicar un efecto sobre la proyección logarítmica de un
    semiespectro DFT 'f'.

    'f' debe proporcionarse en escala lineal (bins equiespaciados de una DFT).

    'speed' (slow, mid, fast) define la velocidad de la transición.

    docs/demo_logTransition.py muestra un gráfica ilustrativa del parámetro 'speed'.
    """
    speeds = { "slow":0.5, "medium":1.2, "fast":3.0}
    speed = speeds[speed]
    if f0 < min(f) or f0 <= 0:
        return np.zeros(len(f))
    if f0 > max(f):
        return np.ones(len(f))
    return 1 / ( 1 + (f/f0)**(2**speed) )


def read_REW_EQ_txt(rew_eq_fname):
    """
     Lee un archivo .txt de filtros paramétricos de RoomEqWizard
     y devuelve un diccionario con los parámetros de los filtros

     (i) Se precisa que en REW se utilice [Equaliser: Generic]
    """
    f = open(rew_eq_fname, 'r')
    txt = f.read()
    f.close()

    PEQs = {}   # Diccionario con el resultado de paramétricos leidos

    i = 0
    for linea in txt.split("\n"):
        if "Filter" in linea and (not "Settings" in linea) and ("Fc") in linea:
            active  = ( linea[11:14].strip() == "ON" )
            fc      = float( linea[28:34].strip().replace(",",".") )
            gain    = float( linea[44:49].strip().replace(",",".") )
            Q       = float( linea[56:61].strip().replace(",",".") )
            BW = round( q2bw(float(Q)), 4)  # convertimos Q en BW(oct)
            # Añadimos el filtro
            PEQs[i] = {'active':active, 'fc':fc, 'gain':gain, 'Q':Q, 'BW':BW}
            i += 1

    return PEQs


def MP2LP(imp, windowed=True, kaiserBeta=6):
    """
    audiotools/tools.MP2LP(imp, windowed=True, kaiserBeta=3)

    Obtiene un impulso linear phase cuyo espectro se corresponde
    en magnitud con la del impulso causal proporcionado.

    imp:        Impulso a procesar

    windowed:   Boolean para aplicar una ventana al impulso resultante,
                True por defecto (*)

    kaiserBeta: Ajuste de forma de la ventana kaiser (6 Similar to a Hann)
                Ver scipy.signal.kaiser en https://docs.scipy.org

    (*) El enventado afectará a la resolución en IRs con espectro
        en magnitud muy accidentado. Por contra suaviza los microartifactos
        de retardo de grupo del impulso resultante, que son visibles haciendo
        zoom con 'IR_tool.py'. El GD debe ser constante.
     """
    # MUESTRA LA DOC DE ESTA FUNCIÓN:
    # print MP2LP.__doc__

    # Obtenemos el espectro completo del impulso dado
    Nbins = len(imp)
    _, h = signal.freqz(imp, worN=Nbins, whole=True)
    wholemag = np.abs(h)

    # Obtenemos el impulso equivalente en linear phase
    return wholemag2LP(wholemag , windowed=windowed, kaiserBeta=kaiserBeta)


def ba2LP(b, a, m, windowed=True, kaiserBeta=3):
    """
    audiotools/tools.ba2LP(b, a, m, windowed=True, kaiserBeta=4)

    Obtiene un impulso linear phase de longitud m cuyo espectro
    se corresponde en magnitud con la de la función de
    transferencia definida por los coeff 'b,a' proporcionados.

    b, a:       Coeffs numerador y denominador de la func de transferencia

    m:          Longitud del impulso resultante

    windowed:   Boolean para aplicar una ventana al impulso resultante,
                True por defecto (*)

    kaiserBeta: Ajuste de forma de la ventana kaiser (3 Similar to a Hamming)
                Ver scipy.signal.kaiser en https://docs.scipy.org

    (*) El enventanado afecta a la resolución final y se nota sustancialmente
        si procesamos coeffs 'b,a' correspondientes a un biquad type='peakingEQ'
        estrecho. Por contra suaviza los microartifactos de retardo de grupo
        del impulso resultante que son visibles haciendo zoom con 'IR_tool.py'.
        El GD debe ser constante.
    """
    # MUESTRA LA DOC DE ESTA FUNCIÓN:
    # print ba2LP.__doc__

    # Obtenemos el espectro completo correspondiente
    # a los coeff b,a de func de transferencia
    Nbins = m
    _, h = signal.freqz(b, a, worN=Nbins, whole=True)
    wholemag = np.abs(h)

    # Obtenemos el impulso equivalente en linear phase
    return wholemag2LP(wholemag , windowed=windowed, kaiserBeta=kaiserBeta)


def wholemag2LP(wholemag, windowed=True, kaiserBeta=3):
    """
    Obtiene un impulso linear phase cuyo espectro se corresponde
    en magnitud con el espectro fft proporcionado 'wholemag',
    que debe ser un espectro fft completo y causal.

    La longitud del impulso resultante ifft se corresponde con la longitud
    del espectro de entrada.

    Se le aplica una ventana kaiser con 'beta' ajustable.

    wholemag:   La magnitud de espectro completo y causal a procesar

    windowed:   Boolean para aplicar una ventana al impulso resultante,
                True por defecto (*)

    kaiserBeta: Ajuste de forma de la ventana kaiser
                Ver scipy.signal.kaiser en https://docs.scipy.org

    """

    # Volvemos al dom de t, tomamos la parte real de IFFT
    imp = np.real( np.fft.ifft( wholemag ) )
    # y shifteamos la IFFT para conformar el IR con el impulso centrado:
    imp = np.roll(imp, int(len(wholemag)/2))

    # Enventanado simétrico
    if windowed:
        # imp = pydsd.blackmanharris(len(imp)) * imp
        # Experimentamos con valores 'beta' de kaiser:
        return signal.windows.kaiser(len(imp), beta=kaiserBeta) * imp
    else:
        return imp


def RoomGain2impulse(imp, fs, gaindB):
    """
    Aplica ecualización Room Gain a un impulso
    (Adaptación de DSD/RoomGain.m que se aplica a un espectro)

    fs       = Frecuencia de muestreo.
    imp      = Impulso al que se aplica la ecualización.
    gaindB   = Ganancia total a DC sobre la respuesta plana.
    """
    # Parámetros convencionales para una curva Room Gain
    f1 = 120
    Q  = 0.707
    # Obtenemos los coeff de la curva y la aplicamos al impulso
    b, a = pydsd.biquad(fs, f1, Q, "lowShelf", gaindB)
    return signal.lfilter(b, a, imp)


def maxdB(imp, fs):
    """ busca el máximo en el espectro de un impulso
    """
    # Obtenemos el espectro 'mag' con cierta resolución 1024 bins
    Nbins = 1024
    w, h = signal.freqz(imp, worN=Nbins, whole=False)
    mag  = np.abs(h)
    # buscamos el máximo
    amax = np.amax(mag)             # magnitud máx
    wmax = w[ np.argmax(mag) ]      # frec máx
    fmax = wmax * fs/len(imp)
    return fmax, 20*np.log10(amax)  # frec y mag en dBs


def isPowerOf2(n):
    return np.floor(np.log2(n)) == np.ceil(np.log2(n))


def isPowerOf10(n):
    return np.floor(np.log10(n)) == np.ceil(np.log10(n))


def Ktaps(x):
    """ cutre conversor para mostrar la longitud de un FIR """
    if x >= 1024:
        return str(int(x / 1024)) + " Ktaps"
    else:
        return str(int(x)) + " taps"


def KHz(f):
    """ cutre formateo de frecuencias en Hz o KHz """
    f = int(round(f, 0))
    if f in range(1000):
        f = str(f) + "Hz"
    else:
        f = round(f/1000.0, 1)
        f = str(f) + "KHz"
    return f.ljust(8)


def readPIR(fname):
    """ read PIR files from ARTA

        *** CREDITS: ***
        This is a translation from the original Matlab code published at:
        https://github.com/mbrennwa/mataa/mataa_tools/mataa_import_PIR.m
        Copyright (C) 2019 Matthias S. Brennwald.
    """

    def b2int(b, byteorder='little', signed=False):
        return int.from_bytes(b, byteorder=byteorder, signed=signed)

    with open(fname, 'rb') as f:

        # HEADER (80 bytes)
                                     # https://es.mathworks.com/help/matlab/ref/fread.html
                                     #
                                     # Matlab type /bytes
                                     #
                                     #              Contents

        filesignature    = f.read(4) # uchar    /1  file signature, should be PIR
        version          = f.read(4) # uint32   /4  file format version
        infosize         = f.read(4) # int32    /4  length of user defined text at end of file
        reserved1        = f.read(4) # int32
        reserved2        = f.read(4) # int32
        fskHz            = f.read(4) # float32  /4  sample rate in kHz
        samplerate       = f.read(4) # int32        sample rate in Hz
        length           = f.read(4) # int32        length of signal (number of samples)
        inputdevice      = f.read(4) # int32        0: voltage probe, 1: mic, 2: accelerometer
        devicesens       = f.read(4) # float32      V/V or V/Pa (mic input)
        measurement_type = f.read(4) # int32        0: signal recorded, external excitation / 1: IR, single channel correlation, 2: IR, dual channel IR
        avgtype          = f.read(4) # int32        type of averaging (0: time, 1: freq)
        numavg           = f.read(4) # int32        number of averages used in measurements
        bfiltered        = f.read(4) # int32        forced antialiasing filtering in 2ch
        gentype          = f.read(4) # int32        generator type
        peakleft         = f.read(4) # float32      peak value (ref 1.0) in left input channel
        peakright        = f.read(4) # float32      peak value (ref 1.0) in right input channel
        gensubtype       = f.read(4) # int32        0: male, 1: female for Speech PN ...
        reserved3        = f.read(4) # float32
        reserved4        = f.read(4) # float32

        # converting types
        filesignature   = filesignature.decode()
        fskHz           = np.fromstring(fskHz, dtype='<f4')[0]

        samplerate      = b2int(samplerate)
        length          = b2int(length)
        infosize        = b2int(infosize)

        # print( 'pointer is at position:', f.tell() )  # position = 80.

        # IMPULSE DATA (float32_4bytes * length)
        imp = np.fromstring( f.read(4 * length) , dtype='<f4')

        # print( 'pointer is at position:', f.tell() )  # e.g. position = 80 + 64K*4

        # USER DEFINED INFOTEXT:
        usertext    = f.read(infosize)  # uchar /1byte
        usertext    = usertext.decode()

    #print('ARTA file read:')
    #print('filesignature:', filesignature)
    #print('fskHz:', fskHz, 'KHz')
    #print('samplerate:', samplerate, 'Hz')
    #print('length:', length, 'samples')
    #print('usertext:', usertext)

    return samplerate, imp


def readWAV(fname):
    """
    scipy.io.wavfile.read

        Notes

            This function cannot read wav files with 24-bit data.

            Common data types: [1]

            WAV format              Min         Max             NumPy dtype
            ----------              ---         ---             -----------
            32-bit floating-point   -1.0        +1.0            float32
            32-bit PCM              -2147483648 +2147483648     int32
            16-bit PCM              -32768      +32767          int16
            8-bit PCM               0           255             uint8

        Note that 8-bit PCM is unsigned.

        mmap:   Whether to read data as memory-mapped.
                Only to be used on real files

    """

    fs, imp = wavfile.read(fname, mmap=True)

    # Impulse type can vary, also the span values, see above table

    if imp.dtype == 'int32':
        imp2 = imp / 2 ** 31      # -186 dB error on positive values can live with that

    elif imp.dtype == 'int16':
        imp2 = imp / 32768.0

    else:
        imp2 = imp

    # We want to use always 'float32'
    return fs, imp2.astype('float32')


def saveWAV(fname, rate, data, bits=16):
    """ stereo data must have shape (Nsamples, 2)
    """

    if bits == 16:
        t='int16'
    elif bits == 32:
        t='float32'
    else:
        raise ValueError('tools.saveWAV use 16 or 32 bits depth')

    wavfile.write(fname, rate, data.astype(t))


def readPCM(fname, dtype='float32'):
    """ lee un archivo pcm float32
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype=dtype, mode='r')


def readPCM32(fname):
    """ alias for legacy scripts
    """
    return readPCM(fname, dtype='float32')


def savePCM32(raw, fout):
    # guardamos en raw binary float32
    f = open(fout, 'wb')
    raw.astype('float32').tofile(f)
    f.close()


def readFRD(fname):
    """
    Reads a .frd file (Frequency Response Data).

    The file can have a header with sampling freq information

    Returns: ndarray[freq, mag, phase], fs
    """
    fs = 0

    # (i) Some .frd files as the ones from ARTA, includes a header with
    # no commented out lines.

    # We neeed to skip any header lines when calling numpy.loadtxt()
    # We can extract fs info from a header.

    with open(fname, 'r') as f:
        lines = f.readlines()

    header = [ l for l in lines if not l.strip()[:2].replace('.', '').isdecimal()]

    # try to extract fs from header
    for line in header:
        if 'rate' in line.lower() or 'fs' in line.lower():
            items = line.split()
            for item in items:
                if item.isdigit():
                    fs = int(item)

    # Reading frd text file, by skipping the header lines
    columns = np.loadtxt( fname, skiprows=len(header) )

    return columns, fs


def saveFRD(fname, freq, mag, pha=np.array(0), fs=None, comments='', verbose=True):
    """
    'mag' al ser esta una función que guarda FRDs, se debe dar en dBs.

    'fs'  se usa para la cabecera informativa del archivo de texto.

    v2.0   Incluimos la phase
    v2.0a  + opcion 'Processed by'
    """
    if not fs:
        fs = "unknwon"
    header =  "Frequency Response\n"
    if comments:
        header += comments + "\n"
    header += "Numpoints = " + str(len(freq)) + "\n"
    header += "SamplingRate = " + str(fs) + " Hz\n"
    header += "Frequency(Hz)   Magnitude(dB) Phase"
    # Si no hay phase, nos inventamos una columna de zeros
    if not pha.any():
        if verbose: print('(saveFRD) phase is zeroed')
        pha = np.zeros(len(mag))
    if verbose: print( f'(saveFRD) saving file: {fname}' )
    np.savetxt( fname, np.column_stack((freq, mag, pha)),
             delimiter="\t", fmt='%1.4e', header=header)


def make_beep(f=1000, fs=48000, dBFS=-9.0, duration=0.10):
    """ a simple general purpose beep waveform maker
    """
    head = np.zeros( int(duration/10 * fs) )    # 1/10 of duration
    tail = np.zeros( int(duration/5  * fs) )    # 2/10 of duration
    x = np.arange( fs * duration )              # a bare silence array
    y = np.sin( 2 * np.pi * f * x / fs )        # the waveform itself
    y = np.concatenate( [head, y, tail] )       # adding head and tail silences
    y *= 10 ** (dBFS/20.0)                      # attenuation as per dBFS
    return y


def SoX_pcm2wav(pcmpath1=None, pcmpath2=None, fs=0, wavpath=None, bits=32):
    """ A wrapper using SoX to convert pcm files (float32) to wav file.
        If two pcm are given, then mix to stereo wav.
    """

    from subprocess import run

    test = run( 'which sox'.split() )
    if test !=0:
        print('tools.SoX_pcm2wav() needs SoX')
        return False

    if (fs not in (44100, 48000)) or (not os.path.isfile(pcmpath1)) or \
       (bits not in (16,32)):
        return False

    if pcmpath2 and not os.path.isfile(pcmpath2):
        return False


    # SoX needs .f32 extension
    f32path1 = pcmpath1.replace('.pcm', '.f32')
    run( f'ln -s  "{pcmpath1}" "{f32path1}" 1>/dev/null 2>&1', shell=True)
    if pcmpath2:
        f32path2 = pcmpath2.replace('.pcm', '.f32')
        run( f'ln -s  "{pcmpath2}" "{f32path2}" 1>/dev/null 2>&1', shell=True)

    # wav file name
    if not wavpath:
        if os.path.dirname(pcmpath1):
            wavpath = f'{os.path.dirname(pcmpath1)}/pcm2wav.wav'
        else:
            wavpath = 'pcm2wav.wav'

    # SoX mixing
    # sox -m  -c1 -r44100 L.f32  -c1 -r44100 R.f32  -c 2 -b 16 L+R.wav
    if pcmpath2:
        cmd = f'sox -m -c1 -r{fs} {f32path1} -c1 -r{fs} {f32path2}  -c2'
    else:
        cmd = f'sox -c1 -r{fs} {f32path1} -c1'

    cmd += f' -b{bits} {wavpath}'

    run( cmd, shell=True )

    print(f'(tools.SoX_pcm2wav) saved: {wavpath}')

    # Removing symlinks
    run( f'rm "{f32path1}" 1>/dev/null 2>&1', shell=True)
    if pcmpath2:
        run( f'rm "{f32path2}" 1>/dev/null 2>&1', shell=True)

    return True


def pcm2stereowav(pcmpathL=None, pcmpathR=None, fs=0, wavpath=None, bits=32):
    """ mixes regular audiotools pcm float 32 files to wav stereo
    """

    if fs not in (44100, 48000, 96000):
        raise ValueError('(tools.pcm2stereowav) invalid rate')

    L = readPCM(pcmpathL)
    R = readPCM(pcmpathR)

    LR = np.array( (L, R) ).transpose()

    saveWAV(fname=wavpath, rate=fs, data=LR, bits=bits)

