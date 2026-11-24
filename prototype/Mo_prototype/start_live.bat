@echo off
cd /d "%~dp0"
echo Mo prototype - LIVE mode
echo.
echo Works with any OpenAI-compatible API (OpenAI, DeepSeek, Qwen/DashScope, ...).
echo Press Enter to accept the default shown in [brackets].
echo.
set /p LLM_API_KEY=API key: 
set LLM_BASE_URL=https://api.openai.com/v1
set /p LLM_BASE_URL=Base URL [https://api.openai.com/v1]: 
set LLM_MODEL=gpt-4o-mini
set /p LLM_MODEL=Model [gpt-4o-mini]: 
where python >nul 2>nul && (python serve_live.py) || (py serve_live.py)
pause
