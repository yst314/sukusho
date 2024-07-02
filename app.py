import os
import zipfile
from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO
import yt_dlp
import cv2
from tqdm import tqdm
import time

app = Flask(__name__)
socketio = SocketIO(app)

def capture_screenshots(url, interval):
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'out/%(id)s/%(id)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_id = info_dict.get("id", None)
        video_ext = info_dict.get("ext", None)
        filename = f"{video_id}.{video_ext}"

        folder_name = os.path.join(out_dir, video_id)
        os.makedirs(folder_name, exist_ok=True)

        ydl.download([url])
        video_path = os.path.join(folder_name, filename)
    
    return folder_name, video_path, interval

def capture_screenshots_py(folder_name, video_path, interval):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = int(fps * interval)

    start_time = time.time()
    num_screenshots = total_frames // frame_interval

    for i in range(num_screenshots):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
        ret, frame = cap.read()
        if not ret:
            break

        screenshot_filename = f"{os.path.join(folder_name, seconds_to_time_string(i * interval))}.png"
        cv2.imwrite(screenshot_filename, frame)

        # Update progress
        progress = (i + 1) / num_screenshots * 100
        socketio.emit('progress_update', {'progress': progress})

    cap.release()
    print(f"PYTHON ELAPSED TIME: {time.time() - start_time}")

def seconds_to_time_string(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02}_{minutes:02}_{remaining_seconds:02}"

def create_zip(folder_name):
    zip_filename = f"{folder_name}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_name):
            for file in files:
                zipf.write(os.path.join(root, file), 
                           os.path.relpath(os.path.join(root, file), 
                                           os.path.join(folder_name, '..')))
    return zip_filename

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        interval = int(request.form['interval'])
        
        folder_name, video_path, interval = capture_screenshots(url, interval)
        capture_screenshots_py(folder_name, video_path, interval)
        
        zip_filename = create_zip(folder_name)
        
        return send_file(zip_filename, as_attachment=True)
    
    return render_template('index.html')

@socketio.on('start_processing')
def handle_start_processing(data):
    url = data['url']
    interval = int(data['interval'])
    
    folder_name, video_path, interval = capture_screenshots(url, interval)
    capture_screenshots_py(folder_name, video_path, interval)
    
    zip_filename = create_zip(folder_name)
    
    socketio.emit('processing_complete', {'zip_filename': zip_filename})

if __name__ == '__main__':
    socketio.run(app, debug=True)