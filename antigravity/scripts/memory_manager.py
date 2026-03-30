#!/usr/bin/env python3
import json
import os
import datetime
import sqlite3

# ==============================================================================
# THE AKASHIC RECORDS: LONG-TERM VECTOR MEMORY (MEMORY MANAGER)
# Muc tieu: Luu tru cac bai hoc sau khi giai quyet xong Bug tang kien truc.
# Dam bao he thong khong mac phai loi tuong tu trong tuong lai.
# ==============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "akashic_records.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        symptom TEXT,
        failed_attempts TEXT,
        real_root_cause TEXT,
        winning_solution TEXT,
        ai_lesson_learned TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_post_mortem(symptom, failed_attempts, real_root_cause, winning_solution, ai_lesson_learned):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    failed_attempts_str = json.dumps(failed_attempts)
    
    cursor.execute('''
    INSERT INTO memory_records (timestamp, symptom, failed_attempts, real_root_cause, winning_solution, ai_lesson_learned)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, symptom, failed_attempts_str, real_root_cause, winning_solution, ai_lesson_learned))
    
    conn.commit()
    conn.close()
    
    print("[SYSTEM] Post-mortem record saved to The Akashic Records successfully.")

def search_memory(keyword):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "%" + keyword + "%"
    cursor.execute('''
    SELECT timestamp, symptom, real_root_cause, winning_solution, ai_lesson_learned 
    FROM memory_records 
    WHERE symptom LIKE ? OR real_root_cause LIKE ? OR ai_lesson_learned LIKE ?
    ORDER BY timestamp DESC LIMIT 5
    ''', (query, query, query))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print("[SYSTEM] Khong tim thay ky uc nao lien quan den tu khoa:", keyword)
        return []
        
    print(f"\n[AKASHIC RECORDS] Tim thay {len(results)} bai hoc qua khu lien quan:")
    for row in results:
        print(f" - Thoi gian: {row[0]}")
        print(f" - Trieu chung: {row[1]}")
        print(f" - Nguyen nhan goc re: {row[2]}")
        print(f" - Bai hoc rut ra: {row[4]}\n")
        
    return results

if __name__ == "__main__":
    import sys
    
    init_db()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Tao data mau de kiem thu
        save_post_mortem(
            symptom="Server Node.js crash lien tuc luc 2h sang.",
            failed_attempts=["Tang RAM len 4GB (That bai)", "Cai them PM2 (That bai)"],
            real_root_cause="Cronjob hach toan dung vong lap dong bo nghen Event Loop.",
            winning_solution="Chuyen Cronjob sang Worker Thread. Bat dong bo hoan toan.",
            ai_lesson_learned="Lam viec voi Node.js va Data lon: Kiem tra Cronjob va vong lap truoc khi do loi do thieu RAM."
        )
        search_memory("Node.js")
    else:
        print("[SYSTEM] Memory Manager Initialized. Use 'search_memory(keyword)' or 'save_post_mortem(...)'.")
