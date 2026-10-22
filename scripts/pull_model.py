"""
Model Downloader for PsycoSupport Ollama Backend
CS InfoSec Lab - FAST-NUCES
"""

import sys
import json
import urllib.request

MODEL_NAME = "llama3.2:1b"
URL = "http://127.0.0.1:11434/api/pull"

print(f"[*] Sending pull request for model '{MODEL_NAME}' to http://127.0.0.1:11434...")

req = urllib.request.Request(
    URL,
    data=json.dumps({"name": MODEL_NAME, "stream": True}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        last_pct = -1
        last_status = ""
        for line in resp:
            if not line:
                continue
            data = json.loads(line.decode("utf-8"))
            status = data.get("status", "")
            total = data.get("total", 0)
            completed = data.get("completed", 0)
            
            if total > 0:
                pct = int(completed / total * 100)
                if pct != last_pct and pct % 5 == 0:
                    print(f"[{status}] {pct}% ({completed // (1024*1024)} MB / {total // (1024*1024)} MB)")
                    last_pct = pct
            else:
                if status and status != last_status:
                    print(f"[{status}]")
                    last_status = status
                    
    print(f"\n[+] Successfully pulled model '{MODEL_NAME}'!")
except Exception as e:
    print(f"[!] Error pulling model: {e}")
    sys.exit(1)
