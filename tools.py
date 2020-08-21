#!/usr/bin/env python3
"""
    common use tools
"""
import os.path
from os import remove as os_remove # para borrar el archivo temporal de readFRD()
import sys
import numpy as np
from scipy.io import wavfile
from scipy import signal
from scipy.interpolate import interp1d
from scipy.fftpack import fftfreq, fft, ifft
import pydsd
from q2bw import *
import yaml


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


def nearest_pow2(x):
    """ returns the nearest power of 2 greater or equal to x
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
        zoom con 'IRs_viewer.py'. El GD debe ser constante.
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
        del impulso resultante que son visibles haciendo zoom con 'IRs_viewer.py'.
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


def readWAV16(fname):
    fs, imp = wavfile.read(fname)
    return fs, imp.astype('float32') / 32768.0


def readPCM32(fname):
    """ lee un archivo pcm float32
    """
    #return np.fromfile(fname, dtype='float32')
    return np.memmap(fname, dtype='float32', mode='r')


def savePCM32(raw, fout):
    # guardamos en raw binary float32
    f = open(fout, 'wb')
    raw.astype('float32').tofile(f)
    f.close()


def readFRD(fname):
    """
    Reads a .frd file (Frequency Response Data).
    The file can have FS information inside commented out lines.

    Returns: ndarray[freq, mag, phase], fs
    """
    fs = 0

    with open(fname, 'r') as f:
        lines = f.read().split("\n")

    # Some .frd files as yhe ARTA ones, includes a header with no commented out
    # lines, this produces an error when using numpy.loadtxt().
    #
    # Here we prepare a temporary file to be safely loaded from numpy.loadtxt()
    #
    with open("tmpreadfrd", "w") as ftmp:

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if 'rate' in line.lower() or 'fs' in line.lower():
                items = line.split()
                for item in items:
                    if item.isdigit():
                        fs = int(item)

            if not line[0].isdigit():
                line = "# " + line

            line = line.replace(";", " ") \
                       .replace(",", " ") \
                       .replace("\t", " ") \
                       .strip()

            ftmp.write(line + "\n")

    # Reading and removing the temporary file
    columns = np.loadtxt("tmpreadfrd")
    os_remove("tmpreadfrd")

    return columns, fs


def saveFRD(fname, freq, mag, pha=np.array(0), fs=None, comments=''):
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
        print('(saveFRD) phase is zeroed')
        pha = np.zeros(len(mag))
    print( f'(saveFRD) saving file: {fname}' )
    np.savetxt( fname, np.column_stack((freq, mag, pha)),
             delimiter="\t", fmt='%1.4e', header=header)


def readPCMcfg(f):
    """ lee el .cfg asociado a un filtro .pcm de FIRtro

        Ejemplo de archivo 'viaX.cfg' (La sintaxis es YAML):

        fs      : 44100
        gain    : -6.8     # Ganancia ajustada en el convolver.
        gainext : 8.0      # Resto de ganancia.
    """
    fs = 0
    gain = 0.0
    gainext = 0.0

    if os.path.isfile(f):
        with open(f,'r') as f:
            config = yaml.load(f)
        fs      = config["fs"]
        gain    = config["gain"]
        gainext = config["gainext"]
    else:
        print( f'(!) no se puede accecer a: {f}' )
        sys.exit()
    return fs, gain, gainext
