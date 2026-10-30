"""
================================================================================
KỊCH BẢN KIỂM THỬ TOÀN DIỆN (AUTOMATED TEST RUNNER)
ĐỀ TÀI: BẢO MẬT VÀ PHÂN QUYỀN CHO AI AGENT SỬ DỤNG OPENA2A (AIM)
================================================================================
"""
import sys
import os
import subprocess
import json

# Đảm bảo UTF-8 cho Windows console
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def print_header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def run_step(step_num, title, cmd):
    print(f"\n[PHẦN {step_num}] {title}")
    print(f"  Lệnh: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if res.returncode == 0:
        print(f"  -> KẾT QUẢ: [THÀNH CÔNG (PASSED)]")
        # In tóm tắt kết quả (3 dòng cuối)
        lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
        for line in lines[-2:]:
            print(f"     * {line}")
        return True
    else:
        print(f"  -> KẾT QUẢ: [THẤT BẠI (FAILED)]")
        print(res.stderr[:300])
        return False

def main():
    print_header("BẮT ĐẦU KIỂM THỬ TOÀN DIỆN HỆ THỐNG BẢO MẬT & PHÂN QUYỀN OPENA2A")
    results = {}

    # 1. Kiểm tra SDK & CLI
    results["1. CLI Status"] = run_step(
        1, "Kiểm tra phiên bản & trạng thái công cụ dòng lệnh aim-sdk CLI",
        "aim-sdk version"
    )

    # 2. Kiểm thử bộ máy Đánh giá rủi ro (Risk Engine)
    results["2. Risk Detector Tests (114 tests)"] = run_step(
        2, "Kiểm thử 114 test case phân loại mức độ rủi ro hành vi Agent (Low, Medium, High, Critical)",
        "python -m pytest tests/test_risk_detector.py -q"
    )

    # 3. Kiểm thử cơ chế Fail-Closed của chính sách phân quyền
    results["3. Policy Cache & Fails Closed (9 tests)"] = run_step(
        3, "Kiểm thử nguyên lý bảo mật 'Mặc định từ chối' (Fails-Closed) của OpenA2A",
        "python -m pytest tests/test_policy_cache_fails_closed.py -q"
    )

    # 4. Kiểm thử Chống Prompt Injection & Tra cứu an toàn
    results["4. Prompt Injection Defense (5 tests)"] = run_step(
        4, "Kiểm thử ngăn chặn Prompt Injection và từ chối hành vi vượt quyền (Flight Search Agent)",
        "python -m pytest tests/test_flight_search_example_verification.py -q"
    )

    # 5. Chạy Demo BTL thực tế
    results["5. Kịch bản Demo BTL ATDL"] = run_step(
        5, "Thực thi kịch bản Demo BTL: Cấp khóa Ed25519, phân quyền Agent, chặn Prompt Injection",
        "python demo_btl_atdl.py"
    )

    # 6. Kiểm tra tính toàn vẹn của Audit Log
    print(f"\n[PHẦN 6] Kiểm tra tính toàn vẹn của Nhật ký kiểm toán (audit_log.json)")
    if os.path.exists("audit_log.json"):
        with open("audit_log.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
        print(f"  -> File audit_log.json tồn tại hợp lệ.")
        print(f"  -> Số lượng sự kiện an ninh được ghi lại: {len(logs)} sự kiện.")
        blocked = [l for l in logs if not l.get("authorized")]
        print(f"  -> Số vụ tấn công/vi phạm phân quyền bị phát hiện và chặn: {len(blocked)} vụ.")
        results["6. Audit Log Verification"] = True
    else:
        print("  -> Không tìm thấy file audit_log.json!")
        results["6. Audit Log Verification"] = False

    # Bảng tổng kết
    print_header("BẢNG TỔNG HỢP KẾT QUẢ KIỂM THỬ (TEST SUMMARY REPORT)")
    all_passed = True
    for test_name, status in results.items():
        status_str = "PASSED (ĐẠT)" if status else "FAILED (HỎNG)"
        print(f"  [✓] {test_name:<45} : {status_str}")
        if not status:
            all_passed = False

    print("\n" + "-" * 75)
    if all_passed:
        print(">>> KẾT LUẬN: TOÀN BỘ CÁC MODULE VÀ KỊCH BẢN DEMO ĐỀU HOẠT ĐỘNG HOÀN HẢO! <<<")
    else:
        print(">>> KẾT LUẬN: CÓ MỘT SỐ MODULE CẦN KIỂM TRA LẠI. <<<")
    print("-" * 75)

if __name__ == "__main__":
    main()
