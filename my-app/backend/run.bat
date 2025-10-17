@echo off
uvicorn app.main:app --reload --port 8001 --log-level warning
pause