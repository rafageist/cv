# Script to generate CV using WeasyPrint with GTK4

# Save original PATH
$originalPath = $env:PATH

# Configure environment variables for GTK4
$env:GTK_PATH = "D:\apps\gtk4"

# Rebuild PATH without Meld and with GTK at the beginning
$systemPath = $env:PATH -split ';' | Where-Object { $_ -notmatch 'Meld' }
$newPath = @("$env:GTK_PATH\bin") + $systemPath
$env:PATH = $newPath -join ';'

$env:GI_TYPELIB_PATH = "$env:GTK_PATH\lib\girepository-1.0"
$env:XDG_DATA_DIRS = "$env:GTK_PATH\share"

Write-Host "Testing WeasyPrint..." -ForegroundColor Yellow
python -c "import weasyprint; print('WeasyPrint version:', weasyprint.__version__)"

if ($LASTEXITCODE -eq 0) {
    Write-Host "WeasyPrint loaded successfully!" -ForegroundColor Green
    Write-Host "Building CV..." -ForegroundColor Yellow
    # Execute the Python script
    python scripts\build_cv.py
} else {
    Write-Host "Error loading WeasyPrint. Check GTK installation." -ForegroundColor Red
}

# Restore original PATH
$env:PATH = $originalPath
