# PsycoSupport Cryptanalysis & Automation Suite
**CS Information Security Lab — FAST-NUCES (Fall 2026)**
**Author / Analyst:** Student Cryptanalyst

---

## 📁 Directory Structure & Overview

This directory contains the complete set of reproducible Python scripts for environment deployment, loopback network traffic capture, Al-Kindi frequency cryptanalysis, key recovery, mathematical proofs, and automated decryption.

```
scripts/
├── capture_traffic.py     # Captures 10 loopback TCP sessions and generates ciphertexts.csv & PCAP
├── freq_analysis.py       # Computes letter counts, %, Index of Coincidence, and generates charts
├── key_recovery.py        # Al-Kindi congruence equation solver & Chi-squared key search
├── decrypt.py             # Decrypts all captured sessions with full modular arithmetic steps
├── general_decryptor.py   # Universal autonomous key recovery & decryption engine (Bonus task)
└── README.md              # This documentation and run guide
```

---

## 🚀 How to Run the Scripts

### Prerequisites
Make sure Python 3.12+ is installed and the virtual environment is activated:
```powershell
# In the project root:
.\venv\Scripts\Activate.ps1
```

### 1. Traffic Capture (`capture_traffic.py`)
Executes 10 synthetic sessions across moods 1–10 against `127.0.0.1:5000`, generates `evidence/capture.pcap`, stream transcripts `evidence/stream_*.txt`, and saves `ciphertexts.csv`:
```powershell
python scripts\capture_traffic.py
```

### 2. Frequency Analysis & Statistics (`freq_analysis.py`)
Performs Al-Kindi frequency analysis on every ciphertext, computes the Index of Coincidence (IC), generates markdown summary tables in `evidence/tables/`, and creates high-resolution comparison plots in `evidence/plots/`:
```powershell
python scripts\freq_analysis.py
```

### 3. Key Recovery & Cryptanalysis (`key_recovery.py`)
Performs blind key derivation using linear congruence equations ($c \equiv a \cdot p + b \pmod{26}$), solves for multiplicative inverses using the Extended Euclidean Algorithm, and evaluates Chi-Squared statistics:
```powershell
python scripts\key_recovery.py
```

### 4. Full Dataset Decryption (`decrypt.py`)
Decrypts all 20 captured ciphertexts (C1–C10 and S1–S10), outputs sample character-level modular arithmetic proofs, de-armors hex-nibble streams, and logs to `evidence/tables/decrypted_dataset.csv`:
```powershell
python scripts\decrypt.py
```

### 5. Universal Autonomous Decryptor (`general_decryptor.py` — Bonus)
The universal cryptanalysis engine that accepts any ciphertext and automatically determines direction, mood, recovered keys $(a, b)$, and outputs plaintext:
```powershell
# Run self-test across all captured sessions:
python scripts\general_decryptor.py --test-all

# Decrypt a custom ciphertext blindly:
python scripts\general_decryptor.py --ciphertext "PIIFKTW FAE ITIVWS GTB HIVCKCJITJ CJVICC..."
```
