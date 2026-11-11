#!/usr/bin/env sh
# Plan B (Linux/Mac): corre Chacra Clara en esta laptop con un solo comando: sh correr_local.sh
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Creando el entorno por primera vez..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --quiet -r requirements.txt
fi
.venv/bin/python -m streamlit run app.py --server.port 8501
