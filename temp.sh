#!/bin/bash
# Run MEE2024, automatically creating a virtualenv if needed
set -e

APP_NAME="mee2024"
ENV_DIR="$HOME/.mee2024env"
REPO_URL="git+https://github.com/andrew551/MEE2024.git"

echo "Using environment: $ENV_DIR"

if [ ! -d "$ENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ENV_DIR"
fi

source "$ENV_DIR/bin/activate"

if ! command -v mee2024 >/dev/null 2>&1; then
    echo "Installing / reinstalling MEE2024..."
    pip install --upgrade pip
    pip install --upgrade "$REPO_URL"
fi

echo "Launching MEE2024..."
exec mee2024
