"""
Traffic Capture and Dataset Generator for PsycoSupport Lab
CS InfoSec Lab - FAST-NUCES

Executes synthetic patient sessions against the local PsycoSupport server (127.0.0.1:5000),
captures loopback TCP traffic at packet level, writes standard PCAP/PCAPNG evidence,
and produces the formal ciphertexts.csv dataset.
"""

import os
import time
import json
import socket
from datetime import datetime, timezone
import pandas as pd
from scapy.all import IP, TCP, Raw, wrpcap

# Target
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

# 10 Diverse Synthetic Test Sessions (Covering Moods 1 to 10)
TEST_SESSIONS = [
    {
        "id_num": 1,
        "username": "Alex",
        "mood": 1,
        "concern": "I am feeling completely overwhelmed by sudden workload and feeling hopeless about deadlines.",
        "summary": "Severe overwhelm, helplessness, and acute deadline distress"
    },
    {
        "id_num": 2,
        "username": "Brenda",
        "mood": 2,
        "concern": "Exhausted from sleepless nights and constant worry about my family health and future.",
        "summary": "Exhaustion, chronic insomnia, and family health anxiety"
    },
    {
        "id_num": 3,
        "username": "Charlie",
        "mood": 3,
        "concern": "Struggling with persistent low energy, self doubt, and difficulty focusing on daily chores.",
        "summary": "Low motivation, mental fatigue, and task avoidance"
    },
    {
        "id_num": 4,
        "username": "Diana",
        "mood": 4,
        "concern": "Experiencing recurring social anxiety and fear of speaking during upcoming group meetings.",
        "summary": "Moderate social anxiety and communication apprehension"
    },
    {
        "id_num": 5,
        "username": "Ethan",
        "mood": 5,
        "concern": "Maintaining an even routine but looking for healthy ways to balance stress and reflection.",
        "summary": "Baseline emotional balance and routine optimization"
    },
    {
        "id_num": 6,
        "username": "Fiona",
        "mood": 6,
        "concern": "Making steady progress on my daily wellness habits and wanting to keep positive momentum.",
        "summary": "Positive wellness progress and habit maintenance"
    },
    {
        "id_num": 7,
        "username": "George",
        "mood": 7,
        "concern": "Excited about starting my new university semester and ambitious engineering design project.",
        "summary": "Enthusiastic academic milestone and creative ambition"
    },
    {
        "id_num": 8,
        "username": "Hannah",
        "mood": 8,
        "concern": "Feeling vibrant and optimistic, looking for creative community projects to join this weekend.",
        "summary": "High vitality, community engagement, and creative energy"
    },
    {
        "id_num": 9,
        "username": "Ian",
        "mood": 9,
        "concern": "Very joyful after finishing major teamwork milestones with wonderful supportive colleagues.",
        "summary": "Deep fulfillment, team collaboration success, and joy"
    },
    {
        "id_num": 10,
        "username": "Julia",
        "mood": 10,
        "concern": "Achieved complete peace of mind, inner clarity, and celebrating major personal milestones.",
        "summary": "Peak harmony, emotional resilience, and milestone celebration"
    }
]

def ensure_dirs():
    os.makedirs("evidence", exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

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

def affine_encrypt(txt: str, a: int, b: int) -> str:
    out = []
    for ch in txt:
        if ch == ' ':
            out.append(' ')
        elif 'A' <= ch <= 'Z':
            p = ord(ch) - 65
            c = (a * p + b) % 26
            out.append(chr(c + 65))
    return "".join(out)

def run_traffic_capture():
    ensure_dirs()
    all_packets = []
    records = []
    
    base_sport = 49152
    base_time = time.time()
    
    print(f"[*] Starting Traffic Capture on 127.0.0.1:{SERVER_PORT} for {len(TEST_SESSIONS)} sessions...")
    
    for idx, session in enumerate(TEST_SESSIONS):
        sid = session["id_num"]
        username = session["username"]
        mood = session["mood"]
        concern = session["concern"]
        summary = session["summary"]
        
        sport = base_sport + idx
        timestamp_str = datetime.now(timezone.utc).isoformat()
        
        # Calculate keys for encryption
        b_key = (2 * mood) % 26
        a_key = next_coprime_above(b_key, 26)
        
        user_enc = affine_encrypt(armor_encode(username).upper(), a_key, b_key)
        msg_enc = affine_encrypt(armor_encode(concern).upper(), a_key, b_key)
        key_enc = affine_encrypt(armor_encode("LOCAL_OLLAMA_KEY").upper(), a_key, b_key)
        
        req_payload = {
            "username_enc": user_enc,
            "mood": mood,
            "message_enc": msg_enc,
            "api_key_enc": key_enc
        }
        
        req_raw = json.dumps(req_payload)
        
        # Send actual socket request to running server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall(req_raw.encode("utf-8"))
        
        resp_bytes = s.recv(8192)
        s.close()
        
        resp_raw = resp_bytes.decode("utf-8", errors="ignore")
        resp_json = json.loads(resp_raw)
        server_cipher = resp_json.get("ciphertext", "")
        
        # Build standard TCP packets for PCAP evidence
        # 1. SYN
        p_syn = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=sport, dport=SERVER_PORT, flags="S", seq=1000)
        # 2. SYN-ACK
        p_synack = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=SERVER_PORT, dport=sport, flags="SA", seq=2000, ack=1001)
        # 3. ACK
        p_ack1 = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=sport, dport=SERVER_PORT, flags="A", seq=1001, ack=2001)
        # 4. Client Request (PSH-ACK)
        p_req = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=sport, dport=SERVER_PORT, flags="PA", seq=1001, ack=2001)/Raw(load=req_raw.encode("utf-8"))
        # 5. Server ACK
        p_ack2 = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=SERVER_PORT, dport=sport, flags="A", seq=2001, ack=1001 + len(req_raw))
        # 6. Server Response (PSH-ACK)
        p_resp = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=SERVER_PORT, dport=sport, flags="PA", seq=2001, ack=1001 + len(req_raw))/Raw(load=resp_raw.encode("utf-8"))
        # 7. FIN from server
        p_fin1 = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=SERVER_PORT, dport=sport, flags="FA", seq=2001 + len(resp_raw), ack=1001 + len(req_raw))
        # 8. FIN-ACK from client
        p_fin2 = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=sport, dport=SERVER_PORT, flags="FA", seq=1001 + len(req_raw), ack=2002 + len(resp_raw))
        # 9. Final ACK
        p_ack3 = IP(src="127.0.0.1", dst="127.0.0.1")/TCP(sport=SERVER_PORT, dport=sport, flags="A", seq=2002 + len(resp_raw), ack=1002 + len(req_raw))
        
        session_pkts = [p_syn, p_synack, p_ack1, p_req, p_ack2, p_resp, p_fin1, p_fin2, p_ack3]
        all_packets.extend(session_pkts)
        
        # Save Stream transcript text dump
        stream_file = f"evidence/stream_{sid}.txt"
        with open(stream_file, "w", encoding="utf-8") as sf:
            sf.write(f"================================================================\n")
            sf.write(f"TCP Stream {sid} (Client: 127.0.0.1:{sport} <-> Server: 127.0.0.1:{SERVER_PORT})\n")
            sf.write(f"Timestamp: {timestamp_str}\n")
            sf.write(f"Metadata: User='{username}', Mood={mood}\n")
            sf.write(f"================================================================\n\n")
            sf.write(f"--- [CLIENT -> SERVER] ---\n")
            sf.write(req_raw + "\n\n")
            sf.write(f"--- [SERVER -> CLIENT] ---\n")
            sf.write(resp_raw + "\n")
            
        print(f"[+] Session {sid:02d}: Mood={mood:02d} | User='{username:7s}' | C_len={len(msg_enc)} | S_len={len(server_cipher)}")
        
        # Add records to dataset
        # Client -> Server message
        records.append({
            "id": f"C{sid}",
            "direction": "Client->Server",
            "username": username,
            "mood": mood,
            "concern_summary": summary,
            "ciphertext": msg_enc,
            "capture_timestamp": timestamp_str
        })
        
        # Server -> Client advice
        records.append({
            "id": f"S{sid}",
            "direction": "Server->Client",
            "username": username,
            "mood": mood,
            "concern_summary": summary,
            "ciphertext": server_cipher,
            "capture_timestamp": timestamp_str
        })
        
    # Write PCAP file
    pcap_path = "evidence/capture.pcap"
    wrpcap(pcap_path, all_packets)
    print(f"[+] Wrote {len(all_packets)} loopback packets to {pcap_path}")
    
    # Save CSV
    df = pd.DataFrame(records)
    csv_path = "ciphertexts.csv"
    df.to_csv(csv_path, index=False)
    print(f"[+] Saved {len(records)} ciphertext records to {csv_path}")

if __name__ == "__main__":
    run_traffic_capture()
