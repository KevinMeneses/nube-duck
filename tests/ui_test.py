"""Pruebas de la interfaz con el mouse (cliclick). Abre antes la demo: tests/reopen.sh 21 (preset "Por defecto").
OJO: mueve el mouse de verdad; no usar la Mac mientras corre. Con otras sesiones, envolver con /tmp/nube-reaper.lock."""
import math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from ui import *

fails = 0


def check(name, got, want):
    global fails
    ok = want(got) if callable(want) else got == want
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:52s} {got!r}")


def num(s): return float(s.split()[0]) if s else float("nan")
def knob(k): return KNOB[k], KY


focus()
check("arranca con Por defecto (B1 1000-4000)", (num(param("B1 Desde")), num(param("B1 Hasta"))), (1000, 4000))

# ---- menús de la banda
for ctl, name, k, want in ((FORMA, "B1 Forma", 2, "Agudos (desde)"), (FORMA, "B1 Forma", 0, "Banda (desde-hasta)"),
                           (CANAL, "B1 Canal", 1, "Centro (Mid)"), (CANAL, "B1 Canal", 0, "Estereo"),
                           (MODO, "B1 Modo", 1, "Solo voz (umbral)"), (MODO, "B1 Modo", 0, "Competencia (beat vs voz)"),
                           (VOZEN, "B1 Voz detectada", 1, "Toda la voz"), (VOZEN, "B1 Voz detectada", 0, "Misma banda")):
    cc(f"c:{pt(*ctl)}", wait=0.9); menu_item(k, *ctl)
    check(f"menu {name.split()[1]}: fila {k}", param(name), want)

# ---- perillas: arrastrar, rueda, doble clic
x, y = knob("margen"); drag(x, y, x, y - 40)
check("arrastrar Margen 40 px arriba (+5.5 dB)", num(param("B1 Margen")), lambda v: 18.5 <= v <= 20.5)
cc(f"dc:{pt(x, y)}"); check("doble clic en Margen = 14", num(param("B1 Margen")), 14.0)
x, y = knob("umbral"); drag(x, y, x, y + 30)
check("arrastrar Umbral hacia abajo baja", num(param("B1 Umbral")), lambda v: v < -55)
cc(f"dc:{pt(x, y)}"); check("doble clic en Umbral = -50", num(param("B1 Umbral")), -50.0)
x, y = knob("max"); drag(x, y, x, y - 50)
check("arrastrar Reduccion max arriba (+5.5 dB)", num(param("B1 Reduccion")), lambda v: 9 <= v <= 10)
cc(f"dc:{pt(x, y)}"); check("doble clic en Reduccion max = 4", num(param("B1 Reduccion")), 4.0)
x, y = knob("release"); cc(f"m:{pt(x, y)}"); wheel(5)
check("rueda sobre Release sube", num(param("B1 Release")), lambda v: 125 < v < 200)
cc(f"dc:{pt(x, y)}"); check("doble clic en Release = 120", num(param("B1 Release")), 120.0)
x, y = knob("prop"); drag(x, y, x, y - 30)
check("arrastrar Proporcion arriba", num(param("B1 Proporcion")), lambda v: 0.75 <= v <= 0.9)
x, y = knob("desde"); drag(x, y, x, y - 20)
check("arrastrar Desde arriba", num(param("B1 Desde")), lambda v: 1300 < v < 2200)
cc(f"c:{pt(*REINI)}")
check("Reiniciar: Desde, Proporcion, Estado", (num(param("B1 Desde")), num(param("B1 Proporcion")), param("B1 Estado")),
      (1000, 0.7, "Encendida"))

# ---- gráfica: bordes, cuerpo, rueda
yz = d2y(-2)
drag(f2x(1000), yz, f2x(700), yz)
check("arrastrar borde izquierdo a 700 Hz", num(param("B1 Desde")), lambda v: 670 <= v <= 730)
drag(f2x(4000), yz, f2x(6000), yz)
check("arrastrar borde derecho a 6 kHz", num(param("B1 Hasta")), lambda v: 5750 <= v <= 6250)
xc = f2x(math.sqrt(700 * 6000)); drag(xc, yz, xc + 40, yz + 30)
check("arrastrar cuerpo: mueve desde (x1.35)", num(param("B1 Desde")), lambda v: 900 <= v <= 990)
check("arrastrar cuerpo: hasta se mueve igual", num(param("B1 Hasta")), lambda v: 7700 <= v <= 8500)
check("arrastrar cuerpo hacia abajo: max +1.3", num(param("B1 Reduccion")), lambda v: 5 <= v <= 6)
lo, hi = num(param("B1 Desde")), num(param("B1 Hasta"))
xc = f2x(math.sqrt(lo * hi)); cc(f"m:{pt(xc, yz)}"); wheel(4)
lo2, hi2 = num(param("B1 Desde")), num(param("B1 Hasta"))
check("rueda sobre la banda: mas ancha, mismo centro", (round(hi2 / lo2, 1), round(math.sqrt(lo2 * hi2) / math.sqrt(lo * hi), 2)),
      lambda v: v[0] > hi / lo * 1.2 and abs(v[1] - 1) < 0.03)

# ---- doble clic en vacío / Alt+clic
cc(f"dc:{pt(f2x(150), d2y(-6))}")
check("doble clic en vacio a 150 Hz: enciende B2", param("B2 Estado"), "Encendida")
check("  B2 una octava alrededor de 150", (num(param("B2 Desde")), num(param("B2 Hasta"))),
      lambda v: 95 <= v[0] <= 118 and 190 <= v[1] <= 235)
cc("kd:alt"); cc(f"c:{pt(f2x(150), d2y(-2))}"); cc("ku:alt")
check("Alt+clic sobre B2: la apaga", param("B2 Estado"), "Apagada")

# ---- chips, encendido, solo
cc(f"dc:{pt(*CHIP(2))}"); check("doble clic en chip 3: enciende B3", param("B3 Estado"), "Encendida")
cc(f"c:{pt(*ENC)}"); check("boton Encendida (B3 seleccionada): apaga", param("B3 Estado"), "Apagada")
cc(f"c:{pt(*CHIP(0))}"); cc(f"c:{pt(*SOLO)}"); check("Solo con B1 seleccionada", param("Solo de banda"), "Banda 1")
cc(f"c:{pt(*SOLO)}"); check("Solo otra vez: apagado", param("Solo de banda"), "Apagado")

# ---- barra superior
cc(f"c:{pt(*VOZ)}"); check("Escuchar Voz (SC)", param("Escuchar"), "Voz (sidechain 3/4)")
cc(f"c:{pt(*QUITA)}"); check("Escuchar Lo que se quita", param("Escuchar"), "Lo que se quita")
cc(f"c:{pt(*SOLO)}"); cc(f"c:{pt(*NORMAL)}")
check("Normal: vuelve a normal y quita el solo", (param("Escuchar"), param("Solo de banda")), ("Normal", "Apagado"))
x, y = MEZCLA; drag(x, y, x, y + 44)
check("arrastrar Mezcla hacia abajo (-20 %)", num(param("Mezcla")), lambda v: 75 <= v <= 85)
cc(f"dc:{pt(x, y)}"); check("doble clic en Mezcla = 100", num(param("Mezcla")), 100.0)
x, y = SALIDA; drag(x, y, x, y - 22)
check("arrastrar Salida arriba (+4.8 dB)", num(param("Salida")), lambda v: 4 <= v <= 5.5)
cc(f"dc:{pt(x, y)}"); check("doble clic en Salida = 0", num(param("Salida")), 0.0)
cc(f"c:{pt(*ESCALA)}"); check("boton Escala: 12 -> 24 dB", param("Escala"), "24 dB")
cc(f"c:{pt(*ESCALA)}"); cc(f"c:{pt(*ESCALA)}"); check("Escala dos veces mas: vuelve a 12", param("Escala"), "12 dB")
cc(f"c:{pt(*ANALIZ)}"); check("boton Analizador: apagado", param("Analizador"), "Apagado")
cc(f"c:{pt(*ANALIZ)}"); check("Analizador otra vez: encendido", param("Analizador"), "Encendido")

# ---- clic derecho sobre la banda: menú (Forma>, Canal>, Modo>, Voz>, Solo, Apagar, Reiniciar)
lo, hi = num(param("B1 Desde")), num(param("B1 Hasta")); xc = f2x(math.sqrt(lo * hi))
cc(f"rc:{pt(xc, yz)}", wait=0.9); menu_item(5, xc, yz)
check("clic derecho en B1 > Apagar banda", param("B1 Estado"), "Apagada")
cc(f"dc:{pt(*CHIP(0))}"); check("doble clic en chip 1: la enciende", param("B1 Estado"), "Encendida")
cc(f"rc:{pt(xc, yz)}", wait=0.9); menu_item(6, xc, yz)
check("clic derecho en B1 > Reiniciar banda", (num(param("B1 Desde")), num(param("B1 Hasta")), num(param("B1 Reduccion"))),
      (1000, 4000, 4))

# ---- presets (fila 0 = título deshabilitado; preset n = fila n)
cc(f"c:{pt(*PRESETS)}", wait=0.9); menu_item(7, *PRESETS)
check("menu Presets > 7 (808 / bajo)", (num(param("B1 Desde")), num(param("B1 Hasta")), param("Cargar preset")), (150, 300, "-"))
cc(f"rc:{pt(f2x(60), d2y(-8))}", wait=0.9); menu_item(1, f2x(60), d2y(-8))
check("clic derecho en vacio > preset 1 (Nube baja)", (num(param("B1 Desde")), num(param("B1 Hasta")), num(param("B1 Margen"))),
      (1000, 4000, 14))
shot(str(ROOT / "tests/out/ui_final.png"))
print("FALLAS:", fails)
sys.exit(1 if fails else 0)
