@echo off
set SCRIPT_DIR=%~dp0

pip install -r "%SCRIPT_DIR%requirements.txt"

cd /d "%SCRIPT_DIR%scripts"

python malayalam_m3u.py > ..\malayalam_m3u.m3u
python tamil_m3u.py > ..\tamil_m3u.m3u
@REM python movies_m3u.py > ..\movies_m3u.m3u
python xxx_m3u.py > ..\xxx_m3u.m3u
python tamil_local_json.py > ..\tamil_local_json.m3u
python malayalam_local_json.py > ..\malayalam_local_json.m3u
@REM python test_m3u.py > ..\test_m3u.m3u
