"""Modelo de referencia de Nube Duck (muestra a muestra, mismo orden de operaciones que el JSFX)
y del JSFX de origen claude_duck_band, para compararlos fuera de REAPER y contra los renders.

Uso: from model import duck, original, BAND_DEFAULT
"""
import math
import numpy as np

# parámetros de banda (mismo orden que los sliders del JSFX)
BAND_KEYS = ["on", "forma", "desde", "hasta", "canal", "modo", "umbral", "margen", "prop", "max", "att", "rel", "vozen"]
BAND_DEFAULT = dict(on=1, forma=0, desde=1000, hasta=4000, canal=0, modo=0, umbral=-50, margen=14, prop=0.7,
                    max=4, att=5, rel=120, vozen=0)
GLOBAL_DEFAULT = dict(salida=0, mezcla=100, escuchar=0, solo=0)


class LP:
    """SVF trapezoidal (Simper), salida pasa bajos, k = sqrt(2): idéntico a svf_init/lp del original."""
    def __init__(self, f, sr):
        g = math.tan(math.pi * f / sr); k = 1.41421356
        self.a1 = 1 / (1 + g * (g + k)); self.a2 = g * self.a1; self.a3 = g * self.a2
        self.ic1 = self.ic2 = 0.0

    def __call__(self, x):
        v3 = x - self.ic2
        v1 = self.a1 * self.ic1 + self.a2 * v3
        v2 = self.ic2 + self.a2 * self.ic1 + self.a3 * v3
        self.ic1 = 2 * v1 - self.ic1; self.ic2 = 2 * v2 - self.ic2
        return v2


def original(x, sr=48000, s=(1000, 4000, 14, 0.7, 4, 5, 120, -50)):
    """claude_duck_band.jsfx tal cual. x: (n, 4) -> (n, 2)."""
    f1, f2, margen, prop, mx, att, rel, thr = s
    hpL, hpR, hpVL, hpVR = (LP(f1, sr) for _ in range(4))
    lpL, lpR, lpVL, lpVR = (LP(f2, sr) for _ in range(4))
    ce = math.exp(-1 / (0.01 * sr)); ca = math.exp(-1 / (att * 0.001 * sr)); cr = math.exp(-1 / (rel * 0.001 * sr))
    envR = envV = gr = 0.0
    out = np.zeros((len(x), 2)); grs = np.zeros(len(x))
    for i in range(len(x)):
        s0, s1, s2, s3 = x[i]
        bL = lpL(s0) - hpL(s0); bR = lpR(s1) - hpR(s1)
        vb = (lpVL(s2) - hpVL(s2) + lpVR(s3) - hpVR(s3)) * 0.5
        envR = ce * envR + (1 - ce) * (((bL + bR) * 0.5) ** 2)
        envV = ce * envV + (1 - ce) * (vb * vb)
        lR = 10 * math.log10(envR + 1e-12); lV = 10 * math.log10(envV + 1e-12)
        want = 0.0
        if lV > thr:
            want = (lR - (lV - margen)) * prop; want = max(0.0, min(mx, want))
        gr = ca * gr + (1 - ca) * want if want > gr else cr * gr + (1 - cr) * want
        g = 10 ** (-gr / 20)
        out[i] = s0 - bL * (1 - g), s1 - bR * (1 - g)
        grs[i] = gr
    return out, grs


class Band:
    def __init__(self, p, sr):
        self.p = p
        lo, hi = sorted((p["desde"], p["hasta"]))
        if p["forma"] == 1: hi = p["hasta"]          # Graves: solo "hasta"
        if p["forma"] == 2: lo = p["desde"]          # Agudos: solo "desde"
        self.lo, self.hi = lo, hi
        self.f = {k: (LP(hi, sr), LP(lo, sr)) for k in ("a", "b", "v")}   # L (o M/S), R, voz
        self.ce = math.exp(-1 / (0.01 * sr))
        self.ca = math.exp(-1 / (p["att"] * 0.001 * sr)); self.cr = math.exp(-1 / (p["rel"] * 0.001 * sr))
        self.envR = self.envV = self.gr = 0.0

    def band(self, x, key):
        hi, lo = self.f[key]; fo = self.p["forma"]
        if fo == 0: return hi(x) - lo(x)
        if fo == 1: return hi(x)
        if fo == 2: return x - lo(x)
        return x


def duck(x, bands, sr=48000, g=None):
    """Nube Duck. x: (n, 4). bands: lista de hasta 4 dicts (faltantes = BAND_DEFAULT). g: globales.
    Devuelve (salida (n,2), reducción por banda (n,4) en dB)."""
    g = {**GLOBAL_DEFAULT, **(g or {})}
    B = [Band({**BAND_DEFAULT, **b}, sr) if b.get("on", 1) else None for b in bands]
    B += [None] * (4 - len(B))
    solo = g["solo"] if g["solo"] and B[g["solo"] - 1] is not None else 0   # solo de una banda apagada = sin solo
    ce = math.exp(-1 / (0.01 * sr))
    og = 10 ** (g["salida"] / 20); mix = g["mezcla"] / 100
    out = np.zeros((len(x), 2)); grs = np.zeros((len(x), 4))
    envT = 0.0
    for i in range(len(x)):
        s0, s1, s2, s3 = x[i]
        L, R = s0, s1
        vm = (s2 + s3) * 0.5
        envT = ce * envT + (1 - ce) * (vm * vm)   # voz completa (para "Toda la voz")
        soloL = soloR = 0.0
        for k, b in enumerate(B):
            if b is None: continue
            p = b.p; ch = p["canal"]
            if ch == 0:
                bL = b.band(L, "a"); bR = b.band(R, "b"); det = (bL + bR) * 0.5
            else:
                m = (L + R) * 0.5; s = (L - R) * 0.5
                bL = b.band(m if ch == 1 else s, "a"); det = bL
            vb = b.band(vm, "v")
            b.envR = b.ce * b.envR + (1 - b.ce) * (det * det)
            b.envV = b.ce * b.envV + (1 - b.ce) * (vb * vb)
            lR = 10 * math.log10(b.envR + 1e-12)
            lV = 10 * math.log10((b.envV if p["vozen"] == 0 else envT) + 1e-12)
            want = 0.0
            if lV > p["umbral"]:
                want = ((lR - (lV - p["margen"])) if p["modo"] == 0 else (lV - p["umbral"])) * p["prop"]
                want = max(0.0, min(p["max"], want))
            b.gr = b.ca * b.gr + (1 - b.ca) * want if want > b.gr else b.cr * b.gr + (1 - b.cr) * want
            gg = 10 ** (-b.gr / 20)
            if solo == k + 1:
                soloL, soloR = (bL, bR) if ch == 0 else (bL, bL) if ch == 1 else (bL, -bL)
            if ch == 0:
                L = L - bL * (1 - gg); R = R - bR * (1 - gg)
            elif ch == 1:
                m = m - bL * (1 - gg); L = m + s; R = m - s
            else:
                s = s - bL * (1 - gg); L = m + s; R = m - s
            grs[i, k] = b.gr
        if solo:
            oL, oR = soloL, soloR
        elif g["escuchar"] == 1:
            oL, oR = s2, s3
        else:
            oL, oR = (L, R) if mix >= 1 else (s0 + (L - s0) * mix, s1 + (R - s1) * mix)
            if g["escuchar"] == 2:
                oL = s0 - oL; oR = s1 - oR
        out[i] = oL * og, oR * og
    return out, grs


if __name__ == "__main__":
    # autoverificación: con los ajustes por defecto, Nube Duck == claude_duck_band
    sr = 48000; n = sr // 2; rng = np.random.default_rng(3)
    t = np.arange(n) / sr
    beat = 0.3 * np.sin(2 * np.pi * 2000 * t) + 0.05 * rng.standard_normal(n)
    voz = 0.2 * rng.standard_normal(n) * (t > 0.1)
    x = np.stack([beat, beat * 0.8, voz, voz * 0.9], 1)
    a, ga = original(x, sr)
    b, gb = duck(x, [dict()], sr)
    print("máx dif muestra:", np.abs(a - b).max(), " máx dif GR:", np.abs(ga - gb[:, 0]).max(), " GR final:", ga[-1])
