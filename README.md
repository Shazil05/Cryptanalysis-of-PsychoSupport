# Cryptanalysis of PsychoSupport
### CS Information Security — Assignment #1 / #2 | FAST-NUCES | Fall 2026
**Author / Security Analyst:** Shazil05  
**Target System:** PsychoSupport Tele-Mental Health Application (v1.0-Alpha)  
**Deliverables:** Academic Research Report (`report.pdf`), Cryptanalytic Toolsuite (`scripts/`), Captured Evidence (`evidence/`), Dataset (`ciphertexts.csv`)

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#-executive-summary--problem-statement)
2. [Target System Architecture](#-target-system-architecture)
3. [Cryptographic Design & Flaws](#-cryptographic-design--flaws)
4. [Vulnerability Catalog](#-vulnerability-catalog)
5. [Mathematical Formulations](#-mathematical-formulations)
6. [Attack Methodology & Toolsuite](#-attack-methodology--toolsuite)
7. [Experimental Results & Verification](#-experimental-results--verification)
8. [Repository Branches & Structure](#-repository-branches--structure)
9. [How to Run & Reproduce (Quick Start)](#-how-to-run--reproduce-quick-start)
10. [Comprehensive Ethical Statement & Responsible Disclosure](#-comprehensive-ethical-statement--responsible-disclosure)
11. [Remediation & Defense Roadmap](#-remediation--defense-roadmap)
12. [References](#-references)

---

## 🔍 Executive Summary & Problem Statement

**PsychoSupport** is a prototype tele-psychology and mental-health counseling platform designed to allow patients to record their current mood state and engage in confidential therapeutic dialogues with an AI mental-health counselor powered by a local Large Language Model (`llama3.2:1b`).

The system claimed to secure patient communications and protect doctor-patient confidentiality over the network using custom "proprietary military-grade encryption." In reality, reverse engineering and traffic analysis revealed that the application relies on an insecure implementation of a classical **Affine substitution cipher** operating over modular arithmetic $(\mathbb{Z}_{26})$, coupled with deterministic key derivation directly tied to the patient's plaintext mood input.

This repository presents the complete **tester-cryptanalyst work-product**:
- Non-invasive loopback packet capture (`evidence/capture.pcap`)
- Mathematical and statistical cryptanalysis (Index of Coincidence, Al-Kindi frequency analysis)
- Blind key recovery using Chi-squared ($\chi^2$) goodness-of-fit scoring
- Known-plaintext crib exploitation leveraging LLM disclaimer boilerplate
- Autonomous general-purpose decryptor breaking 100% of intercepted communications
- A publication-standard, 5-page academic report (`report.pdf`)

---

## 🏗 Target System Architecture

The application operates over a client-server model communicating via a TCP loopback socket on port `5000`:

```
+-------------------------------------------------------------------------+
|                           PATIENT CLIENT (GUI)                          |
|  - Tkinter User Interface                                               |
|  - Inputs: Username, Mood Rating (1 - 10), Message                      |
|  - Key Deriv: b = (2 * mood) % 26, a = next_coprime_above(b, 26)        |
|  - Encrypts via Affine Cipher: c = (a * p + b) mod 26                   |
|  - Armors client bytes to 16-character alphabet (A-P)                   |
+-------------------------------------------------------------------------+
                                    |
                           TCP Stream (Port 5000)
                Payload: {"mood": X, "ciphertext": "..."}
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        PSYCOSUPPORT SERVER DAEMON                       |
|  - Backend Socket Listener / Flask Service                              |
|  - Reads plaintext "mood", computes exact matching key pair (a, b)      |
|  - Inverts Affine Cipher: p = a^-1 * (c - b) mod 26                     |
|  - Dispatches prompt to Ollama AI Engine (llama3.2:1b)                  |
|  - Receives AI response, encrypts with Affine Cipher                    |
|  - Transmits encrypted AI response to Client in 26-char alphabet (A-Z)  |
+-------------------------------------------------------------------------+
```

---

## 🔐 Cryptographic Design & Flaws

### 1. The Affine Cipher
The encryption algorithm maps each plaintext letter $p \in \{0, 1, \dots, 25\}$ to ciphertext letter $c \in \{0, 1, \dots, 25\}$:

$$c = E_{(a,b)}(p) = (a \cdot p + b) \pmod{26}$$

Decryption computes:

$$p = D_{(a,b)}(c) = a^{-1} \cdot (c - b) \pmod{26}$$

where $a^{-1}$ is the modular multiplicative inverse of $a$ modulo $26$, satisfying:

$$a \cdot a^{-1} \equiv 1 \pmod{26}$$

A valid key requires $\gcd(a, 26) = 1$. The coprime integers in $\mathbb{Z}_{26}$ are the 12 values:
$$\{1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25\}$$

### 2. Predictable Key Derivation
The keys $(a, b)$ are computed strictly from the patient's mood input (an integer from 1 to 10):
```python
b = (2 * mood) % 26
a = next_coprime_above(b, 26)
```
Because `mood` $\in [1, 10]$, **only 10 distinct key pairs can ever be generated by the application**:

| Mood | $b = (2 \cdot \text{mood}) \bmod 26$ | Key $a$ | Key $a^{-1} \bmod 26$ | Effective Key $(a, b)$ |
|:---:|:---:|:---:|:---:|:---:|
| 1 | 2 | 3 | 9 | **(3, 2)** |
| 2 | 4 | 5 | 21 | **(5, 4)** |
| 3 | 6 | 7 | 15 | **(7, 6)** |
| 4 | 8 | 9 | 3 | **(9, 8)** |
| 5 | 10 | 11 | 19 | **(11, 10)** |
| 6 | 12 | 15 | 7 | **(15, 12)** |
| 7 | 14 | 15 | 7 | **(15, 14)** |
| 8 | 16 | 17 | 23 | **(17, 16)** |
| 9 | 18 | 19 | 11 | **(19, 18)** |
| 10 | 20 | 21 | 5 | **(21, 20)** |

---

## ⚠️ Vulnerability Catalog

1. **V1: Catastrophic Plaintext Parameter Leakage**
   - The JSON frame transmitted across TCP explicitly includes `"mood": X` unencrypted alongside the ciphertext.
   - Any passive observer sniffing port 5000 can instantaneously compute $(a, b)$ and $a^{-1} \bmod 26$ without performing any cryptanalysis whatsoever.
2. **V2: Trivial Key Space ($|\mathcal{K}| = 312$)**
   - The entire theoretical key space of the Affine cipher on $\mathbb{Z}_{26}$ is $\phi(26) \times 26 = 12 \times 26 = 312$ keys.
   - A modern CPU can brute-force all 312 candidates against English frequency dictionaries in **under 5 milliseconds**.
   - In practice, the application constrains the active key space to only **10 distinct keys**.
3. **V3: Statistical Preservation (Monoalphabetic Substitution)**
   - Because each plaintext character deterministically maps to exactly one ciphertext character, letter frequencies, digrams, and trigrams are strictly preserved.
   - High-frequency English letters (`E`, `T`, `A`, `O`, `I`, `N`) manifest as prominent frequency spikes in the ciphertext.
4. **V4: Directional Asymmetry & Armoring Bias**
   - **Client $\to$ Server (C1–C10):** The client hex-encodes payload bytes into a restricted 16-character alphabet (`A` through `P`). This concentrates letter frequencies into only 16 bins, driving the Index of Coincidence up to $IC \approx 0.150$ (extreme non-random clustering).
   - **Server $\to$ Client (S1–S10):** The server encrypts raw English sentences from the LLM across all 26 letters (`A` through `Z`), yielding $IC \approx 0.065$ (characteristic of natural English text).
5. **V5: LLM Disclaimer Boilerplate as Known-Plaintext Cribs**
   - The Ollama `llama3.2:1b` model consistently emits stereotyped therapeutic disclaimers (e.g., `"I CANNOT PROVIDE MEDICAL OR HEALTH ADVICE..."` or `"GIVEN THE PATIENT'S RECENT SURGE..."`).
   - Identifying just two letters (e.g., finding the ciphertext corresponding to `"TH"`) yields two linear congruences in two unknowns, immediately cracking the key via:
     $$a \equiv (c_1 - c_2)(p_1 - p_2)^{-1} \pmod{26}$$
     $$b \equiv (c_1 - a \cdot p_1) \pmod{26}$$
6. **V6: Deterministic Encryption (No Salt, IV, or Nonce)**
   - Encrypting the identical plaintext with the same mood produces bit-for-bit identical ciphertext, enabling traffic correlation and replay attacks.

---

## 🧮 Mathematical Formulations

### 1. Index of Coincidence (IC)
The Index of Coincidence quantifies the probability that two randomly chosen letters from a ciphertext are identical:

$$IC = \frac{\sum_{i=A}^Z f_i (f_i - 1)}{N(N - 1)}$$

- Flat random text (polyalphabetic / OTP): $IC \approx 0.038$
- Natural English text: $IC \approx 0.065$
- PsychoSupport Server responses (S1–S10): $IC \in [0.061, 0.071]$
- PsychoSupport Client payloads (C1–C10): $IC \in [0.142, 0.165]$

### 2. Chi-Squared ($\chi^2$) Goodness-of-Fit
To recover the key blindly without knowing the mood, our decryptor tests all candidate key pairs $(a', b')$ and computes the Chi-squared divergence against the canonical English letter frequency distribution $E_i$:

$$\chi^2 = \sum_{i=0}^{25} \frac{(O_i - E_i)^2}{E_i}$$

where $O_i$ is the observed frequency of letter $i$ in the decrypted candidate text, and $E_i = N \cdot p_i$ is the expected count based on standard English corpus frequencies. The candidate key yielding the minimum $\chi^2$ value is selected as the recovered key.

---

## 🛠 Attack Methodology & Toolsuite

The cryptanalytic pipeline is structured into independent, modular scripts located in [`scripts/`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts):

```
                        [ Loopback Traffic ]
                                 |
                                 v
                     [ capture_traffic.py ]
                     (Generates capture.pcap)
                                 |
        +------------------------+------------------------+
        |                                                 |
        v                                                 v
[ freq_analysis.py ]                             [ key_recovery.py ]
- Letter frequency histograms                    - Chi-squared optimization
- Index of Coincidence (IC)                      - Blind key recovery
- 22 PNG plots in evidence/plots/                - Ground-truth validation
        |                                                 |
        +------------------------+------------------------+
                                 |
                                 v
                          [ decrypt.py ]
                - Exact modular inverse math
                - Generates decrypted_dataset.csv
                - Produces verification tables
                                 |
                                 v
                    [ general_decryptor.py ]
           Autonomous universal decryptor (100% blind)
                                 |
                                 v
                  [ generate_pdf_report.py ]
          Compiles publication-grade 5-page PDF report
```

### Script Inventory
| Script | Description |
|---|---|
| [`scripts/capture_traffic.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/capture_traffic.py) | Uses Scapy to sniff loopback TCP traffic on port 5000, dumping raw packets to `evidence/capture.pcap`. |
| [`scripts/freq_analysis.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/freq_analysis.py) | Computes single-letter frequencies, IC values, and generates 22 publication-grade visual plots in `evidence/plots/`. |
| [`scripts/key_recovery.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/key_recovery.py) | Performs blind Chi-squared scoring across all 312 key possibilities to extract the optimal key pair. |
| [`scripts/decrypt.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/decrypt.py) | Decrypts all 20 streams with complete mathematical audit trails, generating CSV and Markdown tables. |
| [`scripts/general_decryptor.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/general_decryptor.py) | Autonomous end-to-end decryptor accepting any arbitrary PsychoSupport ciphertext. |
| [`scripts/generate_pdf_report.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/generate_pdf_report.py) | Generates the formal, all-black academic submission report (`report.pdf`) using ReportLab. |
| [`scripts/regenerate_all.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/regenerate_all.py) | Master harness orchestrating 10 fresh patient interactions through Ollama and capturing all data. |
| [`scripts/pull_model.py`](file:///c:/Users/DELL/OneDrive/Desktop/Info%20Sec%20A2/scripts/pull_model.py) | Downloads the required `llama3.2:1b` model from Ollama library. |

---

## 📊 Experimental Results & Verification

All 10 patient sessions (20 total ciphertexts) were decrypted with **100% precision (20/20)**.

### Master Decryption Summary Table
| Stream | Patient / Persona | Mood | Intercepted Ciphertext (Excerpt) | Recovered Key $(a, b)$ | $\chi^2$ Score | Decrypted Plaintext (Excerpt) | Status |
|:---:|:---|:---:|:---|:---:|:---:|:---|:---:|
| **S1** | Alex (Overwhelmed) | 1 | `IUXIT RNO VMROTI...` | **(3, 2)** | 61.2 | `GIVEN THE PATIENT S RECENT SURGE IN WORKLOAD...` | ✅ Broken |
| **S2** | Brenda (Burnout) | 2 | `U GEJJAZ BDAVUKO...` | **(5, 4)** | 27.5 | `I CANNOT PROVIDE MEDICAL OR HEALTH ADVICE...` | ✅ Broken |
| **S3** | Charlie (Depression) | 3 | `MIJIT WLMDNUK E...` | **(7, 6)** | 42.7 | `GIVEN CHARLIE S STRUGGLES WITH PERSISTENT LOW...` | ✅ Broken |
| **S4** | Diana (Social Anxiety) | 4 | `CEZIT RCEFE E...` | **(9, 8)** | 55.5 | `GIVEN DIANA S RECURRING SOCIAL ANXIETY...` | ✅ Broken |
| **S5** | Ethan (Insomnia) | 5 | `MCZIT ODHFT E...` | **(11, 10)** | 50.7 | `GIVEN ETHAN S MESSAGE IT SEEMS LIKE HE S...` | ✅ Broken |
| **S6** | Fiona (Health Anxiety) | 6 | `OMZIT LEAFE E...` | **(15, 12)** | 50.6 | `GIVEN FIONA S PROGRESS ON HER DAILY WELLNESS...` | ✅ Broken |
| **S7** | George (Grief/Loss) | 7 | `U SEJJET BDEPUTO...` | **(15, 14)** | 53.3 | `I CANNOT PROVIDE THERAPEUTIC ADVICE...` | ✅ Broken |
| **S8** | Hannah (Exam Panic) | 8 | `KMZIT RNO VMROTI...` | **(17, 16)** | 46.1 | `GIVEN THE PATIENT S POSITIVE MOOD...` | ✅ Broken |
| **S9** | Ian (Workplace Stress) | 9 | `KMZIT RNO VMEURR...` | **(19, 18)** | 41.9 | `GIVEN THE POSITIVE AND UPLIFTING MOOD OF IAN...` | ✅ Broken |
| **S10**| Julia (Panic Disorder) | 10 | `EMZIT DKVUE E...` | **(21, 20)** | 81.8 | `GIVEN JULIA S REMARKABLE JOURNEY...` | ✅ Broken |

---

## 📂 Repository Branches & Structure

This repository is maintained across two distinct branches:

### 1. `main` Branch (Clean Academic Submission)
Contains exclusively the clean, essential source code, analysis suite, evidence artifacts, and final report required for evaluation and grading. All reverse-engineering decompression dumps and compiler temporaries are omitted.

```
.
├── psycare_lab/
│   ├── client.py             # PsychoSupport patient client GUI
│   ├── server.py             # PsychoSupport server daemon
│   └── requirements.txt      # Python dependencies
├── scripts/
│   ├── capture_traffic.py    # Packet capture tool
│   ├── decrypt.py            # Mathematical decryption script
│   ├── freq_analysis.py      # Statistical & frequency analyzer
│   ├── general_decryptor.py  # Autonomous blind decryptor
│   ├── generate_pdf_report.py# Academic report generator
│   ├── key_recovery.py       # Chi-squared key recovery engine
│   ├── pull_model.py         # Ollama model helper
│   ├── regenerate_all.py     # End-to-end dataset regenerator
│   └── README.md             # Scripts guide
├── evidence/
│   ├── capture.pcap          # Intercepted raw TCP loopback packets
│   ├── session_log.json      # Intercepted plaintext and metadata log
│   ├── stream_1..10.txt      # Raw stream session logs
│   ├── plots/                # 22 frequency histogram charts (PNG)
│   └── tables/               # CSV and Markdown proof tables
├── ciphertexts.csv           # Master dataset of 20 captured ciphertexts
├── report.pdf                # Publication-grade academic report (5 pages)
├── START_LAB.ps1             # One-click Windows PowerShell lab runner
├── .gitignore                # Exclusion rules for temporary files
└── README.md                 # Complete project documentation
```

### 2. `all-files` Branch (Full Research Archive)
Includes all project assets, including original reverse-engineering artifacts, decompilation outputs, PyInstaller extractor tools, and original binaries (`client`, `server`, `pyinstxtractor.py`, `client_extracted/`, `server_extracted/`).

---

## 🚀 How to Run & Reproduce (Quick Start)

### Prerequisites
- **Operating System:** Windows 10/11 or Linux
- **Python:** Version 3.12 or newer
- **Ollama:** Download and install from [ollama.com](https://ollama.com/download)

### Method A: One-Click Automated Run (Windows PowerShell)
From the repository root, execute:
```powershell
.\START_LAB.ps1
```
This script automatically executes all 7 phases:
1. Terminates any conflicting background Ollama or server processes
2. Launches `ollama serve`
3. Downloads the `llama3.2:1b` language model
4. Starts the `psycare_lab/server.py` daemon
5. Runs `scripts/regenerate_all.py` to record 10 fresh patient sessions
6. Executes the complete cryptanalysis pipeline
7. Builds the submission PDF report (`report.pdf`)

### Method B: Manual Step-by-Step Execution
```powershell
# 1. Install required dependencies
pip install -r psycare_lab/requirements.txt
pip install scapy reportlab matplotlib pandas

# 2. Start Ollama daemon (in a separate terminal)
ollama serve

# 3. Pull LLM model
python scripts/pull_model.py

# 4. Run the PsychoSupport Server
python psycare_lab/server.py

# 5. Run the PsychoSupport Client GUI (optional manual exploration)
python psycare_lab/client.py

# 6. Run the full cryptanalysis pipeline
python scripts/freq_analysis.py
python scripts/key_recovery.py
python scripts/decrypt.py
python scripts/general_decryptor.py

# 7. Generate the Academic PDF Report
python scripts/generate_pdf_report.py
```

---

## ⚖️ Comprehensive Ethical Statement & Responsible Disclosure

### 1. Educational and Controlled Scope
This research and cryptanalysis was performed strictly within the academic boundaries of the **Information Security course at FAST-NUCES (Fall 2026)**. The entire environment was isolated, air-gapped, and executed over local TCP loopback (`127.0.0.1`). All patient personas, clinical scenarios, and dialogue records were **100% synthetically generated** using prompt templates and local language models. No actual human patients, identifiable medical records, or live healthcare systems were observed, accessed, or endangered.

### 2. The Dual-Use Dilemma
The tools and mathematical principles employed in this project (frequency analysis, Chi-squared inference, packet sniffing, reverse engineering) represent **dual-use capabilities**. When wielded by defenders and security auditors, they uncover critical flaws before malicious adversaries can exploit them. However, when deployed without authorization, the identical techniques enable mass surveillance, extortion, and catastrophic identity theft. 

### 3. Legal and Regulatory Statutes
Applying these techniques against real tele-health or production systems without explicit written consent is illegal and carries severe civil and criminal penalties under:
- **Pakistan Prevention of Electronic Crimes Act (PECA 2016):**
  - *Section 10 (Cyber Terrorism & Critical Infrastructure Interception)*
  - *Section 11 (Unauthorized Access to Transmission of Data)*
  - *Section 14 (Unauthorized Interception)*
- **US Health Insurance Portability and Accountability Act (HIPAA):**
  - *Security Rule (45 CFR § 164.312)* mandating encryption in transit for Protected Health Information (PHI).
- **EU General Data Protection Regulation (GDPR):**
  - *Article 9* classifying health and psychiatric data as *Special Category Data* demanding the highest degree of technical security and privacy by design.

### 4. Coordinated Vulnerability Disclosure (CVD) Protocol
Should vulnerabilities of this nature be uncovered in a commercial or open-source production application, security researchers must adhere to established ethical disclosure frameworks:
1. **Private Reporting:** Privately contact the organization’s designated security contact or CISO. Never publish details or proof-of-concept exploits publicly before notification.
2. **Actionable Remediation Guidance:** Provide the development team with detailed reproduction steps, threat assessments, and clear mitigation blueprints (e.g., modern TLS 1.3 integration).
3. **Reasonable Grace Period:** Allow a 90-day window for developers to design, test, and distribute secure patches before public disclosure.
4. **Harm Minimization:** Redact any live endpoints, credentials, or customer data from technical writeups.
5. **Adherence to Professional Codes:** Strict compliance with the **ACM Code of Ethics and Professional Conduct** (Rule 1.2 "Avoid Harm", Rule 2.9 "Design and implement systems that are robustly and usably secure") and the **IEEE Code of Ethics**.

---

## 🛡 Remediation & Defense Roadmap

To transform PsychoSupport into an enterprise-grade secure platform, the following cryptographic mitigations must be implemented:

1. **Mandatory TLS 1.3 Transport Security**
   - Completely deprecate the custom Affine cipher.
   - Encapsulate all socket communications in standard **TLS 1.3** (`RFC 8446`) utilizing authenticated ciphersuites (e.g., `TLS_AES_256_GCM_SHA384` or `TLS_CHACHA20_POLY1305_SHA256`).
   - Guarantees confidentiality, data integrity, and Perfect Forward Secrecy (PFS).
2. **Mutual TLS (mTLS) Authentication**
   - Enforce cryptographic X.509 client and server certificates to eliminate impersonation and Man-in-the-Middle (MitM) attacks.
3. **Secure Local IPC Alternatives**
   - For desktop loopback communications between client GUI and backend, replace raw TCP sockets with OS-level access-controlled **Named Pipes** (Windows) or **UNIX Domain Sockets** with strict file permissions (`0600`), rendering traffic invisible to standard network packet sniffers.
4. **Complete Elimination of Plaintext Metadata**
   - Never transmit security-critical parameters (`mood`, session IDs, user roles) outside the encrypted payload envelope.

---

## 📚 References

1. **Al-Kindi.** *Manuscript on Deciphering Cryptographic Messages* (Risalah fi Istikhraj al-Mu'amma), c. 850 AD.
2. **Shannon, C. E.** "Communication Theory of Secrecy Systems." *Bell System Technical Journal*, Vol. 28, No. 4, pp. 656–715, 1949.
3. **Stallings, W.** *Cryptography and Network Security: Principles and Practice*, 8th Edition, Pearson, 2020.
4. **Rescorla, E.** "The Transport Layer Security (TLS) Protocol Version 1.3." *RFC 8446*, Internet Engineering Task Force (IETF), August 2018.
5. **Association for Computing Machinery (ACM).** *ACM Code of Ethics and Professional Conduct*, 2018.

---

*Department of Computer Science — FAST National University of Computer and Emerging Sciences (FAST-NUCES)*  
*CS Information Security — Fall 2026*
