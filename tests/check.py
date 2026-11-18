"""Compara los renders de tests/out con el modelo de referencia (model.py) y con claude_duck_band.
Sale con código 1 si algo falla."""
import math, pathlib, sys
import numpy as np, soundfile as sf
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from model import duck
from cases import CASES, model_bands

T = pathlib.Path(__file__).resolve().parent
D = T / "out"; S = T / "signals"; SR = 48000
only = sys.argv[1] if len(sys.argv) > 1 else None
fails = 0


def load(p):
    x, sr = sf.read(p, always_2d=True); assert sr == SR; return x


def db(x): return 20 * math.log10(max(x, 1e-30))


def report(ok, name, msg):
    global fails
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:16s} {msg}")


def diff(name, a, b, tol):
    n = min(len(a), len(b)); d = np.abs(a[:n] - b[:n]).max()
    report(d <= tol, name, f"dif. máx {db(d):7.1f} dBFS (tolerancia {db(tol):.0f})")


def rms(x): return math.sqrt(np.mean(x ** 2))


cases = {c[0]: c for c in CASES}
sigs = {}
for name, c in cases.items():
    if only and only not in name: continue
    f = D / f"{name}.wav"
    if not f.exists():
        report(False, name, "no hay render"); continue
    y = load(f)
    if c[1] not in sigs:
        sigs[c[1]] = load(S / f"{c[1]}.wav")
    x = sigs[c[1]]
    if c[2] == "orig":
        # el original tal cual en REAPER: ¿hace algo?
        d = np.abs(y - x[:len(y), :2]).max()
        print(f"    {name:16s} claude_duck_band en REAPER: salida - entrada máx {db(d):.1f} dBFS" + (" (NO HACE NADA)" if d == 0 else ""))
        continue
    if c[2] == "orig_ni":
        from model import original
        ref, _ = original(x.astype(np.float64), SR, c[6]) if "real" not in name else (None, None)
        if ref is not None: diff(name + " (modelo)", y, ref.astype(np.float32), 2e-6)
        continue
    if name.startswith("n_"):      # sin voz útil: la salida tiene que ser la entrada, bit a bit
        diff(name, y, x[:, :2].astype(np.float32), 0)
    elif name.startswith("f_"):
        continue
    elif "real" in name:
        pass
    else:
        ref, _ = duck(x.astype(np.float64), model_bands(c), SR, c[3])
        diff(name, y, ref.astype(np.float32), 2e-6)

# igual que claude_duck_band (los dos renders en REAPER)
for a, b in (("duck_def", "origni_def"), ("duck_p1", "origni_def"), ("duck_cust", "origni_cust"), ("duck_real_p1", "origni_real")):
    if only and only not in a: continue
    if (D / f"{a}.wav").exists() and (D / f"{b}.wav").exists():
        ya, yb = load(D / f"{a}.wav"), load(D / f"{b}.wav")
        diff(f"{a}=orig", ya, yb, 2e-7)
        if a == "duck_real_p1":
            xr = sigs.get("real")
            if xr is None: xr = load(S / "real.wav")
            red = db(rms(xr[:, 0] - ya[:, 0])) - db(rms(xr[:, 0]))
            print(f"    (material real: lo que se quita al instrumental queda {red:.1f} dB bajo el instrumental)")

# medidas físicas en régimen (escalón: beat 1 kHz -10 dBFS pico, voz 300 Hz -20 dBFS RMS de 0.5 a 1.5 s)
def seg(y, t0, t1): return y[int(t0 * SR):int(t1 * SR), 0]
if (not only or "f_" in only) and (D / "f_todo_sv.wav").exists():
    y = load(D / "f_todo_sv.wav"); x = load(S / "step.wav")
    got = db(rms(seg(y, 1.0, 1.45))) - db(rms(seg(x, 1.0, 1.45)))
    want = -min(24, (-20 + 40) * 0.5)           # Solo voz: (nivel voz - umbral) * proporción
    report(abs(got - want) < 0.15, "f_todo_sv", f"reducción {got:+.2f} dB (teoría {want:+.2f})")
    got0 = db(rms(seg(y, 0.1, 0.45))) - db(rms(seg(x, 0.1, 0.45)))
    report(abs(got0) < 0.001, "f_todo_sv antes", f"{got0:+.4f} dB sin voz")
if (not only or "f_" in only) and (D / "f_comp.wav").exists():
    y = load(D / "f_comp.wav"); x = load(S / "step.wav")
    # banda 500-2000 en 1 kHz: B = LP(2000) - LP(500) (SVF = bilineal de Butterworth 2.º orden)
    def lp(f, fc):
        w = math.tan(math.pi * f / SR) / math.tan(math.pi * fc / SR); return 1 / complex(1 - w * w, math.sqrt(2) * w)
    B = lp(1000, 2000) - lp(1000, 500)
    lR = db(10 ** (-10 / 20) / math.sqrt(2) * abs(B))
    gr = min(24, max(0, (lR - (-20 - 14)) * 0.7))     # Competencia, voz completa a -20
    want = db(abs(1 - (1 - 10 ** (-gr / 20)) * B))
    got = db(rms(seg(y, 1.0, 1.45))) - db(rms(seg(x, 1.0, 1.45)))
    report(abs(got - want) < 0.15, "f_comp", f"reducción en 1 kHz {got:+.2f} dB (teoría {want:+.2f}; banda a {gr:.1f} dB)")

print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
