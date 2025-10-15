@echo off
rem Bootstrap: activate venv, then run app with passed args
call activate_venv.bat || exit /b 1
python app.py %*
