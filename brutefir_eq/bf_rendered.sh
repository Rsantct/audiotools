#!/bin/bash

if [[ $1 ]]; then
    fs=$1
    "$HOME"/audiotools/IRs_viewer.py "/tmp/brutefir-rendered-0.txt" $fs -pha -pdf

else
    echo
    echo "Plots the rendered impulse given from the Brutefir logic eq runtime module"
    echo "at /tmp/brutefir-rendered-0.txt"
    echo
    echo "Usage:bf_rendered.sh fs"
    echo
    exit 0
fi
