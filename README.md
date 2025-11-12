# Ứng dụng AI trong nhận diện hành động nguy hiểm
<div align="center">
<p align="center">
  <img width="200" height="200" alt="Image" src="https://github.com/user-attachments/assets/626bce02-3119-4f69-a839-82bbc3c8bc97" />
</p>
</div>

## 📝 Giới thiệu
Nhận diện hành động nguy hiểm qua camera và cảnh báo cho người dùng qua ứng dụng TELEGRAM và thông
báo âm thanh.

## ⚙️ Công nghệ sử dụng
- Python: Được dùng để xử lý logic, thuật toán mã hóa, quản lý dữ liệu, và điều khiển toàn bộ ứng dụng.
- OpenCV: Thư viện xử lý ảnh và video.
- YOLO (You Only Look Once): Mô hình học sâu dùng để nhận diện đối tượng trong ảnh và video.
- gTTS (Google Text-to-Speech): Chuyển văn bản thành giọng nói.

## 📁 Cấu trúc thư mục dự án
```
├── __pycache__/           # Thư mục chứa các file biên dịch Python
├── captures/              # Thư mục lưu trữ các ảnh chụp khi phát hiện bạo lực
├── processed/             # Thư mục lưu trữ video đã được xử lý
├── templates/             # Thư mục chứa các template HTML
│   ├── index.html         # Trang chính của ứng dụng
│   ├── live.html          # Trang live stream video
│   └── upload.html        # Trang upload video
├── train/                 # Thư mục chứa mô hình YOLO đã huấn luyện
│   └── content/
│       └── runs/
│           └── ...        # Các file và dữ liệu mô hình YOLO đã huấn luyện
├── uploads/               # Thư mục chứa video tải lên để xử lý
├── alert.mp3              # File âm thanh cảnh báo
├── app.py                 # File chính chứa mã nguồn Flask
└── requirements.txt       # File chứa các thư viện yêu cầu cho dự án
````

## 🚀 Cách chạy chương trình
```bash
# Clone repo
git clone https://github.com/MaiLan2907/NHANDIENHANHDONGNGUYHIEM

# Cài thư viện
pip install -r requirements.txt

# Chạy chương trình
python main.py
```


