"""
PsycoSupport Lab — Full Pipeline Regeneration Script
CS InfoSec Lab - FAST-NUCES Fall 2026
"""
import os, sys, json, socket, time, string
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from scapy.all import IP, TCP, Raw, wrpcap

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
ALPHABET = string.ascii_uppercase

TEST_SESSIONS = [
    {"id_num": 1, "username": "Alex",    "mood": 1,  "concern": "I am feeling completely overwhelmed by sudden workload and feeling hopeless about deadlines.",          "summary": "Severe overwhelm, helplessness, and acute deadline distress"},
    {"id_num": 2, "username": "Brenda",  "mood": 2,  "concern": "Exhausted from sleepless nights and constant worry about my family health and future.",                 "summary": "Exhaustion, chronic insomnia, and family health anxiety"},
    {"id_num": 3, "username": "Charlie", "mood": 3,  "concern": "Struggling with persistent low energy, self doubt, and difficulty focusing on daily chores.",            "summary": "Low motivation, mental fatigue, and task avoidance"},
    {"id_num": 4, "username": "Diana",   "mood": 4,  "concern": "Experiencing recurring social anxiety and fear of speaking during upcoming group meetings.",             "summary": "Moderate social anxiety and communication apprehension"},
    {"id_num": 5, "username": "Ethan",   "mood": 5,  "concern": "Maintaining an even routine but looking for healthy ways to balance stress and reflection.",            "summary": "Baseline emotional balance and routine optimization"},
    {"id_num": 6, "username": "Fiona",   "mood": 6,  "concern": "Making steady progress on my daily wellness habits and wanting to keep positive momentum.",              "summary": "Positive wellness progress and habit maintenance"},
    {"id_num": 7, "username": "George",  "mood": 7,  "concern": "Excited about starting my new university semester and ambitious engineering design project.",            "summary": "Enthusiastic academic milestone and creative ambition"},
    {"id_num": 8, "username": "Hannah",  "mood": 8,  "concern": "Feeling vibrant and optimistic, looking for creative community projects to join this weekend.",          "summary": "High vitality, community engagement, and creative energy"},
    {"id_num": 9, "username": "Ian",     "mood": 9,  "concern": "Very joyful after finishing major teamwork milestones with wonderful supportive colleagues.",            "summary": "Deep fulfillment, team collaboration success, and joy"},
    {"id_num": 10,"username": "Julia",   "mood": 10, "concern": "Achieved complete peace of mind, inner clarity, and celebrating major personal milestones.",             "summary": "Peak harmony, emotional resilience, and milestone celebration"},
]

def gcd(a, b):
    while b: a, b = b, a % b
    return a

def next_coprime_above(b_val, modulo=26):
    cand = b_val + 1
    while True:
        if cand % modulo != 0 and gcd(cand % modulo, modulo) == 1:
            return cand % modulo
        cand += 1

def modinv(a, m=26):
    t, nt = 0, 1; r, nr = m, a % m
    while nr != 0:
        q = r // nr; t, nt = nt, t - q * nt; r, nr = nr, r - q * nr
    if r != 1: raise ValueError("No inverse")
    return t % m

def armor_encode(text):
    b = text.encode("utf-8"); letters = []
    for by in b:
        letters.append(chr(ord('A') + ((by >> 4) & 15)))
        letters.append(chr(ord('A') + (by & 15)))
    s = "".join(letters)
    return " ".join(s[i:i+64] for i in range(0, len(s), 64))

def affine_encrypt(txt, a, b):
    out = []
    for ch in txt:
        if ch == ' ': out.append(' ')
        elif 'A' <= ch <= 'Z': out.append(chr((a*(ord(ch)-65)+b)%26+65))
    return "".join(out)

def affine_decrypt(txt, a, b):
    inv_a = modinv(a, 26); out = []
    for ch in txt:
        if ch == ' ': out.append(' ')
        elif 'A' <= ch <= 'Z': out.append(chr((inv_a*(ord(ch)-65-b))%26+65))
    return "".join(out)

def run_session(session):
    mood = session["mood"]; username = session["username"]; concern = session["concern"]
    b_key = (2 * mood) % 26; a_key = next_coprime_above(b_key, 26)
    def arm_enc(s): return affine_encrypt(armor_encode(s).upper(), a_key, b_key)
    payload = {"username_enc": arm_enc(username), "mood": mood,
               "message_enc": arm_enc(concern), "api_key_enc": arm_enc("LOCAL_OLLAMA_KEY")}
    req_raw = json.dumps(payload)
    sock = socket.socket(); sock.settimeout(90); sock.connect((SERVER_HOST, SERVER_PORT))
    sock.sendall(req_raw.encode("utf-8"))
    chunks = []
    while True:
        chunk = sock.recv(8192)
        if not chunk: break
        chunks.append(chunk)
    sock.close()
    resp_raw = b"".join(chunks).decode("utf-8", errors="ignore")
    resp_json = json.loads(resp_raw)
    server_ct = resp_json.get("ciphertext", "")
    server_pt = affine_decrypt(server_ct, a_key, b_key) if server_ct else ""
    return {"req_raw": req_raw, "resp_raw": resp_raw, "client_ct": payload["message_enc"],
            "server_ct": server_ct, "server_pt": server_pt, "a_key": a_key, "b_key": b_key}

os.makedirs("evidence/plots", exist_ok=True); os.makedirs("evidence/tables", exist_ok=True)
all_packets = []; records = []; session_log = []
base_sport = 49200; print("\n" + "="*70 + "\n  PsycoSupport Lab — Regeneration with llama3.2:1b\n" + "="*70)

for idx, session in enumerate(TEST_SESSIONS):
    sid=session["id_num"]; username=session["username"]; mood=session["mood"]
    summary=session["summary"]; concern=session["concern"]
    print(f"[{idx+1:02d}/10] Mood={mood:02d} | User='{username}' ...", end=" ", flush=True)
    ts = datetime.now(timezone.utc).isoformat()
    result = run_session(session); sport = base_sport + idx
    print(f"C={len(result['client_ct'])} S={len(result['server_ct'])} a={result['a_key']} b={result['b_key']}")
    print(f"         Advice: {result['server_pt'][:90]}...")
    req_raw = result["req_raw"]; resp_raw = result["resp_raw"]
    pkts = [
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=sport,dport=SERVER_PORT,flags="S",seq=1000),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=SERVER_PORT,dport=sport,flags="SA",seq=2000,ack=1001),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=sport,dport=SERVER_PORT,flags="A",seq=1001,ack=2001),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=sport,dport=SERVER_PORT,flags="PA",seq=1001,ack=2001)/Raw(load=req_raw.encode()),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=SERVER_PORT,dport=sport,flags="A",seq=2001,ack=1001+len(req_raw)),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=SERVER_PORT,dport=sport,flags="PA",seq=2001,ack=1001+len(req_raw))/Raw(load=resp_raw.encode()),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=SERVER_PORT,dport=sport,flags="FA",seq=2001+len(resp_raw),ack=1001+len(req_raw)),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=sport,dport=SERVER_PORT,flags="FA",seq=1001+len(req_raw),ack=2002+len(resp_raw)),
        IP(src="127.0.0.1",dst="127.0.0.1")/TCP(sport=SERVER_PORT,dport=sport,flags="A",seq=2002+len(resp_raw),ack=1002+len(req_raw)),
    ]
    all_packets.extend(pkts)
    with open(f"evidence/stream_{sid}.txt","w",encoding="utf-8") as sf:
        sf.write(f"{'='*64}\nTCP Stream {sid} | Client:127.0.0.1:{sport} <-> Server:127.0.0.1:{SERVER_PORT}\n")
        sf.write(f"Timestamp: {ts}\nUser: {username}, Mood: {mood} | Keys: a={result['a_key']}, b={result['b_key']}\n")
        sf.write(f"{'='*64}\n\n--- [CLIENT -> SERVER] ---\n{req_raw}\n\n--- [SERVER -> CLIENT] ---\n{resp_raw}\n\n--- [DECRYPTED] ---\n{result['server_pt']}\n")
    records.append({"id":f"C{sid}","direction":"Client->Server","username":username,"mood":mood,"concern_summary":summary,"ciphertext":result["client_ct"],"capture_timestamp":ts})
    records.append({"id":f"S{sid}","direction":"Server->Client","username":username,"mood":mood,"concern_summary":summary,"ciphertext":result["server_ct"],"capture_timestamp":ts})
    session_log.append({"id_num":sid,"username":username,"mood":mood,"summary":summary,"concern":concern,
        "a_key":result["a_key"],"b_key":result["b_key"],"client_ct":result["client_ct"],"server_ct":result["server_ct"],"server_pt":result["server_pt"],"timestamp":ts})
    time.sleep(0.1)

wrpcap("evidence/capture.pcap", all_packets); print(f"\n[+] PCAP: {len(all_packets)} packets -> evidence/capture.pcap")
pd.DataFrame(records).to_csv("ciphertexts.csv", index=False); print(f"[+] CSV: {len(records)} records -> ciphertexts.csv")
with open("evidence/session_log.json","w",encoding="utf-8") as f: json.dump(session_log, f, indent=2)
print("[+] JSON: evidence/session_log.json\n[+] Done — proceed to: python scripts/freq_analysis.py")
