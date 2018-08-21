#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    pydsd v0.02
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%  DSD  %%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% Traslación a python/scipy de funciones del paquete DSD  %%
    %%             https://github.com/rripio/DSD               %%
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    DISCLAIMER: El autor de DSD no garantiza ni supervisa
                esta traslación.
                
    ACHTUNG:    WORK IN PROGRESS
"""
# v0.01a
# + blackmanharris
# funciones 'blackman' renombradas a 'blackmanharris'
# v0.02
# + funciones de crossover

# -----------------------------------------------------------
# Notas:
# - Abajo podemos ver código original de DSD en octave comentado con %%
# - Algunas convenciones usadas en DSD:
#   'sp'    suele referirse al spectrum completo
#   'ssp'   suele referirse al semi spectrum
# -----------------------------------------------------------

import numpy as np
from scipy import signal, interpolate

def delta(m):
    """
    %% Obtiene un impulso de longitud m con valor uno en su primera muestra.
    %%
    %% imp = Coeficientes del filtro FIR.
    %% m = Número de muestras.
    """
    imp = np.zeros(m)
    imp[0] = 1.0
    return imp

def deltacentered(m):
    """
    %% Obtiene un impulso de longitud m con valor uno en su muestra central.
    %%
    %% m = Número de muestras. Debe ser impar.
    """
    if m % 2 == 0:
        raise ValueError("deltacentered: Impulse length must be odd");

    imp = np.zeros(m)           # array de zeros de longitud m
    ptomedio = int(np.ceil(m/2.0))
    imp[ptomedio] = 1.0         # ponemos un uno en tolmedio
    return imp

def centerimp(imp, m):
    """
    %% Aumenta la longitud de un impulso centrándolo.
    %% El impulso original debe tener longitud impar.
    %%
    %% imp = Impulso a centrar, debe ser de longitud impar.
    %% m   = Longitud final del impulso.
    """

    l = len(imp)
    if l > m:
        raise ValueError("centerimp: impulse length must be equal or less than m")

    if l % 2 == 0:
        raise ValueError("centerimp: Impulse length must be odd");

    # En Octave se hace zero padding (imp, longitud_deseada) en dos pasadas :
    # %% imp = prepad(imporig, l + floor((m-l)/2) );
    # %% imp = postpad(imp, m);

    # En numpy no hay equivalente.
    # Añadiremos (m-len(imp)) zeros extras, repartidos por delante y por detrás.
    extra  = m - len(imp)
    extra1 = int(np.floor( extra/2.0 ) + 1)
    extra2 = extra - extra1
    imp = np.append( np.zeros(extra1), imp )
    return np.append( imp, np.zeros(extra2) )

def crossButterworth(fs=44100, m=32768, n=2, flp=0 , fhp=0):
    """
    %% Obtiene el filtro FIR de un filtro Butterworth de orden n.
    %% Si se proporcionan las dos frecuencias 'flp' y 'fhp' genera un pasabanda.
    %%
    %% Ejemplo de uso para obtener un FIR de 32 Ktaps Butt pasabajos de orden 2 a 100 Hz :
    %%
    %%      crossButterworth( fs=44100, m=32768, n=2, flp=100 )
    %%
    %%      fs  = Frecuencia de muestreo.
    %%      m   = Número de muestras.
    %%      n   = Orden del filtro.
    %%      flp = Frecuencia de corte pasabajos, si 0 u omitida sin corte pasabajos.
    %%      fhp = Frecuencia de corte pasaaltos, si 0 u omitida sin corte pasaaltos.
    """

    wlp  = flp / (fs/2.0)   # Frecs normalizadas
    whp  = fhp / (fs/2.0)
    imp  = delta(m)         # Delta a la que aplicaremos el filtro para entregar el FIR resultado

    # 1. Calculamos los coeff 'b,a' de la func de transferencia de un filtro Butterworth estandar
    if   flp > 0  and fhp == 0:
        b, a = signal.butter(n, wlp,       btype="lowpass",  analog=False, output="ba")

    elif flp == 0 and fhp > 0:
        b, a = signal.butter(n, whp,       btype="highpass", analog=False, output="ba")

    elif flp > 0  and fhp > 0:
        b, a = signal.butter(n, (wlp, whp), btype="bandpass", analog=False, output="ba")

    else:
        return imp  # delta sin filtrar

    # 2. Aplicamos el Butterwoth al FIR
    return signal.lfilter(b, a , imp)

def crossButterworthLP(fs=44100, m=32768, n=2, flp=0 , fhp=0):
    """
    %% Obtiene el filtro FIR de fase lineal con 
    %% la magnitud de un filtro Butterworth de orden n.
    %%
    %% Si se proporcionan las dos frecuencias 'flp' y 'fhp' genera un pasabanda.
    %%
    %% Ejemplo de uso para obtener un FIR lineal phase de 32 Ktaps Butt orden 1 pasabajos a 80 Hz :
    %%
    %%      crossButterworthLP( fs=44100, m=32768, n=1, flp=80 )
    %%
    %%      fs  = Frecuencia de muestreo.
    %%      m   = Número de muestras.
    %%      n   = Orden del filtro.
    %%      flp = Frecuencia de corte pasabajos, si 0 u omitida sin corte pasabajos.
    %%      fhp = Frecuencia de corte pasaaltos, si 0 u omitida sin corte pasaaltos.    
    """

    wlp  = flp / (fs/2.0)   # freq normalizadas de los cortes
    whp  = fhp / (fs/2.0)

    # 1. Calculamos los coeff del filtro Butterworth
    if flp > 0 and fhp == 0:
        b, a = signal.butter(n, wlp, btype="lowpass", analog=False, output="ba")

    elif flp == 0 and fhp > 0:
        b, a = signal.butter(n, whp, btype="highpass", analog=False, output="ba")

    elif flp > 0 and fhp > 0:
        b, a = signal.butter(n, (wlp,whp), btype="bandpass", analog=False, output="ba")

    elif flp == 0 and fhp == 0:
        imp = centerimp(deltacentered(m-1), m)
        return imp  # delta sin filtrar

    # 2. Calculamos la magnitud del semiespectro

    # Cód. original DSD, en Octave:
    # Nota: Se trabaja con el vector ssF de frecuencias físicas y la fs, es uno de los posibles
    #       modos de usar freqz en Octave. Al no usar 'whole' devuelve el semiespectro.
    # %% mLow = fs/m;                   % low freq, freq jump
    # %% ssK = 0:m/2;                   % indexes of non aliased frequency vector
    # %% ssF = mLow * (ssK);            % non aliased frequency vector
    # %% h = freqz(b, a , ssF, fs);
    # %% mag = abs(h);

    # En Scipy freqz trabaja con freqs normalizadas no se usa la fs como parámetro.
    # Aquí obtendremos el espectro completo para evitar reconstruirlo más abajo con 'wholesplp'.
    Nbins = m
    w, h = signal.freqz(b, a, Nbins, whole=True)
    mag = np.abs(h)

    # 3. Se calcula el impulso correspondiente a 'mag': se toma la parte real de la IFFT, 
    #    y se shiftea para que quede LP linear phase.
    # Cód. original en Octave:
    # %% imp = real( ifft( wholesplp(mag') ) );
    # %% imp = circshift(imp, m/2);
    imp = np.real( np.fft.ifft( mag ) )
    imp = np.roll(imp, m/2)

    # 4. Se aplica una ventana antes de devolver el resultado
    # Cód. original en Octave
    # %% imp = blackmanharris (m) .* imp;
    return blackmanharris(m) * imp
    
def crossLinkwitzRiley(fs=44100, m=32768, n=2, flp=0 , fhp=0):
    """
    %% Obtiene el filtro FIR de un filtro Linkwitz-Riley de orden n, n par.
    %% Si se proporcionan las dos frecuencias 'flp' y 'fhp' genera un pasabanda.
    %%
    %% Ejemplo de uso para obtener un FIR de 32 Ktaps LR4 pasabajos 100 Hz :
    %%
    %%      crossLinkwitzRiley(fs=44100, m=32768, n=4, flp=100)
    %%
    %%      fs  = Frecuencia de muestreo.
    %%      m   = Número de muestras.
    %%      n   = Orden del filtro.
    %%      flp = Frecuencia de corte pasabajos, si 0 u omitida sin corte pasabajos.
    %%      fhp = Frecuencia de corte pasaaltos, si 0 u omitida sin corte pasaaltos.
    """

    imp = delta(m)    # Delta a la que aplicaremos el filtro para entregar el FIR resultado

    if n % 2:
        return imp          # Devolvemos una delta ya que el orden debe ser par.

    n    = n / 2            # El orden se doblará en la cascada
    wlp  = flp / (fs/2.0)   # Frecs normalizadas
    whp  = fhp / (fs/2.0)

    # 1. Obtenemos los coeff de un filtro Butterworth estandar
    if flp > 0  and  fhp == 0:
        b, a = signal.butter(n, wlp, btype="lowpass", analog=False, output="ba")

    elif flp == 0  and  fhp > 0:
        b, a = signal.butter(n, whp, btype="highpass", analog=False, output="ba")

    elif flp > 0  and  fhp > 0:
        b, a = signal.butter(n, (wlp, whp), btype="bandpass", analog=False, output="ba")

    else:
        return imp  # delta sin filtrar

    # 2. Aplicamos el Butterwoth a la delta, en cascada para obtener un Linkwitz-Riley
    imp = signal.lfilter(b, a , imp)
    imp = signal.lfilter(b, a , imp)
    return imp

def semiblackmanharris(m):
    """
    %% Obtiene la mitad derecha de una ventana Blackman-Harris de longitud m.
    %% w = Ventana.
    %% m = Número de muestras.
    """
    # generamos la ventana con tamaño 2*m
    w = signal.blackmanharris(2*m)
    # devolvemos la mitad derecha
    return w[m:]

def blackmanharris(m):
    """
    %% Obtiene una ventana Blackman-Harris de longitud m.
    """
    return signal.blackmanharris(m)

def minphsp(sp):
    """
    %% Obtiene el espectro de fase mínima a partir de un espectro completo.
    %% minph = Espectro completo de fase mínima con la misma magnitud de espectro que imp.
    %% sp    = Espectro completo. Longitud par.
    Nota del traductor:
        El espectro en phase minima se consigue simplemente haciendo
        la transformada de Hilbert de la magnitud del espectro proporcionado.
    """

    if not sp.ndim == 1:
        raise ValueError("ssp must be a column vector")

    #%% exp(conj(hilbert(log(abs(sp)))));
    return np.exp(np.conj(signal.hilbert(np.log(abs(sp)))));

def wholespmp(ssp): # whole spectrum minimum phase
    """
    %% Obtiene el espectro CAUSAL completo a partir 
    %% del espectro de las frecuencias positivas.
    %%
    %% ssp = Espectro de las frecuencias positivas entre 0 y m/2.
    %% wsp = Espectro completo entre 0 y m-1 (m par).
    
    Nota del traductor:
        entrada: un semiespectro de trabajo de freq positivas
        salida:  el espectro completo
    """

    if not ssp.ndim == 1:
        raise ValueError("ssp must be a column vector")

    m = len(ssp) 
    # Verifica que la longitud del espectro proporcionado sea impar 
    if m % 2 == 0:
        raise ValueError("wholespmp: Spectrum length must be odd")


    # nsp = flipud(conj(ssp(2:m-1)));   # desglosamos el cód octave en dos líneas:
    nsp = np.conj(ssp[1 : m-2])
    nsp = nsp[::-1]                     # flipud

    # wsp = [ssp;nsp];                  # cód. octave
    return np.concatenate([ssp, nsp])

def wholesplp(ssp): # whole spectrum linear phase
    """
    %% Obtiene el espectro SIMÉTRICO completo a partir 
    %% del espectro de las frecuencias positivas.
    %%
    %% ssp = Espectro de las frecuencias positivas entre 0 y m/2.
    %% wsp = Espectro completo entre 0 y m-1 (m par).
    """

    if not ssp.ndim == 1:
        raise ValueError("ssp must be a column vector")

    m = len(ssp) 
    # Verifica que la longitud del espectro proporcionado sea impar 
    if m % 2 == 0:
        raise ValueError("wholesplp: Spectrum length must be odd")

    # nsp = flipud(ssp(2:m-1));         # desglosamos el cód. octave en dos líneas:
    nsp = ssp[1 : m-2]
    nsp = nsp[::-1]                     # flipud

    # wsp = [ssp;nsp];                  # cód. octave
    return np.concatenate([ssp, nsp])
    
def lininterp(F, mag, m, fs):
    """
    %% Obtiene la valores de magnitud interpolados sobre el semiespectro.
    %% mag    = Magnitud a interpolar.
    %% F      = Vector de frecuencias.
    %% m      = Longitud del espectro completo (debe ser par).
    %% fs     = Frecuencia de muestreo.
    """

    if not F.ndim == 1:
        raise ValueError("F must be a column vector")
    if not m % 2 == 0:
        raise ValueError("m must be even")

    # Prepara el nuevo vector de frecuencias OjO lo genera de long impar m/2+1
    #%% fnew = (0:m/2)'*fs/m; % column vector
    fnew = np.arange(0, m/2) * fs/m
    
    # DSD usa a la funcion de interpolación interp1:
    # (nota: maglin es la variable resultado que entregará esta función)
    #%% maglin = interp1(F, mag, fnew, "spline");
    #   Traducción a scipy de la función de interpolación.
    #   Primero se define, luego se usa.
    #   Eludimos errores si se pidieran valores fuera de rango,
    #   y rellenamos extrapolando si fuera necesario.
    #   'cubic' == 'spline 3th order'
    I = interpolate.interp1d(F, mag, kind="cubic", bounds_error=False, 
                             fill_value="extrapolate")
    # Obtenemos las magnitudes interpoladas en las 'fnew':
    maglin = I(fnew)
    
    # Y esto ¿¿¿??
    #%% maglin(fnew<F(1)  )=mag(1);
    #%% maglin(fnew>F(end))=mag(end);

    return maglin        
