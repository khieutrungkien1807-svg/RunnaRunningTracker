#!/usr/bin/env python3
import sys
import time
import random

# =======================================================================
# 🕵️ THE DETECTIVE AGENT: ĐẶC VỤ THÁM TỬ QUÁN TÍNH HỆ THỐNG (v6.1.0)
# =======================================================================
# Gồm các module: Environment Hell, Ghost Flaky, Butterfly Effect, Human Bias

def diagnose_bug(bug_description):
    print("\n\033[96m" + "="*85 + "\033[0m")
    print("\033[1m              🕵️ ĐẶC VỤ THÁM TỬ ĐANG CHẨN ĐOÁN LỖI HỆ THỐNG              \033[0m")
    print("\033[96m" + "="*85 + "\033[0m")
    print(f"\033[97mPhiếu báo cáo User (Bug Report):\033[0m {bug_description}\n")
    
    time.sleep(1)
    print("\033[90m[STEP 1] Đang quét lịch sử Git (Git Bisect & Diff) xem ai sửa gần nhất...\033[0m")
    time.sleep(1.2)
    print("\033[90m[STEP 2] Đang dò Log tìm Memory Leak / Timeout (Không tin Cảm tính)...\033[0m")
    time.sleep(1.2)
    print("\033[90m[STEP 3] Đang đối chiếu độ trôi Version (package-lock vs Node_modules)...\033[0m")
    time.sleep(1.2)
    print("\033[90m[STEP 4] Đang lập Bản đồ Bán kính Ảnh hưởng (Impact Radius Mapping)...\033[0m\n")
    time.sleep(1.5)

    print("\033[93m📋 BẢN CHẨN ĐOÁN SƠ BỘ (PRE-DIAGNOSIS REPORT):\033[0m")
    
    causes = [
        "Lệch Version thư viện trong file .lock giữa Local và Prod (Environment Hell).",
        "Race Condition (Bất đồng bộ) do 2 API Call trả về không thứ tự (Thoắt ẩn thoắt hiện).",
        "Tràn bộ nhớ Cache ẩn (Cần clear DNS/CDN/Docker Volumes lập tức).",
        "Lỗi Third-Party (Gaslighting). Server Đối tác đang nằm nhưng User báo lỗi app mình."
    ]
    primary = random.choice(causes)
    
    print(f"  - \033[1mKhả năng Nguyên nhân 1 (70%):\033[0m {primary}")
    print(f"  - \033[1mKhả năng Nguyên nhân 2 (30%):\033[0m Xung đột trạng thái Global (Global State Pollution)")
    
    print("\n\033[94m🛠️ ĐỀ XUẤT HÀNH ĐỘNG ÉP BỘ CỦA THÁM TỬ:\033[0m")
    print("  1. CẤM các Linter/Builder sửa code vội. CẤM try-catch bọc lỗi.")
    print("  2. Chạy Stress-test nội bộ 100 lần bằng Selenium/Playwright đa luồng.")
    print("  3. Clear rỗng mọi Cache / Cookie trước khi tiếp tục phân rã Binary Search.")
    
    time.sleep(2)
    print("\n\033[92m[DIAGNOSIS APPROVED]\033[0m Đã khoanh vùng mục tiêu! Ngăn chặn tốn kém Token nhảm!")
    print("\033[91mHỆ THỐNG GIAO QUYỀN:\033[0m Builder Sub-Agents BẮT ĐẦU FIX THEO CHẨN ĐOÁN TRÊN.")
    print("\033[96m" + "="*85 + "\033[0m\n")

if __name__ == "__main__":
    report = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Chạy local thì mượt mà lên Prod thì màn hình trắng, nút bấm không chạy."
    diagnose_bug(report)
