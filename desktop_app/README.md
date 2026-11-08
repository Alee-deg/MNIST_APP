# Digit Studio

Ứng dụng desktop ngoại tuyến để vẽ hoặc mở ảnh một chữ số và so sánh dự đoán từ nhiều mô hình. Các checkpoint được đọc từ `saved_models/` và được đóng gói cùng ứng dụng. Bản đóng gói chạy với các checkpoint có sẵn.

| Mô hình | Checkpoint | Tăng cường dữ liệu |
|---|---|---|
| CNN | `cnn.joblib` | Mạnh |
| CNN | `cnn_no_data_au.joblib` | Nhẹ |
| MLP | `mlp.joblib` | Không |
| Logistic Regression | `logistic_regression.joblib` | Nhẹ |
| Linear SVM | `svm.joblib` | Nhẹ |
| Naive Bayes | `naive_bayes.joblib` | Không |
| Stacking Ensemble | `ensemble.joblib` | Không |
| AdaBoost | `ada.joblib` | Không |

## Tạo bản đóng gói qua GitHub Actions

1. Giải nén gói mã nguồn. Đưa **nội dung bên trong** `app_buil/` lên thư mục gốc của repository, gồm cả `.github/workflows/build-desktop.yml`.
2. Vào **Actions → Build Digit Studio → Run workflow**.
3. Khi job hoàn tất, tải artifact tương ứng trong trang kết quả. Mỗi artifact chứa gói ứng dụng và báo cáo kiểm tra dự đoán.

| Đích | Cách mở sau khi giải nén gói ứng dụng |
|---|---|
| Windows x86-64 | Mở `DigitStudio/DigitStudio.exe` |
| Linux x86-64 | Chạy `./DigitStudio/DigitStudio` |
| macOS Apple Silicon | Mở `DigitStudio.app` từ gói `darwin-arm64` |
| macOS Intel | Mở `DigitStudio.app` từ gói `darwin-x86_64` |

Giữ nguyên cả thư mục ứng dụng sau khi giải nén. Mỗi bản chạy trên hệ điều hành và kiến trúc tương ứng. Bản macOS dùng để thử nghiệm nội bộ. Phát hành công khai cần bổ sung ký bằng Developer ID và notarization. Bản Linux được build trên Ubuntu 22.04, khả năng chạy trên bản phân phối khác còn phụ thuộc vào các thư viện hệ thống.

## Chạy từ mã nguồn

Dùng Python 3.12. Mở terminal trong `app_buil/`, thư mục có `DigitStudio.spec`. Trên Ubuntu cài Tk và venv trước bằng `sudo apt install python3-venv python3-tk`. Trên Windows và macOS, dùng bản Python có Tkinter. Có thể kiểm tra Tk bằng `python -m tkinter`.

Tạo môi trường ảo bằng `python -m venv .venv` (hoặc `python3 -m venv .venv` trên Ubuntu/macOS). Trong các lệnh sau, `python` là Python trong môi trường ảo. Bạn có thể dùng `.venv/bin/python` trên Linux/macOS hoặc `.venv\Scripts\python.exe` trên Windows.

```bash
python -m pip install -r desktop_app/requirements.txt
```

Trên Linux và Windows, cài PyTorch từ kho CPU:

```bash
python -m pip install --timeout 120 --retries 5 torch --index-url https://download.pytorch.org/whl/cpu
```

Trên macOS, cài PyTorch từ kho mặc định bằng `python -m pip install torch`. PyTorch cần cho cả MLP và Stacking Ensemble.

```bash
python -m desktop_app --check-models
python -m desktop_app
```

## Tự build trên máy hiện tại

Sau khi cài các phụ thuộc ở trên, chạy:

```bash
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm DigitStudio.spec
python -m desktop_app.package_build
```

Gói phân phối nằm trong `packages/`. Lệnh cuối kiểm tra dự đoán trực tiếp bằng bản đóng gói và dừng nếu một mô hình gặp lỗi.
