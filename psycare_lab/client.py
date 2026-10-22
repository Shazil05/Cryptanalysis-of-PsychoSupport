"""
PsyCare Patient Client (Tkinter GUI & CLI)
CS InfoSec Lab - FAST-NUCES

Encrypts username, message, and api_key using mood-derived Affine cipher over an armored alphabet.
Sends JSON: {"username_enc", "mood", "message_enc", "api_key_enc"} to server.
Receives {"ciphertext"} and decrypts to plaintext advice.
"""

import socket
import json
import string
import tkinter as tk
from tkinter import ttk, messagebox

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
ALPHABET = string.ascii_uppercase

def armor_encode(text: str) -> str:
    b = text.encode("utf-8")
    letters = []
    for by in b:
        hi = (by >> 4) & 15
        lo = by & 15
        letters.append(chr(ord('A') + hi))
        letters.append(chr(ord('A') + lo))
    s = "".join(letters)
    return " ".join(s[i:i+64] for i in range(0, len(s), 64))

def armor_decode(armored: str) -> str:
    s = armored.replace(" ", "")
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

def next_coprime_above(b_val: int, modulo: int = 26) -> int:
    cand = b_val + 1
    while True:
        if cand % modulo != 0 and gcd(cand % modulo, modulo) == 1:
            return cand % modulo
        cand += 1

def modinv(a: int, m: int = 26) -> int:
    t, nt = 0, 1
    r, nr = m, a % m
    while nr != 0:
        q = r // nr
        t, nt = nt, t - q * nt
        r, nr = nr, r - q * nr
    if r != 1:
        raise ValueError("No inverse")
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

def send_request(host: str, port: int, payload: dict) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(10.0)
        s.connect((host, port))
        data = json.dumps(payload).encode("utf-8")
        s.sendall(data)
        
        chunks = []
        while True:
            chunk = s.recv(8192)
            if not chunk:
                break
            chunks.append(chunk)
        raw_resp = b"".join(chunks).decode("utf-8", errors="ignore")
        return json.loads(raw_resp)
    except Exception as e:
        return {"error": str(e)}
    finally:
        s.close()

def send_session(username: str, mood: int, message: str, api_key: str = "LOCAL_OLLAMA", host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """Helper function to perform an end-to-end client session and return all captured artifacts."""
    b = (2 * mood) % 26
    a = next_coprime_above(b, 26)
    
    def arm_enc(s: str) -> str:
        arm = armor_encode(s).upper()
        return affine_encrypt(arm, a, b)
    
    payload = {
        "username_enc": arm_enc(username),
        "mood": mood,
        "message_enc": arm_enc(message),
        "api_key_enc": arm_enc(api_key)
    }
    
    resp = send_request(host, port, payload)
    if "ciphertext" in resp:
        plain = affine_decrypt(resp["ciphertext"], a, b)
        resp["plaintext"] = plain
    return {
        "request_payload": payload,
        "response": resp,
        "key_a": a,
        "key_b": b
    }

class PsyCareClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PsyCare Patient Client")
        self.root.geometry("600x550")
        
        # Frame
        frame = ttk.Frame(root, padding="10")
        frame.pack(fill="both", expand=True)
        
        # Host/Port
        conn_frame = ttk.Frame(frame)
        conn_frame.pack(fill="x", pady=5)
        ttk.Label(conn_frame, text="Host:").pack(side="left")
        self.host_entry = ttk.Entry(conn_frame, width=15)
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.pack(side="left", padx=5)
        
        ttk.Label(conn_frame, text="Port:").pack(side="left")
        self.port_entry = ttk.Entry(conn_frame, width=8)
        self.port_entry.insert(0, str(DEFAULT_PORT))
        self.port_entry.pack(side="left", padx=5)
        
        # Username
        ttk.Label(frame, text="Username:").pack(anchor="w", pady=(5,0))
        self.user_entry = ttk.Entry(frame)
        self.user_entry.insert(0, "Alice")
        self.user_entry.pack(fill="x", pady=2)
        
        # Mood
        ttk.Label(frame, text="Mood (1=Very Low, 10=Excellent):").pack(anchor="w", pady=(5,0))
        self.mood_slider = ttk.Scale(frame, from_=1, to=10, orient="horizontal")
        self.mood_slider.set(5)
        self.mood_slider.pack(fill="x", pady=2)
        
        # Message
        ttk.Label(frame, text="Your Concern / Thoughts:").pack(anchor="w", pady=(5,0))
        self.msg_entry = tk.Text(frame, height=5)
        self.msg_entry.insert("1.0", "I have been feeling stressed about upcoming exam deadlines.")
        self.msg_entry.pack(fill="x", pady=2)
        
        # Send Button
        self.send_btn = ttk.Button(frame, text="Encrypt & Send to Psychologist", command=self.on_send)
        self.send_btn.pack(pady=10)
        
        # Response Output
        ttk.Label(frame, text="Therapist Advice (Decrypted Response):").pack(anchor="w", pady=(5,0))
        self.plain_out = tk.Text(frame, height=8, state="disabled", wrap="word")
        self.plain_out.pack(fill="both", expand=True, pady=2)
        
    def _set_plain(self, text: str):
        self.plain_out.config(state="normal")
        self.plain_out.delete("1.0", "end")
        self.plain_out.insert("1.0", text)
        self.plain_out.config(state="disabled")

    def on_send(self):
        host = self.host_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Invalid port")
            return
            
        username = self.user_entry.get().strip()
        mood = int(round(self.mood_slider.get()))
        message = self.msg_entry.get("1.0", "end").strip()
        
        if not username or not message:
            messagebox.showwarning("Input Error", "All fields required")
            return
            
        res = send_session(username, mood, message, host=host, port=port)
        resp = res.get("response", {})
        if "error" in resp:
            self._set_plain(f"[ERROR] {resp['error']}")
        elif "plaintext" in resp:
            self._set_plain(resp["plaintext"])
        else:
            self._set_plain("[ERROR] No response received")

if __name__ == "__main__":
    root = tk.Tk()
    app = PsyCareClientGUI(root)
    root.mainloop()
