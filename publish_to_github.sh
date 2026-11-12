#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${REPO_NAME:-gemini-airgapped-drive-relay}"
DESCRIPTION="RFC & Reference Architecture: Air-Gapped Cloud-Drive Relay for Google Gemini Live, Antigravity 2.0, and Google Drive"

echo "[1/4] Running reference verifier self-test..."
python3 reference-cli/drive_pull_verify.py --self-test

echo "[2/4] Initializing clean Git repository..."
if [ ! -d .git ]; then
  git init -b main
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "Initial RFC: Air-Gapped Cloud-Drive Relay architecture for Gemini & Antigravity"
fi

echo "[3/4] Checking GitHub CLI authentication..."
if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed. Install gh or set a git remote manually." >&2
  exit 1
fi

gh auth status

echo "[4/4] Creating public GitHub repository '${REPO_NAME}' and pushing main..."
if gh repo view "${REPO_NAME}" >/dev/null 2>&1; then
  GH_USER="$(gh api user -q .login)"
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/${GH_USER}/${REPO_NAME}.git"
  git push -u origin main
else
  gh repo create "${REPO_NAME}" \
    --public \
    --description "${DESCRIPTION}" \
    --source=. \
    --remote=origin \
    --push
fi

# Add discoverability topics so Google DevRel / Security / Antigravity engineers find it
GH_USER="$(gh api user -q .login)"
gh repo edit "${GH_USER}/${REPO_NAME}" \
  --add-topic "google-gemini" \
  --add-topic "google-antigravity" \
  --add-topic "gvisor" \
  --add-topic "beyondcorp" \
  --add-topic "ai-security" \
  --add-topic "agentic-workflows" \
  --add-topic "rfc" || true

echo "Published: https://github.com/${GH_USER}/${REPO_NAME}"
