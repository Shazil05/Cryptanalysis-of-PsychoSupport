"""
PDF Report Generator — PsycoSupport Cryptanalysis Lab
CS InfoSec — FAST-NUCES (Fall 2026) — Assignment #1
Visual-first design: black headings, stat boxes, charts dominant, minimal prose.
"""

import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

# ── Colour Palette (ALL BLACK theme) ────────────────────────
C_BLACK   = colors.HexColor("#111111")
C_DARK    = colors.HexColor("#222222")
C_MID     = colors.HexColor("#555555")
C_LIGHT   = colors.HexColor("#F2F2F2")
C_WHITE   = colors.white
C_BORDER  = colors.HexColor("#BBBBBB")
C_ACCENT  = colors.HexColor("#E05C00")   # amber — used only for key highlights
C_CODE_BG = colors.HexColor("#F7F7F7")

# ============================================================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_chrome(n)
            super().showPage()
        super().save()

    def _draw_chrome(self, total):
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MID)
        # Header line
        self.setStrokeColor(C_BLACK)
        self.setLineWidth(0.8)
        self.line(36, 11*72 - 24, 8.5*72 - 36, 11*72 - 24)
        self.drawString(36, 11*72 - 18, "FAST-NUCES  |  Information Security Lab  |  PsycoSupport Cryptanalysis Report")
        self.drawRightString(8.5*72 - 36, 11*72 - 18, "Assignment #1  |  Fall 2026")
        # Footer line
        self.line(36, 34, 8.5*72 - 36, 34)
        self.drawString(36, 24, "CONFIDENTIAL — Academic Submission")
        self.drawRightString(8.5*72 - 36, 24, f"Page {self._pageNumber} of {total}")
        self.restoreState()

# ============================================================
def build_pdf_report():
    pdf_filename = "report.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=40, rightMargin=40,
        topMargin=40, bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # ── Typography (all black) ───────────────────────────────
    def style(name, **kw):
        base = kw.pop("parent", styles["Normal"])
        return ParagraphStyle(name, parent=base, **kw)

    title_s   = style("T", fontName="Helvetica-Bold", fontSize=22, leading=26,
                       textColor=C_BLACK, spaceAfter=2)
    sub_s     = style("S", fontName="Helvetica",      fontSize=10, leading=14,
                       textColor=C_MID,  spaceAfter=10)
    h1_s      = style("H1", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                       textColor=C_BLACK, spaceBefore=14, spaceAfter=4, keepWithNext=True)
    h2_s      = style("H2", fontName="Helvetica-Bold", fontSize=10,   leading=13,
                       textColor=C_BLACK, spaceBefore=8,  spaceAfter=3, keepWithNext=True)
    body_s    = style("B", fontName="Helvetica",      fontSize=8.5, leading=11.5,
                       textColor=C_DARK, spaceAfter=4)
    cell_s    = style("C", fontName="Helvetica",      fontSize=7.5, leading=9.5,
                       textColor=C_DARK)
    hdr_s     = style("TH", fontName="Helvetica-Bold", fontSize=7.5, leading=9.5,
                       textColor=C_WHITE)
    code_s    = style("CD", fontName="Courier",        fontSize=7.5, leading=9.5,
                       textColor=colors.HexColor("#8B0000"))
    callout_s = style("CL", fontName="Helvetica",      fontSize=8,   leading=11,
                       textColor=C_DARK)

    story = []

    # ══════════════════════════════════════════════════════════
    # COVER
    # ══════════════════════════════════════════════════════════
    story.append(Spacer(1, 14))
    story.append(Paragraph("FAST-NUCES — Department of Computer Science", sub_s))
    story.append(Paragraph("Information Security — Assignment #1 Lab Report", title_s))
    story.append(HRFlowable(width="100%", thickness=2, color=C_BLACK, spaceBefore=4, spaceAfter=6))
    story.append(Paragraph("<b>End-to-End Cryptanalysis of PsycoSupport</b> — Affine Cipher, Frequency Analysis &amp; Key Recovery", sub_s))

    # Meta table
    meta = [
        [Paragraph("<b>Course:</b> CS InfoSec (Fall 2026)", cell_s),
         Paragraph("<b>App:</b> PsycoSupport v1.0-Alpha", cell_s),
         Paragraph("<b>Server:</b> 127.0.0.1:5000", cell_s)],
        [Paragraph("<b>Role:</b> Tester-Cryptanalyst", cell_s),
         Paragraph("<b>LLM Backend:</b> Ollama llama3.2:1b (1.26 GB)", cell_s),
         Paragraph("<b>Deliverable:</b> lab_submission.zip", cell_s)],
    ]
    tm = Table(meta, colWidths=[173, 173, 174])
    tm.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_LIGHT),
        ("BOX",        (0,0), (-1,-1), 0.8, C_BLACK),
        ("INNERGRID",  (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ]))
    story.append(tm)
    story.append(Spacer(1, 10))

    # ── Summary stat boxes ───────────────────────────────────
    stats = [
        ("20", "Ciphertexts\nCaptured"),
        ("10", "Sessions\n(Moods 1-10)"),
        ("312", "Key Space\nSize"),
        ("100%", "Decryption\nAccuracy"),
        ("0 ms", "Brute-Force\nTime*"),
    ]
    stat_data = [[Paragraph(
        f"<b><font size='18'>{v}</font></b><br/><font size='7' color='#555555'>{l.replace(chr(10),' ')}</font>",
        style("ST", fontName="Helvetica-Bold", fontSize=18, leading=22,
              textColor=C_BLACK, alignment=1)
    ) for v, l in stats]]
    ts = Table(stat_data, colWidths=[104]*5)
    ts.setStyle(TableStyle([
        ("BOX",       (0,0),(-1,-1), 1.2, C_BLACK),
        ("INNERGRID", (0,0),(-1,-1), 0.5, C_BORDER),
        ("BACKGROUND",(0,0),(-1,-1), C_LIGHT),
        ("ALIGN",     (0,0),(-1,-1), "CENTER"),
        ("VALIGN",    (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ]))
    story.append(ts)
    story.append(Paragraph("<i>*All 312 keys brute-forced in &lt;5 ms. Mood value leaked in plaintext JSON.</i>", sub_s))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BLACK, spaceBefore=4, spaceAfter=2))

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — Architecture
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("1. System Architecture", h1_s))

    arch_box = [[Paragraph(
        "<b>Client → Server:</b> Armored hex nibbles (A..P alphabet), Affine-encrypted, sent as JSON.<br/>"
        "<b>Server → Client:</b> Uppercase English text (A..Z), Affine-encrypted reply from Ollama LLM.<br/>"
        "<b>Key Leak:</b> <code>mood</code> integer sent in <b>plaintext JSON</b> → attacker can compute (a, b) directly.<br/>"
        "<b>Key Formula:</b> <code>b = (2 × mood) mod 26</code>, <code>a = next_coprime_above(b, 26)</code>.",
        callout_s)]]
    ta = Table(arch_box, colWidths=[520])
    ta.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), C_LIGHT),
        ("BOX",        (0,0),(-1,-1), 1.2, C_BLACK),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story.append(ta)
    story.append(Spacer(1, 6))

    # ══════════════════════════════════════════════════════════
    # SECTION 2 — Ciphertext Collection
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("2. Ciphertext Collection — Captured Traffic (127.0.0.1:5000)", h1_s))
    df_c = pd.read_csv("ciphertexts.csv")

    ct_data = [[
        Paragraph("ID", hdr_s), Paragraph("Dir", hdr_s), Paragraph("User", hdr_s),
        Paragraph("Mood", hdr_s), Paragraph("Concern", hdr_s), Paragraph("Ciphertext Snippet", hdr_s)
    ]]
    for _, r in df_c.iterrows():
        snip = r["ciphertext"][:30] + "…"
        ct_data.append([
            Paragraph(f"<b>{r['id']}</b>", cell_s),
            Paragraph("C→S" if "Client" in r["direction"] else "S→C", cell_s),
            Paragraph(str(r["username"]), cell_s),
            Paragraph(str(r["mood"]), cell_s),
            Paragraph(str(r["concern_summary"])[:38] + "…", cell_s),
            Paragraph(f"<code>{snip}</code>", code_s),
        ])
    tc = Table(ct_data, colWidths=[28, 30, 48, 30, 168, 216])
    tc.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1, 0), C_BLACK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ("GRID",        (0,0),(-1,-1), 0.4, C_BORDER),
        ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
    ]))
    story.append(tc)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — Frequency Analysis
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("3. Al-Kindi Frequency Analysis &amp; Index of Coincidence (IC)", h1_s))
    story.append(Paragraph(
        "IC formula: <code>IC = Σ f_i(f_i−1) / N(N−1)</code>. "
        "English ≈ 0.065. Uniform random ≈ 0.038. "
        "Client→Server IC ≈ 0.14 (only 16 symbols used). Server→Client IC ≈ 0.065 (natural English).",
        body_s))

    df_f = pd.read_csv("evidence/tables/frequency_summary.csv")
    fr_data = [[
        Paragraph("ID", hdr_s), Paragraph("Dir", hdr_s), Paragraph("Mood", hdr_s),
        Paragraph("N", hdr_s),  Paragraph("IC", hdr_s),  Paragraph("Top Cipher Letters", hdr_s),
        Paragraph("Interpretation", hdr_s),
    ]]
    for _, r in df_f.iterrows():
        interp = "Armored hex (16-char)" if r["direction"] == "Client->Server" else "Natural English mono"
        fr_data.append([
            Paragraph(f"<b>{r['id']}</b>", cell_s),
            Paragraph("C→S" if r["direction"] == "Client->Server" else "S→C", cell_s),
            Paragraph(str(r["mood"]), cell_s),
            Paragraph(str(r["clean_len"]), cell_s),
            Paragraph(f"<b>{r['ic']:.4f}</b>", cell_s),
            Paragraph(r["top_5_cipher_letters"], cell_s),
            Paragraph(interp, cell_s),
        ])
    tf = Table(fr_data, colWidths=[28, 30, 30, 30, 44, 210, 148])
    tf.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), C_BLACK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 1.5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1.5),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
    ]))
    story.append(tf)
    story.append(Spacer(1, 6))

    # Charts — 2×2 grid, larger
    story.append(Paragraph("<b>Figure 1:</b> Frequency Histograms vs Standard English (Server→Client sessions S1, S3; Client→Server C1; Aggregate Server)", h2_s))
    img_grid = [
        [Image("evidence/plots/freq_S1.png", width=3.8*inch, height=1.7*inch),
         Image("evidence/plots/freq_S3.png", width=3.8*inch, height=1.7*inch)],
        [Image("evidence/plots/freq_C1.png", width=3.8*inch, height=1.7*inch),
         Image("evidence/plots/freq_aggregate_server.png", width=3.8*inch, height=1.7*inch)],
    ]
    timg = Table(img_grid, colWidths=[273, 273])
    timg.setStyle(TableStyle([
        ("ALIGN",   (0,0),(-1,-1), "CENTER"),
        ("VALIGN",  (0,0),(-1,-1), "MIDDLE"),
        ("PADDING", (0,0),(-1,-1), 2),
        ("BOX",     (0,0),(-1,-1), 0.5, C_BORDER),
    ]))
    story.append(timg)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — Key Recovery
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("4. Key Derivation &amp; Mathematical Proof", h1_s))

    # Worked proof box
    proof_box = [[Paragraph(
        "<b>Worked Proof — Session S1 (Alex, Mood 1):</b><br/>"
        "Top cipher letter: O (13.8%) → maps to E (4).  Second: H (7.8%) → maps to T (19).<br/>"
        "<b>Eq 1:</b> 14 ≡ 4a + b (mod 26)    <b>Eq 2:</b> 7 ≡ 19a + b (mod 26)<br/>"
        "Subtract: 7 ≡ −15a ≡ 11a (mod 26)  →  a = 7 × 11⁻¹ = 7 × 19 = 133 ≡ <b>3</b> (mod 26)<br/>"
        "Solve b: b = 14 − 3×4 = <b>2</b> (mod 26).  Decryption: <b>p ≡ 9 · (c − 2) (mod 26)</b>",
        callout_s)]]
    tp = Table(proof_box, colWidths=[520])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), C_LIGHT),
        ("BOX",        (0,0),(-1,-1), 1.5, C_BLACK),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story.append(tp)
    story.append(Spacer(1, 6))

    # Key recovery table (Server→Client only — cleaner)
    story.append(Paragraph("<b>Table 4.1:</b> Recovered Keys — All 10 Server→Client Sessions (Chi² score confirms correct key)", h2_s))
    df_k = pd.read_csv("evidence/tables/key_recovery_summary.csv")
    kd = [[
        Paragraph("Mood", hdr_s), Paragraph("Key (a,b)", hdr_s),
        Paragraph("a⁻¹", hdr_s),  Paragraph("Decrypt Formula", hdr_s),
        Paragraph("χ²", hdr_s),   Paragraph("Recovered Plaintext (first 50 chars)", hdr_s),
    ]]
    for _, r in df_k[df_k["direction"] == "Server->Client"].iterrows():
        kd.append([
            Paragraph(f"<b>{r['mood']}</b>", cell_s),
            Paragraph(f"<b>({r['recovered_a']}, {r['recovered_b']})</b>", cell_s),
            Paragraph(str(r["inv_a"]), cell_s),
            Paragraph(f"p ≡ {r['inv_a']}·(c−{r['recovered_b']})", code_s),
            Paragraph(f"{r['chi2_score']:.1f}", cell_s),
            Paragraph(str(r["decrypted_snippet"])[:50] + "…", cell_s),
        ])
    tk = Table(kd, colWidths=[30, 55, 30, 100, 40, 265])
    tk.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), C_BLACK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
    ]))
    story.append(tk)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 5 — Decryption Results
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("5. Decryption Results — All 20 Ciphertexts", h1_s))
    df_d = pd.read_csv("evidence/tables/decrypted_dataset.csv")
    dd = [[
        Paragraph("ID", hdr_s), Paragraph("Dir", hdr_s), Paragraph("Mood", hdr_s),
        Paragraph("Key (a,b)", hdr_s), Paragraph("Formula", hdr_s),
        Paragraph("Recovered Plaintext", hdr_s),
    ]]
    for _, r in df_d.iterrows():
        dd.append([
            Paragraph(f"<b>{r['id']}</b>", cell_s),
            Paragraph("C→S" if "Client" in r["direction"] else "S→C", cell_s),
            Paragraph(str(r["mood"]), cell_s),
            Paragraph(f"({r['a']},{r['b']})", cell_s),
            Paragraph(str(r["formula"]), code_s),
            Paragraph(f"<b>[{r['username']}]</b> {str(r['final_plaintext'])[:70]}…", cell_s),
        ])
    tdec = Table(dd, colWidths=[26, 30, 28, 50, 100, 286])
    tdec.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), C_BLACK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_LIGHT]),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
    ]))
    story.append(tdec)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 6 — Universal Decryptor (Bonus)
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("6. Universal Autonomous Decryptor — Bonus Task", h1_s))
    bonus_box = [[Paragraph(
        "<b>Script:</b> <code>scripts/general_decryptor.py</code><br/>"
        "<b>Mode A (Rule-based):</b> Given mood → compute b=(2·mood)%26, a=next_coprime(b,26). O(1).<br/>"
        "<b>Mode B (Blind search):</b> Try all 312 keys; score with χ² (English) or hex-nibble containment.<br/>"
        "<b>Result: 20/20 ciphertexts correctly decrypted (100%) — zero false positives.</b>",
        callout_s)]]
    tb = Table(bonus_box, colWidths=[520])
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), C_LIGHT),
        ("BOX",        (0,0),(-1,-1), 1.5, C_BLACK),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story.append(tb)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 7 — Security Engineering
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("7. Security Engineering Analysis", h1_s))
    vuln_box = [[Paragraph(
        "<b>Vulnerability — LLM Boilerplate as Known-Plaintext Crib:</b> "
        "Ollama LLMs emit predictable disclaimers (e.g. 'I cannot provide medical advice…'). "
        "Knowing just 2 character mappings solves (a, b) instantly — no frequency analysis needed.",
        callout_s)]]
    tvuln = Table(vuln_box, colWidths=[520])
    tvuln.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#FFF3E0")),
        ("BOX",        (0,0),(-1,-1), 1.5, C_BLACK),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story.append(tvuln)
    story.append(Spacer(1, 5))

    sec_data = [
        [Paragraph("Alternative 1 — IPC (Unix Sockets / Named Pipes)", hdr_s),
         Paragraph("Alternative 2 — Mutual TLS 1.3 (mTLS + ECDHE)", hdr_s)],
        [Paragraph(
            "<b>How:</b> Replace TCP socket with kernel IPC channel.<br/>"
            "<b>Security:</b> OS-enforced access control; invisible to packet sniffers.<br/>"
            "<b>Pros:</b> Zero network overhead; high throughput.<br/>"
            "<b>Cons:</b> Single-host only.", cell_s),
         Paragraph(
            "<b>How:</b> TLS 1.3 over loopback with x509 certificates.<br/>"
            "<b>Security:</b> IND-CCA2 AEAD + PFS + mutual authentication.<br/>"
            "<b>Pros:</b> Immune to sniffing, replay, MITM; scales remotely.<br/>"
            "<b>Cons:</b> Requires PKI / cert management.", cell_s)],
    ]
    tsec = Table(sec_data, colWidths=[260, 260])
    tsec.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1, 0), C_BLACK),
        ("GRID",        (0,0),(-1,-1), 0.5, C_BORDER),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
        ("BACKGROUND",  (0,1),(-1,-1), C_LIGHT),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
    ]))
    story.append(tsec)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 8 — Reflection
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("8. Reflection &amp; Critical Analysis", h1_s))
    refl = [
        [Paragraph("(a) Input Influence", hdr_s),
         Paragraph("<code>mood</code> is the sole key driver (b=2·mood, a=coprime). "
                   "Same mood + same message → identical ciphertext → traffic correlation attack possible.", cell_s)],
        [Paragraph("(b) Directional Asymmetry", hdr_s),
         Paragraph("C→S: armored 16-char alphabet → IC≈0.15 (very high spikes). "
                   "S→C: natural English 26-char → IC≈0.065. Both are trivially broken.", cell_s)],
        [Paragraph("(c) Cipher Weaknesses", hdr_s),
         Paragraph("1-to-1 substitution preserves frequency. Key space = 312. "
                   "Brute force &lt;5 ms. Mood transmitted in plaintext → zero secrecy.", cell_s)],
        [Paragraph("(d) Ethics &amp; Responsible Disclosure", hdr_s),
         Paragraph(
             "As a computer science student studying information security at FAST-NUCES, I recognize that cryptanalytic "
             "capabilities present a classic <b>dual-use dilemma</b>: techniques utilized to audit and secure software "
             "can cause immense harm if weaponized. This research was strictly executed in an <b>air-gapped, isolated "
             "educational laboratory</b> using exclusively synthetic, AI-generated conversation prompts. No real patient records, "
             "identifying information, or actual psychiatric communications were targeted or compromised.<br/><br/>"
             "Mental health telemetry represents <i>special category personal data</i> of the highest sensitivity. "
             "Unauthorized interception or eavesdropping breaches fundamental bioethical tenets (beneficence, non-maleficence, "
             "patient autonomy) and constitutes severe criminal misconduct under Pakistan's <b>PECA 2016</b> (Sections 10 &amp; 11 — "
             "Unauthorized access/copying of data), the US <b>HIPAA</b> Privacy &amp; Security Rules (45 CFR § 164.312), and the EU "
             "<b>GDPR</b> (Article 9). Furthermore, this work adheres strictly to the <b>ACM Code of Ethics</b> (Sections 1.2 'Avoid harm' "
             "and 2.9 'Design robustly secure systems').<br/><br/>"
             "When critical cryptographic failures (such as broken substitution ciphers and plaintext key disclosure) are uncovered "
             "in production environments, ethical practitioners must enforce <b>Coordinated Vulnerability Disclosure (CVD)</b>: "
             "privately alerting engineering teams, providing remediation roadmaps (TLS 1.3 / AEAD), granting a 90-day remediation window, "
             "and mitigating patient harm above all else.",
             cell_s)],
    ]
    trefl = Table(refl, colWidths=[110, 410])
    trefl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,-1), C_BLACK),
        ("BACKGROUND",    (1,0),(1,-1), C_LIGHT),
        ("ROWBACKGROUNDS",(1,0),(1,-1), [C_LIGHT, C_WHITE]),
        ("GRID",          (0,0),(-1,-1), 0.5, C_BORDER),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
    ]))
    story.append(trefl)
    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════
    # SECTION 9 — Verification + References
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("9. Source Code Verification &amp; References", h1_s))
    story.append(Paragraph(
        "Source code review of <code>server.py</code> confirms: "
        "<code>b = (2·mood) % 26</code>, <code>a = next_coprime_above(b, 26)</code>. "
        "Cryptanalytic keys match ground-truth with <b>100% precision</b>.", body_s))

    refs = [
        [Paragraph("1", cell_s), Paragraph("Al-Kindi. <i>Manuscript on Deciphering Cryptographic Messages</i>, c. 850 AD.", cell_s)],
        [Paragraph("2", cell_s), Paragraph("Shannon. 'Communication Theory of Secrecy Systems.' <i>Bell System Technical Journal</i>, 1949.", cell_s)],
        [Paragraph("3", cell_s), Paragraph("Stallings. <i>Cryptography and Network Security</i>, 8th Ed., Pearson, 2020.", cell_s)],
        [Paragraph("4", cell_s), Paragraph("Rescorla. 'TLS 1.3.' <i>RFC 8446</i>, IETF, 2018.", cell_s)],
    ]
    tref = Table(refs, colWidths=[20, 500])
    tref.setStyle(TableStyle([
        ("VALIGN", (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))
    story.append(tref)

    # Build
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] report.pdf generated successfully.")

if __name__ == "__main__":
    build_pdf_report()
