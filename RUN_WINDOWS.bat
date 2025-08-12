@echo off
setlocal
where py >nul 2>&1
if %ERRORLEVEL%==0 ( set PY=py -3 ) else ( set PY=python )
%PY% -m venv .venv
call .venv\Scripts\python -m pip install --upgrade pip
call .venv\Scripts\python -m pip install -r requirements.txt
call .venv\Scripts\python -m streamlit run app.py
pause
