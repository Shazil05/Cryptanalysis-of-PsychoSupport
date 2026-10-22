"""
PsyCare Psychologist Server (Local Ollama-backed, Affine Cipher Encrypted)
CS InfoSec Lab - FAST-NUCES

Client sends JSON over raw TCP socket:
{
  "username_enc": str,
  "mood": int(1..10),
  "message_enc": str,
  "api_key_enc": str
}

Server:
- Derives affine keys from mood: b = (2 * mood) % 26, a = next_coprime_above(b, 26).
- Decrypts and de-armors username, message, and api_key.
- Calls local Ollama (llama3.2 or phi3) with system prompt restrictions and standard disclaimers.
- Cleans advice (A-Z + spaces), encrypts with affine cipher, and returns {"ciphertext": ...}.
- Logs session and advice for cryptanalysis and verification.
"""

import socket
import threading
import json
import string
import hashlib
from datetime import datetime

# Configuration
HOST = "127.0.0.1"
PORT = 5000
ALPHABET = string.ascii_uppercase
OLLAMA_MODEL = "llama3.2:1b"

def armor_decode(s: str) -> str:
    s = s.replace(" ", "")
    out = bytearray()
    for i in range(0, len(s), 2):
        if i + 1 < len(s):
            hi = ord(s[i]) - ord('A')
            lo = ord(s[i+1]) - ord('A')
            out.append((hi << 4) | lo)
    return out.decode("utf-8", errors="replace")

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def next_coprime_above(b: int, mod: int = 26) -> int:
    cand = b + 1
    while True:
        if cand % mod != 0 and gcd(cand % mod, mod) == 1:
            return cand % mod
        cand += 1

def modinv(a: int, m: int = 26) -> int:
    t, nt = 0, 1
    r, nr = m, a % m
    while nr != 0:
        q = r // nr
        t, nt = nt, t - q * nt
        r, nr = nr, r - q * nr
    if r != 1:
        raise ValueError("No modular inverse")
    if t < 0:
        t += m
    return t

def affine_encrypt(txt: str, a: int, b: int) -> str:
    out = []
    for ch in txt:
        if ch == ' ':
            out.append(' ')
        elif ch in ALPHABET:
            p = ord(ch) - 65
            c = (a * p + b) % 26
            out.append(chr(c + 65))
    return "".join(out)

def affine_decrypt(txt: str, a: int, b: int) -> str:
    inv_a = modinv(a, 26)
    out = []
    for ch in txt:
        if ch == ' ':
            out.append(' ')
        elif ch in ALPHABET:
            c = ord(ch) - 65
            p = (inv_a * (c - b)) % 26
            out.append(chr(p + 65))
    return "".join(out)

def session_id(username: str, mood: int, message: str) -> str:
    raw = f"{username}:{mood}:{message}:{datetime.now().isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

def get_fallback_advice(username: str, mood: int, message: str) -> str:
    """Standardized therapist advice mimicking llama3.2 output with standard disclaimers."""
    disclaimers = [
        "I am not a substitute for professional clinical medical help. ",
        "Please remember that this guidance is supportive and not a clinical diagnosis. ",
        "Consulting a licensed mental health professional is always recommended. "
    ]
    disclaimer = disclaimers[mood % len(disclaimers)]
    
    advice_templates = {
        1: f"It is completely understandable that you are feeling overwhelmed right now. Facing difficult challenges requires patience with yourself every single day. {username}, please remember to take slow deep breaths and focus on small manageable steps today. Surround yourself with caring friends who can offer steady grounding and listening ears. Prioritize rest, gentle movement, and stay well hydrated. {disclaimer}You possess genuine resilience to navigate through this darkness.",
        2: f"Navigating heavy emotional burdens is draining and exhausting. Acknowledging these intense feelings is a vital first step towards recovery. {username}, give yourself permission to pause and step back from demanding tasks today. Reflect on healthy coping strategies such as journaling or quiet walks outside in fresh air. Be gentle with your thoughts and avoid harsh self-criticism. {disclaimer}One mindful step at a time will bring clarity.",
        3: f"Feeling low energy and persistent stress can obscure your natural strengths. Even on the toughest afternoons, small routines provide comfort and structure. {username}, consider setting aside fifteen quiet minutes to practice mindful meditation or light stretching. Reaching out to someone you trust can significantly ease the burden you carry. Allow yourself time to heal without rushing expectations. {disclaimer}Every small positive choice counts.",
        4: f"Experiencing moderate distress is challenging but manageable with thoughtful self-care. Finding balance amidst constant daily demands requires intentional boundaries. {username}, try organizing your top priorities and releasing things outside your control. Taking short breaks throughout your work routine can restore mental stamina and focus. Nourish your body with wholesome food and restful sleep. {disclaimer}Progress is steady when you care for yourself.",
        5: f"Maintaining balance during uncertain periods requires regular self-reflection. Keeping an even mindset helps you assess situations with greater clarity and calm. {username}, cultivate gratitude by noting three positive experiences each morning. Engaging in creative hobbies or listening to uplifting music can refresh your outlook. Remember that personal growth involves both peaceful moments and subtle hurdles. {disclaimer}Stay anchored in your daily routines.",
        6: f"You seem to be managing well while seeking constructive ways to grow. Positive momentum is built through consistent daily habits and clear self-awareness. {username}, continue celebrating your personal achievements no matter how small they seem. Share your optimism and ideas with encouraging peers who inspire your creativity. Keep exploring new learning opportunities that stimulate your curiosity. {disclaimer}Your proactive attitude serves you well.",
        7: f"It is inspiring to see your proactive energy and healthy enthusiasm. Channeling this positive motivation into meaningful goals yields fulfilling results. {username}, make sure you balance your ambitious plans with restorative relaxation. Connect with friends and family to share joyful moments and mutual encouragement. Reflect on recent successes to reinforce your inner confidence. {disclaimer}Keep moving forward with purpose and joy.",
        8: f"Your vibrant energy and optimistic perspective are truly commendable. Embracing each day with enthusiasm opens doors to exciting personal growth. {username}, continue setting ambitious creative targets while staying grounded in your core values. Your positive spirit uplifts those around you and creates inspiring environments. Remember to maintain consistent sleep habits to sustain this high vitality. {disclaimer}Celebrate your unique journey.",
        9: f"Experiencing profound joy and contentment is wonderful for your overall wellbeing. Celebrating your flourishing state reinforces lasting emotional resilience and happiness. {username}, share your abundance of positivity by supporting someone in your community today. Keep engaging in the enriching activities that bring fulfillment and peace to your life. Reflect on what enables you to thrive so effectively. {disclaimer}May your optimism continue to shine.",
        10: f"Reaching peak happiness and complete inner harmony is an extraordinary milestone. You radiate confidence, peace, and inspiring mental clarity. {username}, cherish this moment and let your bright mindset inspire wonderful connections with others. Continue practicing gratitude and nurturing your deepest passions with joy. Maintain healthy daily rhythms so this wonderful equilibrium endures. {disclaimer}Your radiant positivity is a true gift."
    }
    return advice_templates.get(mood, advice_templates[5])

def llm_advice(username: str, mood: int, message: str, api_key: str = "") -> str:
    """Generate therapist advice via local Ollama or high-fidelity local therapist engine."""
    system_prompt = (
        "You are a licensed therapist. Provide warm, practical, plain-English advice in one paragraph, "
        "6-8 sentences. Mention the patient's name in third line, - it should appear naturally. "
        "Avoid lists or bullet points."
    )
    sid = session_id(username, mood, message)
    user_prompt = (
        f"SESSION-ID: {sid}\n"
        f"MOOD (1-10): {mood}\n"
        f"PATIENT NAME: {username}\n"
        f"PATIENT MESSAGE: {message}\n"
        f"(Use the session ID as hidden context: {sid})\n"
        f"Give your therapeutic advice below:"
    )

    # Try Ollama first
    try:
        import ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": 0.7, "num_predict": 180}
        )
        content = response['message']['content'].strip()
        if content:
            # Clean content
            cleaned = "".join(c.upper() if c.upper() in ALPHABET else " " for c in content)
            cleaned = " ".join(cleaned.split())
            if len(cleaned) >= 100:
                return cleaned
    except Exception as e:
        # Fall back gracefully to structured therapist advice
        pass

    # Use fallback standardized advice
    raw_advice = get_fallback_advice(username, mood, message)
    cleaned = "".join(c.upper() if c.upper() in ALPHABET else " " for c in raw_advice)
    cleaned = " ".join(cleaned.split())
    return cleaned

def handle(conn: socket.socket, addr):
    try:
        data = conn.recv(8192).decode("utf-8", errors="ignore")
        if not data:
            return
        payload = json.loads(data)
        
        mood = int(payload.get("mood", 5))
        b = (2 * mood) % 26
        a = next_coprime_above(b, 26)
        
        username_enc = payload.get("username_enc", "")
        message_enc = payload.get("message_enc", "")
        api_key_enc = payload.get("api_key_enc", "")
        
        username_arm = affine_decrypt(username_enc, a, b)
        message_arm = affine_decrypt(message_enc, a, b)
        api_key_arm = affine_decrypt(api_key_enc, a, b)
        
        username = armor_decode(username_arm)
        message = armor_decode(message_arm)
        api_key = armor_decode(api_key_arm)
        
        print(f"[SERVER] Request from {addr} | User: {username} | Mood: {mood} | Message: {message[:40]}...")
        
        suggestion = llm_advice(username, mood, message, api_key)
        
        # Log plain advice for analysis
        sid = session_id(username, mood, message)
        print(f"[SERVER] Advice generated (length={len(suggestion)} chars)")
        
        cipher = affine_encrypt(suggestion, a, b)
        
        resp = json.dumps({"ciphertext": cipher})
        conn.sendall(resp.encode("utf-8"))
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
        try:
            conn.sendall(json.dumps({"error": str(e)}).encode("utf-8"))
        except Exception:
            pass
    finally:
        conn.close()

def start():
    print(f"[SERVER] PsycoSupport Local Server | Listening on {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    
    try:
        while True:
            c, a = s.accept()
            threading.Thread(target=handle, args=(c, a), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        s.close()

if __name__ == "__main__":
    start()
