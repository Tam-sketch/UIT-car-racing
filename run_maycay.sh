#!/bin/bash

echo "=========================================================="
echo "🏎️  KHỞI ĐỘNG HỆ THỐNG LÁI XE TỰ HÀNH UIT-CAR-RACING  🏎️"
echo "=========================================================="

# 1. Dọn dẹp tiến trình socat cũ
pkill -9 socat 2>/dev/null
fuser -k 11000/tcp 2>/dev/null
sleep 1

# 2. Tìm IP máy chủ Unity (WSL2 hoặc Host)
WSL_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
TARGET_IP="172.27.111.165"

# Thử kết nối IP WSL2 trước, nếu không được thì dùng WSL_IP / host.docker.internal
echo "[INFO] Dang ket noi toi Unity Simulator tai IP: $TARGET_IP:11000 ..."
socat TCP-LISTEN:11000,reuseaddr,fork TCP:$TARGET_IP:11000 &
SOCAT_PID=$!
sleep 1

# 3. Chạy maycay.py
cd /workspace/UIT-CAR-RACING 2>/dev/null || cd /mnt/d/UIT-CAR-RACING 2>/dev/null || cd "$(dirname "$0")"

unset QT_QPA_PLATFORM
unset ENABLE_GUI

echo "[INFO] Khoi chay maycay.py..."
python maycay.py

# Dọn dẹp khi thoát
kill $SOCAT_PID 2>/dev/null
