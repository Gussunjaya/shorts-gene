import os
import sys
import json
import argparse
import urllib.request
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

# ----------------------------------------------------
# 1. GITHUB MODELS API
# ----------------------------------------------------
def call_github_models(prompt: str, token: str) -> Optional[str]:
    print("[INFO] Mencoba Provider 1: GitHub Models API...")
    models_to_try = ["gpt-4o-mini", "gpt-4o"]
    
    for model_name in models_to_try:
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=token,
                timeout=15.0
            )
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}
                ],
                model=model_name,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[WARNING] GitHub Models ({model_name}) Gagal: {e}")
    return None

# ----------------------------------------------------
# 2. GOOGLE GEMINI API (HTTP REST Native - Tanpa Kendala SDK)
# ----------------------------------------------------
def call_gemini(prompt: str, api_key: str) -> Optional[str]:
    print("[INFO] Mencoba Provider 2: Google Gemini API...")
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash"]
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": get_system_prompt()}]
            },
            "contents": [{
                "parts": [{"text": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                text_content = res_body['candidates'][0]['content']['parts'][0]['text']
                return text_content
        except Exception as e:
            print(f"[WARNING] Gemini API ({model_name}) Gagal: {e}")
            
    return None

# ----------------------------------------------------
# 3. GROQ API
# ----------------------------------------------------
def call_groq(prompt: str, api_key: str) -> Optional[str]:
    print("[INFO] Mencoba Provider 3: Groq API...")
    # Daftar model Groq aktif
    models_to_try = ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama-3.1-80b-instant", "llama3-8b-8192"]
    
    for model_name in models_to_try:
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=api_key,
                timeout=15.0
            )
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}
                ],
                model=model_name,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[WARNING] Groq API ({model_name}) Gagal: {e}")
            
    return None

# ----------------------------------------------------
# MAIN ROUTER WITH FAILOVER
# ----------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--output", type=str, default="script_output.json")
    args = parser.parse_args()

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    raw_res = None
    
    # 1. Coba GitHub Models
    if github_token:
        raw_res = call_github_models(args.topic, github_token)
        
    # 2. Coba Gemini jika GitHub Models gagal
    if not raw_res and gemini_key:
        raw_res = call_gemini(args.topic, gemini_key)
        
    # 3. Coba Groq jika Gemini gagal
    if not raw_res and groq_key:
        raw_res = call_groq(args.topic, groq_key)

    if not raw_res:
        print("[ERROR] Semua Provider AI Gagal!")
        sys.exit(1)

    # Clean JSON
    cleaned = raw_res.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        data = json.loads(cleaned)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] Skrip tersimpan di {args.output}")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Gagal memparsing respon AI ke JSON: {e}")
        print(f"Respon mentah: {raw_res}")
        sys.exit(1)

if __name__ == "__main__":
    main()
