# Digit Studio — Hướng dẫn cài đặt

Digit Studio là ứng dụng nhận dạng chữ số viết tay từ 0 đến 9. Bạn có thể vẽ trực tiếp hoặc mở ảnh và so sánh dự đoán của các mô hình. Gói ứng dụng đã build đi kèm thư viện và checkpoint, nên người dùng có thể chạy ngoại tuyến mà không cần cài Python hay huấn luyện mô hình.

## 1. Tải đúng bản cho máy của bạn

1. Mở [trang Actions của MNIST_APP](https://github.com/Alee-deg/MNIST_APP/actions).
2. Chọn **Build Digit Studio**, rồi mở lần chạy có job dành cho máy bạn đã thành công.
3. Tìm **Artifacts** và tải mục tương ứng trong bảng. Nếu GitHub yêu cầu, hãy đăng nhập.
4. Giải nén tệp tải từ **Artifacts**. Bên trong có **gói ứng dụng** và tệp báo cáo `*-model-check.txt`. Dùng gói ứng dụng trong cột cuối để làm tiếp.

| Máy | Tên artifact | Gói ứng dụng bên trong |
|---|---|---|
| Windows x64 | `DigitStudio-windows-x86_64` | `DigitStudio-windows-x86_64.zip` |
| Linux x86-64 | `DigitStudio-linux-x86_64` | `DigitStudio-linux-x86_64.tar.gz` |
| Mac Apple Silicon | `DigitStudio-macos-arm64` | `DigitStudio-darwin-arm64.zip` |
| Mac Intel | `DigitStudio-macos-x86_64` | `DigitStudio-darwin-x86_64.zip` |

Nếu chưa thấy artifact cần tải, mở job tương ứng để xem trạng thái. Job phải hoàn tất bước **Verify executable and archive distribution** rồi mới tải gói lên. `Digit_Studio_3_OS.zip` là gói mã nguồn dùng để tạo các bản phân phối trong bảng.

## 2. Windows x64

1. Vào **Settings → System → About** và xem **System type**. Chọn bản Windows x64 nếu máy dùng bộ xử lý x64.
2. Trong File Explorer, nhấp chuột phải vào `DigitStudio-windows-x86_64.zip` rồi chọn **Extract All…**.
3. Mở thư mục `DigitStudio` vừa giải nén và nhấp đúp vào **`DigitStudio.exe`**.
4. Nếu muốn chuyển ứng dụng sang chỗ khác, hãy di chuyển cả thư mục `DigitStudio` để giữ các thư viện và checkpoint đi cùng.

Nếu cửa sổ đóng ngay, mở PowerShell trong thư mục chứa thư mục `DigitStudio` và tạo báo cáo kiểm tra:

```powershell
Start-Process -FilePath ".\DigitStudio\DigitStudio.exe" -ArgumentList "--check-models", "--report", "model-check.txt" -Wait
Get-Content .\model-check.txt
```

## 3. Linux x86-64

1. Chạy `uname -m` trong terminal. Chọn bản này nếu kết quả là `x86_64`.
2. Mở terminal tại thư mục chứa `DigitStudio-linux-x86_64.tar.gz`. Nếu gói đã được lưu ở một thư mục khác, hãy mở terminal tại thư mục đó.
3. Giải nén và mở ứng dụng trong phiên desktop:

```bash
tar -xzf DigitStudio-linux-x86_64.tar.gz
./DigitStudio/DigitStudio
```

Nếu báo **Permission denied**, cấp quyền chạy rồi thử lại:

```bash
chmod +x ./DigitStudio/DigitStudio
./DigitStudio/DigitStudio
```

Gói Linux được build trên Ubuntu 22.04. Khi thử trên bản phân phối khác, nếu terminal báo thiếu thư viện hệ thống, lưu nguyên văn thông báo để xác định thư viện cần bổ sung. Nếu báo thiếu màn hình như `no display name`, chạy từ terminal trong phiên desktop Ubuntu.

## 4. macOS

1. Mở ** → About This Mac**. Nếu mục **Chip** hiển thị Apple M-series, tải bản **Apple Silicon**. Nếu mục **Processor** hiển thị Intel, tải bản **Intel**.
2. Nhấp đúp gói `DigitStudio-darwin-arm64.zip` hoặc `DigitStudio-darwin-x86_64.zip` để giải nén.
3. Trong Finder, kéo cả **`DigitStudio.app`** vào **Applications**, rồi mở ứng dụng từ đó.

Bạn cũng có thể mở ứng dụng từ Terminal, sau khi chép vào **Applications**:

```bash
open /Applications/DigitStudio.app
```

Bản macOS hiện dành cho thử nghiệm nội bộ và chưa được Apple notarize. Nếu macOS chặn mở, kiểm tra bạn đã chọn đúng kiến trúc và lấy gói từ lần build của dự án. Để phân phối công khai, chuẩn bị bản được ký bằng Developer ID và notarize.

## 5. Kiểm tra sau khi cài

1. Mở Digit Studio và vẽ một chữ số trong ô bên trái.
2. Bấm **Chọn tất cả → Nhận dạng chữ số**. Kiểm tra giao diện hiển thị ảnh sau tiền xử lý và kết quả của tám mô hình.
3. Dùng **Tải ảnh** để thử một ảnh có một chữ số. Đọc kết quả từng mô hình ở cột bên phải.

Báo cáo `*-model-check.txt` đi kèm artifact ghi kết quả kiểm tra dự đoán khi build. Nếu ứng dụng báo lỗi, ghi lại hệ điều hành, tên gói và thông báo lỗi để đối chiếu với báo cáo.

## 6. Chạy từ mã nguồn khi cần kiểm thử

Phần này dành cho người phát triển hoặc khi chưa có gói ứng dụng phù hợp. Dùng **Python 3.12 có Tkinter** và chạy lệnh từ `app_buil/`, thư mục có `DigitStudio.spec`.

**Windows — PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop_app/requirements.txt
.\.venv\Scripts\python.exe -m pip install --timeout 120 --retries 5 torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m desktop_app --check-models
.\.venv\Scripts\python.exe -m desktop_app
```

**Ubuntu — Terminal** (với `python3` là Python 3.12)

```bash
sudo apt install python3-venv python3-tk
python3 -m venv .venv
.venv/bin/python -m pip install -r desktop_app/requirements.txt
.venv/bin/python -m pip install --timeout 120 --retries 5 torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m desktop_app --check-models
.venv/bin/python -m desktop_app
```

**macOS — Terminal** (chọn Python 3.12 có kiến trúc phù hợp với máy)

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r desktop_app/requirements.txt
.venv/bin/python -m pip install --timeout 120 --retries 5 torch
.venv/bin/python -m desktop_app --check-models
.venv/bin/python -m desktop_app
```

Dừng ở bước báo lỗi để xử lý trước khi chạy lệnh kế tiếp. PyTorch dùng cho MLP và Stacking Ensemble. Chi tiết tạo lại gói bằng PyInstaller nằm trong [desktop_app/README.md](desktop_app/README.md).
