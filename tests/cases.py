"""Casos de prueba: los usa render_cases.lua (vía tests/out/cases.txt) y check.py (para el modelo).

slider N del JSFX = parámetro N-1 en REAPER. Globales 1..7; banda b (0..3), parámetro p (0..12) = slider 11 + 13 b + p.
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from model import BAND_KEYS, BAND_DEFAULT

ROOT = pathlib.Path(__file__).resolve().parent.parent
GKEYS = {"salida": 1, "mezcla": 2, "escuchar": 3, "solo": 4}
BAND_DEF = [(1, 0, 1000, 4000), (0, 0, 150, 300), (0, 0, 5000, 10000), (0, 0, 400, 1000)]   # = tools/build.py


def default_bands():
    return [{**BAND_DEFAULT, "on": d[0], "forma": d[1], "desde": d[2], "hasta": d[3]} for d in BAND_DEF]


def bands_with(*changes):
    """changes: (b, dict) -> lista de 4 bandas completas a partir de los valores por defecto del plugin."""
    B = default_bands()
    for b, d in changes:
        B[b].update(d)
    return B


def presets():
    """Lee load_preset() de la plantilla y devuelve {n: lista de 4 bandas}."""
    src = (ROOT / "src/nube_duck.template.jsfx").read_text()
    body = src[src.index("function load_preset(n)"):src.index("sel = 0; drag = 0;")]
    out = {}
    for m in re.finditer(r"n == (\d+) \? \((.*?)\n  \)", body, re.S):
        n = int(m.group(1)); B = default_bands()
        for b in B: b["on"] = 0
        if "band_default(b)" in m.group(2):
            B = default_bands()
        for f, args in re.findall(r"(band_set|band_dyn)\(([^)]*)\)", m.group(2)):
            a = [float(v) for v in args.split(",")]; b = int(a[0])
            if f == "band_set":
                B[b].update(on=1, forma=a[1], desde=a[2], hasta=a[3], canal=a[4])
            else:
                B[b].update(modo=a[1], umbral=a[2], margen=a[3], prop=a[4], max=a[5], att=a[6], rel=a[7], vozen=a[8])
        out[n] = B
    return out


PRESETS = presets()
ORIG_DEF = (1000, 4000, 14, 0.7, 4, 5, 120, -50)
ORIG_CUST = (200, 500, 10, 0.5, 6, 10, 200, -45)   # el original no baja de 200 Hz en "Banda desde"

# (nombre, señal, fx, globales, bandas (None = las del plugin sin tocar), preset, sliders del original)
CASES = [
    ("orig_def", "beat_voz", "orig", {}, None, 0, ORIG_DEF),
    ("origni_def", "beat_voz", "orig_ni", {}, None, 0, ORIG_DEF),
    ("origni_cust", "beat_voz", "orig_ni", {}, None, 0, ORIG_CUST),
    ("origni_real", "real", "orig_ni", {}, None, 0, ORIG_DEF),
    ("duck_def", "beat_voz", "duck", {}, None, 0, None),
    ("duck_p1", "beat_voz", "duck", {}, None, 1, None),
    ("orig_cust", "beat_voz", "orig", {}, None, 0, ORIG_CUST),
    ("duck_cust", "beat_voz", "duck", {}, bands_with((0, dict(desde=200, hasta=500, margen=10, prop=0.5, max=6, att=10, rel=200, umbral=-45))), 0, None),
    ("orig_real", "real", "orig", {}, None, 0, ORIG_DEF),
    ("duck_real_p1", "real", "duck", {}, None, 1, None),
    ("m_mid_side", "beat_voz", "duck", {}, bands_with((0, dict(canal=1, max=8)), (1, dict(on=1, canal=2, max=8, margen=20))), 0, None),
    ("m_graves", "beat_voz", "duck", {}, bands_with((0, dict(forma=1, hasta=400, max=6))), 0, None),
    ("m_agudos", "beat_voz", "duck", {}, bands_with((0, dict(forma=2, desde=5000, max=6, att=1, rel=60))), 0, None),
    ("m_todo", "beat_voz", "duck", {}, bands_with((0, dict(forma=3, modo=1, umbral=-40, vozen=1, max=10, prop=0.5))), 0, None),
    ("m_vozen", "beat_voz", "duck", {}, bands_with((0, dict(vozen=1, max=10))), 0, None),
    ("m_swap", "beat_voz", "duck", {}, bands_with((0, dict(desde=4000, hasta=1000))), 0, None),
    ("m_4bands", "beat_voz", "duck", {}, bands_with((0, dict(max=6, att=2, rel=80)), (1, dict(on=1, max=5, margen=18, att=20, rel=400)),
                                                     (2, dict(on=1, max=9, canal=1, modo=1, umbral=-35, prop=0.3)),
                                                     (3, dict(on=1, max=3, canal=2, vozen=1, att=0.5, rel=10))), 0, None),
    ("m_mix50", "beat_voz", "duck", {"mezcla": 50}, bands_with((0, dict(max=10))), 0, None),
    ("m_out-6", "beat_voz", "duck", {"salida": -6}, None, 0, None),
    ("m_esc_voz", "beat_voz", "duck", {"escuchar": 1}, None, 0, None),
    ("m_esc_quita", "beat_voz", "duck", {"escuchar": 2}, bands_with((0, dict(max=10))), 0, None),
    ("m_solo2", "beat_voz", "duck", {"solo": 2}, bands_with((1, dict(on=1))), 0, None),
    ("m_solo_side", "beat_voz", "duck", {"solo": 1}, bands_with((0, dict(canal=2))), 0, None),
    ("m_solo_off", "beat_voz", "duck", {"solo": 3}, None, 0, None),
    ("n_sola_p10", "beat_sola", "duck", {}, None, 10, None),
    ("n_baja_p11", "beat_vozbaja", "duck", {}, None, 11, None),
    ("f_todo_sv", "step", "duck", {}, bands_with((0, dict(forma=3, modo=1, umbral=-40, vozen=1, prop=0.5, max=24))), 0, None),
    ("f_comp", "step", "duck", {}, bands_with((0, dict(desde=500, hasta=2000, vozen=1, prop=0.7, max=24))), 0, None),
] + [(f"p{n}", "beat_voz", "duck", {}, None, n, None) for n in sorted(PRESETS)]


def sliders(case):
    """{slider: valor} que el script de REAPER pone al FX."""
    name, sig, fx, g, bands, preset, orig = case
    if fx.startswith("orig"):
        return {i + 1: v for i, v in enumerate(orig)}
    s = {GKEYS[k]: v for k, v in g.items()}
    if bands:
        for b, d in enumerate(bands):
            for p, k in enumerate(BAND_KEYS):
                s[11 + 13 * b + p] = d[k]
    if preset:
        s[7] = preset
    return s


def model_bands(case):
    name, sig, fx, g, bands, preset, orig = case
    return PRESETS[preset] if preset else (bands or default_bands())


if __name__ == "__main__":
    out = ROOT / "tests/out"; out.mkdir(exist_ok=True)
    with open(out / "cases.txt", "w") as f:
        for c in CASES:
            f.write(";".join([c[0], c[1] + ".wav", c[2], ",".join(f"{k}={v:g}" for k, v in sliders(c).items())]) + "\n")
    print(len(CASES), "casos;", len(PRESETS), "presets")
