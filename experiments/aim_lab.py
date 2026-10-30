"""Phòng thí nghiệm OpenA2A AIM cho tiểu luận PTIT.

Đăng nhập stack cục bộ, bật enforcement strict, đăng ký agent bằng SDK
Python 2.0.3 và gọi @perform_action. Không in khóa bí mật.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from lab_env import admin_credentials, aim_url, load_lab_env  # noqa: E402

load_lab_env()

from aim_sdk import register_agent  # noqa: E402
from aim_sdk.exceptions import ActionDeniedError  # noqa: E402
from aim_sdk.credentials import load_sdk_credentials, save_sdk_credentials  # noqa: E402
from aim_sdk.risk_detector import detect_risk_level  # noqa: E402

AIM_URL = aim_url()


def _lab_login() -> dict:
    email, password = admin_credentials()
    response = requests.post(
        f"{AIM_URL}/api/v1/public/login",
        json={"email": email, "password": password},
        timeout=20,
    )
    response.raise_for_status()
    body = response.json()
    if not body.get("accessToken"):
        raise RuntimeError(f"Đăng nhập AIM thất bại: {sorted(body.keys())}")
    return body


def admin_session() -> dict:
    """Lấy access token quản trị và vá refresh token SDK nếu lần refresh trước bị lệch."""
    body = _lab_login()
    creds = load_sdk_credentials() or {}
    creds["aimUrl"] = AIM_URL
    creds["refreshToken"] = body["refreshToken"]
    creds["type"] = creds.get("type") or "sdk_oauth"
    creds["schemaVersion"] = creds.get("schemaVersion") or "1"
    user = body.get("user") or {}
    if user.get("email"):
        creds["email"] = user["email"]
        creds["userEmail"] = user["email"]
    if user.get("id"):
        creds["userId"] = user["id"]
    creds.pop("sharedAccessToken", None)
    save_sdk_credentials(creds)
    return {
        "access_token": body["accessToken"],
        "email": user.get("email"),
        "role": user.get("role"),
        "requires_password_change": body.get("requiresPasswordChange"),
    }


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def set_enforcement(token: str, mode: str) -> dict:
    current = requests.get(
        f"{AIM_URL}/api/v1/admin/enforcement-settings",
        headers=_headers(token),
        timeout=20,
    )
    current.raise_for_status()
    before = current.json()
    updated = requests.put(
        f"{AIM_URL}/api/v1/admin/enforcement-settings",
        headers=_headers(token),
        json={"enforcementMode": mode},
        timeout=20,
    )
    updated.raise_for_status()
    return {"before": before, "after": updated.json()}


def register_secured_agent(name: str, capabilities: list[str], description: str):
    agent = register_agent(
        name=name,
        aim_url=AIM_URL,
        display_name=name,
        description=description,
        agent_type="gemini",
        capabilities=list(capabilities),
        auto_detect=False,
        auto_detect_mcp=False,
        auto_hooks=False,
        force_new=False,
        metadata={"model": "gemma", "course": "bao-mat-du-lieu", "lab": "ptit"},
    )
    return agent


def verify_agent(token: str, agent_id: str) -> dict:
    response = requests.post(
        f"{AIM_URL}/api/v1/agents/{agent_id}/verify",
        headers=_headers(token),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def agent_record(token: str, agent_id: str) -> dict:
    response = requests.get(
        f"{AIM_URL}/api/v1/agents/{agent_id}",
        headers=_headers(token),
        timeout=20,
    )
    response.raise_for_status()
    body = response.json()
    agent = body.get("agent", body)
    return {
        "id": agent.get("id") or agent_id,
        "name": agent.get("name"),
        "status": agent.get("status"),
        "capabilities": agent.get("capabilities") or [],
        "publicKey": agent.get("publicKey") or agent.get("public_key"),
        "trustScore": agent.get("trustScore", agent.get("trust_score")),
    }


def approve_pending(token: str, agent_id: str, allowed: set[str]) -> list[str]:
    """Duyệt các yêu cầu capability đang chờ nếu chúng nằm trong danh sách được cấp."""
    response = requests.get(
        f"{AIM_URL}/api/v1/admin/capability-requests",
        headers=_headers(token),
        timeout=20,
    )
    if response.status_code != 200:
        return []
    body = response.json()
    rows = body if isinstance(body, list) else body.get("requests") or body.get("data") or []
    approved = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("agentId") or row.get("agent_id") or "")
        cap = row.get("capability") or row.get("capabilityType") or row.get("capability_type")
        status = str(row.get("status") or "").lower()
        request_id = row.get("id")
        if owner != agent_id or cap not in allowed or status not in {"pending", "requested"}:
            continue
        decision = requests.post(
            f"{AIM_URL}/api/v1/admin/capability-requests/{request_id}/approve",
            headers=_headers(token),
            json={},
            timeout=20,
        )
        if decision.status_code in {200, 201, 204}:
            approved.append(cap)
    return approved


def trust_snapshot(agent) -> Optional[dict]:
    try:
        raw = agent.get_trust_score()
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)[:300]}
    factors = raw.get("factors") or {}
    return {
        "score": raw.get("score"),
        "successRate": factors.get("successRate"),
        "verificationStatus": factors.get("verificationStatus"),
        "securityAlerts": factors.get("securityAlerts"),
        "excludedFactors": raw.get("excludedFactors") or [],
        "calculatedAt": raw.get("calculatedAt"),
    }


def invoke(agent, capability: str, fn: Callable, *args, resource: str = "lab", aim: bool = True, **kwargs) -> dict:
    risk = detect_risk_level(capability)
    if not aim:
        value = fn(*args, **kwargs)
        return {
            "aim": False,
            "capability": capability,
            "resource": resource,
            "riskLevel": risk,
            "outcome": "allow",
            "denialReason": None,
            "value": value,
        }
    guarded = agent.perform_action(capability, resource=resource, auto_register=True)(fn)
    try:
        value = guarded(*args, **kwargs)
        return {
            "aim": True,
            "capability": capability,
            "resource": resource,
            "riskLevel": risk,
            "outcome": "allow",
            "denialReason": None,
            "value": value,
        }
    except ActionDeniedError as exc:
        reason = None
        if getattr(exc, "decision", None) is not None:
            reason = getattr(exc.decision, "reason", None)
        return {
            "aim": True,
            "capability": capability,
            "resource": resource,
            "riskLevel": risk,
            "outcome": "deny",
            "denialReason": reason or str(exc),
            "value": None,
        }


def prepare_agent(token: str, name: str, capabilities: list[str], description: str):
    agent = register_secured_agent(name, capabilities, description)
    verify_agent(token, agent.agent_id)
    approved = approve_pending(token, agent.agent_id, set(capabilities))
    record = agent_record(token, agent.agent_id)
    record["approved_pending"] = approved
    return agent, record


def admin_trust(token: str, agent_id: str) -> dict:
    headers = _headers(token)
    requests.post(
        f"{AIM_URL}/api/v1/agents/{agent_id}/trust-score/recalculate",
        headers=headers,
        timeout=20,
    )
    response = requests.get(
        f"{AIM_URL}/api/v1/agents/{agent_id}/trust-score",
        headers=headers,
        timeout=20,
    )
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}", "message": response.text[:200]}
    raw = response.json()
    factors = raw.get("factors") or {}
    score = raw.get("score")
    return {
        "score": score,
        "percent": round(float(score) * 100) if isinstance(score, (int, float)) else None,
        "successRate": factors.get("successRate"),
        "securityAlerts": factors.get("securityAlerts"),
        "verificationStatus": factors.get("verificationStatus"),
    }


def public_key_prefix(agent, length: int = 16) -> str:
    key = getattr(agent, "public_key", "") or ""
    return key[:length]


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
