#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math

def q2bw(Q):
    """ http://www.rane.com/note167.html#qformula
        http://www.rane.com/note170.html
    """
    bw = 2.0 / math.log10(2.0) * math.log10( 0.5 * (1/Q + math.sqrt(1/Q**2 + 4)))
    return bw


if __name__ == '__main__':
    pass

