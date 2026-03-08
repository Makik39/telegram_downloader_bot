import os
import yt_dlp
import asyncio
import re
import config

class VideoDownloader:
    def __init__(self):
        self.path = config.DOWNLOAD_PATH
        os.makedirs(self.path, exist_ok=True)
        self.cookies = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    
    async def download_video(self, url):
        try:
            ydl_opts = {
                'format': 'best[height<=720][ext=mp4]/bestaudio/best',
                'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'retries': 3,
            }
            if os.path.exists(self.cookies):
                ydl_opts['cookiefile'] = self.cookies
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    return filename
                base = os.path.splitext(filename)[0]
                for ext in ['.mp4', '.mp3']:
                    f = base + ext
                    if os.path.exists(f):
                        return f
        except Exception as e:
            print(f"Ошибка: {e}")
        return None
    
    def cleanup(self, filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass