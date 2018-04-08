#!/bin/bash

cd ~/
touch master.zip
rm master.zip*
wget https://github.com/Rsantct/audiotools/archive/master.zip
unzip -o master.zip
mv audiotools-master audiotools
chmod +x audiotools/*
