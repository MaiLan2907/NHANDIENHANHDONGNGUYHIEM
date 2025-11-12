from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
import cv2
import torch
from ultralytics import YOLO
import time
import datetime
import threading
import requests
from gtts import gTTS
import os
from playsound import playsound
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ====================== CẤU HÌNH ======================
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
CAPTURE_FOLDER = "captures"  
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(CAPTURE_FOLDER, exist_ok=True)

# LƯU Ý: Đường dẫn này là cục bộ (local) và cần thay đổi khi triển khai.
model = YOLO(r'E:\MaiLan\train\content\runs\detect\train\weights\best.pt')
class_names = ['violence', 'no_violence']

TELEGRAM_BOT_TOKEN = '8515623217:AAHQO3GZa02VbshONqUNOZxt2Ule39_pkN8'
TELEGRAM_CHAT_ID = '-5005731018'


ALERT_COOLDOWN = 150
AUDIO_ALERT_FILE = "alert.mp3"

violence_detected = False
last_alert_time = 0
camera = None

# LƯU Ý: Địa chỉ IP DroidCam này là cục bộ và có thể cần thay đổi.
DROIDCAM_URL = "http://192.168.1.15:4747/video"
# =====================================================


# ---- Gửi Telegram tin nhắn ----
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Lỗi Telegram: {e}")


# ---- Gửi Telegram kèm ảnh ----
def send_telegram_photo(photo_path, caption="Cảnh báo bạo lực!"):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}, files={'photo': photo}, timeout=10)
        print(f"📸 Đã gửi ảnh lên Telegram: {photo_path}")
    except Exception as e:
        print(f"Lỗi gửi ảnh Telegram: {e}")


# ---- Cảnh báo giọng nói ----
def speak_alert(text="Cảnh báo! Phát hiện bạo lực tại khuôn viên!"):
    try:

        gTTS(text=text, lang='vi').save(AUDIO_ALERT_FILE)
        playsound(AUDIO_ALERT_FILE)
    except Exception as e:
        print(f"Lỗi âm thanh: {e}")


# ---- Stream camera ----
def generate_frames():
    global camera, violence_detected, last_alert_time

    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(DROIDCAM_URL)
        if not camera.isOpened():
            print(" Không thể mở DroidCam! Kiểm tra IP và kết nối Wi-Fi.")
            return
        
        # Cấu hình FPS hiện tại là 15
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        camera.set(cv2.CAP_PROP_FPS, 15)
        print(" Đã kết nối DroidCam!")

    while True:
        success, frame = camera.read()
        if not success:
            print(" Mất kết nối camera hoặc không nhận được frame.")
            # Thử kết nối lại sau 5 giây
            time.sleep(5) 
            if camera is not None:
                camera.release()
                camera = None
            break

        results = model(frame, stream=False, verbose=False)[0]
        current_violence = False

        for result in results.boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = result.conf[0]
            cls = int(result.cls[0])
            label = f'{class_names[cls]} {conf:.2f}'

            if class_names[cls] == 'violence' and conf >= 0.7:
                current_violence = True
                color = (0, 0, 255)
                thickness = 4
            elif class_names[cls] == 'no_violence' and conf >= 0.5:
                color = (0, 255, 0)
                thickness = 2
            else:
                continue

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, thickness)

        if current_violence:
            violence_detected = True
            current_time = time.time()

            # 🕒 Kiểm tra Cooldown: 300 giây (5 phút)
            if current_time - last_alert_time > ALERT_COOLDOWN:
                now = datetime.datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                message = f"⚠️ Phát hiện bạo lực lúc {now.strftime('%H:%M:%S, ngày %d/%m/%Y')}"

                # 📸 Lưu lại khung hình
                photo_path = os.path.join(CAPTURE_FOLDER, f"alert_{timestamp}.jpg")
                cv2.imwrite(photo_path, frame)
                print(f" Ảnh được lưu: {photo_path}")

                #  Gửi song song Telegram và cảnh báo âm thanh
                threading.Thread(target=send_telegram_message, args=(message,)).start()
                threading.Thread(target=send_telegram_photo, args=(photo_path, message)).start()
                threading.Thread(target=speak_alert).start()

                last_alert_time = current_time
        else:
            violence_detected = False

        if violence_detected:
            cv2.putText(frame, 'CANH BAO: DANG CO DANH NHAU!!!', (50, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 2.0, (0, 0, 255), 4)

        cv2.putText(frame, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    (frame.shape[1] - 500, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            break
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    print("❌ Dừng stream và giải phóng camera.")
    if camera is not None:
        camera.release()
        camera = None


# ---- Xử lý video upload ----
def process_uploaded_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    # Cần đảm bảo codec mp4v hoạt động hoặc thay bằng XVID/DIVX nếu cần
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    fps = cap.get(cv2.CAP_PROP_FPS)
    w, h = int(cap.get(3)), int(cap.get(4))
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, stream=False, verbose=False)[0]
        for result in results.boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            conf = result.conf[0]
            cls = int(result.cls[0])
            color = (0, 0, 255) if class_names[cls] == 'violence' else (0, 255, 0)
            label = f'{class_names[cls]} {conf:.2f}'
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        out.write(frame)

    cap.release()
    out.release()
    print(f"✅ Video xử lý xong: {output_path}")


# ====================== ROUTES ======================

@app.route('/')
def index():
    # Cần file index.html để render
    return render_template('index.html')


@app.route('/live')
def live():
    # Cần file live.html để render
    return render_template('live.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global camera
    if camera is not None:
        camera.release()
        camera = None
        print("🔒 Camera được giải phóng trước khi upload video.")

    if request.method == 'POST':
        file = request.files.get('video')
        if not file or file.filename == '':
            return "Chưa chọn file", 400
        
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(PROCESSED_FOLDER, f"processed_{filename}")
        
        try:
            file.save(input_path)
            process_uploaded_video(input_path, output_path)
            # Cần file upload.html để render
            return render_template('upload.html', processed_video=output_path)
        except Exception as e:
            return f"Lỗi xử lý file: {e}", 500
            
    # Cần file upload.html để render GET request
    return render_template('upload.html')


# Route để xem video đã xử lý (chỉ dùng tạm, cần phải có setup máy chủ file)
@app.route('/processed/<filename>')
def serve_processed_video(filename):
    # Flask không nên phục vụ file tĩnh trong môi trường production, 
    # nhưng dùng send_from_directory cho mục đích demo.
    from flask import send_from_directory
    return send_from_directory(PROCESSED_FOLDER, filename)


@app.route('/status')
def status():
    return jsonify({
        'violence_detected': violence_detected,
        'timestamp': datetime.datetime.now().isoformat(),
        'cooldown_seconds': ALERT_COOLDOWN
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)