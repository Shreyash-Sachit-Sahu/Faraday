$ErrorActionPreference = "Stop"
Start-Transcript -Path C:\faraday-data\overnight_expand.log -Append
& C:\venvs\faraday\Scripts\Activate.ps1
$env:PYTHONUTF8 = "1"
Set-Location (Join-Path $PSScriptRoot "..\ai-service")
python -m app.pipeline.stage1_wikipedia --max-scan 6500000 --max-articles 40000
if ($LASTEXITCODE -ne 0) { throw "stage1 failed" }
python -m app.pipeline.stage4_embed_qdrant
if ($LASTEXITCODE -ne 0) { throw "stage4 failed" }
python -m app.pipeline.stage5_bm25
if ($LASTEXITCODE -ne 0) { throw "stage5 failed" }
python -m app.pipeline.verify_phase1
python -m app.eval.build_evalset
python -m app.eval.run_eval
python -m app.retrieval.retriever "What happens during the TCP three-way handshake?"
Stop-Transcript
