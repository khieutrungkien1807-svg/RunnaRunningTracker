# GITHUB_AUTOMATION_SKILL.md

> **Phiên bản:** 1.1.0
> **Chức năng:** Tự động hóa quy trình đẩy code lên GitHub, tạo file `push.bat` chuẩn xác và bảo mật.

---

## ⚡ QUY TRÌNH THỰC THI (WORKFLOW)

### 1. Nhận diện Repo & Khởi tạo
Khi User cung cấp link GitHub (qua text hoặc screenshot):
- **Phân tích:** Trích xuất URL `https://github.com/...`
- **Khởi tạo:** Nếu chưa có `.git`, thực hiện `git init` và `git branch -M main`.
- **Remote:** `git remote add origin <URL_NHAN_DIEN>`. Nếu đã có remote khác, thực hiện `git remote set-url origin <URL_NHAN_DIEN>`.

### 2. Quản lý Metadata Dự án (`PROJECT_MAP.md`)
Khi khởi tạo hoặc nhận diện Repo, Agent PHẢI tự động tạo hoặc cập nhật file **`PROJECT_MAP.md`** tại thư mục gốc của dự án để lưu trữ thông tin Git:
- **Repo URL:** `https://github.com/...`
- **Git Push URL:** `git@github.com:...`
- **Project Type:** `PUBLIC` | `PRIVATE`
- **Auto-Push Script:** `YES` (Đính kèm xác nhận đã tạo `push.bat`)

Mục tiêu: Khi User quy trở lại hoặc Agent khác tiếp quản, chỉ cần đọc `PROJECT_MAP.md` là có thể gọi lệnh `push.bat` hoặc đẩy code ngay lập tức mà không cần hỏi lại link.

### 3. Tạo File `push.bat` Chuẩn (Full Version)
Mỗi dự án mới sẽ được Agent tự động tạo file `push.bat` tại thư mục gốc với nội dung NGUYÊN BẢN (Không rút gọn) như sau:

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM =============================================
REM Antigravity - AUTO GIT PUSH SCRIPT
REM Tu dong commit va push code len GitHub
REM =============================================

echo.
echo ==============================================================
echo     Antigravity - AUTO GIT PUSH
echo     Tu dong luu code len GitHub
echo ==============================================================
echo.

REM Khoi tao git va remote neu chua co
if not exist ".git\" (
    echo [INFO] Khoi tao Git repository...
    git init
    git branch -M main
    echo [INFO] Dang ket noi voi GitHub...
    REM Agent se tu dong dien link vao lenh git remote add origin neu co san
    echo.
)

REM Kiem tra xem co thay doi khong
git status --porcelain > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "!STATUS!"=="" (
    echo [INFO] Khong co thay doi nao de commit.
    echo.
    pause
    exit /b 0
)

REM Hien thi cac file thay doi
echo [FILES] Cac file da thay doi:
echo --------------------------------------------------------------
git status --short
echo.

REM Hoi commit message
set /p COMMIT_MSG="[INPUT] Nhap noi dung commit (Enter de dung mac dinh): "

REM Neu khong nhap, dung message mac dinh voi timestamp
if "!COMMIT_MSG!"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%c-%%b-%%a
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a:%%b
    set COMMIT_MSG=Auto save: !DATE! !TIME!
)

echo.
echo [COMMIT] Message: !COMMIT_MSG!
echo.

REM Add tat ca cac file
echo [1/3] Adding files...
git add -A
if !errorlevel! neq 0 (
    echo [ERROR] Loi khi add files!
    pause
    exit /b 1
)
echo      OK - Done

REM Commit
echo [2/3] Committing...
git commit -m "!COMMIT_MSG!"
if !errorlevel! neq 0 (
    echo [ERROR] Loi khi commit!
    pause
    exit /b 1
)
echo      OK - Done

REM Push
echo [3/3] Pushing to GitHub...
git push -u origin main
if !errorlevel! neq 0 (
    echo [ERROR] Push that bai! Khong tu dong --force de bao ve lich su git.
    echo [HINT] Hay kiem tra conflict/rebase, sau do push lai thu cong.
    pause
    exit /b 1
)
echo      OK - Done

echo.
echo ==============================================================
echo     PUSH THANH CONG!
echo ==============================================================
echo.
echo [INFO] Code da duoc luu len GitHub.
echo.

REM Hien thi commit moi nhat
echo [LAST COMMIT]:
git log -1 --oneline
echo.

pause
```

### 3. Bảo mật & Loại trừ (Conditional Privacy Logic)
Trước khi khởi tạo hoặc đẩy code, Agent PHẢI xác minh loại Repo (Public hay Private):

- **PROJECT_TYPE: PRIVATE (Mã nguồn kín):**
  - Đẩy 100% dữ liệu (Trừ `node_modules`, `.cache` khổng lồ).
  - Cho phép đẩy `push.bat`, `.env` (Nếu User yêu cầu sao lưu cấu hình riêng tư).
  - Mục tiêu: Sao lưu nguyên bản (Full Backup).

- **PROJECT_TYPE: PUBLIC (Mã nguồn mở/Cộng đồng):**
  - **TỰ ĐỘNG BLOCK:** `push.bat`, `.env`, `*.log`, `[PERSONAL_ACCOUNT_INFO]`.
  - Bắt buộc thêm các file này vào `.gitignore`.
  - Mục tiêu: Chia sẻ an toàn (Scrubbed Presentation).

### 4. Xác minh Tự Động
Agent có thể xác minh qua URL (Vd: Github CLI `gh repo view`) hoặc hỏi trực tiếp: "Dự án này là Public hay Private?".
