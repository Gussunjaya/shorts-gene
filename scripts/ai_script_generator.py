import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

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

# ----------------------------------------------------
# DYNAMIC MODEL DISCOVERY
# ----------------------------------------------------
def fetch_active_gemini_models(api_key: str) -> List[str]:
    """Mengambil daftar model Gemini yang sedang aktif langsung dari Google API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = []
            for m in data.get('models', []):
                methods = m.get('supportedGenerationMethods', [])
                if 'generateContent' in methods:
                    name = m['name'].replace('models/', '')
                    models.append(name)
            print(f"[DISCOVERY] Gemini active models found: {models}")
            return models
    except Exception as e:
        print(f"[DISCOVERY WARNING] Gagal fetching list model Gemini: {e}")
        return []

def fetch_active_groq_models(api_key: str) -> List[str]:
    """Mengambil daftar model Groq yang sedang aktif langsung dari Groq API"""
    url = "https://api.groq.com/openai/v1/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m['id'] for m in data.get('data', [])]
            print(f"[DISCOVERY] Groq active models found: {models}")
            return models
    except Exception as e:
        print(f"[DISCOVERY WARNING] Gagal fetching list model Groq: {e}")
        return []

# ----------------------------------------------------
# 1. GOOGLE GEMINI EXECUTION
# ----------------------------------------------------
def call_gemini(prompt: str, api_key: str) -> Optional[str]:
    print("\n[RUN] Memulai eksekusi Gemini API...")
    active_models = fetch_active_gemini_models(api_key)
    
    if not active_models:
        # Fallback manual jika discovery gagal
        active_models = ["gemini-1.5-flash-002", "gemini-1.5-pro-002", "gemini-2.0-flash-exp"]

    for model_name in active_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": get_system_prompt()}]},
            "contents": [{"parts": [{"text": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        try:
            print(f" -> Mencoba Gemini model: {model_name}")
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                text_content = res_body['candidates'][0]['content']['parts'][0]['text']
                print(f"[SUCCESS] Gemini ({model_name}) BERHASIL!")
                return text_content
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            print(f"   [!] Gemini ({model_name}) HTTP {e.code}: {err_body[:80]}...")
        except Exception as e:
            print(f"   [!] Gemini ({model_name}) Error: {e}")

    return None

# ----------------------------------------------------
# 2. GROQ EXECUTION
# ----------------------------------------------------
def call_groq(prompt: str, api_key: str) -> Optional[str]:
    print("\n[RUN] Memulai eksekusi Groq API...")
    active_models = fetch_active_groq_models(api_key)
    
    if not active_models:
        active_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        for model_name in active_models:
            try:
                print(f" -> Mencoba Groq model: {model_name}")
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": get_system_prompt()},
                        {"role": "user", "content": f"Buatkan skrip Shorts lengkap untuk topik: {prompt}"}
                    ],
                    model=model_name,
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                print(f"[SUCCESS] Groq ({model_name}) BERHASIL!")
                return response.choices[0].message.content
            except Exception as e:
                print(f"   [!] Groq ({model_name}) Error: {e}")
    except Exception as e:
        print(f"   [!] Groq Client Init Error: {e}")

    return None

# ----------------------------------------------------
# MAIN ROUTER
# ----------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--output", type=str, default="script_output.json")
    args = parser.parse_args()

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    raw_res = None

    if gemini_key:
        raw_res = call_gemini(args.topic, gemini_key)

    if not raw_res and groq_key:
        raw_res = call_groq(args.topic, groq_key)

    if not raw_res:
        print("\n[CRITICAL ERROR] Gagal menghubungkan ke AI Provider!")
        sys.exit(1)

    cleaned = raw_res.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(cleaned)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n[FINISH] Skrip Shorts berhasil dibuat & disimpan di '{args.output}'")
    except Exception as e:
        print(f"[ERROR] Memparsing JSON Gagal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
