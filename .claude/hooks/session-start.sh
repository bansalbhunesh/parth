#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "=== Pramaan session-start hook ==="

# --- Python scraping dependencies ---
echo "[1/5] Installing Python scraping deps..."
pip install -q firecrawl-py crawl4ai 2>/dev/null || true

# --- Backend dependencies ---
echo "[2/5] Installing backend deps..."
if [ -f "$CLAUDE_PROJECT_DIR/backend/requirements.txt" ]; then
  pip install -q -r "$CLAUDE_PROJECT_DIR/backend/requirements.txt" 2>/dev/null || true
fi

# --- Chromium for Playwright/Crawl4ai ---
echo "[3/5] Setting up Chromium..."
CHROME_BIN="/opt/chromium/chrome-linux/chrome"
PW_CHROME="/opt/pw-browsers/chromium-1223/chrome-linux64/chrome"
if [ ! -x "$CHROME_BIN" ]; then
  apt-get install -y -qq chromium-browser 2>/dev/null || true
  LAST_REV=$(wget -q "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/LAST_CHANGE" -O - 2>/dev/null || echo "1650722")
  wget -q "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/${LAST_REV}/chrome-linux.zip" -O /tmp/chrome-linux.zip 2>/dev/null || true
  if [ -f /tmp/chrome-linux.zip ]; then
    mkdir -p /opt/chromium
    unzip -q -o /tmp/chrome-linux.zip -d /opt/chromium 2>/dev/null || true
    rm -f /tmp/chrome-linux.zip
  fi
fi
# Symlink for Playwright's expected path
if [ -x "$CHROME_BIN" ]; then
  mkdir -p "$(dirname "$PW_CHROME")"
  ln -sf "$CHROME_BIN" "$PW_CHROME"
  echo "  Chromium ready at $CHROME_BIN"
fi

# --- Frontend dependencies ---
echo "[4/5] Installing frontend deps..."
if [ -f "$CLAUDE_PROJECT_DIR/frontend/package.json" ]; then
  cd "$CLAUDE_PROJECT_DIR/frontend"
  npm install --prefer-offline 2>/dev/null || true
  cd "$CLAUDE_PROJECT_DIR"
fi

# --- Run standards scraper ---
echo "[5/5] Running standards scraper..."
if [ -f "$CLAUDE_PROJECT_DIR/data/scrape_standards.py" ]; then
  python3 "$CLAUDE_PROJECT_DIR/data/scrape_standards.py" 2>&1 || true
fi

# --- Regenerate corpus ---
echo "[+] Regenerating corpus..."
if [ -f "$CLAUDE_PROJECT_DIR/data/generate_corpus.py" ]; then
  python3 "$CLAUDE_PROJECT_DIR/data/generate_corpus.py" 2>&1 || true
fi

echo "=== Pramaan session-start hook complete ==="
