"""Graba el video de respaldo (60 a 90 s) del software real, narrado con mi voz clonada.

Pasos:
  1. Narración: video/narracion.json -> scripts/generar_voz.py --entrada video/narracion.json --salida video/audio
     (una pista por escena, con mi voz clonada; ver README).
  2. Este script abre la app con Playwright, graba la pantalla y hace los clics de cada escena,
     esperando lo que dura su narración.
  3. ffmpeg une la grabación con las pistas de voz, cada una en el segundo en que empieza su escena.

Uso:
  python scripts/grabar_video.py --url http://localhost:8601
  python scripts/grabar_video.py --url https://chacra-clara.streamlit.app
Salida: video/demo_respaldo.mp4 (1280 x 720, H.264 + AAC)
"""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
AUDIO = RAIZ / "video" / "audio"
PAUSA = 0.8   # segundos de aire después de cada frase

AVISO = """
const d = document.createElement('div');
d.textContent = 'Chacra Clara · demo real · voz de Amanda generada con IA';
d.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:99999;background:rgba(43,29,20,.88);color:#FBF7F0;' +
  'font:600 15px Public Sans,sans-serif;padding:6px 12px;border-radius:8px;pointer-events:none';
document.body.appendChild(d);
"""


def duraciones():
    registro = json.loads((AUDIO / "generadas.json").read_text(encoding="utf-8"))
    return {k: v["segundos"] + PAUSA for k, v in registro.items()}


def esperar_app(pagina, ms=1500):
    pagina.wait_for_timeout(ms)
    pagina.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=90_000)


def mapa(pagina):
    marco = next(f for f in pagina.frames if f != pagina.main_frame and "leaflet" in f.content())
    return marco, marco.locator(".leaflet-container").first


def grabar(url, salida_cruda):
    dur = duraciones()
    inicios = {}
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        contexto = navegador.new_context(viewport={"width": 1280, "height": 720}, locale="es-PE",
                                         record_video_dir=str(salida_cruda), record_video_size={"width": 1280, "height": 720})
        pagina = contexto.new_page()
        pagina.goto(url, wait_until="networkidle", timeout=120_000)
        esperar_app(pagina, 4000)
        pagina.evaluate(AVISO)
        cero = time.time()

        def escena(clave):
            inicios[clave] = time.time() - cero
            return time.time()

        def completar(clave, desde):
            falta = dur[clave] - (time.time() - desde)
            if falta > 0:
                pagina.wait_for_timeout(int(falta * 1000))

        # 1. Portada con el one-liner
        t = escena("escena_1")
        pagina.mouse.wheel(0, 250)
        completar("escena_1", t)

        # 2. Dibujar una parcela
        t = escena("escena_2")
        pagina.get_by_role("button", name="Ingresar mis parcelas").click()
        esperar_app(pagina, 3500)
        pagina.evaluate(AVISO)
        pagina.mouse.wheel(0, 260)
        pagina.wait_for_timeout(800)
        marco, contenedor = mapa(pagina)
        marco.click(".leaflet-draw-draw-polygon")
        caja = contenedor.bounding_box()
        cx, cy = caja["width"] / 2, caja["height"] / 2
        puntos = [(cx - 40, cy - 30), (cx + 40, cy - 35), (cx + 45, cy + 30), (cx - 35, cy + 35), (cx - 40, cy - 30)]
        for x, y in puntos:
            contenedor.click(position={"x": x, "y": y})
            pagina.wait_for_timeout(450)
        pagina.wait_for_timeout(1500)
        completar("escena_2", t)

        # 3. Resultado y evidencia
        t = escena("escena_3")
        pagina.get_by_role("button", name="Analizar esta parcela").click()
        esperar_app(pagina, 3000)
        pagina.evaluate(AVISO)
        pagina.get_by_text("Parcela PR-NUEVO-A", exact=True).scroll_into_view_if_needed()
        pagina.wait_for_timeout(2500)
        pagina.get_by_text("Evidencia por fuente").scroll_into_view_if_needed()
        completar("escena_3", t)

        # 4. Antes y después, nota de voz
        t = escena("escena_4")
        pagina.get_by_text("Imágenes Sentinel-2: antes y después").scroll_into_view_if_needed()
        pagina.wait_for_timeout(int(dur["escena_4"] * 450))
        pagina.get_by_text("Nota de voz para el productor").scroll_into_view_if_needed()
        completar("escena_4", t)

        # 5. Tablero de la cooperativa de demo
        t = escena("escena_5")
        pagina.get_by_role("link", name="Inicio").first.click()
        esperar_app(pagina, 2000)
        pagina.get_by_role("button", name="Demo Puno (Sandia y Carabaya)").click()
        esperar_app(pagina, 3000)
        pagina.get_by_role("link", name="3. Tablero y visitas").first.click()
        esperar_app(pagina, 2500)
        pagina.evaluate(AVISO)
        pagina.wait_for_timeout(2500)
        pagina.get_by_text("Visitas de campo, en orden").scroll_into_view_if_needed()
        completar("escena_5", t)

        # 6. Sus datos y descargas
        t = escena("escena_6")
        pagina.get_by_role("link", name="Sus datos").first.click()
        esperar_app(pagina, 2500)
        pagina.evaluate(AVISO)
        completar("escena_6", t)
        pagina.wait_for_timeout(1200)

        video = pagina.video.path()
        contexto.close()
        navegador.close()
    # El video empieza antes de 'cero' (carga de la app): ese tramo se recorta
    return Path(video), inicios, time.time() - cero


def unir(video, inicios, salida):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = subprocess.run([ffmpeg, "-i", str(video)], capture_output=True, text=True).stderr
    duracion = [linea for linea in total.splitlines() if "Duration" in linea][0].split("Duration: ")[1].split(",")[0]
    h, m, s = duracion.split(":")
    largo = int(h) * 3600 + int(m) * 60 + float(s)
    fin_escenas = max(inicios.values()) + duraciones()["escena_6"] + 1.2
    recorte = max(0.0, largo - fin_escenas)   # segundos de carga inicial que se cortan
    entradas, filtros = ["-ss", f"{recorte:.2f}", "-i", str(video)], []
    for n, (clave, inicio) in enumerate(sorted(inicios.items()), start=1):
        entradas += ["-i", str(AUDIO / f"{clave}.mp3")]
        filtros.append(f"[{n}:a]adelay={int(inicio * 1000)}|{int(inicio * 1000)}[a{n}]")
    mezcla = "".join(f"[a{n}]" for n in range(1, len(inicios) + 1))
    filtros.append(f"{mezcla}amix=inputs={len(inicios)}:normalize=0,loudnorm=I=-16:TP=-1.5[voz]")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", *entradas, "-filter_complex", ";".join(filtros),
                    "-map", "0:v", "-map", "[voz]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
                    "-preset", "medium", "-c:a", "aac", "-b:a", "96k", "-shortest", str(salida)], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8601")
    args = p.parse_args()
    cruda = RAIZ / "video" / "crudo"
    shutil.rmtree(cruda, ignore_errors=True)
    video, inicios, _ = grabar(args.url, cruda)
    salida = RAIZ / "video" / "demo_respaldo.mp4"
    unir(video, inicios, salida)
    shutil.rmtree(cruda, ignore_errors=True)
    print(f"Listo: {salida.relative_to(RAIZ)}  escenas: { {k: round(v, 1) for k, v in inicios.items()} }")


if __name__ == "__main__":
    main()
