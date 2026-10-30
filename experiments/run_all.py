"""Chạy ba demo và ghi kết quả JSON. Không in khóa hay token."""

from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

from aim_lab import (  # noqa: E402
    AIM_URL,
    admin_session,
    prepare_agent,
    set_enforcement,
    stamp,
    write_json,
)
from demo1_crud import run as run_crud  # noqa: E402
from demo2_rag import run as run_rag  # noqa: E402
from demo3_multiagent import run as run_multi  # noqa: E402

RESULTS = os.path.join(os.path.dirname(__file__), "results")


def main() -> None:
    session = admin_session()
    enforcement = set_enforcement(session["access_token"], "strict")
    suffix = stamp()
    identities = {}

    crud_agent, identities["crud"] = prepare_agent(
        session["access_token"],
        f"ptit-crud-{suffix}",
        ["db:read"],
        "Agent CRUD chi duoc doc du lieu",
    )
    rag_agent, identities["rag"] = prepare_agent(
        session["access_token"],
        f"ptit-rag-{suffix}",
        ["rag:read"],
        "Agent RAG chi duoc doc tai lieu",
    )
    coordinator, identities["coordinator"] = prepare_agent(
        session["access_token"],
        f"ptit-coordinator-{suffix}",
        ["a2a:delegate"],
        "Coordinator ky yeu cau A2A",
    )
    summary_worker, identities["summary_worker"] = prepare_agent(
        session["access_token"],
        f"ptit-summary-{suffix}",
        ["doc:summarize"],
        "Worker tom tat tai lieu",
    )
    grade_worker, identities["grade_worker"] = prepare_agent(
        session["access_token"],
        f"ptit-grade-{suffix}",
        ["grade:read"],
        "Worker chi duoc doc diem",
    )

    report = {
        "stamp": suffix,
        "aim_url": AIM_URL,
        "sdk": "aim-sdk-python 2.0.3",
        "enforcement": {
            "before": enforcement["before"].get("enforcementMode") or enforcement["before"],
            "after": enforcement["after"].get("enforcementMode") or enforcement["after"],
        },
        "admin_role": session.get("role"),
        "identities": identities,
        "demos": {
            "crud": run_crud(crud_agent),
            "rag": run_rag(rag_agent),
            "multi": run_multi(coordinator, summary_worker, grade_worker),
        },
    }
    out = os.path.join(RESULTS, f"run_{suffix}.json")
    latest = os.path.join(RESULTS, "latest.json")
    write_json(out, report)
    write_json(latest, report)
    print("WROTE", out)
    print("ENFORCEMENT", report["enforcement"])
    for key, record in identities.items():
        print(key, record.get("status"), record.get("capabilities"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
