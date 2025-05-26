# PowerShell script to test Windows wheel installation
# This script demonstrates the proper way to handle wheel installation on Windows

Write-Host "Testing Windows wheel installation..."
Write-Host ""

# Check if wheelhouse directory exists
if (-not (Test-Path "wheelhouse")) {
    Write-Host "❌ wheelhouse directory not found"
    exit 1
}

# Get all wheel files
$wheels = Get-ChildItem wheelhouse\*.whl
Write-Host "Found $($wheels.Count) wheels:"

if ($wheels.Count -eq 0) {
    Write-Host "❌ No wheels found in wheelhouse directory"
    exit 1
}

# List all wheels
foreach ($wheel in $wheels) {
    Write-Host "  📦 $($wheel.Name)"
}

Write-Host ""
Write-Host "Testing installation..."

# Test installation of each wheel
$successCount = 0
$totalCount = $wheels.Count

foreach ($wheel in $wheels) {
    Write-Host "Installing $($wheel.Name)..." -NoNewline

    try {
        # Capture output and errors
        $output = python -m pip install $wheel.FullName --force-reinstall 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅ SUCCESS" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host " ⚠️  FAILED (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
            Write-Host "    Output: $output" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host " ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Summary: $successCount/$totalCount wheels installed successfully"

if ($successCount -eq $totalCount) {
    Write-Host "🎉 All wheels installed successfully!" -ForegroundColor Green
    exit 0
} elseif ($successCount -gt 0) {
    Write-Host "⚠️  Some wheels installed successfully" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "❌ No wheels could be installed" -ForegroundColor Red
    exit 1
}
