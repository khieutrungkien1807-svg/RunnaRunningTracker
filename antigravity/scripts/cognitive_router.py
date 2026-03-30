#!/usr/bin/env python3
import sys
import json
import os

# ==============================================================================
# OMNI-EXPERT COGNITIVE ROUTER (ZERO-FLUFF PROTOCOL)
# Kien truc C-Level / CTO: Dung lai Isolate -> Kiem tra cheo da nganh.
# ==============================================================================

def load_supreme_db():
    db_path = os.path.join(os.path.dirname(__file__), \"supreme_database_v7.json\")
    if os.path.exists(db_path):
        with open(db_path, \"r\", encoding=\"utf-8\") as f:
            return json.load(f)
    return {}

def analyze_input(user_input):
    print(\"\\n========================== OMNI-EXPERT PIPELINE ======================\")
    print(\"Input:\", user_input)
    print(\"----------------------------------------------------------------------\")
    
    db = load_supreme_db()
    
    # 1. STOP & ISOLATE (Bypass the obvious)
    print(\"[1] STOP & ISOLATE:\")
    if \"cham\" in user_input.lower() or \"quay\" in user_input.lower() or \"slow\" in user_input.lower() or \"outage\" in user_input.lower():
        print(\"YEU CAU DATA: Chay F12 Network tab, xem loi la TTFB hay Content Download?\")
        print(\"              Kiem tra chi so Infrastructure truoc khi dua ra code.\")
        if \"server_outage_or_slow\" in db.get(\"system_knowledge_graph\", {}):
            checks = db[\"system_knowledge_graph\"][\"server_outage_or_slow\"][\"level_1_checks\"]
            print(\"-> Lenh yeu cau chay ngay:\", \", \".join(checks))
    else:
        print(\"Da co lap module can xu ly. Bo qua cac gia thuyet khong can thiet.\")

    # 2. CROSS-DISCIPLINARY CHECK (Goc nhin CTO)
    print(\"\\n[2] CROSS-DISCIPLINARY CHECK (Kiem tra cheo):\")
    if \"mail\" in user_input.lower() or \"gui\" in user_input.lower():
        print(\"[Dev] Sinh he thong Queue (Celery/RabbitMQ) xu ly bat dong bo.\")
        print(\"[Security] Canh bao cau hinh DNS (SPF, DKIM, DMARC) de khong vao Spam.\")
        print(\"[Business] De xuat gan Pixel 1x1 tracking ty le mo mail.\")
    else:
        print(\"Ap dung Nguyen Ly Goc (First Principles): Kiem tra [User -> Network -> Logic -> Hardware -> Sec]\")

    # 3. YOUTH & YAML FORMAT CHECK (Output Constraint)
    print(\"\\n[3] GIAI PHAP PHAU THUAT (YAML OUTPUT):\")
    yaml_out = f\"\"\"
root_cause_hypotheses:
  - Yeu cau cung cap them data tu Metrics/Log. Khong du doan mu quang.
diag_required:
  - \"{checks[0] if 'checks' in locals() and checks else 'Chay kiem tra tong the he thong mien nhiem.'}\"
solution_plan:
  - [Action 1]: Ap dung O(1) Architecture.
  - [Action 2]: Toi uu Cloud Cost & SEO.
\"\"\"
    print(yaml_out.strip())
    print(\"======================================================================\\n\")

if __name__ == \"__main__\":
    test_input = \" \".join(sys.argv[1:]) if len(sys.argv) > 1 else \"App web load cham qua, quay mong mong!\"
    analyze_input(test_input)
