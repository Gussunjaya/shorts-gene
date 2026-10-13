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
          "sfx_or_meme": "nama efek suara atau meme GIF (contoh: 'whoosh', 'vine_boom', 'confused_cat')"
        }
      ],
      "cta": "kalimat penutup / call to action"
    }
    """

def call_github_models(prompt: str, token: str) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://models.inference.ai.azure.com", api_key=token)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}
            ],
            model="gpt-4o-mini",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[WARNING] GitHub Models Gagal: {e}")
        return None

def call_gemini(prompt: str, api_key: str) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=get_system_prompt(),
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(f"Buatkan skrip Shorts lengkap untuk topik: {prompt}")
        return response.text
    except Exception as e:
        print(f"[WARNING] Gemini API Gagal: {e}")
        return None

def call_groq(prompt: str, api_key: str) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[WARNING] Groq API Gagal: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--output", type=str, default="script_output.json")
    args = parser.parse_args()

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    raw_res = None
    if github_token:
        raw_res = call_github_models(args.topic, github_token)
    if not raw_res and gemini_key:
        raw_res = call_gemini(args.topic, gemini_key)
    if not raw_res and groq_key:
        raw_res = call_groq(args.topic, groq_key)

    if not raw_res:
        print("[ERROR] Semua Provider AI Gagal!")
        sys.exit(1)

    cleaned = raw_res.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] Skrip tersimpan di {args.output}")

if __name__ == "__main__":
    main()
