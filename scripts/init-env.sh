#!/bin/bash
# Initialize .env file from GitHub Secrets or manual input.
# Usage:
#   ./scripts/init-env.sh          # Interactive: prompt for missing values
#   ./scripts/init-env.sh --ci     # CI mode: create .env from GitHub Secrets via Actions artifact
set -e

ENV_FILE=".env"
ENV_EXAMPLE=".env.example"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Required secret names (must match GitHub Secrets)
REQUIRED_SECRETS=(
  "ODOO_URL"
  "ODOO_DB"
  "ODOO_USERNAME"
  "ODOO_PASSWORD"
  "ODOO_TIMEZONE"
  "B4B_API_URL"
  "B4B_TOKEN"
  "B4B_ENTITY_ID"
)

# Secrets that should be entered silently (no echo)
SENSITIVE_KEYS=("ODOO_PASSWORD" "B4B_TOKEN")

# Optional settings with defaults
OPTIONAL_SETTINGS=(
  "TZ:Asia/Ho_Chi_Minh"
  "SYNC_INTERVAL_HOURS:4"
  "PAYMENT_METHODS:VNPayQR,ATM,Digital"
  "MAX_ORDERS_PER_BATCH:100"
  "DEBUG:false"
  "DRY_RUN:false"
  "SKIP_EXISTING:true"
  "GENERATE_INVOICES:true"
)

# Portable sed in-place edit (macOS and Linux)
_sed_i() {
  if sed --version 2>/dev/null | grep -q GNU; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

cd "$PROJECT_DIR"

# --- CI Mode: download .env from GitHub Actions artifact ---
if [[ "${1:-}" == "--ci" ]]; then
  echo "CI mode: fetching .env from GitHub Actions artifact..."
  if ! command -v gh &>/dev/null; then
    echo "ERROR: gh CLI required. Install: https://cli.github.com"
    exit 1
  fi

  echo "Triggering env-generator workflow..."
  gh workflow run env-generator.yml

  echo "Waiting for workflow run to appear..."
  sleep 5
  # Poll for the latest run until it shows up
  for i in $(seq 1 12); do
    RUN_ID=$(gh run list --workflow=env-generator.yml --limit 1 --json databaseId -q '.[0].databaseId')
    if [[ -n "$RUN_ID" ]]; then
      break
    fi
    sleep 5
  done

  if [[ -z "$RUN_ID" ]]; then
    echo "ERROR: Could not find workflow run after 60s"
    exit 1
  fi

  echo "Watching run $RUN_ID..."
  gh run watch "$RUN_ID" --exit-status

  gh run download "$RUN_ID" --name env-file --dir .
  echo "Done. .env created from GitHub Secrets."
  exit 0
fi

# --- Interactive Mode ---
echo "=== Odoo Sync - Environment Setup ==="
echo ""

# Check if .env already exists
if [[ -f "$ENV_FILE" ]]; then
  echo "Found existing .env file."
  MISSING=0
  for SECRET in "${REQUIRED_SECRETS[@]}"; do
    if ! grep -q "^${SECRET}=" "$ENV_FILE" || grep -q "^${SECRET}=$" "$ENV_FILE"; then
      echo "  MISSING: $SECRET"
      MISSING=$((MISSING + 1))
    fi
  done

  if [[ $MISSING -eq 0 ]]; then
    echo "All required variables are set. Nothing to do."
    exit 0
  fi
  echo ""
  read -rp "Fill in missing values? [Y/n] " CONFIRM
  [[ "${CONFIRM:-Y}" == [nN] ]] && exit 0
fi

# Check GitHub Secrets availability
HAS_GH=false
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
  HAS_GH=true
  echo "GitHub CLI detected and authenticated."
  echo ""

  echo "Checking GitHub Secrets..."
  MISSING_SECRETS=()
  for SECRET in "${REQUIRED_SECRETS[@]}"; do
    if ! gh secret list | grep -q "^${SECRET}"; then
      MISSING_SECRETS+=("$SECRET")
    fi
  done

  if [[ ${#MISSING_SECRETS[@]} -eq 0 ]]; then
    echo "All required secrets found in GitHub."
    echo ""
    echo "NOTE: GitHub Secrets are write-only (cannot be read back via API)."
    echo "Options:"
    echo "  1. Enter values manually below"
    echo "  2. Run: ./scripts/init-env.sh --ci  (generates via GitHub Actions)"
    echo ""
  else
    echo "Missing GitHub Secrets: ${MISSING_SECRETS[*]}"
    echo "Set them with: gh secret set SECRET_NAME --body 'value'"
    echo ""
  fi
fi

# Create .env from example if not exists
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_EXAMPLE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "Created .env from .env.example"
  else
    touch "$ENV_FILE"
    echo "Created empty .env"
  fi
fi

# Check if a key is sensitive (should be entered silently)
_is_sensitive() {
  local key="$1"
  for sk in "${SENSITIVE_KEYS[@]}"; do
    [[ "$key" == "$sk" ]] && return 0
  done
  return 1
}

# Prompt for required values
echo ""
echo "=== Required Settings ==="
for SECRET in "${REQUIRED_SECRETS[@]}"; do
  CURRENT=""
  if grep -q "^${SECRET}=" "$ENV_FILE"; then
    CURRENT=$(grep "^${SECRET}=" "$ENV_FILE" | cut -d'=' -f2-)
  fi

  if [[ -z "$CURRENT" ]]; then
    if _is_sensitive "$SECRET"; then
      read -rsp "  ${SECRET}: " VALUE
      echo ""
    else
      read -rp "  ${SECRET}: " VALUE
    fi
    if [[ -n "$VALUE" ]]; then
      if grep -q "^${SECRET}=" "$ENV_FILE"; then
        _sed_i "s|^${SECRET}=.*|${SECRET}=${VALUE}|" "$ENV_FILE"
      else
        echo "${SECRET}=${VALUE}" >> "$ENV_FILE"
      fi
    fi
  else
    echo "  ${SECRET}=*** (already set)"
  fi
done

# Add optional settings if not present
echo ""
echo "=== Optional Settings (defaults) ==="
for SETTING in "${OPTIONAL_SETTINGS[@]}"; do
  KEY="${SETTING%%:*}"
  DEFAULT="${SETTING#*:}"
  if ! grep -q "^${KEY}=" "$ENV_FILE"; then
    echo "${KEY}=${DEFAULT}" >> "$ENV_FILE"
    echo "  ${KEY}=${DEFAULT}"
  fi
done

echo ""
echo "Done. .env file created at: ${ENV_FILE}"
