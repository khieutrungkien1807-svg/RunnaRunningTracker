#!/usr/bin/env python3
import time
import sys

# ==============================================================================
# THE TRIBUNAL SWARM (MULTI-AGENT ORCHESTRATOR)
# Co che lap "Hoi dong": Builder -> Breaker -> Judge
# Chong ao giac, giam code rac thong qua khau kiem tran cheo (Cross-check).
# ==============================================================================

class AgentBuilder:
    def __init__(self, task):
        self.task = task
        self.code_draft = ""
        
    def execute(self):
        print(f"[THE BUILDER] Dang ket xuat giai phap cho tac vu: '{self.task}'")
        time.sleep(1)
        # Gia lap viec sinh code
        if "sql" in self.task.lower() or "database" in self.task.lower():
            self.code_draft = "SELECT * FROM users WHERE id = " + "{user_input}"
        else:
            self.code_draft = "def auto_mailer():\n    print('Sending emails async')\n"
        print("[THE BUILDER] Da sinh code Base version 1.0.")
        return self.code_draft

class AgentBreaker:
    def __init__(self, draft):
        self.draft = draft
        self.feedback = []
        
    def execute(self):
        print("[THE BREAKER - RED TEAM] Dang quet lo hong va logic...")
        time.sleep(1)
        # Quet lo hong bao mat & toi uu hoa
        if "user_input" in self.draft:
            self.feedback.append("[CRITICAL] Lo hong SQL Injection truc tiep qua con tro 'user_input'.")
            self.feedback.append("[REQUIREMENT] Phai dung Parameterized Query/Prepared Statement.")
            print(" -> Breaker Reject: Ma nguon khong dat chuan an toan.")
            return False, self.feedback
        
        print(" -> Breaker Accept: Khong tim thay lo hong rui ro.")
        return True, self.feedback

class AgentJudge:
    def __init__(self, original_task, final_code, breaker_logs):
        self.original_task = original_task
        self.final_code = final_code
        self.breaker_logs = breaker_logs
        
    def execute(self):
        print("[THE JUDGE - CTO] Tong hop ket luan tu Hoi Dong...")
        time.sleep(1)
        if not self.breaker_logs:
            print("[THE JUDGE] Phe duyet giai phap. Ma nguon sach va an toan.")
            return "[APPROVED] " + self.final_code
        else:
            print("[THE JUDGE] Tu choi ban nhap ban dau. Yeu cau Builder phai sua tuong ung voi chi thi tu Breaker.")
            return "[REJECTED_NEEDS_REVISION]"

def simulate_tribunal(task):
    print("===========================================================================")
    print("                    HOI DONG THANH TRA (THE TRIBUNAL)                     ")
    print("===========================================================================")
    
    # 1. Builder
    builder = AgentBuilder(task)
    draft = builder.execute()
    
    # 2. Breaker & Repetitive Mutation loop
    breaker = AgentBreaker(draft)
    passed, logs = breaker.execute()
    
    attempts = 1
    max_retries = 3
    
    while not passed and attempts < max_retries:
        print(f"\n[SYSTEM] Vong {attempts}: Builder dang thuc hien ban va code...")
        time.sleep(1)
        # Gia lap Builder sua code sau gop y
        draft = "SELECT * FROM users WHERE id = ?"
        breaker = AgentBreaker(draft)
        passed, logs = breaker.execute()
        attempts += 1
        
    # 3. Judge
    judge = AgentJudge(task, draft, logs)
    final_output = judge.execute()
    
    print("\n---------------------- FINAL OUTPUT CHI THI -------------------------------")
    print(final_output)
    print("===========================================================================\n")

if __name__ == "__main__":
    task_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Viet lenh truy van database can ho cho quan tri vien."
    simulate_tribunal(task_input)
