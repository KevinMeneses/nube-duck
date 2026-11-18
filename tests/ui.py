"""Ayudante para probar la interfaz con cliclick. Las coordenadas son las de la interfaz en puntos (gfx con
SC = 2 en retina = puntos de pantalla); el origen se toma de la ventana real del FX (tests/winid.swift)."""
import math, pathlib, re, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
GY0 = 53            # alto de la barra de título + barra de presets de REAPER sobre el área gráfica (puntos)


def window():
    out = subprocess.run(["swift", str(ROOT / "tests/winid.swift")], capture_output=True, text=True).stdout.split()
    if not out: raise SystemExit("no está abierta la ventana del FX (tests/reopen.sh)")
    wid, x, y, w, h = (float(v) for v in out[:5])
    return int(wid), x, y, w, h


WID, WX, WY, WW, WH = window()
OX, OY = WX, WY + GY0
W, H = WW, WH - GY0                                    # tamaño del área de la interfaz

# layout (mismas fórmulas que la plantilla, SC = 1)
TOPH, PANH, FOOTH, ZH = 44, 196, 26, 20
GX, GY = 40, TOPH + 6
GW = W - GX - 16
GH = max(H - TOPH - PANH - FOOTH - ZH - 14, 110)
PY = GY + GH + 2 + ZH + 6
DRNG = 12


def f2x(f): return GX + GW * math.log10(f / 20) / 3
def d2y(d, rng=None): return GY + 8 + (GH - 22) * (-d / (rng or DRNG))


PRESETS, NORMAL, VOZ, QUITA = (180, 22), (334, 22), (407, 22), (507, 22)
MEZCLA, SALIDA = (max(576, W - 270) + 50, 22), (max(576, W - 270) + 166, 22)
ESCALA, ANALIZ = (GX + GW - 196 + 48, GY + GH - 32), (GX + GW - 96 + 45, GY + GH - 32)
CHIP = lambda b: (72 + 30 * b + 13, PY + 15)
ROW = PY + 47
ENC, FORMA, CANAL, MODO, VOZEN, SOLO, REINI = ((60, ROW), (202, ROW), (378, ROW), (549, ROW), (720, ROW),
                                               (834, ROW), (903, ROW))
KY = PY + 124
KNOB = {"desde": 50, "hasta": 124, "umbral": 198, "margen": 314, "prop": 388, "max": 462, "ataque": 536, "release": 610}


def pt(x, y): return f"{round(OX + x)},{round(OY + y)}"
def _cl(*a): subprocess.run(["cliclick", *a], check=True)


def cc(*args, wait=0.45):
    """como cliclick, pero c: y dc: son presiones explícitas (con REAPER cargado se pierden los clics muy cortos)
    y antes de apretar en un punto nuevo se mueve el mouse ahí y se espera un cuadro de la interfaz."""
    for a in args:
        k, _, p = a.partition(":")
        if k in ("c", "dc", "rc", "dd"):
            _cl("m:" + p); time.sleep(0.25)
        if k == "c":
            _cl("dd:" + p); time.sleep(0.12); _cl("du:" + p)
        elif k == "dc":
            _cl("dd:" + p); time.sleep(0.07); _cl("du:" + p); time.sleep(0.07)
            _cl("dd:" + p); time.sleep(0.07); _cl("du:" + p)
            time.sleep(1.0)   # si enseguida corre un script de REAPER (dump) se puede perder el arrastre siguiente
        else:
            _cl("-w", "200", a)
    time.sleep(wait)


def wheel(n): subprocess.run(["swift", str(ROOT / "tests/scroll.swift"), str(n)], check=True); time.sleep(0.5)
def shot(path): subprocess.run(["screencapture", "-x", "-o", f"-l{WID}", path], check=True); return path
def focus(): subprocess.run(["osascript", "-e", 'tell application "REAPER" to activate']); time.sleep(0.6); cc(f"c:{round(WX + 300)},{round(WY + 12)}")


def drag(x0, y0, x1, y1, steps=8, mods=None):
    if mods: cc(f"kd:{mods}")
    cc(f"dd:{pt(x0, y0)}", wait=0.15)
    for k in range(1, steps + 1): cc(f"dm:{pt(x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps)}", wait=0.08)
    cc(f"du:{pt(x1, y1)}")
    if mods: cc(f"ku:{mods}")


def dump():
    p = ROOT / "tests/out/dump.txt"; p.unlink(missing_ok=True)
    subprocess.Popen(["/Applications/REAPER.app/Contents/MacOS/REAPER", "-nonewinst", str(ROOT / "tests/ui_dump.lua")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if p.exists() and "done" in p.read_text(): break
        time.sleep(0.25)
    d = {}
    for line in p.read_text().splitlines():
        if "|" in line:
            i, n, f, v = line.split("|"); d[n] = (f, float(v))
    return d


def param(name, raw=False):
    """valor de un parámetro por su nombre (p. ej. 'B1 Desde (Hz)'): texto formateado o valor crudo."""
    d = dump()
    for n, (f, v) in d.items():
        if n.startswith(name): return v if raw else f
    return None


def menu_item(k, x, y, row=24, top=3):
    """clic en la fila k (0 = primera) de un menú que se abrió con el mouse en (x, y)."""
    cc(f"c:{pt(x + 30, y + top + row * k + row / 2)}", wait=0.7)
