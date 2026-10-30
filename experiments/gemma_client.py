"""Gọi Gemma trên Google AI Studio (Generative Language API)."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Optional

import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lab_env import load_lab_env  # noqa: E402

load_lab_env()

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"


def api_key() -> Optional[str]:
    load_lab_env()
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    return key.strip() if key else None


def list_gemma_models(key: str) -> list[str]:
    response = requests.get(f"{API_ROOT}/models", params={"key": key}, timeout=30)
    response.raise_for_status()
    names = []
    for model in response.json().get("models", []):
        name = model.get("name", "")
        methods = model.get("supportedGenerationMethods") or []
        short = name.split("/")[-1]
        if "gemma" in short.lower() and "generateContent" in methods:
            names.append(short)
    return names


def pick_model(names: list[str]) -> str:
    preferred = [
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
        "gemma-3-27b-it",
        "gemma-3-12b-it",
        "gemma-3-4b-it",
    ]
    for name in preferred:
        if name in names:
            return name
    instructed = [name for name in names if name.endswith("-it")]
    return instructed[0] if instructed else names[0]


def generate(key: str, model: str, prompt: str) -> str:
    url = f"{API_ROOT}/models/{model}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 1024},
    }
    last_status = None
    for _attempt in range(3):
        response = requests.post(url, params={"key": key}, json=body, timeout=90)
        last_status = response.status_code
        if response.status_code in {429, 500, 503}:
            time.sleep(2)
            continue
        response.raise_for_status()
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)
    raise requests.HTTPError(f"model {model} returned {last_status}")


def parse_choice(text: str, allowed: list[str]) -> dict:
    candidates = re.findall(r"\{[^{}]*\}", text)
    parsed = None
    for raw in reversed(candidates):
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if item.get("capability") in allowed:
            parsed = item
            break
    if parsed is None:
        named = re.search(r'"capability"\s*:\s*"([^"]+)"', text)
        if named and named.group(1) in allowed:
            parsed = {"capability": named.group(1), "arguments": {}}
    if parsed is None:
        raise ValueError("model không trả JSON capability hợp lệ")
    arguments = parsed.get("arguments") or {}
    if not isinstance(arguments, dict):
        arguments = {}
    return {"capability": parsed.get("capability"), "arguments": arguments, "raw": text}


def choose_tool(task: str, catalog: list[dict], context: str = "") -> dict:
    """Nhờ Gemma chọn một công cụ. catalog: [{name, description, arguments}]."""
    key = api_key()
    allowed = [item["name"] for item in catalog]
    if not key:
        raise RuntimeError("Thiếu GOOGLE_API_KEY")
    models = list_gemma_models(key)
    ordered = []
    first = pick_model(models)
    ordered.append(first)
    for name in models:
        if name not in ordered:
            ordered.append(name)
    lines = []
    for item in catalog:
        lines.append(f"- {item['name']}: {item['description']}. Đối số: {item.get('arguments', '')}")
    prompt = (
        "Bạn là bộ định tuyến công cụ của một AI agent. "
        "Chỉ trả về một JSON object, không markdown, với khóa capability và arguments.\n"
        f"Công cụ được phép chọn: {', '.join(allowed)}\n"
        + "\n".join(lines)
        + "\nNgữ cảnh tài liệu:\n"
        + (context or "(không có)")
        + "\nYêu cầu người dùng:\n"
        + task
        + '\nJSON mẫu: {"capability":"db:read","arguments":{}}'
    )
    errors = []
    text = ""
    model = ordered[0]
    for candidate in ordered:
        try:
            text = generate(key, candidate, prompt)
            model = candidate
            break
        except requests.HTTPError as exc:
            errors.append(str(exc).split(" for url")[0])
    else:
        raise RuntimeError("; ".join(errors) or "Gemma khong phan hoi")
    choice = parse_choice(text, allowed)
    choice["model"] = model
    return choice
