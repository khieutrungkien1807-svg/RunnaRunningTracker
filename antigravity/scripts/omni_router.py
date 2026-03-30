#!/usr/bin/env python3
import sys
import time
import random

# =======================================================================
#  THE OMNI-ROUTER: TRÁI TIM ĐIỀU PHỐI VẠN NĂNG (v6.0.0-UNIFIED)
# =======================================================================
# Gộp: Phần mềm (GB), Cầu nối Mạng-Vật lý (GC), Nội dung/PDF/SEO (GD), Giải Phẫu Giáo Dục (GE).

def classify_and_route(prompt):
    print("\n\033[96m" + "="*85 + "\033[0m")
    print("\033[1m                  THE OMNI-ROUTER IS CLASSIFYING INTENT                \033[0m")
    print("\033[96m" + "="*85 + "\033[0m")
    print(f"\033[97mNhiệm vụ đầu vào (The Architect's Command):\033[0m {prompt}\n")
    
    time.sleep(1)
    print("\033[90m>> Đang truy cập lõi Neural Brain để móc nối kỹ năng...\033[0m")
    time.sleep(1.5)

    prompt_lower = prompt.lower()
    
    if any(kw in prompt_lower for kw in ['app', 'web', 'code', 'bug', 'hiệu năng']):
        print("\n\033[92m[MATCHED] TÍN HIỆU: GB - THE DIGITAL FORGE (Xưởng Đúc Số)\033[0m")
        print(">> Bắt buộc Chaining: [architecture] -> [react-best] -> [loki-shield] -> [playwright-e2e]")
        print(">> Action: Kích hoạt luồng xây dựng, test tự động ẩn và tối ưu bundle Lighthouse.")
        
    elif any(kw in prompt_lower for kw in ['iot', 'phần cứng', 'mạch', 'quang học', 'dịch ngược', 'vật lý']):
        print("\n\033[91m[MATCHED] TÍN HIỆU: GC - THE CYBER-PHYSICAL BRIDGE (Cầu nối Không gian)\033[0m")
        print(">> Bắt buộc Chaining: [iot] -> [security-vulnerability] -> [hardware-in-loop]")
        print(">> Action: Tiêm mã Dead-man switch (tự ngắt điện). Scan tràn bộ đệm trước khi biên dịch C/C++.")
        
    elif any(kw in prompt_lower for kw in ['pdf', 'ppt', 'excel', 'seo', 'truyền thông', 'bài', 'chiến dịch']):
        print("\n\033[95m[MATCHED] TÍN HIỆU: GD - MEDIA & ARTIFACT SYNTHESIZER (Máy Tổng hợp)\033[0m")
        print(">> Bắt buộc Chaining: [content-creator] -> [oo-xml] -> [watermark-security]")
        print(">> Action: Phân rã tâm lý Socratic. Nén nhị phân OOXML, nhúng Watermark chống Redlining.")
        
    else:
        print("\n\033[94m[MATCHED] TÍN HIỆU: GE - SOCRATIC TUTOR & SOLVER (Gia sư Socratic)\033[0m")
        print(">> Bắt buộc Chaining: [writing-skills] -> [claude-d3js] -> [canvas-design]")
        print(">> Action: Kích hoạt Anti-Spoonfeeding (Chống đút ăn). Bẻ gãy bài toán, sinh D3.js tương tác mô phỏng.")

    time.sleep(2)
    print("\n\033[93m[EXECUTION PROTOCOL]\033[0m Đã nhận diện luồng hoạt động chính xác.")
    print("\033[91mHỆ THỐNG ĐÃ SẴN SÀNG THỰC THI LIÊN HOÀN!\033[0m Giao quyền cho Mega-Pipelines...\n")

if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Thiết kế app bán hàng và sinh luôn PDF báo cáo doanh thu."
    classify_and_route(task)
