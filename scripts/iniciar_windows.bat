@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado.
  echo Execute primeiro: py -m venv .venv
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
streamlit run app.py
