#!/usr/bin/env python3
import json
import os
from pathlib import Path

# ==============================================================================
# 🧠 TRAINING DATA EXTRACTOR (EU.1 - KNOWLEDGE DISTILLATION)
# Muc tieu: Chuyen doi cac Agent Events thanh dataset training JSONL (SFT Format)
# ==============================================================================

EVENT_LOG = Path(r"C:\Users\<USER_NAME>\.gemini\antigravity\agent_flow_events.jsonl")
OUTPUT_JSONL = Path(r"C:\Users\<USER_NAME>\.gemini\antigravity\scripts\antigravity_training_set.jsonl")

def extract_training_pairs():
    if not EVENT_LOG.exists():
        print(f"❌ Khong tim thay file log: {EVENT_LOG}")
        return

    print(f"🏗️  Dang trich xuat du lieu tu: {EVENT_LOG} ...")
    
    with open(EVENT_LOG, 'r', encoding='utf-8') as f:
        events = [json.loads(line) for line in f if line.strip()]

    # Nhan dien cac phien (Session-based grouping)
    training_data = []
    current_session = []

    for event in events:
        current_session.append(event)
        if event.get("type") == "agent_complete" and event.get("payload", {}).get("sessionEnd"):
            # Ket thuc mot session -> đóng gói thành 1 cặp training
            instruction = ""
            response = ""
            thought_chain = []
            
            for e in current_session:
                etype = e.get("type")
                payload = e.get("payload", {})
                
                if etype == "message" and e.get("message", {}).get("role") == "user":
                    instruction = e["message"]["content"]
                
                elif etype == "tool_call_start":
                    thought_chain.append(f"Thought: {payload.get('preview', '')}")
                
                elif etype == "tool_call_end":
                    thought_chain.append(f"Result: {payload.get('result', '')}")
                
                elif etype == "agent_complete" and payload.get("task"):
                    response = payload.get("task")

            if instruction and response:
                training_data.append({
                    "instruction": instruction,
                    "thought": "\n".join(thought_chain),
                    "response": response
                })
            current_session = []

    # Write to JSONL
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for entry in training_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"✅ Da tao thanh cong {len(training_data)} cap du lieu training tai: {OUTPUT_JSONL}")
    return training_data

if __name__ == "__main__":
    extract_training_pairs()
