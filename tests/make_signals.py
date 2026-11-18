"""Señales de prueba (48 kHz, 4 canales float32: beat en 1/2, voz en 3/4)."""
import pathlib
import numpy as np, soundfile as sf
from scipy import signal as sg

D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
rng = np.random.default_rng(7)


def save(name, L, R, V1, V2):
    sf.write(D / name, np.stack([L, R, V1, V2], 1).astype(np.float32), SR, subtype="FLOAT")


def db(x): return 10 ** (x / 20)


n = SR * 2; t = np.arange(n) / SR
# beat: tonos repartidos por todo el espectro + ruido; R distinto de L (hay lados)
beat = sum(db(a) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6))
           for f, a in ((120, -14), (250, -16), (700, -18), (2000, -16), (3000, -20), (7000, -24)))
nz = sg.lfilter([1], [1, -0.97], rng.standard_normal(n)); nz *= db(-30) / nz.std()
L = beat + nz
R = 0.8 * beat + 0.6 * nz + db(-26) * np.sin(2 * np.pi * 1500 * t)
# voz: armónicos de 180 Hz con sílabas (~5 Hz) + aire; frases 0.25-1.1 s y 1.4-1.8 s, ruido de fondo -75 dB
f0 = 180 * (1 + 0.03 * np.sin(2 * np.pi * 3 * t))
ph = 2 * np.pi * np.cumsum(f0) / SR
voz = sum((1 / k) * np.sin(k * ph) for k in range(1, 30))
air = sg.sosfilt(sg.butter(2, [3000, 9000], "band", fs=SR, output="sos"), rng.standard_normal(n))
voz = voz / voz.std() + 0.3 * air / air.std()
syl = np.clip(np.sin(2 * np.pi * 5 * t), 0, 1) ** 0.5
frase = ((t > 0.25) & (t < 1.1)) | ((t > 1.4) & (t < 1.8))
env = sg.sosfiltfilt(sg.butter(1, 30, fs=SR, output="sos"), (syl * frase).astype(float))
voz = db(-18) * voz * env + db(-75) * rng.standard_normal(n)
save("beat_voz.wav", L, R, voz, voz * 0.95)
save("beat_sola.wav", L, R, 0 * t, 0 * t)
save("beat_vozbaja.wav", L, R, voz * db(-50), voz * db(-50))

# escalón: beat = 1 kHz a -10 dBFS; voz = 300 Hz a -20 dBFS RMS de 0.5 a 1.5 s (para medir la reducción en régimen)
s1 = db(-10) * np.sin(2 * np.pi * 1000 * t)
v = db(-20) * np.sqrt(2) * np.sin(2 * np.pi * 300 * t) * ((t > 0.5) & (t < 1.5))
save("step.wav", s1, s1, v, v)

# material real (grabaciones propias, no están en el repo): 20 s del instrumental de Nube baja + la voz seca
HOME = pathlib.Path.home() / "Music/ClaudeBeats"
INS = HOME / "Master/Instrumental Nube baja con Nube plugins (-13 LUFS).wav"
VOZ = HOME / "Media/voz_sola_seca.wav"
if INS.exists() and VOZ.exists():
    a, sra = sf.read(INS, frames=SR * 90, always_2d=True); v, srv = sf.read(VOZ, frames=SR * 90, always_2d=True)
    assert sra == SR and srv == SR, (sra, srv)
    t0, t1 = SR * 60, SR * 80
    vv = v[t0:t1]; vv = np.repeat(vv[:, :1], 2, 1) if vv.shape[1] == 1 else vv[:, :2]
    sf.write(D / "real.wav", np.concatenate([a[t0:t1, :2], vv], 1).astype(np.float32), SR, subtype="FLOAT")
print("ok", sorted(p.name for p in D.iterdir()))
