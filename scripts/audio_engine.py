import asyncio
import json
import os
import sys
import edge_tts
from pydub import AudioSegment

async def generate_voice_and_subtitles(script_json_path: str, output_audio: str, output_json_sub: str):
    with open(script_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    full_text = data.get("narration_full", "")
    if not full_text:
        # Fallback jika narration_full tidak ada
        full_text = data.get("hook", "") + " " + " ".join([s["narration_chunk"] for s in data.get("scenes", [])]) + " " + data.get("cta", "")

    voice = "id-ID-ArdiNeural" # Suara pria natural bahasa Indonesia
    communicate = edge_tts.Communicate(full_text, voice, rate="+3%")

    submaker = edge_tts.SubMaker()
    with open(output_audio, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    # Simpan word timestamp untuk animasi caption di Remotion
    word_boundaries = submaker.offset_data
    formatted_words = []
    for start, duration, text in word_boundaries:
        formatted_words.append({
            "word": text,
            "start": start / 10_000_000,  # Konversi ke detik
            "end": (start + duration) / 10_000_000
        })

    with open(output_json_sub, "w", encoding="utf-8") as f:
        json.dump(formatted_words, f, ensure_ascii=False, indent=2)

    print(f"[AUDIO] Voiceover & Subtitle Timestamp berhasil dibuat!")

def mix_bgm(voice_path: str, bgm_path: str, final_audio_path: str):
    voice = AudioSegment.from_file(voice_path)
    if os.path.exists(bgm_path):
        bgm = AudioSegment.from_file(bgm_path)
        if len(bgm) < len(voice):
            bgm = bgm * (len(voice) // len(bgm) + 1)
        bgm = bgm[:len(voice)] - 22 # Volume BGM dikecilkan -22dB
        combined = voice.overlay(bgm)
        combined.export(final_audio_path, format="mp3")
    else:
        voice.export(final_audio_path, format="mp3")

if __name__ == "__main__":
    script_file = sys.argv[1] if len(sys.argv) > 1 else "script_output.json"
    asyncio.run(generate_voice_and_subtitles(script_file, "voice_raw.mp3", "subtitles.json"))
    mix_bgm("voice_raw.mp3", "assets/bgm.mp3", "final_audio.mp3")
