"""Kiểm tra máy đã sẵn sàng chạy demo AIM hay chưa. Không in khóa hay mật khẩu."""

from __future__ import annotations

import os
import sys

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lab_env import admin_credentials, aim_url, has_google_key, load_lab_env  # noqa: E402


def main() -> int:
    load_lab_env()
    url = aim_url()
    print("AIM_API_URL =", url)
    print("GOOGLE_API_KEY set =", has_google_key())
    try:
        email, _password = admin_credentials()
        print("AIM_ADMIN_EMAIL =", email)
        print("AIM_ADMIN_PASSWORD set = True")
    except RuntimeError as exc:
        print("admin credentials:", exc)
        return 1
    try:
        health = requests.get(f"{url}/health", timeout=5)
        print("GET /health", health.status_code, health.text[:120].replace("\n", " "))
    except requests.RequestException as exc:
        print("GET /health FAILED:", type(exc).__name__)
        print("Chưa bật stack. Chạy: docker compose -f docker-compose.quickstart.yml up -d")
        return 1
    try:
        login = requests.post(
            f"{url}/api/v1/public/login",
            json={"email": email, "password": admin_credentials()[1]},
            timeout=20,
        )
        print("POST /login", login.status_code, "accessToken" if login.ok and login.json().get("accessToken") else login.text[:160])
        if not login.ok:
            return 1
    except requests.RequestException as exc:
        print("POST /login FAILED:", type(exc).__name__)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
