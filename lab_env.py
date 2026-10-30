"""Nạp biến môi trường từ .env ở thư mục gốc repo.

Biến đã có trong môi trường tiến trình không bị ghi đè, nên có thể
`set GOOGLE_API_KEY=...` trước khi chạy. Không in giá trị bí mật.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_lab_env() -> Path | None:
    for candidate in (ROOT / ".env", ROOT / "experiments" / ".env"):
        if candidate.is_file():
            _apply(candidate)
            return candidate
    return None


def _apply(path: Path) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not name or name in os.environ:
            continue
        os.environ[name] = value.strip().strip('"').strip("'")


def aim_url() -> str:
    load_lab_env()
    return (
        os.environ.get("AIM_API_URL")
        or os.environ.get("AIM_URL")
        or "http://127.0.0.1:8080"
    ).rstrip("/")


def admin_credentials() -> tuple[str, str]:
    load_lab_env()
    email = os.environ.get("AIM_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("AIM_ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD")
    if email and password:
        return email.strip(), password
    setup = ROOT / "setup_creds.py"
    if setup.is_file():
        text = setup.read_text(encoding="utf-8")
        found_email = re.search(r"'email': '([^']+)'", text)
        found_password = re.search(r"'password': '([^']+)'", text)
        if found_email and found_password:
            return found_email.group(1), found_password.group(1)
    raise RuntimeError(
        "Thiếu AIM_ADMIN_EMAIL / AIM_ADMIN_PASSWORD. "
        "Sao chép .env.example thành .env rồi điền mật khẩu dashboard."
    )


def has_google_key() -> bool:
    load_lab_env()
    return bool(
        (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    )
