#!/bin/bash
# Mo prototype - LIVE mode (macOS). Double-click this file.
cd "$(dirname "$0")"
echo "Works with any OpenAI-compatible API (OpenAI, DeepSeek, Qwen/DashScope, ...)."
read -r -p "API key: " LLM_API_KEY
read -r -p "Base URL [https://api.openai.com/v1]: " LLM_BASE_URL
read -r -p "Model [gpt-4o-mini]: " LLM_MODEL
export LLM_API_KEY
export LLM_BASE_URL="${LLM_BASE_URL:-https://api.openai.com/v1}"
export LLM_MODEL="${LLM_MODEL:-gpt-4o-mini}"
python3 serve_live.py
