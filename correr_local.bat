@echo off
REM Plan B: corre Chacra Clara en esta laptop con un solo comando (doble clic o "correr_local.bat").
REM La primera vez crea el entorno e instala todo (~3 min). Luego abre http://localhost:8501 en el navegador.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creando el entorno por primera vez...
  python -m venv .venv
  .venv\Scripts\python -m pip install --quiet --upgrade pip
  .venv\Scripts\python -m pip install --quiet -r requirements.txt
)
.venv\Scripts\python -m streamlit run app.py --server.port 8501
