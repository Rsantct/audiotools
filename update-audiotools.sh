#!/bin/bash
# v0.2
# admite actualizar otra branch distinta de 'master'

branch=master
if $1; then
    branch=$1

cd ~/

# Borramos si hubiera algun master.zip
rm -f ~/$branch.zip*

# Bajamos el zip de GitHUb
wget https://github.com/Rsantct/audiotools/archive/$branch.zip
# Descomprimos (se descomprime en audiotools-master)
unzip -o $branch.zip

# Borramos lo antiguo
rm -rf ~/audiotools

# Y renombramos el directorio descomprimido
mv ~/audiotools-$branch ~/audiotools

# Hacemos ejecutables los archivos
chmod +x ~/audiotools/*

# Incluimos auditools en el profile del usuario
#   Buscamos el archivo del profile
profileFile=$(ls -a .*profile*)
#   Si no tiene incluido el path a audiotools, lo incluimos
if ! grep -q "audiotools" "$profileFile"; then
    echo "export PATH=${PATH}:${HOME}/audiotools" >> $profileFile
    export PATH=$PATH:$HOME/audiotools
fi
