import os
import yt_dlp
import asyncio
import aiohttp
import re
import random
from typing import Optional, Tuple
import config

class VideoDownloader:
    def __init__(self):
        self.download_path = config.DOWNLOAD_PATH
        os.makedirs(self.download_path, exist_ok=True)
        
        # Путь к файлу с куками (опционально, для YouTube)
        self.cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        
        # Заголовки для имитации браузера
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
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
                r'youtube\.com/shorts/([^?]+)',
            ]
        else:
            return None
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    # ========== YOUTUBE ==========
    
    async def _download_youtube(self, url: str) -> Optional[str]:
        """Скачивает видео с YouTube (прямой доступ из Нидерландов)"""
        video_id = self.extract_video_id(url, "youtube") or str(abs(hash(url)))[:8]
        print(f"▶️ YouTube ID: {video_id}")
        
        # Проверяем наличие куки
        if os.path.exists(self.cookies_file):
            print(f"🍪 Использую куки из файла")
        
        # Форматы для скачивания (от худшего к лучшему)
        formats_to_try = [
            {'name': 'MP3 (аудио)', 'format': 'bestaudio/best', 'type': 'audio', 'ext': 'mp3'},
            {'name': '360p MP4', 'format': 'best[height<=360][ext=mp4]', 'type': 'video', 'ext': 'mp4'},
            {'name': '480p MP4', 'format': 'best[height<=480][ext=mp4]', 'type': 'video', 'ext': 'mp4'},
            {'name': '720p MP4', 'format': 'best[height<=720][ext=mp4]', 'type': 'video', 'ext': 'mp4'},
            {'name': '1080p MP4', 'format': 'best[height<=1080][ext=mp4]', 'type': 'video', 'ext': 'mp4'},
        ]
        
        for fmt in formats_to_try:
            try:
                print(f"🔄 Пробую: {fmt['name']}")
                
                ydl_opts = {
                    'format': fmt['format'],
                    'outtmpl': os.path.join(self.download_path, f'youtube_{video_id}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'ignoreerrors': True,
                    'retries': 5,
                    'fragment_retries': 5,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web'],
                        }
                    },
                    'headers': {
                        'User-Agent': self.get_random_user_agent(),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                    },
                    'socket_timeout': 30,
                }
                
                # Добавляем куки если есть
                if os.path.exists(self.cookies_file):
                    ydl_opts['cookiefile'] = self.cookies_file
                
                # Для аудио добавляем конвертацию
                if fmt['type'] == 'audio':
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    # Определяем имя файла
                    if fmt['type'] == 'audio':
                        filename = os.path.join(self.download_path, f'youtube_{video_id}.mp3')
                    else:
                        filename = ydl.prepare_filename(info)
                    
                    # Проверяем существование файла
                    if os.path.exists(filename):
                        print(f"✅ Скачано: {filename}")
                        return filename
                    
                    # Ищем файл с другим расширением
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.webm', '.mkv', '.mp3']:
                        test_file = base + ext
                        if os.path.exists(test_file):
                            return test_file
                            
            except Exception as e:
                print(f"⚠️ Ошибка при скачивании {fmt['name']}: {str(e)[:100]}")
                continue
        
        print("❌ Не удалось скачать YouTube видео")
        return None
    
    # ========== TIKTOK ==========
    
    async def _get_full_tiktok_url(self, short_url: str) -> str:
        """Преобразует короткую ссылку vt.tiktok.com в полную"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(short_url, allow_redirects=True, timeout=10) as resp:
                    return str(resp.url)
        except:
            return short_url
    
    async def _download_tiktok_direct(self, url: str) -> Optional[str]:
        """Прямое скачивание TikTok через yt-dlp"""
        video_id = self.extract_video_id(url, "tiktok") or str(abs(hash(url)))[:8]
        
        try:
            print(f"🔄 Пробую прямое скачивание TikTok...")
            
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': os.path.join(self.download_path, f'tiktok_{video_id}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'retries': 3,
                'extractor_args': {
                    'tiktok': {
                        'api_hostname': 'api16-normal-c-useast1a.tiktokv.com',
                        'app_name': 'trill',
                        'app_version': '30.2.2',
                        'download': 'without_watermark',
                    }
                },
                'headers': {
                    'User-Agent': self.get_random_user_agent(),
                    'Referer': 'https://www.tiktok.com/',
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    return filename
                
                base = os.path.splitext(filename)[0]
                for ext in ['.mp4', '.webm', '.mkv']:
                    test_file = base + ext
                    if os.path.exists(test_file):
                        return test_file
                        
        except Exception as e:
            print(f"⚠️ Прямое скачивание не сработало: {e}")
            return None
    
    async def _download_tiktok_tikwm(self, url: str) -> Optional[str]:
        """Скачивает TikTok через tikwm.com (надежный API)"""
        video_id = self.extract_video_id(url, "tiktok") or str(abs(hash(url)))[:8]
        
        try:
            print(f"🔄 Пробую TikWM API...")
            
            async with aiohttp.ClientSession() as session:
                api_url = "https://www.tikwm.com/api/"
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept': 'application/json, text/plain, */*',
                }
                data = {'url': url, 'hd': '1'}
                
                async with session.post(api_url, data=data, headers=headers, timeout=20) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        if result.get('code') == 0 and result.get('data'):
                            video_data = result['data']
                            
                            if video_data.get('play'):
                                video_url = 'https://www.tikwm.com' + video_data['play']
                                
                                async with session.get(video_url, headers=headers) as video_resp:
                                    filename = os.path.join(self.download_path, f'tiktok_{video_data.get("id", video_id)}.mp4')
                                    with open(filename, 'wb') as f:
                                        f.write(await video_resp.read())
                                    return filename
        except Exception as e:
            print(f"⚠️ TikWM ошибка: {e}")
            return None
    
    async def _download_tiktok_snaptik(self, url: str) -> Optional[str]:
        """Скачивает TikTok через snaptik.app"""
        try:
            print(f"🔄 Пробую SnapTik API...")
            
            async with aiohttp.ClientSession() as session:
                # Получаем токен
                async with session.get('https://snaptik.app/', headers={'User-Agent': self.get_random_user_agent()}) as resp:
                    html = await resp.text()
                    token = re.search(r'name="token"[^>]*value="([^"]+)"', html)
                    token = token.group(1) if token else ''
                
                # Отправляем запрос
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
    
    async def _download_tiktok(self, url: str) -> Optional[str]:
        """Скачивает TikTok разными способами"""
        # Преобразуем короткую ссылку если нужно
        if 'vt.tiktok.com' in url:
            url = await self._get_full_tiktok_url(url)
        
        video_id = self.extract_video_id(url, "tiktok") or str(abs(hash(url)))[:8]
        print(f"🎵 TikTok ID: {video_id}")
        
        # Пробуем методы по очереди
        methods = [
            self._download_tiktok_direct,
            self._download_tiktok_tikwm,
            self._download_tiktok_snaptik,
        ]
        
        for method in methods:
            result = await method(url)
            if result:
                return result
            await asyncio.sleep(1)
        
        print("❌ Все методы TikTok не сработали")
        return None
    
    # ========== ОСНОВНОЙ МЕТОД ==========
    
    async def download_video(self, url: str) -> Optional[str]:
        """Основной метод скачивания"""
        try:
            # Определяем платформу
            if 'youtube.com' in url or 'youtu.be' in url or 'youtube.com/shorts' in url:
                print("▶️ Обнаружен YouTube")
                return await self._download_youtube(url)
            
            elif 'tiktok.com' in url or 'vt.tiktok.com' in url:
                print("🎵 Обнаружен TikTok")
                return await self._download_tiktok(url)
            
            else:
                raise Exception("Неподдерживаемая платформа")
                
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            raise
    
    def cleanup(self, filepath: str):
        """Удаляет временный файл"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🧹 Файл удален: {filepath}")
        except:
            pass