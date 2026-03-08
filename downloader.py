import os
import yt_dlp
import asyncio
import aiohttp
import re
import random
import socket
from typing import Optional, Tuple
import config

class VideoDownloader:
    def __init__(self):
        self.download_path = config.DOWNLOAD_PATH
        os.makedirs(self.download_path, exist_ok=True)
        
        # Путь к файлу с куками
        self.cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        
        # Настройки прокси (для TOR или VPN)
        self.use_proxy = False  # Включите, если используете TOR (127.0.0.1:9050)
        self.proxy_url = "socks5://127.0.0.1:9050"  # Для TOR
        # self.proxy_url = "http://127.0.0.1:8080"  # Для HTTP-прокси
        
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
    
    # ========== TikTok через tikwm.com ==========
    
    async def _download_tiktok_tikwm(self, url: str) -> Optional[str]:
        """Скачивает TikTok через tikwm.com"""
        try:
            print("🔄 Пробуем TikWM API...")
            
            # Исправляем URL (убираем лишнее)
            api_url = "https://www.tikwm.com/api/"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept': 'application/json, text/plain, */*',
                }
                data = {'url': url, 'hd': '1'}
                
                async with session.post(api_url, data=data, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        if result.get('code') == 0 and result.get('data'):
                            video_data = result['data']
                            
                            if video_data.get('play'):
                                video_url = 'https://www.tikwm.com' + video_data['play']
                                
                                async with session.get(video_url, headers=headers) as video_resp:
                                    if video_resp.status == 200:
                                        filename = os.path.join(self.download_path, f"tiktok_{video_data.get('id', 'video')}.mp4")
                                        with open(filename, 'wb') as f:
                                            f.write(await video_resp.read())
                                        print(f"✅ TikTok скачан через TikWM")
                                        return filename
        except Exception as e:
            print(f"⚠️ TikWM не сработал: {e}")
        
        return None
    
    async def _download_tiktok(self, url: str) -> Optional[str]:
        """Скачивает TikTok через API"""
        video_id = self.extract_video_id(url, "tiktok") or str(abs(hash(url)))[:8]
        print(f"🎵 TikTok ID: {video_id}")
        
        # Пробуем TikWM
        result = await self._download_tiktok_tikwm(url)
        if result:
            return result
        
        print("❌ Все API TikTok не сработали")
        return None
    
    # ========== YouTube с поддержкой прокси ==========
    
    async def _download_youtube(self, url: str) -> Optional[str]:
        """Скачивает видео с YouTube"""
        video_id = self.extract_video_id(url, "youtube") or str(abs(hash(url)))[:8]
        print(f"▶️ YouTube ID: {video_id}")
        
        if os.path.exists(self.cookies_file):
            print(f"🍪 Использую куки из файла")
        
        # Форматы для YouTube
        youtube_formats = [
            {'name': 'Audio', 'format': 'bestaudio/best', 'quality': 'audio'},
            {'name': '360p', 'format': 'best[height<=360][ext=mp4]', 'quality': 'video'},
        ]
        
        # Настройки для обхода блокировок
        ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
            'headers': {'User-Agent': self.get_random_user_agent()},
            'socket_timeout': 60,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
        }
        
        # Добавляем куки если есть
        if os.path.exists(self.cookies_file):
            ydl_opts_base['cookiefile'] = self.cookies_file
        
        # Добавляем прокси если включено
        if self.use_proxy:
            ydl_opts_base['proxy'] = self.proxy_url
            print(f"🔌 Использую прокси: {self.proxy_url}")
        
        for format_info in youtube_formats:
            try:
                print(f"🔄 YouTube: {format_info['name']}")
                
                ydl_opts = ydl_opts_base.copy()
                ydl_opts['format'] = format_info['format']
                ydl_opts['outtmpl'] = os.path.join(self.download_path, f'youtube_{video_id}.%(ext)s')
                
                if format_info['quality'] == 'audio':
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    if format_info['quality'] == 'audio':
                        filename = os.path.join(self.download_path, f'youtube_{video_id}.mp3')
                    else:
                        filename = ydl.prepare_filename(info)
                    
                    if os.path.exists(filename):
                        print(f"✅ YouTube скачан: {filename}")
                        return filename
                    
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.mp3']:
                        test_file = base + ext
                        if os.path.exists(test_file):
                            return test_file
            
            except Exception as e:
                print(f"⚠️ Ошибка YouTube: {e}")
                continue
        
        return None
    
    # ========== Основной метод ==========
    
    async def download_video(self, url: str) -> Optional[str]:
        """Основной метод скачивания видео"""
        try:
            if 'tiktok.com' in url or 'vt.tiktok.com' in url:
                print("🎵 Обнаружен TikTok")
                result = await self._download_tiktok(url)
                if result:
                    return result
                else:
                    # Если TikTok не работает, пробуем как YouTube (иногда помогает)
                    print("⚠️ TikTok не сработал, пробуем как YouTube...")
            
            if 'youtube.com' in url or 'youtu.be' in url:
                print("▶️ Обнаружен YouTube")
                result = await self._download_youtube(url)
                if result:
                    return result
            
            raise Exception("Не удалось скачать видео")
            
        except Exception as e:
            raise Exception(f"Ошибка: {str(e)}")
    
    def cleanup(self, filepath: str):
        """Удаляет временный файл"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🧹 Файл удален: {filepath}")
        except:
            pass