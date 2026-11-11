"""Genera las notas de voz de los productores con la voz clonada de Amanda (sesión 15).

Usa el mismo flujo que la sesión 15 del curso:
  1. Qwen3-TTS-12Hz-0.6B-Base clona la voz a partir de voz/voz_ref.wav y su texto exacto (voz/voz_ref.txt).
  2. faster-whisper transcribe cada audio generado y se calcula el WER contra el texto.
  3. Si el WER supera MAX_WER, se vuelve a generar (hasta 3 intentos) y se guarda el mejor.

Va en un entorno aparte porque qwen-tts fija su propia versión de transformers:
  uv venv .venv-voz
  uv pip install --python .venv-voz/Scripts/python qwen-tts faster-whisper soundfile jiwer num2words imageio-ffmpeg

Uso:
  .venv-voz/Scripts/python scripts/generar_voz.py                      # todas las notas de audios/notas.json
  .venv-voz/Scripts/python scripts/generar_voz.py --solo P-SAN-01      # una sola nota
  .venv-voz/Scripts/python scripts/generar_voz.py --entrada video/narracion.json --salida video/audio

Entrada: un JSON {id: texto}. Lo escribe la app con el botón "Preparar notas de voz" o scripts/preparar_notas.py.
Salida: <salida>/<id>.mp3 (mono, 48 kbps: unos 120 KB por cada 20 s, liviano para WhatsApp)
        y <salida>/generadas.json con el texto, la duración y el WER de cada nota.
"""
import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
import jiwer
import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MAX_WER = 0.20
MODELO_TTS = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"


def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\wáéíóúüñ\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def numeros_a_palabras(texto):
    """El modelo de voz lee mejor 'dos mil veinte' que '2020'."""
    from num2words import num2words

    def cambiar(m):
        n = m.group(0).replace(" ", "").replace(".", "").replace(",", ".")
        try:
            return num2words(float(n) if "." in n else int(n), lang="es")
        except ValueError:
            return m.group(0)
    return re.sub(r"\d[\d.,]*\d|\d", cambiar, texto)


def huella(texto):
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12]


def audio_16k(ruta):
    crudo = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(ruta), "-f", "f32le",
                            "-ac", "1", "-ar", "16000", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(crudo, dtype=np.float32)


def a_mp3(wav, mp3):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5",
                    "-ac", "1", "-ar", "24000", "-b:a", "48k", str(mp3)], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--entrada", default=str(RAIZ / "audios" / "notas.json"))
    p.add_argument("--salida", default=str(RAIZ / "audios"))
    p.add_argument("--solo", default=None, help="id de una sola nota")
    p.add_argument("--forzar", action="store_true", help="regenera aunque el texto no haya cambiado")
    args = p.parse_args()

    import torch
    from faster_whisper import WhisperModel
    from qwen_tts import Qwen3TTSModel

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    notas = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
    registro_ruta = salida / "generadas.json"
    registro = json.loads(registro_ruta.read_text(encoding="utf-8")) if registro_ruta.exists() else {}

    pendientes = {}
    for id_nota, texto in notas.items():
        if args.solo and id_nota != args.solo:
            continue
        ya = registro.get(id_nota)
        if ya and ya["huella"] == huella(texto) and (salida / f"{id_nota}.mp3").exists() and not args.forzar:
            continue
        pendientes[id_nota] = texto
    print(f"Notas por generar: {len(pendientes)}")
    if not pendientes:
        return

    ref_wav = RAIZ / "voz" / "voz_ref.wav"
    ref_texto = (RAIZ / "voz" / "voz_ref.txt").read_text(encoding="utf-8").strip()
    t0 = time.time()
    tts = Qwen3TTSModel.from_pretrained(MODELO_TTS, device_map="cpu", dtype=torch.float32)
    prompt = tts.create_voice_clone_prompt(ref_audio=str(ref_wav), ref_text=ref_texto)
    whisper = WhisperModel("small", device="cpu", compute_type="int8")
    print(f"Modelos listos en {time.time() - t0:.0f} s")

    for id_nota, texto in pendientes.items():
        hablado = numeros_a_palabras(texto)
        mejor = None
        for intento in range(1, 4):
            t1 = time.time()
            wavs, sr = tts.generate_voice_clone(text=hablado, language="Spanish", voice_clone_prompt=prompt,
                                                 max_new_tokens=int(12 * (len(hablado.split()) * 0.6 + 4)))
            audio = np.asarray(wavs[0], dtype=np.float32)
            wav = salida / f"{id_nota}.wav"
            sf.write(wav, audio, sr)
            segs, _ = whisper.transcribe(audio_16k(wav), language="es")
            oido = " ".join(s.text.strip() for s in segs)
            wer = jiwer.wer(normalizar(hablado), normalizar(numeros_a_palabras(oido)) or "-")
            dur = len(audio) / sr
            print(f"  {id_nota} intento {intento}: {dur:.1f} s de audio en {time.time() - t1:.0f} s, WER {wer:.0%}")
            if mejor is None or wer < mejor["wer"]:
                mejor = {"audio": audio, "sr": sr, "wer": wer, "dur": dur}
            if wer <= MAX_WER:
                break
        wav = salida / f"{id_nota}.wav"
        sf.write(wav, mejor["audio"], mejor["sr"])
        a_mp3(wav, salida / f"{id_nota}.mp3")
        wav.unlink()
        registro[id_nota] = {"texto": texto, "huella": huella(texto), "segundos": round(mejor["dur"], 1),
                             "wer": round(mejor["wer"], 3), "modelo": MODELO_TTS}
        registro_ruta.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
        if mejor["wer"] > MAX_WER:
            print(f"  ¡Atención! {id_nota} quedó con WER {mejor['wer']:.0%}: escúchala antes de usarla.")


if __name__ == "__main__":
    main()
