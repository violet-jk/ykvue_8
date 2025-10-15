@echo off
uvicorn app.main:app --reload --port 8000 --log-level warning
pause