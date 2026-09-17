#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
if [ ! -x ".venv/bin/python" ]; then
  echo "Ambiente virtual nao encontrado. Execute: python3 -m venv .venv"
  exit 1
fi
source .venv/bin/activate
streamlit run app.py
