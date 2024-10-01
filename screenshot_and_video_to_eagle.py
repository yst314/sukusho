import os
import cv2
import argparse
from pathlib import Path 
import yt_dlp
from typing import Optional, List, Tuple
import tempfile
from typing import Any
from eaglewrapper import Eagle
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import numpy as np 
import numpy.typing as npt
from tqdm import tqdm
import multiprocessing
from functools import partial

def capture_screenshots(video_path: str, sec: float) -> Tuple[str, cv2.typing.MatLike]:
    cap = cv2.VideoCapture(video_path)
    msec = 1000 * sec
    cap.set(cv2.CAP_PROP_POS_MSEC, msec)
    _, frame = cap.read()
    cap.release()
    return sec, frame

def process_frame(args: Tuple[str, float, str, Path]) -> dict:
    video_path, sec, url, image_dir = args
    file_time = str(sec).replace(".", "_")
    sec, frame = capture_screenshots(video_path, sec)
    image_path = image_dir / f'tmp{file_time}.png'
    cv2.imwrite(str(image_path), frame)
    return {
        "path": str(image_path),
        "name": f"{Path(video_path).stem}_{file_time}",
        "website": url,
        "tags": None,
        "annotation": None
    }

def generator_interval(cap: cv2.VideoCapture, interval: float) -> npt.NDArray[np.floating[Any]]:
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_sec = total_frames / fps
    return np.arange(0, total_sec, interval)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    parser.add_argument("interval", type=float)
    args = parser.parse_args()
    return args

@dataclass
class VideoInfo:
    id: str
    ext: str 
    title: str
    
def get_video_info(url:str) -> Optional[VideoInfo]:
    with yt_dlp.YoutubeDL() as ydl:    
        try:
            info_dict = ydl.extract_info(url, download=False)
        except:
            return None
        id = info_dict.get("id", None)
        ext = info_dict.get("ext", None)
        title = info_dict.get("title", None)
        
    return VideoInfo(id, ext, title)

def download_video(url: str, id: str, dist_dir: Path) -> Optional[Path]:
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{dist_dir}/%(id)s/%(id)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download(url)
        except:
            return None
    
    file_names = os.listdir(dist_dir / id)
    try:
        video_name = file_names[0]
    except:
        return None
    video_path = dist_dir / id / video_name
    return video_path

def get_page_title(url:str) -> Optional[str]:
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else None
        return title
    else:
        return None
        
def main():
    args = parse_args()
    eagle = Eagle()

    video_info = get_video_info(args.url)
    if not video_info:
        print(f"Failed to download the video info: {args.url}")
        return
    
    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)
            
    video_path = download_video(args.url, video_info.id, Path(tmp_dir))
    video_path = Path(os.getcwd()) / video_path
    
    print("video", video_path)
    if not video_path:
        print(f"Failed to download the video: {args.url}")
        return 
    
    result_create_dir = eagle.create_folder(video_info.title)
    eagle.add_from_path(str(video_path), video_info.title, website=args.url, folder_id=result_create_dir["id"])
    
    cap = cv2.VideoCapture(str(video_path))
    intervals = generator_interval(cap, args.interval)
    cap.release()
    
    image_dir = Path(os.path.dirname(video_path))
    
    # Prepare arguments for multiprocessing
    process_args = [(str(video_path), sec, args.url, image_dir) for sec in intervals]
    
    # Use multiprocessing to process frames in parallel
    with multiprocessing.Pool() as pool:
        data = list(tqdm(pool.imap(process_frame, process_args), total=len(process_args)))
    
    eagle.add_from_paths(data, folder_id=result_create_dir["id"])

if __name__ == "__main__":
    main()