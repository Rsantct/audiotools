#!/bin/bash

function help {
  echo 
  echo "  v0.01beta"
  echo
  echo "  Cutre script para obtener copias de FIRs a otra Fs"
  echo
  echo "  Ejemplo de uso:  resamplePCM.sh 44100 48000"
  echo
  echo "  Se procesan todos los *.pcm del directorio actual"
  echo "  que se tratarán como Fs original 44100."
  echo "  Los resultados se dejan en carpeta_actual/48000/"
  echo
}

Fs1=$1
Fs2=$2

if [[ ! $Fs1 || ! $Fs2 ]]; then
    help
    exit -1
fi

mkdir -p $Fs1

# 1.Resampling con SoX
for fname in *pcm; do
    fnamef32=${fname/pcm/f32}
    cmd1="cp $fname $fnamef32"
    cmd2="sox   -c1 -r$Fs1 $fnamef32  $Fs2/$fnamef32 rate -v $Fs2"
    cmd3="cp $Fs2/$fnamef32 $Fs2/$fname"
    cmd4="rm $fnamef32"
    cmd5="rm $Fs2/$fnamef32"
    $cmd1 && $cmd2
    $cmd3 && $cmd4 && $cmd5
done

# 2. Recorte de los nuevos PCM a la misma longitud que el original.
#    No obstante Brutefir descartaría el exceso de taps respecto a 
#    lo que tenga configurado en filter_lenght / blocks
for fname in *pcm; do
    # Longitud en bytes del pcm original
    fsize=$(wc -c < $fname)
    # Longitud en taps, en float32 se emplean 4 bytes ( 4*8=32 bits)
    ftaps=$(( $fsize / 4 ))
    # Recortamos
    python ~/audiotools/trimPCM.py $Fs2/$fname -t$ftaps -o
done

# 3. Fin
echo Done, resampled files under $Fs2/
