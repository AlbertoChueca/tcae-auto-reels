"""Graba la misma narración con varias voces de Gemini (español de España) para elegir la favorita.
Salida: out/voices/<Voz>.mp3. La ganadora se pone en Settings > Secrets and variables > Actions > Variables > GEMINI_VOICE."""
import os, subprocess
import numpy as np, soundfile as sf
import voice

VOICES = ["Kore", "Aoede", "Leda", "Despina", "Sulafat", "Callirrhoe", "Achernar", "Charon", "Orus", "Puck"]
TEXTS = ["¿Te sabes esta pregunta del temario de TCAE?",
         "Según la Ley 41/2002, la información al paciente se dará, por regla general, de forma verbal.",
         "La correcta es la B. Y ojo con la trampa de la opción C.",
         "Practica gratis en apruebatcae.com. Tienes el link en la bio."]
STYLES = ["enérgica y cercana", "didáctica y clara", "segura, con una sonrisa", "cálida y motivadora"]
os.makedirs("out/voices", exist_ok=True)
for v in VOICES:
    voice.GEMINI_VOICE = v
    voice.reset()
    try:
        clips = voice.say_many(TEXTS, styles=STYLES)
        if voice.ENGINE_USED != "gemini":
            raise RuntimeError("Gemini TTS no disponible")
        a = np.concatenate([np.concatenate([c, np.zeros(int(voice.SR * .3), np.float32)]) for c in clips])
        sf.write("out/voices/tmp.wav", a, voice.SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "out/voices/tmp.wav", "-b:a", "128k", f"out/voices/{v}.mp3"], check=True)
        print("ok", v, flush=True)
    except Exception as e:
        print("FALLÓ", v, e, flush=True)
if os.path.exists("out/voices/tmp.wav"): os.remove("out/voices/tmp.wav")
