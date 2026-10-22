"""
Decryption Suite for PsycoSupport Lab
CS InfoSec Lab - FAST-NUCES

Decrypts all captured ciphertexts (Client->Server and Server->Client),
showing the mathematical inverse calculation, sample character decryption trace,
de-armoring reconstruction, and complete recovered plaintexts.
"""

import math
import pandas as pd

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def modinv(a: int, m: int = 26) -> int:
    t, nt = 0, 1
    r, nr = m, a % m
    while nr != 0:
        q = r // nr
        t, nt = nt, t - q * nt
        r, nr = nr, r - q * nr
    if r != 1:
        raise ValueError(f"No inverse for a={a} mod {m}")
    if t < 0:
        t += m
    return t

def affine_decrypt(txt: str, a: int, b: int) -> str:
    inv_a = modinv(a, 26)
    out = []
    for ch in txt:
        if ch == ' ':
            out.append(' ')
        elif 'A' <= ch <= 'Z':
            c = ord(ch) - 65
            p = (inv_a * (c - b)) % 26
            out.append(chr(p + 65))
    return "".join(out)

def armor_decode(armored: str) -> str:
    s = armored.replace(" ", "")
    out = bytearray()
    for i in range(0, len(s), 2):
        if i + 1 < len(s):
            hi = ord(s[i]) - ord('A')
            lo = ord(s[i+1]) - ord('A')
            out.append((hi << 4) | lo)
    return out.decode("utf-8", errors="replace")

def format_sample_math(cipher_sample: str, a: int, b: int, inv_a: int) -> str:
    """Show character-by-character modular arithmetic steps."""
    clean = [c for c in cipher_sample.replace(" ", "")[:4]]
    steps = []
    for ch in clean:
        c_val = ord(ch) - 65
        diff = (c_val - b) % 26
        p_val = (inv_a * diff) % 26
        p_ch = chr(p_val + 65)
        steps.append(f"c='{ch}' ({c_val:2d}) -> ({c_val:2d} - {b:2d}) mod 26 = {diff:2d} -> ({inv_a} * {diff:2d}) mod 26 = {p_val:2d} -> p='{p_ch}'")
    return " | ".join(steps)

def run_decryption_suite():
    df = pd.read_csv("ciphertexts.csv")
    
    # Key mapping derived per mood
    # mood -> (a, b)
    mood_keys = {
        1: (3, 2),
        2: (5, 4),
        3: (7, 6),
        4: (9, 8),
        5: (11, 10),
        6: (15, 12),
        7: (15, 14),
        8: (17, 16),
        9: (19, 18),
        10: (21, 20)
    }
    
    print("=" * 90)
    print("PSYCOSUPPORT DECRYPTION RESULTS — ALL 20 CAPTURED CIPHERTEXTS")
    print("=" * 90)
    
    decrypted_records = []
    
    for _, row in df.iterrows():
        cid = row["id"]
        direction = row["direction"]
        username = row["username"]
        mood = int(row["mood"])
        cipher = row["ciphertext"]
        summary = row["concern_summary"]
        
        a, b = mood_keys[mood]
        inv_a = modinv(a, 26)
        
        raw_decrypted = affine_decrypt(cipher, a, b)
        
        if direction == "Client->Server":
            # Client messages are armored
            final_plain = armor_decode(raw_decrypted)
            dec_type = "Affine Decrypt -> UTF-8 Hex Nibble De-Armor"
        else:
            # Server messages are direct cleaned uppercase text
            final_plain = raw_decrypted
            dec_type = "Direct Affine Decrypt"
            
        math_steps = format_sample_math(cipher, a, b, inv_a)
        
        decrypted_records.append({
            "id": cid,
            "direction": direction,
            "username": username,
            "mood": mood,
            "a": a,
            "b": b,
            "inv_a": inv_a,
            "formula": f"p = {inv_a} * (c - {b}) mod 26",
            "sample_math": math_steps,
            "decryption_pipeline": dec_type,
            "ciphertext_snippet": cipher[:60] + "...",
            "final_plaintext": final_plain
        })
        
        print(f"\n--- [{cid}] {direction} | User: {username} | Mood: {mood} ---")
        print(f"Key: (a={a}, b={b}), a^-1 = {inv_a} | Formula: p = {inv_a} * (c - {b}) mod 26")
        print(f"Sample Math: {math_steps}")
        print(f"Plaintext: {final_plain}")

    dec_df = pd.DataFrame(decrypted_records)
    dec_df.to_csv("evidence/tables/decrypted_dataset.csv", index=False)
    
    # Write Markdown Table for Report
    with open("evidence/tables/decryption_report_table.md", "w", encoding="utf-8") as f:
        f.write("# Decryption Results and Mathematical Steps\n\n")
        for rec in decrypted_records:
            f.write(f"### Ciphertext {rec['id']} ({rec['direction']} — {rec['username']}, Mood {rec['mood']})\n")
            f.write(f"- **Recovered Key**: $a = {rec['a']}, b = {rec['b']}$, Modular Inverse $a^{{-1}} = {rec['inv_a']} \\pmod{{26}}$\n")
            f.write(f"- **Decryption Formula**: $p \\equiv {rec['inv_a']} \\cdot (c - {rec['b']}) \\pmod{{26}}$\n")
            f.write(f"- **Sample Arithmetic**: `{rec['sample_math']}`\n")
            f.write(f"- **Ciphertext**: `{rec['ciphertext_snippet']}`\n")
            f.write(f"- **Recovered Plaintext**: **\"{rec['final_plaintext']}\"**\n\n")

if __name__ == "__main__":
    run_decryption_suite()
