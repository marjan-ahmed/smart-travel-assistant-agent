@echo off
cd /d "e:\python\smart-travel-assistant-agent\backend"
echo Starting backend server from: %CD%
python api_server.py
pause