# ============================================================
#  PsycoSupport Lab - ONE-CLICK LAUNCHER
#  Run this from the project root:
#    .\START_LAB.ps1
# ============================================================

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VENV  = "$ROOT\venv\Scripts\python.exe"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PSYCOSUPPORT LAB - AUTOMATED SETUP & RUN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── STEP 1: Kill any stray Ollama processes ──────────────────
Write-Host "[1/7] Clearing port 11434 (killing stray Ollama processes)..." -ForegroundColor Yellow
$ollamaProcs = Get-Process *ollama* -ErrorAction SilentlyContinue
if ($ollamaProcs) {
    $ollamaProcs | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    Write-Host "      Done. Old Ollama processes terminated." -ForegroundColor Green
} else {
    Write-Host "      No stray Ollama processes found." -ForegroundColor Green
}

# ── STEP 2: Start Ollama daemon in background ────────────────
Write-Host "[2/7] Starting Ollama daemon (port 11434)..." -ForegroundColor Yellow
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 4

# Verify it started
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:11434/v1/models" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "      Ollama daemon is running." -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Ollama did not start. Is ollama.exe installed?" -ForegroundColor Red
    Write-Host "      Download from: https://ollama.com/download" -ForegroundColor Red
    exit 1
}

# ── STEP 3: Pull the model ───────────────────────────────────
Write-Host "[3/7] Pulling llama3.2:1b model (skips if already downloaded)..." -ForegroundColor Yellow
& $VENV "$ROOT\scripts\pull_model.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Model pull failed. Check Ollama is running." -ForegroundColor Red
    exit 1
}
Write-Host "      Model ready." -ForegroundColor Green

# ── STEP 4: Start PsycoSupport server in background ─────────
Write-Host "[4/7] Starting PsycoSupport server on 127.0.0.1:5000..." -ForegroundColor Yellow
$serverJob = Start-Job -ScriptBlock {
    param($py, $root)
    & $py "$root\psycare_lab\server.py" 2>&1
} -ArgumentList $VENV, $ROOT

Start-Sleep -Seconds 5

# Verify server is up
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "      PsycoSupport server is running." -ForegroundColor Green
} catch {
    # Server may not have an HTTP root - try a TCP connect instead
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    try {
        $tcpClient.Connect("127.0.0.1", 5000)
        $tcpClient.Close()
        Write-Host "      PsycoSupport server is running (TCP)." -ForegroundColor Green
    } catch {
        Write-Host "      WARNING: Server may still be starting. Continuing..." -ForegroundColor Yellow
    }
}

# ── STEP 5: Regenerate 10 sessions of real LLM data ─────────
Write-Host "[5/7] Generating 10 fresh sessions (real LLM output)..." -ForegroundColor Yellow
Write-Host "      This may take 1-3 minutes depending on your hardware." -ForegroundColor Gray
& $VENV "$ROOT\scripts\regenerate_all.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Session regeneration failed." -ForegroundColor Red
    exit 1
}
Write-Host "      Sessions generated. ciphertexts.csv and evidence/ updated." -ForegroundColor Green

# ── STEP 6: Run analysis scripts ────────────────────────────
Write-Host "[6/7] Running cryptanalysis pipeline..." -ForegroundColor Yellow

Write-Host "      -> Frequency analysis..." -ForegroundColor Gray
& $VENV "$ROOT\scripts\freq_analysis.py"

Write-Host "      -> Key recovery (Al-Kindi / Chi-Squared)..." -ForegroundColor Gray
& $VENV "$ROOT\scripts\key_recovery.py"

Write-Host "      -> Decryption verification..." -ForegroundColor Gray
& $VENV "$ROOT\scripts\decrypt.py"

Write-Host "      -> Universal decryptor (bonus)..." -ForegroundColor Gray
& $VENV "$ROOT\scripts\general_decryptor.py"

Write-Host "      Cryptanalysis complete." -ForegroundColor Green

# ── STEP 7: Build PDF report ─────────────────────────────────
Write-Host "[7/7] Generating PDF report..." -ForegroundColor Yellow
& $VENV "$ROOT\scripts\generate_pdf_report.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: PDF generation failed." -ForegroundColor Red
    exit 1
}
Write-Host "      report.pdf created." -ForegroundColor Green

# ── Package ZIP ──────────────────────────────────────────────
Write-Host ""
Write-Host "Packaging lab_submission.zip..." -ForegroundColor Yellow

$zipScript = @"
import zipfile, pathlib, os
KEEP = {'.py','.csv','.txt','.md','.pdf','.pcap','.pcapng','.png','.json'}
SKIP = {'venv','__pycache__','.git','client_extracted','server_extracted'}
root = pathlib.Path('.')
with zipfile.ZipFile('lab_submission.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if not p.is_file(): continue
        if p.name == 'lab_submission.zip': continue
        if any(s in p.parts for s in SKIP): continue
        if p.suffix.lower() in KEEP:
            z.write(p, p.relative_to(root).as_posix())
sz = os.path.getsize('lab_submission.zip')//1024
print(f'lab_submission.zip: {sz} KB')
"@

$zipScript | & $VENV -
Write-Host "      lab_submission.zip ready." -ForegroundColor Green

# ── Done ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ALL DONE! Outputs:" -ForegroundColor Cyan
Write-Host "    report.pdf           <- Full academic PDF report" -ForegroundColor White
Write-Host "    ciphertexts.csv      <- 20 captured ciphertexts" -ForegroundColor White
Write-Host "    evidence/            <- PCAP, plots, tables, logs" -ForegroundColor White
Write-Host "    lab_submission.zip   <- Ready to submit" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To also open the GUI client (optional demo):" -ForegroundColor Gray
Write-Host "  & '$VENV' '$ROOT\psycare_lab\client.py'" -ForegroundColor Gray
Write-Host ""
