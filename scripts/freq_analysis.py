"""
Frequency Analysis and Statistical Profiling for PsycoSupport Lab
CS InfoSec Lab - FAST-NUCES

Performs Al-Kindi Frequency Analysis, Index of Coincidence (IC) calculations,
comparison against standard English letter frequencies, generates markdown/CSV
tables and side-by-side histogram charts.
"""

import os
import string
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Standard English Letter Frequencies (Source: Beker & Piper, 1982 / Lewand, 2000)
ENGLISH_FREQ = {
    'E': 12.70, 'T': 9.06, 'A': 8.17, 'O': 7.51, 'I': 6.97, 'N': 6.75, 'S': 6.33,
    'H': 6.09, 'R': 5.99, 'D': 4.25, 'L': 4.03, 'C': 2.78, 'U': 2.76, 'M': 2.41,
    'W': 2.36, 'F': 2.23, 'G': 2.02, 'Y': 1.97, 'P': 1.93, 'B': 1.29, 'V': 0.98,
    'K': 0.77, 'J': 0.15, 'X': 0.15, 'Q': 0.10, 'Z': 0.07
}

ALPHABET = list(string.ascii_uppercase)

def ensure_dirs():
    os.makedirs("evidence/plots", exist_ok=True)
    os.makedirs("evidence/tables", exist_ok=True)

def preprocess_text(text: str):
    """Clean text to uppercase A-Z only, recording removed non-letters."""
    removed = []
    cleaned_chars = []
    for idx, ch in enumerate(text):
        if ch.upper() in ALPHABET:
            cleaned_chars.append(ch.upper())
        else:
            removed.append((idx, ch))
    cleaned_str = "".join(cleaned_chars)
    return cleaned_str, removed

def compute_frequency(cleaned_str: str):
    """Count letter occurrences and calculate relative percentages."""
    counts = {ch: 0 for ch in ALPHABET}
    total = len(cleaned_str)
    for ch in cleaned_str:
        if ch in counts:
            counts[ch] += 1
    
    freq_pct = {ch: (counts[ch] / total * 100.0) if total > 0 else 0.0 for ch in ALPHABET}
    return counts, freq_pct, total

def compute_index_of_coincidence(counts: dict, total: int) -> float:
    """Compute the Index of Coincidence (IC) for monoalphabetic verification."""
    if total <= 1:
        return 0.0
    numerator = sum(f * (f - 1) for f in counts.values())
    denominator = total * (total - 1)
    return numerator / denominator

def plot_frequency_histogram(freq_pct: dict, cid: str, direction: str, mood: int, output_path: str):
    """Generate side-by-side bar chart comparing Ciphertext vs Standard English."""
    # Order letters alphabetically
    letters = ALPHABET
    cipher_vals = [freq_pct.get(ch, 0.0) for ch in letters]
    english_vals = [ENGLISH_FREQ.get(ch, 0.0) for ch in letters]
    
    x = np.arange(len(letters))
    width = 0.38
    
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=300)
    
    rects1 = ax.bar(x - width/2, cipher_vals, width, label='Ciphertext Frequency (%)', color='#2b5c8f', edgecolor='black', alpha=0.9)
    rects2 = ax.bar(x + width/2, english_vals, width, label='Standard English (%)', color='#d95f02', edgecolor='black', alpha=0.85)
    
    ax.set_ylabel('Relative Frequency (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Letter Frequency Distribution — Ciphertext {cid} ({direction}, Mood={mood}) vs Standard English', fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(letters, fontsize=10, fontweight='bold')
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    ax.set_ylim(0, max(max(cipher_vals), max(english_vals)) + 3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def run_frequency_analysis():
    ensure_dirs()
    df = pd.read_csv("ciphertexts.csv")
    
    results = []
    aggregate_client = {ch: 0 for ch in ALPHABET}
    aggregate_server = {ch: 0 for ch in ALPHABET}
    total_client_letters = 0
    total_server_letters = 0
    
    print("=" * 80)
    print("PSYCOSUPPORT CRYPTANALYSIS — FREQUENCY ANALYSIS & STATISTICAL PROFILING")
    print("=" * 80)
    
    for _, row in df.iterrows():
        cid = row["id"]
        direction = row["direction"]
        username = row["username"]
        mood = int(row["mood"])
        cipher_raw = row["ciphertext"]
        
        cleaned, removed = preprocess_text(cipher_raw)
        counts, freqs, total = compute_frequency(cleaned)
        ic = compute_index_of_coincidence(counts, total)
        
        # Aggregate
        if direction == "Client->Server":
            for ch in ALPHABET:
                aggregate_client[ch] += counts[ch]
            total_client_letters += total
        else:
            for ch in ALPHABET:
                aggregate_server[ch] += counts[ch]
            total_server_letters += total
            
        # Top 5 ciphertext letters
        sorted_letters = sorted(freqs.items(), key=lambda x: x[1], reverse=True)
        top5_str = ", ".join([f"{ch}: {pct:.1f}%" for ch, pct in sorted_letters[:5] if pct > 0])
        
        # Save individual plot
        plot_path = f"evidence/plots/freq_{cid}.png"
        plot_frequency_histogram(freqs, cid, direction, mood, plot_path)
        
        results.append({
            "id": cid,
            "direction": direction,
            "username": username,
            "mood": mood,
            "raw_len": len(cipher_raw),
            "clean_len": total,
            "removed_non_letters": len(removed),
            "ic": ic,
            "top_5_cipher_letters": top5_str,
            "plot_file": plot_path
        })
        
        print(f"[{cid}] {direction:14s} | User: {username:7s} | Mood: {mood:2d} | N={total:3d} | IC={ic:.4f} | Top: {top5_str}")

    # Summary DataFrame
    summary_df = pd.DataFrame(results)
    summary_df.to_csv("evidence/tables/frequency_summary.csv", index=False)
    
    # Generate Aggregate Plots
    agg_client_freq = {ch: (aggregate_client[ch] / total_client_letters * 100) for ch in ALPHABET}
    agg_server_freq = {ch: (aggregate_server[ch] / total_server_letters * 100) for ch in ALPHABET}
    
    plot_frequency_histogram(agg_client_freq, "AGG_CLIENT", "Client->Server (All)", 0, "evidence/plots/freq_aggregate_client.png")
    plot_frequency_histogram(agg_server_freq, "AGG_SERVER", "Server->Client (All)", 0, "evidence/plots/freq_aggregate_server.png")
    
    ic_agg_client = compute_index_of_coincidence(aggregate_client, total_client_letters)
    ic_agg_server = compute_index_of_coincidence(aggregate_server, total_server_letters)
    
    print("\n" + "=" * 80)
    print("AGGREGATE DIRECTIONAL STATISTICS:")
    print(f"Client->Server Aggregate: Total Letters = {total_client_letters}, IC = {ic_agg_client:.4f}")
    print(f"Server->Client Aggregate: Total Letters = {total_server_letters}, IC = {ic_agg_server:.4f}")
    print("=" * 80)
    
    # Save formatted Markdown tables for report
    with open("evidence/tables/frequency_report_tables.md", "w", encoding="utf-8") as f:
        f.write("# Frequency Analysis & Preprocessing Tables\n\n")
        f.write("## 1. Ciphertext Summary & Index of Coincidence (IC)\n\n")
        f.write(summary_df[["id", "direction", "username", "mood", "raw_len", "clean_len", "ic", "top_5_cipher_letters"]].to_markdown(index=False))
        f.write("\n\n")
        f.write("## 2. Directional Characteristics\n\n")
        f.write(f"- **Client->Server (Armored Hex Nibbles + Affine)**: Mean IC = {summary_df[summary_df['direction']=='Client->Server']['ic'].mean():.4f}, Letters restricted to 16-character subset.\n")
        f.write(f"- **Server->Client (Natural English Advice + Affine)**: Mean IC = {summary_df[summary_df['direction']=='Server->Client']['ic'].mean():.4f}, Natural English monoalphabetic distribution.\n")

if __name__ == "__main__":
    run_frequency_analysis()
