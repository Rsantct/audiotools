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

# Remove previous 
rm -f ~/$branch.zip*  1>/dev/null 2>&1

# Download project from GitHUb
curl -LO "$gitsite"/audiotools/archive/$branch.zip
# Descomprimos ( se descomprime en audiotools-$branch )
unzip -o $branch.zip

# Remove old
rm -rf ~/audiotools 1>/dev/null 2>&1

# Rename folder
mv ~/audiotools-$branch ~/audiotools

# Executable flags
chmod +x ~/audiotools/*
chmod +x ~/audiotools/brutefir_eq/*py
chmod +x ~/audiotools/brutefir_eq/*sh

# Leaving a dummy file with the installes branch name
touch ~/audiotools/THIS_BRANCH_IS_$branch

# Adding ~/audiotools to user's environment
#   Finding user's profile file
profileFile=$(ls -a .*profile*)
#   If not included, uptating $PATH whith ~/audiotools
if ! grep -q "audiotools" "$profileFile"; then
    echo "export PATH=\"\$PATH\":${HOME}/audiotools" >> "$profileFile"
    export PATH=$PATH:$HOME/audiotools
fi

# Removing <branch>.zip
cd ~/
rm -f ~/$branch.zip
