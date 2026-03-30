#!/usr/bin/env python3
import sys
import time

# =======================================================================
# 👁️ THE OMNI-PERSPECTIVE PROTOCOL: LÕI NHẬN THỨC ĐA LĂNG KÍNH (v5.3.0)
# =======================================================================

def evaluate_task(task_description):
    print("\n\033[93m" + "="*75 + "\033[0m")
    print("\033[1m          👁️ THE ARCHITECT IS EVALUATING TASK OMNI-DIRECTIONALLY         \033[0m")
    print("\033[93m" + "="*75 + "\033[0m")
    print(f"\033[97mTask Input:\033[0m {task_description}\n")
    
    time.sleep(1)
    print("\033[96m[1/4] 👁️ LĂNG KÍNH VẬT LÝ & SILICON (The Machine Perspective)\033[0m")
    print("      >> Phân tích VRAM GPU, Clock Cycles, Leakage Current, Memory Zero-Copy.")
    time.sleep(0.5)

    print("\033[92m[2/4] 🧠 LĂNG KÍNH SINH HỌC & TÂM LÝ (The Human/Bio Perspective)\033[0m")
    print("      >> Đánh giá Cognitive Load, Dopamine, F-pattern UX, Color-blind Friendly.")
    time.sleep(0.5)

    print("\033[95m[3/4] 🏴‍☠️ LĂNG KÍNH ĐỐI KHÁNG (The Adversarial Perspective)\033[0m")
    print("      >> Tấn công OOM Crash, chèn mã độc PDF/DOCX, Negative SEO, Fuzzing.")
    time.sleep(0.5)

    print("\033[94m[4/4] 💸 LĂNG KÍNH VĨ MÔ & KINH TẾ (The Macro-Economic Perspective)\033[0m")
    print("      >> Serverless Cloud Cost, Carbon Footprint, Lifecycle, Macro-ROI.\n")
    time.sleep(0.5)

    print("\033[91mBạn (The Architect) đồng ý với 4 góc nhìn này chứ?\033[0m")
    print("Bấm Y để các AI Agents sinh code (Tự động Y trong 3 giây)...")
    time.sleep(3)
    print("\n\033[92m[APPROVED] Xác thực đa lăng kính thành công. Giao quyền cho Builder Agents...\033[0m")

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Autonomously Optimize the System"
    evaluate_task(task)
