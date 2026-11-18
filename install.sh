#!/bin/zsh
# Instala Nube Duck en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube Duck"
cd "$(dirname "$0")"
python3 tools/build.py
mkdir -p "$DST"
ln -sf "$PWD/nube_duck.jsfx" "$DST/nube_duck.jsfx"
echo "Listo: en REAPER busca \"Nube Duck\" en el navegador de FX (JS: Nube Duck)."
