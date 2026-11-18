#!/usr/bin/env python3
"""Genera nube_duck.jsfx desde src/nube_duck.template.jsfx.

JSFX no tiene arreglos de sliders, asi que este script escribe:
  - las declaraciones de los sliders (7 globales + 4 bandas x 13 parametros)
  - slider_set(i, v) y slider_aut(i): acceso por indice con un arbol de comparaciones,
    porque slider_automate() necesita la referencia literal sliderN.
"""
from pathlib import Path

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent.parent
NB, NP, P0 = 4, 13, 11

# mismos nombres y orden que preset_name() en la plantilla (sin comas: separan la lista)
PRESETS = [
    "Nube baja - Rhodes se aparta de la voz",
    "Rhodes / piano - hueco en el centro",
    "Guitarra (reggaeton / R&B) - hueco para la voz",
    "Pads / coros - atras de la voz",
    "Lead / melodia (trap) - cede la presencia",
    "Campanas / kalimba / plucks",
    "808 / bajo - deja el cuerpo de la voz",
    "808 drill (glides) - suave",
    "Hi-hats - no tapan las s",
    "Instrumental completo - 3 bandas",
    "Instrumental completo - solo el centro (M/S)",
    "Dancehall - organo y stab ceden la voz",
    "Reggaeton - beat completo suave",
    "Rap rapido - reaccion corta",
    "Voz cantada / R&B - movimientos lentos",
    "Ad-libs / dobles - abren paso a la voz principal",
    "Reverb / delay de la voz - se apartan al cantar",
    "Hablado / intro - el beat baja entero",
    "Tag / drop - ducking clasico",
    "Lo-fi - sutil",
    "Por defecto",
]

GLOBALS = [
    (1, "0<-24,24,0.1>-Salida (dB)"),
    (2, "100<0,100,1>-Mezcla (%)"),
    (3, "0<0,2,1{Normal,Voz (sidechain 3/4),Lo que se quita}>-Escuchar"),
    (4, "0<0,4,1{Apagado,Banda 1,Banda 2,Banda 3,Banda 4}>-Solo de banda"),
    (5, "1<0,2,1{6 dB,12 dB,24 dB}>-Escala de la grafica"),
    (6, "1<0,1,1{Apagado,Encendido}>-Analizador"),
    (7, "0<0,%d,1{-,%s}>-Cargar preset" % (len(PRESETS), ",".join(PRESETS))),
]

# valores por defecto por banda: estado, forma, desde, hasta (el resto es igual en todas)
BAND_DEF = [(1, 0, 1000, 4000), (0, 0, 150, 300), (0, 0, 5000, 10000), (0, 0, 400, 1000)]
BAND = [
    ("%d<0,1,1{Apagada,Encendida}>", "Estado"),
    ("%d<0,3,1{Banda (desde-hasta),Graves (hasta),Agudos (desde),Todo}>", "Forma"),
    ("%d<20,20000,1:log=1000>", "Desde (Hz)"),
    ("%d<20,20000,1:log=1000>", "Hasta (Hz)"),
    ("0<0,2,1{Estereo,Centro (Mid),Lados (Side)}>", "Canal"),
    ("0<0,1,1{Competencia (beat vs voz),Solo voz (umbral)}>", "Modo"),
    ("-50<-80,0,0.5>", "Umbral de voz (dB)"),
    ("14<0,30,0.5>", "Margen bajo la voz (dB)"),
    ("0.7<0.1,1,0.05>", "Proporcion"),
    ("4<0,24,0.5>", "Reduccion max (dB)"),
    ("5<0.5,200,0.1:log=10>", "Ataque (ms)"),
    ("120<10,2000,1:log=200>", "Release (ms)"),
    ("0<0,1,1{Misma banda,Toda la voz}>", "Voz detectada en"),
]


def slider_lines():
    lines = [f"slider{i}:{d}" for i, d in GLOBALS]
    for b in range(NB):
        for p, (spec, name) in enumerate(BAND):
            idx = P0 + b * NP + p
            if p < 4:
                spec = spec % BAND_DEF[b][p]
            lines.append(f"slider{idx}:{spec}-B{b + 1} {name}")
    return lines


def indices():
    return [i for i, _ in GLOBALS] + [P0 + k for k in range(NB * NP)]


def tree(idx, leaf):
    if len(idx) == 1:
        return leaf(idx[0])
    mid = len(idx) // 2
    return f"(i < {idx[mid]} ? ({tree(idx[:mid], leaf)}) : ({tree(idx[mid:], leaf)}))"


def setters():
    idx = indices()
    s = "function slider_set(i, v) (\n  " + tree(idx, lambda n: f"slider{n} = v") + ";\n);\n"
    s += "function slider_aut(i) (\n  " + tree(idx, lambda n: f"slider_automate(slider{n})") + ";\n);\n"
    return s


def defaults_code():
    """Valores por defecto de cada banda para el preset 'Por defecto' y el boton de reiniciar banda."""
    return "\n".join(f"  b == {b} ? ( st = {d[0]}; fo = {d[1]}; f1 = {d[2]}; f2 = {d[3]}; ) :" for b, d in enumerate(BAND_DEF)) + \
        "\n  ( st = 0; fo = 0; f1 = 1000; f2 = 4000; );"


def check_presets(src):
    for i, name in enumerate(PRESETS, 1):
        assert f'n == {i} ? "{name}"' in src, f"preset {i} no coincide con la plantilla: {name}"
    assert f"NPRESETS = {len(PRESETS)};" in src, "NPRESETS no coincide"


def main():
    src = (ROOT / "src" / "nube_duck.template.jsfx").read_text()
    check_presets(src)
    out = (src.replace("@@SLIDERS@@", "\n".join(slider_lines()))
              .replace("@@SETTERS@@", setters())
              .replace("@@BAND_DEFAULTS@@", defaults_code())
              .replace("@@VERSION@@", VERSION))
    dst = ROOT / "nube_duck.jsfx"
    dst.write_text(out)
    print(f"{dst} ({len(out.splitlines())} lineas, {len(indices())} sliders)")


if __name__ == "__main__":
    main()
