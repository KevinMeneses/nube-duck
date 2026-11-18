#!/bin/zsh
# Renderiza los casos en REAPER (pestaña propia) y los compara con el modelo y con claude_duck_band.
# Uso: tests/run.sh [patrón de casos]. Con otras sesiones usando REAPER, envolver con el candado /tmp/nube-reaper.lock.
cd "$(dirname "$0")/.."
python3 tools/build.py >/dev/null || exit 1
PY=${NUBE_PY:-python3}   # necesita numpy, scipy y soundfile
[ -f tests/signals/beat_voz.wav ] || $PY tests/make_signals.py
$PY tests/cases.py >/dev/null || exit 1
# referencia: claude_duck_band con su "1e-12" escrito como 0.000000000001 (EEL2 no lee notación científica: el original
# nunca reduce). Se genera desde el original instalado y se enlaza junto al plugin (solo en esta máquina).
ORIG="$HOME/Library/Application Support/REAPER/Effects/Claude/claude_duck_band.jsfx"
FXD="$HOME/Library/Application Support/REAPER/Effects/Nube Duck"
sed -e 's/^desc:Claude Duck Band/desc:PRUEBA orig con 1e-12 escrito sin notacion cientifica/' -e 's/1e-12/0.000000000001/g' "$ORIG" > tests/orig_fix.jsfx
mkdir -p "$FXD"; ln -sf "$PWD/tests/orig_fix.jsfx" "$FXD/_prueba_orig_fix.jsfx"
echo -n "${1:-}" > tests/out/only.txt   # REAPER no hereda las variables de entorno
rm -f tests/out/log.txt
/Applications/REAPER.app/Contents/MacOS/REAPER -nonewinst "$PWD/tests/render_cases.lua" >/dev/null 2>&1 &
for i in $(seq 1 300); do grep -q done tests/out/log.txt 2>/dev/null && break; sleep 1; done
grep -q done tests/out/log.txt || { echo "REAPER no terminó (¿diálogo abierto?)"; exit 1; }
grep -i error tests/out/log.txt
$PY tests/check.py "${1:-}"
