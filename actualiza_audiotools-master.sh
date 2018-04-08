#!/bin/bash

cd ~/

# Borramos si hubiera algun master.zip
if [[ -f master.zip ]]; then
    rm master.zip*

# Bajamos el zip de GitHUb
wget https://github.com/Rsantct/audiotools/archive/master.zip
# Descomprimos (se descomprime en audiotools-master)
unzip -o master.zip

# Borramos lo antiguo
rm -rf ~/auditools

# Y renombramos el directorio descomprimido 
mv audiotools-master audiotools

# Hacemos ejecutables los archivos
chmod +x audiotools/*

