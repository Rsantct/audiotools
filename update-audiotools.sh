#!/bin/sh
# v0.3
# fix bangshee to sh
# default repo AudioHumLab

if [ -z $1 ] ; then
    echo "usage:"
    echo "    update-audiotools.sh   master   [git_repo]"
    echo
    echo "    (i) Default git_repo:                     'AudioHumLab'"
    echo "        You can use another branch name than  'master' "
    echo
    exit 0
fi
branch=$1

if [ $2 ]; then
    gitsite="https://github.com/""$2"
else
    gitsite="https://github.com/Rsantct"
fi

echo
echo "(i) Will download from: [ ""$gitsite"" ]"
read -r -p "    Is this OK? [y/N] " tmp
if [ "$tmp" != "y" ] && [ "$tmp" != "Y" ]; then
    echo 'Bye.'
    exit 0
fi

cd ~/

# Remove previous
rm -f ~/$branch.zip*    1>/dev/null 2>&1

# Download project from GitHUb
curl -LO "$gitsite"/audiotools/archive/$branch.zip
# Descomprimos ( se descomprime en audiotools-$branch )
unzip -o $branch.zip

# Remove old
rm -rf ~/audiotools     1>/dev/null 2>&1

# Rename folder
mv ~/audiotools-$branch ~/audiotools

# Executable flags
chmod +x ~/audiotools/*
chmod +x ~/audiotools/convolver_eq/*py
chmod +x ~/audiotools/convolver_eq/*sh

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
rm -f ~/$branch.zip         1>/dev/null 2>&1
rm ~/update-audiotools.sh   1>/dev/null 2>&1

echo
echo installed under:  "$HOME"/audiotools
echo
