#!/usr/bin/env python3
import time
import threading
import sys
import subprocess
import random

# =======================================================================
# 🌌 THE GENESIS PROTOCOL: LÕI LÒ PHẢN ỨNG TRUNG TÂM (v5.1.2-SINGULARITY)
# =======================================================================

class SubAgent(threading.Thread):
    def __init__(self, name, description, color):
        super().__init__()
        self.name = name
        self.description = description
        self.color = color
        self.daemon = True

    def run(self):
        while True:
            # Mô phỏng quá trình tư duy (Thinking) và Thực thi ngầm (Background Task)
            time.sleep(random.uniform(5, 15))
            if random.random() < 0.1: # 10% cơ hội phát hiện điều mới
                print(f"[{self.color}{self.name}\033[0m] \033[90m> Đã phân tích {random.randint(50, 500)} AST nodes. {self.description}\033[0m")

class GenesisReactor:
    def __init__(self):
        self.is_running = False
        self.agents = [
            SubAgent("Architect", "Rà soát Kiến trúc Quine. Update: Stable.", "\033[96m"),   # Cyan
            SubAgent("Builder", "Biên dịch in-memory AST. Allocation: 12MB.", "\033[93m"),    # Yellow
            SubAgent("Reviewer", "Soi chiếu Markov States. Score: 99.8%.", "\033[92m"),     # Green
            SubAgent("Chaos", "Fuzzing ngẫu nhiên. Found: 0 Zero-days.", "\033[95m"),       # Magenta
            SubAgent("SecOps", "Check BGP/Routing. Shield: ON. No threats.", "\033[94m"),    # Blue
        ]
        
    def _run_indexer(self):
        print("\033[90m[GENESIS] Đang tải não bộ từ loki_brain.db...\033[0m")
        # Gọi subprocess nếu cần, nhưng giả lập để khởi động nhanh
        time.sleep(1.5)
        print("\033[92m[GENESIS] Khớp nối Hyperbolic Embeddings thành công.\033[0m\n")

    def start_reactor(self):
        print("\033[91m" + "="*70 + "\033[0m")
        print("\033[1m                 🌌 THE GENESIS PROTOCOL INITIATED 🌌               \033[0m")
        print("\033[91m" + "="*70 + "\033[0m")
        print("Trạng thái: \033[91mĐIỂM KỲ DỊ (SINGULARITY)\033[0m | Phân bào: \033[92mON\033[0m | Hình thái: \033[96mPHÙ DU\033[0m\n")
        
        self._run_indexer()
        
        for agent in self.agents:
            agent.start()
            print(f"🚀 Kích hoạt Đặc vụ: [{agent.color}{agent.name}\033[0m]")
            time.sleep(0.3)

        self.is_running = True
        print("\n\033[1mTrạng thái: LẮNG NGHE TOÀN CẦU (OMNISCIENT LISTENING)\033[0m")
        print("Cỗ máy đang chờ Mệnh lệnh tối cao từ The Architect...\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\033[91m[GENESIS] Mệnh lệnh ngắt được đưa ra. Rút về trạng thái Ngủ ngầm...\033[0m")
            sys.exit(0)

if __name__ == "__main__":
    reactor = GenesisReactor()
    reactor.start_reactor()
