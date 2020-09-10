# audiotools

Some tools, intended to manage FIRs files, FRD files, and more.

It is included an Octave to Python/Scipy translation of **[rripio/DSD](https://github.com/rripio/DSD)**

### Install:


    cd ~
    rm -f master.zip*
    rm -f testing.zip*
    rm -f update-audiotools.sh*
    wget https://raw.githubusercontent.com/Rsantct/audiotools/master/update-audiotools.sh
    bash update-audiotools.sh master
    rm update-audiotools.sh
    rm -f master.zip*
    rm -f testing.zip*

If you want to import modules from here, just update yor `~/.profile` file:

    export PYTHONPATH=$PYTHONPATH:$HOME/audiotools


### Update:

    sh ~/audiotools/update-audiotools.sh  master | another_branch


### References:

https://github.com/rripio/DSD

https://github.com/rripio/pre.di.c

https://github.com/rsantct/pe.audio.sys

https://github.com/AudioHumLab/FIRtro/wiki

