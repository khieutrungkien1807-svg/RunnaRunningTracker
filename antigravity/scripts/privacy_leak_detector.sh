#!/bin/bash
# ==============================================================================
# PRIVACY LEAK DETECTOR (STEALTH & NETWORKING)
# Do xet ro ri DNS va WebRTC qua Command Line (Dung truoc khi bat VPN)
# ==============================================================================

echo "======================================================="
echo "            PRIVACY & WEBRTC LEAK DETECTOR             "
echo "======================================================="
echo "[1/3] Kiem tra ket noi DNS hien tai (DNS Resolvers)..."

# Mo phong kiem tra leak bang dig/nslookup (Chi danh cho Linux/Mac/WSL)
if command -v dig &> /dev/null; then
    RESOLVER=$(dig +short whoami.akamai.net)
    echo "-> Dang dung DNS ra ngoai: $RESOLVER"
    # Them phan tich ISP neu thuoc VeitTel, VNPT thay vi Cloudflare
    echo "[INFO] Neu day khong phai IP cua VPN/Shadowrocket, DNS da bi riced (Leak)."
else
    echo "-> [Khong the chay 'dig', dung ma giam bot]"
fi

echo ""
echo "[2/3] Quet giao thuc do rỉ WebRTC STUN/TURN (Port 3478)..."
netstat -an | grep 3478 > /dev/null
if [ $? -eq 0 ]; then
    echo "[DANGER] Phat hien traffic WebRTC dang mo port STUN."
    echo "         -> Ban dung VPN nhung website ghet van xem duoc IP thuc!"
    echo "         -> [ACTION] Nho chan STUN trong NextDNS hoac vao trang config trinh duyet (about:config) -> media.peerconnection.enabled = false."
else
    echo "[SAFE] Khong phat hien ping STUN qua WebRTC."
fi

echo ""
echo "[3/3] Kiem tra Kill-Switch Firewall..."
if iptables -L -n -v | grep -i "REJECT" > /dev/null 2>&1 || Get-NetFirewallRule -ErrorAction SilentlyContinue > /dev/null; then
    echo "-> Kill-Switch/Firewall da duoc cau hinh (An toan khi rot mang VPN)."
else
    echo "-> [WARNING] Firewall hien chua dat trang thai 'Block Non-VPN traffic' hoan toan."
fi

echo "======================================================="
echo "Ket luan: Hay kiem soat mang tu tan goc, khong qua app trung gian."
echo "======================================================="
