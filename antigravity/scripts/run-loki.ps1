$task = if ($args.Count -eq 0) { "implement database module with security auth" } else { $args -join " " }
# run-loki.ps1 (v5.3.0-OMNI)
$omniPath = "C:/Users/<USER_NAME>/.gemini/antigravity/skills/specialized/loki-mode/autonomy/omni_perspective_evaluator.py"
$shieldPath = "C:/Users/<USER_NAME>/.gemini/antigravity/skills/specialized/loki-mode/autonomy/loki_shield.py"
$indexerPath = "C:/Users/<USER_NAME>/.gemini/antigravity/scripts/brain_indexer.py"
$enginePath = "C:/Users/<USER_NAME>/.gemini/antigravity/scripts/orchestrator.py"

$task = if ($args.Count -eq 0) { "Phân tích và tối ưu hóa hệ thống toàn diện" } else { $args -join " " }

Write-Host "🧠 [BRAIN] Refreshing Neural Knowledge Index..." -ForegroundColor Yellow
python $indexerPath

Write-Host "👁️ [OMNI] KÍCH HOẠT LÕI NHẬN THỨC ĐA LĂNG KÍNH..." -ForegroundColor Magenta
python $omniPath "$task"

Write-Host "🛡️ [SHIELD] STARTING LOKI-MODE WITH AUTO-SHIELD PROTECTION..." -ForegroundColor Cyan
python $shieldPath "python $enginePath"

