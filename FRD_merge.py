#!/usr/bin/env python2

"""
    Merge two .frd files 'frd_LOW' , 'frd_HIGH'

    Takes LOW magnitudes below 'freq', and HIGH magnitudes above.

    Usage:

        FRD_merge.py  path/to/frd_LO  path/to/frd_HI  scale_LO scale_HI  freq

        (scales in dB)

    You can try

        FRD_tool.py frd_LOW  frd_HIGH -auto

    as a start point to estimate scales and merging frequency.


"""
# v0.1

import sys
import utils
import numpy as np

if __name__ == '__main__':

    try:
        fnameLO = sys.argv[1]
        fnameHI = sys.argv[2]
        cLO, fsLO = utils.readFRD(fnameLO)
        cHI, fsHI = utils.readFRD(fnameHI)
    except:
        print(__doc__)
        print( 'Error in path/to/frds' )
        sys.exit()


    # Ensure that frequency bands are identical
    if np.sum(cLO[:,0] - cHI[:,0]) != 0:
        print( 'Error: frds bands differs' )
        sys.exit()

    try:
        sLO = float(sys.argv[3])
        sHI = float(sys.argv[4])
    except:
        print(__doc__)
        print( 'Error parsing scale1 and scale2 (mandatories)' )
        sys.exit()

    try:
        f = float(sys.argv[5])
        if f < 20.0 or f > 20e3:
            raise
    except:
        print(__doc__)
        print( 'Error freq must be in 20....20000 Hz' )
        sys.exit()


    # Scale curves with the given dBs, then it is expected
    # both to have the same magnitude at the provided 'freq'
    cLO = cLO + [0, sLO]
    cHI = cHI + [0, sHI]


    # Merged mag takes from curveLOW until reached 'freq' then takes from curveHIGH
    freq = cLO[:,0]
    mag  = np.where( freq < f, cLO[:,1], cHI[:,1] )

    utils.saveFRD( 'merged.frd', freq, mag )

