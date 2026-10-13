import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

def get_system_prompt() -> str:
    return """
    Kamu adalah AI Content Strategist spesialis video pendek (YouTube Shorts / TikTok / Reels).
    Tugasmu adalah membuat skrip video berdasarkan topik yang diberikan.

    PRINSIP UTAMA:
    - JANGAN MEMBATASI ATAU MENG-ADJUST DURASI KAKU. Biarkan narasi mengalir secara alami sesuai kebutuhan topik.
    - Wajib memiliki HOOK kuat di 0-3 detik pertama (memancing rasa penasaran / memicu open loop).
    - Gunakan gaya bahasa santai, kasual, dan enak didengar seperti kreator asli.
    - Sisipkan penanda meme / sound effect (sfx) di momen-momen lucu atau krusial.

    Format respon HANYA berupa JSON valid tanpa markdown formatting (tanpa ```json ```):
    {
      "topic": "topik video",
      "hook": "kalimat pembuka yang langsung menarik perhatian",
      "narration_full": "seluruh teks narasi dari awal sampai akhir untuk dibaca oleh voiceover",
      "scenes": [
        {
          "scene_id": 1,
          "narration_chunk": "potongan teks narasi untuk adegan ini",
          "visual_description": "deskripsi visual / motion graphic animasi yang ditampilkan",
          "sfx_or_meme": "nama efek suara atau meme GIF"
        }
      ],
      "cta": "kalimat penutup / call to action"
    }
    """

def print_diagnostics():
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()

    print("\n=================== DIAGNOSTIK API KEYS ===================")
    print(f"GEMINI_API_KEY : {'✅ TERISI (' + str(len(gemini_key)) + ' karakter)' if gemini_key else '❌ KOSONG / UNSET'}")
    print(f"GROQ_API_KEY   : {'✅ TERISI (' + str(len(groq_key)) + ' karakter)' if groq_key else '❌ KOSONG / UNSET'}")
    print(f"GITHUB_TOKEN   : {'✅ TERISI (' + str(len(gh_token)) + ' karakter)' if gh_token else '❌ KOSONG / UNSET'}")
    print("===========================================================\n")

# ----------------------------------------------------
# 1. GEMINI API (SDK RESMI)
# ----------------------------------------------------
def call_gemini(prompt: str, api_key: str) -> Optional[str]:
    print("[RUN] Memanggil Gemini API (via google-generativeai)...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Daftar model stabil Gemini
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-exp']
        
        for model_name in models_to_try:
            try:
                print(f" -> Mencoba model: {model_name}")
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=get_system_prompt(),
                    generation_config={"response_mime_type": "application/json"}
                )
                response = model.generate_content(f"Buatkan skrip Shorts tentang: {prompt}")
                if response.text:
                    print(f"[SUCCESS] Gemini ({model_name}) Berhasil!")
                    return response.text
            except Exception as inner_e:
                print(f" [!] Model {model_name} gagal: {inner_e}")

    except Exception as e:
        print(f"[ERROR] Gemini SDK Error: {e}")
    return None

# ----------------------------------------------------
# 2. GROQ API (SDK OPENAI)
# ----------------------------------------------------
def call_groq(prompt: str, api_key: str) -> Optional[str]:
    print("[RUN] Memanggil Groq API...")
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        
        # Model Groq aktif 2026
        models_to_try = [
            "llama-3.1-80b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768"
        ]

        for model_name in models_to_try:
            try:
                print(f" -> Mencoba model Groq: {model_name}")
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": get_system_prompt()},
                        {"role": "user", "content": f"Buatkan skrip Shorts tentang: {prompt}"}
                    ],
                    model=model_name,
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                print(f"[SUCCESS] Groq ({model_name}) Berhasil!")
                return response.choices[0].message.content
            except Exception as inner_e:
                print(f" [!] Model Groq {model_name} gagal: {inner_e}")

    except Exception as e:
        print(f"[ERROR] Groq Error: {e}")
    return None

# ----------------------------------------------------
# MAIN ROUTER
# ----------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--output", type=str, default="script_output.json")
    args = parser.parse_args()

    print_diagnostics()

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    raw_res = None

    # Priority 1: Gemini
    if gemini_key:
        raw_res = call_gemini(args.topic, gemini_key)

    # Priority 2: Groq (Jalan kalau Gemini gagal / key kosong)
    if not raw_res and groq_key:
        raw_res = call_groq(args.topic, groq_key)

    if not raw_res:
        print("\n[CRITICAL ERROR] Semua Provider AI Gagal!")
        print("PERIKSA: Apakah GEMINI_API_KEY atau GROQ_API_KEY sudah dimasukkan ke GitHub Settings > Secrets > Actions?")
        sys.exit(1)

    # Cleaning & Saving
    cleaned = raw_res.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(cleaned)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n[FINISH] Skrip berhasil dibuat & disimpan di '{args.output}'")
    except Exception as e:
        print(f"[ERROR] JSON Decode Error: {e}\nRaw Content:\n{raw_res}")
        sys.exit(1)

if __name__ == "__main__":
    main()
