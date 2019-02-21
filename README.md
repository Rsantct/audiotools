# audiotools

Algunas herramientas, orientadas al manejo de FIRs para **AudioHumLab/FIRtro**.

Se incluye una traslación a Python/Scipy de funciones del paquete Octave **rripio/DSD**

### Install:


    cd ~
    rm -f master.zip*
    rm -f testing.zip*
    rm -f update-audiotools.sh*
    wget https://raw.githubusercontent.com/Rsantct/audiotools/master/update-audiotools.sh
    bash update-audiotools.sh
    rm update-audiotools.sh
    rm -f master.zip*
    rm -f testing.zip*

Para poder importar módulos python, ej. `pydsd`, actualizar `~/.profile` con:

    export PYTHONPATH="$PYTHONPATH:/home/yourHome/audiotools"

### Update:

    sh ~/audiotools/update-audiotools.sh  [ master | testing ]

### Referencias:
#### https://github.com/rripio/DSD
#### https://github.com/AudioHumLab/FIRtro

