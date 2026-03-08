import os
import subprocess
import sys

# Принудительная установка aiohttp (должна быть самым первым действием)
try:
    import aiohttp
except ImportError:
    print("⚠️ aiohttp не найден, устанавливаю принудительно...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "aiohttp>=3.9.0"])
    import aiohttp
    print("✅ aiohttp успешно установлен")

import yt_dlp
import asyncio
import re
import random
from typing import Optional, Tuple
import config

class VideoDownloader:
    def __init__(self):
        self.download_path = config.DOWNLOAD_PATH
        os.makedirs(self.download_path, exist_ok=True)
        
        # Путь к файлу с куками
        self.cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        
        # Заголовки
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
    
    def get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)
    
    def extract_video_id(self, url: str, platform: str) -> Optional[str]:
        """Извлекает ID видео из ссылки"""
        if platform == "tiktok":
            patterns = [
                r'tiktok\.com/@[\w\.]+/video/(\d+)',
                r'tiktok\.com/video/(\d+)',
                r'vt\.tiktok\.com/(\w+)'
            ]
        elif platform == "youtube":
            patterns = [
                r'youtube\.com/watch\?v=([^&]+)',
                r'youtu\.be/([^?]+)',
            ]
        else:
            return None
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _download_tiktok(self, url: str) -> Optional[str]:
        """Скачивает видео с TikTok"""
        if 'vt.tiktok.com' in url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, allow_redirects=True, timeout=10) as resp:
                        url = str(resp.url)
            except:
                pass
        
        video_id = self.extract_video_id(url, "tiktok") or str(abs(hash(url)))[:8]
        print(f"🎵 TikTok ID: {video_id}")
        
        # Пробуем через публичные API
        apis = [
            self._download_tiktok_tikwm,
            self._download_tiktok_snaptik,
        ]
        
        for api in apis:
            try:
                result = await api(url)
                if result:
                    return result
            except:
                continue
        
        return None
    
    async def _download_tiktok_tikwm(self, url: str) -> Optional[str]:
        """Скачивает через tikwm.com"""
        try:
            async with aiohttp.ClientSession() as session:
                api_url = "https://www.tikwm.com/api/"
                headers = {'User-Agent': self.get_random_user_agent()}
                data = {'url': url, 'hd': '1'}
                
                async with session.post(api_url, data=data, headers=headers, timeout=20) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get('data') and result['data'].get('play'):
                            video_url = 'https://www.tikwm.com' + result['data']['play']
                            async with session.get(video_url) as video_resp:
                                filename = os.path.join(self.download_path, f"tiktok_{video_id}.mp4")
                                with open(filename, 'wb') as f:
                                    f.write(await video_resp.read())
                                return filename
        except Exception as e:
            print(f"⚠️ TikWM ошибка: {e}")
        return None
    
    async def _download_tiktok_snaptik(self, url: str) -> Optional[str]:
        """Скачивает через snaptik.app"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://snaptik.app/', headers={'User-Agent': self.get_random_user_agent()}) as resp:
                    html = await resp.text()
                    token = re.search(r'name="token"[^>]*value="([^"]+)"', html)
                    token = token.group(1) if token else ''
                
                data = {'url': url, 'token': token}
                async with session.post('https://snaptik.app/action-2025.php', data=data) as resp:
                    text = await resp.text()
                    video_urls = re.findall(r'https?://[^\s"\']+\.snaptik\.app[^\s"\']*\.mp4', text)
                    if video_urls:
                        async with session.get(video_urls[0]) as video_resp:
                            filename = os.path.join(self.download_path, f"tiktok_snaptik.mp4")
                            with open(filename, 'wb') as f:
                                f.write(await video_resp.read())
                            return filename
        except Exception as e:
            print(f"⚠️ SnapTik ошибка: {e}")
        return None
    
    async def _download_youtube(self, url: str) -> Optional[str]:
        """Скачивает видео с YouTube"""
        video_id = self.extract_video_id(url, "youtube") or str(abs(hash(url)))[:8]
        print(f"▶️ YouTube ID: {video_id}")
        
        if os.path.exists(self.cookies_file):
            print(f"🍪 Использую куки из файла")
        
        youtube_formats = [
            {'name': 'Audio', 'format': 'bestaudio/best', 'quality': 'audio'},
            {'name': '360p', 'format': 'best[height<=360][ext=mp4]', 'quality': 'video'},
        ]
        
        for format_info in youtube_formats:
            try:
                ydl_opts = {
                    'format': format_info['format'],
                    'outtmpl': os.path.join(self.download_path, f'youtube_{video_id}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'retries': 3,
                    'headers': {'User-Agent': self.get_random_user_agent()},
                }
                
                if os.path.exists(self.cookies_file):
                    ydl_opts['cookiefile'] = self.cookies_file
                
                if format_info['quality'] == 'audio':
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }]
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    if format_info['quality'] == 'audio':
                        filename = os.path.join(self.download_path, f'youtube_{video_id}.mp3')
                    else:
                        filename = ydl.prepare_filename(info)
                    
                    if os.path.exists(filename):
                        return filename
                    
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.mp3']:
                        test_file = base + ext
                        if os.path.exists(test_file):
                            return test_file
            
            except Exception as e:
                print(f"⚠️ YouTube ошибка: {e}")
                continue
        
        return None
    
    async def download_video(self, url: str) -> Optional[str]:
        """Основной метод скачивания видео"""
        try:
            if 'tiktok.com' in url or 'vt.tiktok.com' in url:
                print("🎵 Обнаружен TikTok")
                result = await self._download_tiktok(url)
                if result:
                    return result
            
            if 'youtube.com' in url or 'youtu.be' in url:
                print("▶️ Обнаружен YouTube")
                result = await self._download_youtube(url)
                if result:
                    return result
            
            raise Exception("Не удалось скачать видео")
            
        except Exception as e:
            raise Exception(f"Ошибка: {str(e)}")
    
    def cleanup(self, filepath: str):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass