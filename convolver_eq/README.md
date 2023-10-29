
## EQ curves

    tones.py
    loudness_compensation_curves.py
    room_curves.py

Scripts to generate the needed files for adjusting bass, treble, loudness contour compensation and target room curves (psychoacoustic room dimension equalization) that can be loaded into the Brutefir's EQ stage of [pe.audio.sys](https://github.com/AudioHumLab/pe.audio.sys), a derivated project from [FIRtro](https://github.com/AudioHumLab)

More details here:

https://github.com/AudioHumLab/pe.audio.sys/tree/master/pe.audio.sys#the-shareeq-folder


## NOTICE:

Former FIRtro curves array files `xxx.dat` were stored in Matlab way, so when reading them with numpy.loadtxt() it was needed to transpose and flipud in order to access to the curves data in a natural way.

Currently the curves are stored in pythonic way, so numpy.loadtxt() will read directly usable data. 


## bf_rendered.sh

Help tool to analize the internal FIR from the Brutefir eq logic runtime module. Brutefir dumps the internal FIR coefficient taps in a text file, e.g. `/tmp/brutefir-rendered-0`.


## bf_config_logic.py

A simple tool to generate the necessary eq bands and cli sections for `brutefir_config`. See details here:

https://torger.se/anders/brutefir.html#bflogic_eq

## Convolver FIR usage
If you need the curves in a FIR file format so that could be loaded in a convolver, use the `-NXX` option, then use `semispectrum2impulse()` function from `tools.py` to convert them from frequency domain to time domain IR.
