# app/server/llm_router.py
import os, json, requests, yaml
from typing import Dict, Any, Optional

CONFIG_PATH = "app/config/models.yaml"

def load_cfg() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _count_chars(text: str) -> int:
    return len(text or "")

def call_openai(prompt: str, system: Optional[str]) -> str:
    cfg = load_cfg()["providers"]["openai"]
    if not cfg.get("enabled"): raise RuntimeError("openai disabled")
    api_key = os.getenv(cfg["api_key_env"], "")
    if not api_key: raise RuntimeError("OPENAI_API_KEY missing")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    messages = []
    if system: messages.append({"role":"system","content":system})
    messages.append({"role":"user","content":prompt})
    data = {"model": cfg["model"], "messages": messages, "temperature": 0}
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def call_anthropic(prompt: str, system: Optional[str]) -> str:
    # uses REST to avoid extra deps
    cfg = load_cfg()["providers"]["anthropic"]
    if not cfg.get("enabled"): raise RuntimeError("anthropic disabled")
    api_key = os.getenv(cfg["api_key_env"], "")
    if not api_key: raise RuntimeError("ANTHROPIC_API_KEY missing")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": cfg["model"],
        "max_tokens": 1200,
        "system": system or "",
        "messages": [{"role":"user","content": prompt}],
        "temperature": 0
    }
    r = requests.post(url, headers=headers, json=data, timeout=120)
    r.raise_for_status()

    # Extract the first text segment from the Anthropic response
    body = r.json()
    content = body.get("content") or []
    for part in content:
        if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
            return part["text"]
    # Fallback: try older/alternative structures
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            return first.get("text", "")
    return json.dumps(body)

def run(prompt: str, system: Optional[str] = None) -> str:
    """Route a prompt to the configured provider and return the response text.

    Falls back to echoing a short summary if all providers are disabled or error.
    """
    cfg = load_cfg()
    providers = cfg.get("providers", {})
    last_error = None
    # Try OpenAI first if enabled
    try:
        if providers.get("openai", {}).get("enabled"):
            return call_openai(prompt, system)
    except Exception as e:
        last_error = e
    # Then Anthropic
    try:
        if providers.get("anthropic", {}).get("enabled"):
            return call_anthropic(prompt, system)
    except Exception as e:
        last_error = e
    # Minimal deterministic fallback
    summary = prompt[:200].replace("\n", " ")
    prefix = "[fallback-without-llm]"
    if system:
        return f"{prefix} system={system[:80]} prompt={summary}"
    return f"{prefix} prompt={summary}"
