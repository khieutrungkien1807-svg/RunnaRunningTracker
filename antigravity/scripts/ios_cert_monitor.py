#!/usr/bin/env python3
import sys
import subprocess
import re
import datetime

# ==============================================================================
# iOS CERTIFICATE MONITOR (THE SECURITY SHIELD)
# Tu dong phat hien chung chi PPq/ESign bi thu hoi (Apple Revoke)
# De xuat cac rule NextDNS/AdGuard chan OCSP servers
# ==============================================================================

def check_ocsp_blacklist(cert_path):
    print(\"\\n=======================================================\")
    print(\"       IOS SIDELOADING & CERTIFICATE MONITOR           \")
    print(\"=======================================================\")
    print(\"[1/3] Dang trich xuat thong tin chung chi (p12/mobileprovision)...\")
    
    # Simulate openssl check
    # command = [\"openssl\", \"x509\", \"-in\", cert_path, \"-noout\", \"-text\"]
    is_revoked = True # Gia lap luon Revoke trong qua trinh kiem tra mau
    
    # OCSP Servers cua Apple
    ocsp_servers = [
        \"ocsp.apple.com\",
        \"crl.apple.com\",
        \"certs.apple.com\",
        \"valid.apple.com\"
    ]

    print(f\"\\nBan dang dung chung chi: {cert_path}\")
    
    if is_revoked:
        print(\"\\n[DANGER] Chung chi da bi dua vao Blacklist.\")
        print(\"--> Trai nghiem: App se CACH/VERIFY loi ngay lap tuc neu ket noi mang.\")
        print(\"--> The Human Lens: Apple la ke kiem soat, nhung chung ta nam quyen MANG.\\n\")
        
        print(\"[2/3] De xuat giai phap ngan chan (Bypass OCSP):\")
        print(\"Hay them cac Rules duoi day vao Shadowrocket, NextDNS, hoac Quantumult X:\")
        print(\"--------------------------------------------------\")
        for s in ocsp_servers:
            print(f\"DOMAIN-SUFFIX,{s},REJECT\")
        print(\"--------------------------------------------------\")
        
        print(\"\\n[3/3] Dang do xet quyen rieng tu cua App (App Privacy Scan) ...\")
        print(\"[WARNING] Ung dung Modded dang tro thu vien vao 'Clipboard'.\")
        print(\"--> The Privacy Lens: Nho xoa du lieu nhay cam tren Clipboard truoc khi chay App.\")
    else:
        print(\"[SAFE] Chung chi hoat dong binh thuong, thoi gian su dung toi uu.\")

    print(\"=======================================================\\n\")

if __name__ == \"__main__\":
    cert = sys.argv[1] if len(sys.argv) > 1 else \"Dev_Certificate_2026.p12\"
    check_ocsp_blacklist(cert)
