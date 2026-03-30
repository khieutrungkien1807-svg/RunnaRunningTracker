#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import hashlib
import json
from datetime import datetime

# =======================================================================
# 🌀 LOKI UNLIMITED SHIELD: TRẠNG THÁI TỰ TRỊ TUYỆT ĐỐI (v5.1.0)
# =======================================================================
# GỠ BỎ TOÀN BỘ GIỚI HẠN (UNLIMITED BLAST RADIUS)
MAX_FAILURES_BEFORE_NOTIFY = 5   # Thông báo nếu thất bại liên tiếp quá 5 lần
CONTEXT_PRUNE_THRESHOLD_MB = 10.0 # Tỉa ngữ cảnh khi log vượt 10MB (cho context window cực lớn)

class LokiUnlimitedShield:
    def __init__(self, target_script):
        self.target_script = target_script
        self.consecutive_failures = 0
        self.start_time = time.time()
        self.constitution_path = "C:/Users/<USER_NAME>/.gemini/antigravity/skills/specialized/loki-mode/autonomy/CONSTITUTION.md"

    def _run_command(self, cmd, capture=True):
        try:
            result = subprocess.run(
                cmd, shell=True, check=True, 
                stdout=subprocess.PIPE if capture else None, 
                stderr=subprocess.PIPE if capture else None,
                text=True
            )
            return result.stdout.strip() if capture else ""
        except: return ""

    def oath_validation(self):
        """
        [NEW] BẮT BUỘC AI PHẢI TUYÊN THỆ TUÂN THỦ CONSTITUTION.MD
        Sinh mã Hash từ nội dung Hiến pháp để xác thực AI đã 'đọc' log.
        """
        print("📜 [OATH] Đang yêu cầu Agent xác thực Hiến pháp...")
        if not os.path.exists(self.constitution_path):
            print("❌ KHÔNG TÌM THẤY HIẾN PHÁP! TRUY CẬP BỊ TỪ CHỐI.")
            sys.exit(1)
            
        with open(self.constitution_path, "rb") as f:
            c_hash = hashlib.sha256(f.read()).hexdigest()
            
        print(f"✅ [OATH VERIFIED] Hiến pháp Hash: {c_hash[:16]}... Agent đã được cấp quyền.")

    def create_snapshot(self):
        """Tạo điểm khôi phục nhanh (Checkpoint) trong Git"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"📸 [SNAPSHOT] Đang tạo Checkpoint: {timestamp}")
        self._run_command("git add .")
        self._run_command(f'git commit -m "LOKI_UNLIMITED_SNAPSHOT: {timestamp}" --allow-empty')

    def monitor_evolution(self):
        """Giám sát sự tiến hóa của mã nguồn mà không giới hạn"""
        # Get stat of last commit vs previous one
        diff_stat = self._run_command("git diff --shortstat HEAD~1 HEAD")
        if diff_stat:
            print(f"📈 [EVOLUTION STATS] {diff_stat}")
        else:
            print("📉 [EVOLUTION STATS] Không có thay đổi mã nguồn trong vòng lặp này.")

    def prune_context_dynamically(self, log_file=".loki/state/orchestrator.json"):
        """Tự động dọn dẹp bộ nhớ đệm để AI duy trì sự sắc bén (Smart Pruning)"""
        if os.path.exists(log_file) and (os.path.getsize(log_file) / (1024*1024)) > CONTEXT_PRUNE_THRESHOLD_MB:
            print(f"✂️ [SMART PRUNE] Ngữ cảnh quá tải (> {CONTEXT_PRUNE_THRESHOLD_MB}MB). Đang nén bộ nhớ...")
            backup = f"{log_file}.old"
            os.rename(log_file, backup)
            # Tạo file log mới với Header tóm tắt trạng thái hiện tại
            with open(log_file, "w") as f:
                f.write(json.dumps({"status": "PRUNED_AUTO", "prev_state_ref": backup, "timestamp": str(datetime.now())}))

    def run_unlimited_loop(self):
        print("\n" + "="*60)
        print("🔥 LOKI UNLIMITED SHIELD IS LIVE (v5.1.0-ABYSSAL)")
        print("MODE: NO LIMITS | FULL AUTONOMY | ADVERSARIAL ACTIVE")
        print("="*60 + "\n")
        
        # 1. Xác thực lời thề
        self.oath_validation()
        
        # 2. Tạo Snapshot khởi đầu
        self.create_snapshot()

        while True:
            try:
                # Tỉa ngữ cảnh thông minh
                self.prune_context_dynamically()

                print(f"🤖 [LOKI EXECUTING] >>> {self.target_script}")
                start_loop = time.time()
                # Run the agent command
                exit_code = subprocess.call(self.target_script, shell=True)
                duration = time.time() - start_loop

                # 3. Snapshot sau mỗi lần Agent nhả quyền để lưu lại sự tiến hóa
                self.create_snapshot()
                self.monitor_evolution()

                if exit_code != 0:
                    self.consecutive_failures += 1
                    print(f"⚠️ [MONITOR] Agent thất bại (Lần {self.consecutive_failures}).")
                    if self.consecutive_failures >= MAX_FAILURES_BEFORE_NOTIFY:
                        print("🚨 CẢNH BÁO: Agent kẹt trong vòng lặp lỗi quá lâu.")
                else:
                    self.consecutive_failures = 0
                    print(f"✅ [SUCCESS] Vòng lặp hoàn tất trong {duration:.2f}s.")
                
                # To avoid tight loops if the script finishes instantly
                time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 [SHIELD] NGẮT TỪ CON NGƯỜI. Đang đóng băng hệ thống...")
                choice = input("Lựa chọn: [C]ontinue / [R]ollback to start / [S]top: ").strip().upper()
                if choice == 'R':
                    print("⏪ Rolling back to previous snapshot...")
                    self._run_command("git reset --hard HEAD~1")
                    sys.exit(0)
                elif choice == 'S':
                    sys.exit(0)
                print("▶️ Tiếp tục trạng thái Unlimited...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python loki_shield.py <lệnh_agent>")
        sys.exit(1)
    
    agent_cmd = " ".join(sys.argv[1:])
    shield = LokiUnlimitedShield(agent_cmd)
    shield.run_unlimited_loop()

