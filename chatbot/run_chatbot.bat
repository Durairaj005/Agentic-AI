@echo off
cd /d "%~dp0"
set OPENROUTER_API_KEY=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
python chatbot_with_openai.py
pause
