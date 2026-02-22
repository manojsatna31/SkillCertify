# -------------------------------
# Initialization
# -------------------------------

# Define base directory
$baseDir = "."

# Define folder structure as an array
$folders = @(
    "$baseDir/config",
    "$baseDir/log",
    "$baseDir/img",
    "$baseDir/web_app/data",
    "$baseDir/web_app/static",
    "$baseDir/web_app/templates",
    "$baseDir/web_app/utils",
    "$baseDir/web_app/static/css"
    "$baseDir/web_app/static/js",
    "$baseDir/web_app/logging_config"
)

# -------------------------------
# Folder Creation
# -------------------------------

Write-Host "Creating folder structure..." -ForegroundColor Cyan

foreach ($folder in $folders) {
    if (-Not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "[+] Created folder: $folder" -ForegroundColor Green
    } else {
        Write-Host "[!] Folder already exists: $folder" -ForegroundColor Yellow
    }
}
# Define files and their content
$files = @{
    "$baseDir/web_app/__init__.py" = "# Package Init";
    "$baseDir/web_app/utils/__init__.py" = "# Utils Package Init";
    "$baseDir/web_app/logging_config/__init__.py" = "# Logging Config Package Init";
    "$baseDir/.env" = "# Environment Variables";
    "$baseDir/requirements.txt" = @"
# -----------------------
# 🌐 Core Web Framework
# -----------------------
Flask==2.3.3               # The main web framework used to build routing, render templates, manage requests, etc.

# ------------------------------
# 🧠 Server-Side Session Support
# ------------------------------
Flask-Session==0.5.0       # Enables server-side sessions (using filesystem, Redis, or Memcached backends)

# -----------------------
# 🎨 Template Rendering
# -----------------------
jinja2==3.1.3              # Template engine used by Flask for rendering HTML with dynamic data

# NOTE: MarkupSafe is a dependency of Jinja2
# It provides automatic escaping of HTML to prevent XSS.
# You do NOT need to include it manually unless used directly.

# -----------------------
# 🛠 Internal Flask Tools
# -----------------------
Werkzeug==2.3.7            # Flask’s internal WSGI utility library; handles requests, responses, routing, etc.

# -------------------------------
# ⚙️ Environment Configuration
# -------------------------------
python-dotenv==1.0.1       # Allows loading config variables from .env files (optional, but helpful for configs)

# -----------------------
# 🔐 Optional Future Additions
# -----------------------

# For Memcached-based sessions or caching (optional)
# pymemcache==4.0.0

# For Redis-based session management (alternative to filesystem)
# redis==5.0.1
PyYAML==6.0.2
#💡 Installation Tip:
# Use this inside a virtual environment:
# python -m venv venv
# source venv/bin/activate  # or venv\\Scripts\\activate on Windows
# pip install -r requirements.txt
# If you're using this in production or sharing with a team:
# pip install -r requirements.txt     
     
"@;
}

# -------------------------------
# File Creation
# -------------------------------

Write-Host "Initializing files with header comments..." -ForegroundColor Cyan

foreach ($filePath in $files.Keys) {
    $fileContent = $files[$filePath]
    # Ensure parent folder exists (in case of missed folders)
    $parentDir = Split-Path $filePath
    if (-Not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir | Out-Null
        Write-Host "[+] Created missing folder: $parentDir" -ForegroundColor Green
    }

    # Overwrite the file with header content
    Set-Content -Path $filePath -Value $fileContent
    Write-Host "[+] Created file: $filePath" -ForegroundColor Green
}
# -------------------------------
# Virtual Environment Setup
# -------------------------------

Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan

# Create virtual environment named 'venv'
python -m venv venv

if (Test-Path "./venv/Scripts/Activate.ps1") {
    Write-Host "[+] Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "[X] Failed to create virtual environment." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "./venv/Scripts/Activate.ps1"