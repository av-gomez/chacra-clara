"""Un solo comando para regenerar el video de respaldo completo, sin que nadie grabe nada a mano.

Hace, en orden:
  1. Narración: sintetiza cada escena de video/narracion.json con la voz clonada de Amanda
     (scripts/generar_voz.py, Qwen3-TTS, sesión 15). Usa voz/voz_ref.wav, que sale de su muestra de voz.
  2. App: levanta la app en local (streamlit run app.py) si no está corriendo.
  3. Pantalla: Playwright recorre la app y graba la pantalla, escena por escena, esperando lo que dura cada
     frase de la narración (scripts/grabar_video.py).
  4. Unión: ffmpeg pone cada frase en el segundo en que empieza su escena y escribe video/demo_respaldo.mp4.
  5. Control: verifica que el video dure entre 60 y 90 segundos.

Uso (desde la raíz del repo, con el entorno de la app activo):
  python scripts/hacer_video.py --python-voz .venv-voz/Scripts/python --desde-cero

  --python-voz   Python del entorno con qwen-tts (ver README, "Generar las notas de voz").
  --desde-cero   borra la narración anterior y la vuelve a sintetizar (si no, reutiliza las frases que no cambiaron).
  --url          graba contra otra URL (por ejemplo, la pública) en vez de levantar la app en local.
"""
import argparse
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import grabar_video  # noqa: E402

PUERTO = 8601


def app_corriendo(url):
    try:
        return urllib.request.urlopen(f"{url}/_stcore/health", timeout=3).read().decode().strip() == "ok"
    except Exception:
        return False


def duracion(ruta):
    import imageio_ffmpeg
    texto = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(ruta)], capture_output=True, text=True).stderr
    h, m, s = texto.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--python-voz", required=True, help="Python del entorno con qwen-tts")
    p.add_argument("--desde-cero", action="store_true")
    p.add_argument("--url", default=None)
    args = p.parse_args()

    # 1. Narración con la voz clonada
    audio = RAIZ / "video" / "audio"
    if args.desde_cero:
        shutil.rmtree(audio, ignore_errors=True)
    print("1/4 Narración con la voz clonada…")
    subprocess.run([args.python_voz, str(RAIZ / "scripts" / "generar_voz.py"),
                    "--entrada", str(RAIZ / "video" / "narracion.json"), "--salida", str(audio)], check=True)

    # 2. App en local
    url = args.url or f"http://localhost:{PUERTO}"
    servidor = None
    if not args.url and not app_corriendo(url):
        print("2/4 Levantando la app en local…")
        servidor = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(RAIZ / "app.py"),
                                     "--server.headless", "true", "--server.port", str(PUERTO)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(120):
            if app_corriendo(url):
                break
            time.sleep(1)

    # 3 y 4. Grabación de pantalla y unión con la narración
    try:
        print("3/4 Grabando la pantalla con Playwright…")
        cruda = RAIZ / "video" / "crudo"
        shutil.rmtree(cruda, ignore_errors=True)
        video, inicios, _ = grabar_video.grabar(url, cruda)
        print("4/4 Uniendo pantalla y narración con ffmpeg…")
        salida = RAIZ / "video" / "demo_respaldo.mp4"
        grabar_video.unir(video, inicios, salida)
        shutil.rmtree(cruda, ignore_errors=True)
    finally:
        if servidor:
            servidor.terminate()

    # 5. Control de duración
    segundos = duracion(salida)
    print(f"Listo: {salida.relative_to(RAIZ)} · {segundos:.0f} s · inicio de cada escena: "
          f"{ {k: round(v, 1) for k, v in inicios.items()} }")
    if not 60 <= segundos <= 90:
        print("¡Atención! El curso pide entre 60 y 90 segundos: ajuste video/narracion.json.")


if __name__ == "__main__":
    main()
