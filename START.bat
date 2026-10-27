@echo off
title Strata NEXUS
cd /d "%~dp0engine"

rem 启动上次用过的模型（engine\.last-model.json）；没有记录时回落到 Qwen
".venv\Scripts\python.exe" -c "import json,pathlib,subprocess,sys;n=pathlib.Path('.last-model.json');d=json.loads(n.read_text(encoding='utf-8')) if n.exists() else {};c=d.get('config') or 'strata-iq2_xs.json';p=pathlib.Path(c);p=p if p.is_absolute() else pathlib.Path.cwd()/p;print('[start]',p.name);sys.exit(subprocess.call([sys.executable,'serve/server.py','--engine','strata','--config',str(p),'--port',str(d.get('port') or 8080),'--open']))"
if errorlevel 1 pause
