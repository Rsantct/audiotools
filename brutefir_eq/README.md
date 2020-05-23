### tones.py, loudness_compensation.py, house_curves.py

Scripts to generate the needed files for adjusting bass, treble, loudness contour compensation and target house curves (psychoacoustic room dimension equalization) that can be loaded into the Brutefir's EQ stage

More details here:

https://github.com/AudioHumLab/pe.audio.sys/tree/master/pe.audio.sys#the-shareeq-folder


### bf_rendered.sh

Help tool to analize the internal FIR from the Brutefir eq logic runtime module. Brutefir dumps the internal FIR coefficient taps in a text file, e.g. `/tmp/brutefir-rendered-0.txt`.

    
### bf_config_logic.py

A simple tool to generate the necessary eq bands and cli sections for `brutefir_config`. See details here:

https://torger.se/anders/brutefir.html#bflogic_eq
