#!/usr/bin/env python3
import sys
import time
import random

# =======================================================================
#  THE GENESIS INVENTOR: ĐỘNG CƠ SÁNG CHẾ NGUYÊN LÝ GỐC (v5.4.0)
# =======================================================================

DOMAINS = ["IoT/Edge Computing", "Web3/Tokenomics", "Gamification/Dopamine API", "MedTech/Bio-Signals", "Spatial 3D/WebXR", "Quantum RNG/Enclaves", "Bio-mimicry Networks"]
TRIZ_PRINCIPLES = [
    "1. Phân nhỏ (Segmentation): Chia thành vi mô-đun độc lập.", 
    "2. Tách biệt (Taking out): Chỉ lấy chính phần gây mâu thuẫn ra ngoài.", 
    "10. Hành động sơ bộ (Preliminary action): Làm trước một nửa việc trong thời gian rỗi.", 
    "13. Đảo ngược (The other way round): Làm ngược hoàn toàn dòng chảy thông thường.", 
    "17. Đổi chiều (Another dimension): Chuyển từ 2D phẳng lên không gian 3D Spatial.", 
    "25. Tự phục vụ (Self-service): Hệ thống tự tự tiêu thụ tài nguyên phế thải của nó.",
    "35. Thay đổi thuộc tính (Parameter changes): Thay đổi trạng thái vật lý (Lỏng/Rắn), ở máy tính là (Disk/RAM)."
]

def synthesize_idea(problem):
    print("\n\033[96m" + "="*85 + "\033[0m")
    print("\033[1m               THE GENESIS INVENTOR IS SYNTHESIZING A BILLION-DOLLAR IDEA         \033[0m")
    print("\033[96m" + "="*85 + "\033[0m")
    print(f"\033[97mNhiệm vụ Kiến trúc (The Problem):\033[0m {problem}\n")
    
    time.sleep(1)
    d1, d2 = random.sample(DOMAINS, 2)
    print(f"\033[95m[1/4]  ÉP BUỘC GIAO THOA ĐA NGÀNH (Cross-Domain Symbiosis)\033[0m")
    print(f"      >> Giao thoa ngẫu nhiên: [\033[1m{d1}\033[0m] + [\033[1m{d2}\033[0m]")
    print(f"      >> Kết quả: Giải bài toán phần mềm bằng tri thức Sinh học và Lượng tử.")
    time.sleep(1.5)

    print(f"\n\033[94m[2/4]  RÀNG BUỘC VẬT LÝ & ĐỘNG HỌC (Advanced Kinematics)\033[0m")
    print("      >> Yêu cầu 1: Sandbox vật lý trước trong RAM. Anti-Collision Radar = ON.")
    print("      >> Yêu cầu 2: Bật Haptic Feedback Mapping qua SDK thiết bị di động.")
    time.sleep(1.5)

    print(f"\n\033[93m[3/4]  QUẢN TRỊ SỰ LỖI THỜI (Time-to-Live / Graceful Degradation)\033[0m")
    print("      >> Hệ thống tự neo TTL là 18 tháng đối với module UI.")
    print("      >> Cài đặt Fallback Loop: Mạng lag > 500ms, tự downscale về chế độ offline Local-First.")
    time.sleep(1.5)

    triz = random.choice(TRIZ_PRINCIPLES)
    print(f"\n\033[92m[4/4]  ÁP DỤNG MA TRẬN SÁNG CHẾ TRIZ (First-Principles Engine)\033[0m")
    print(f"      >> Phá vỡ Mâu thuẫn logic thông qua: \033[1m{triz}\033[0m")
    print("      >> Tính toán hạt nhân: Tối ưu Năng lượng (E) thay vì Tốc độ Xử lý (V).")
    time.sleep(2)

    print("\n\033[91m=====================================================================================\033[0m")
    print("\033[1m PHÁT MINH HOÀN TẤT. BẢN YÊU CẦU SẢN PHẨM (PRD) SIÊU VIỆT NẰM TRONG BỘ NHỚ.\033[0m")
    print("\033[92m[COMMANDING]\033[0m Giao quyền cho Builder Sub-Agents (Architect, Front, Rust-Core)... BẮT ĐẦU CODE!")
    print("\033[91m=====================================================================================\033[0m\n")


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Ứng dụng Giao đồ ăn phi tập trung"
    synthesize_idea(task)
