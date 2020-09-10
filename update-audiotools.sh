#!/bin/sh
# v0.3
# fix bangshee to sh
# default repo AudioHumLab

if [ -z $1 ] ; then
    echo "usage:"
    echo "    update-audiotools.sh  branch_name [git_repo]"
    echo
    echo "    (i) optional git_repo defaults to 'AudioHumLab'"
    echo
    exit 0
fi
branch=$1

if [ $2 ]; then
    gitsite="https://github.com/""$2"
else
    gitsite="https://github.com/AudioHumLab"
fi

echo
echo "WARNING: Will download from: [ ""$gitsite"" ]"
read -r -p "         Is this OK? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo 'Bye.'
    exit 0
fi

cd ~/

# Borramos si hubiera algun <branch>.zip
rm -f ~/$branch.zip*

# Bajamos el zip de GitHUb
wget "$gitsite"/audiotools/archive/$branch.zip
# Descomprimos ( se descomprime en audiotools-$branch )
unzip -o $branch.zip

# Borramos lo antiguo
rm -rf ~/audiotools

# Y renombramos el directorio descomprimido
mv ~/audiotools-$branch ~/audiotools

# Hacemos ejecutables los archivos
chmod +x ~/audiotools/*
chmod +x ~/audiotools/brutefir_eq/*py
chmod +x ~/audiotools/brutefir_eq/*sh

# Dejamos una marca indicando la branch contenida
touch ~/audiotools/THIS_BRANCH_IS_$branch

# Incluimos auditools en el PATH del profile del usuario
#   Buscamos el archivo del profile
profileFile=$(ls -a .*profile*)
#   Si no tiene incluido el path a audiotools, lo incluimos
if ! grep -q "audiotools" "$profileFile"; then
    echo "export PATH=$PATH:$HOME/audiotools" >> $profileFile
    export PATH=$PATH:$HOME/audiotools
fi

# Borramos el <branch>.zip
cd ~/
rm -f ~/$branch.zip
