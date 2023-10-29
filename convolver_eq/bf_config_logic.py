#!/usr/bin/env python3
"""
    Generates the necessary eq and cli sections for 'brutefir_config'

    usage:

    bf_config_logic.py  -RXX -fsXX

        -RXX:   R10 | R20 | R40 | R80  iso R series (default: R20 ~ 1/3 oct)

        -fsXX:  44100 | 48000 | 96000  sampling frequency Hz
                (default: 44100, upper limits RXX to 20000 Hz)

"""

import sys
import os
import numpy as np

HOME = os.path.expanduser("~")
sys.path.append(f'{HOME}/audiotools')
from iso_R import get_iso_R


logic_str = \
"""
logic:

# The command line interface server, listening on a TCP port.
"cli" { port: 3000; },

# The eq module provides a filter coeff to render a run-time EQ.
# (i) Bands here must match with the ones at your xxxxfreq.dat file.
"eq" {
    #debug_dump_filter: "/tmp/brutefir-rendered-%d";
    {
    coeff: "c.eq";
$INFO
$BANDS
    };
};
"""


if __name__ == '__main__':

    # Defaults
    fs      = 44100
    fmin    = 10
    Rseries = 'R20'
    fs      = 44100

    # Read command line options
    if not sys.argv[1:]:
        print(__doc__)
        sys.exit()
    for opc in sys.argv[1:]:
        if opc == '-h' or opc == '--help':
            print(__doc__)
            sys.exit()
        elif '-R' in opc:
            Rseries = opc[1:]
        elif '--fs' in opc:
            value = int(opc[4:])
            if value in (44100, 48000, 96000):
                fs = value

    f = get_iso_R(Rseries, fmin=fmin, fs=fs)
    bands = np.array2string(f, max_line_width=70, separator=', ',
                            formatter={'float_kind':lambda x: "%.1f" % x})
    bands = bands.replace('.0', '')                 \
                 .replace('[', f'    bands:\n ')    \
                 .replace(']',';')                  \
                 .replace('\n ', '\n    ')

    logic_str = logic_str.replace('$INFO', f'    # using audiotools {Rseries} bands')
    logic_str = logic_str.replace('$BANDS', bands)

    print(logic_str)
