import aiohttp
import asyncio
import os
import re
import json
import random
import config

class TikTokAPI:
    def __init__(self):
        self.download_path = config.DOWNLOAD_PATH
        os.makedirs(self.download_path, exist_ok=True)
        
        # Ротация User-Agent для обхода блокировок
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
        ]
    
    async def download_tiktok(self, url: str) -> str:
        """
        Скачивает TikTok видео через сторонние сервисы
        """
        # Специальные методы для обхода региональных блокировок
        apis = [
            self._download_via_tikwm,        # Специализированный TikTok API
            self._download_via_snaptik_alt,  # Альтернативный метод snaptik
            self._download_via_douyin,       # Прямой доступ к Douyin (китайский TikTok)
            self._download_via_tikmate_fixed # Исправленный TikMate
        ]
        
        for api in apis:
            try:
                print(f"🔄 Пробуем API: {api.__name__}")
                filename = await api(url)
                if filename and os.path.exists(filename):
                    print(f"✅ Успешно скачано через {api.__name__}")
                    return filename
            except Exception as e:
                print(f"⚠️ API {api.__name__} не сработал: {e}")
                continue
        
        raise Exception("Все методы для TikTok не сработали")
    
    def _get_headers(self, referer=None):
        """Генерирует случайные заголовки для запроса"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        if referer:
            headers['Referer'] = referer
        return headers
    
    async def _download_via_tikwm(self, url: str) -> str:
        """Использует tikwm.com - один из самых надежных API"""
        async with aiohttp.ClientSession() as session:
            api_url = 'https://www.tikwm.com/api/'
            headers = self._get_headers('https://www.tikwm.com/')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            data = {'url': url, 'count': '12', 'cursor': '0', 'web': '1', 'hd': '1'}
            
            async with session.post(api_url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('code') == 0 and result.get('data'):
                        video_data = result['data']
                        
                        # Пробуем получить видео без водяного знака
                        if video_data.get('play'):
                            video_url = 'https://www.tikwm.com' + video_data['play']
                        elif video_data.get('wmplay'):
                            video_url = 'https://www.tikwm.com' + video_data['wmplay']
                        else:
                            return None
                        
                        print(f"✅ Найдена ссылка через TikWM")
                        
                        # Скачиваем видео
                        async with session.get(video_url, headers=self._get_headers()) as video_resp:
                            if video_resp.status == 200:
                                filename = os.path.join(self.download_path, f"tiktok_{abs(hash(url))}.mp4")
                                with open(filename, 'wb') as f:
                                    f.write(await video_resp.read())
                                return filename
        return None
    
    async def _download_via_snaptik_alt(self, url: str) -> str:
        """Альтернативный метод через snaptik (обход региональных блокировок)"""
        async with aiohttp.ClientSession() as session:
            # Используем мобильный User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://snaptik.app/'
            }
            
            # Получаем страницу с токеном через мобильную версию
            async with session.get('https://snaptik.app/mp4', headers=headers) as resp:
                html = await resp.text()
                
                # Ищем токен в разных форматах
                token = None
                patterns = [
                    r'name="token"[^>]*value="([^"]+)"',
                    r'data-token="([^"]+)"',
                    r'name="_token"[^>]*value="([^"]+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        token = match.group(1)
                        break
                
                if not token:
                    print("❌ Токен не найден на snaptik")
                    return None
            
            # Отправляем запрос с мобильными заголовками
            data = {'url': url, 'token': token, 'locale': 'en'}
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            async with session.post('https://snaptik.app/action-2025.php', data=data, headers=headers) as resp:
                text = await resp.text()
                
                # Ищем ссылки на видео
                video_urls = re.findall(r'https?://[^\s"\']+\.snaptik\.app[^\s"\']*\.mp4[^\s"\']*', text)
                if video_urls:
                    video_url = video_urls[0]
                    print(f"✅ Найдена ссылка через Snaptik Mobile")
                    
                    async with session.get(video_url, headers=self._get_headers()) as video_resp:
                        if video_resp.status == 200:
                            filename = os.path.join(self.download_path, f"tiktok_{abs(hash(url))}.mp4")
                            with open(filename, 'wb') as f:
                                f.write(await video_resp.read())
                            return filename
            return None
    
    async def _download_via_douyin(self, url: str) -> str:
        """Прямой доступ к Douyin (китайская версия TikTok)"""
        async with aiohttp.ClientSession() as session:
            # Конвертируем TikTok URL в Douyin ID
            video_id = None
            if 'video/' in url:
                video_id = url.split('video/')[-1].split('?')[0]
            elif 'vt.tiktok.com' in url:
                # Следуем редиректу
                async with session.get(url, headers=self._get_headers(), allow_redirects=True) as resp:
                    final_url = str(resp.url)
                    if 'video/' in final_url:
                        video_id = final_url.split('video/')[-1].split('?')[0]
            
            if not video_id:
                return None
            
            # Используем Douyin API
            douyin_api = f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}'
            headers = self._get_headers('https://www.douyin.com/')
            headers['Accept'] = 'application/json'
            
            async with session.get(douyin_api, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('item_list'):
                        video_data = data['item_list'][0]['video']
                        if video_data.get('play_addr'):
                            # Получаем URL видео
                            url_list = video_data['play_addr']['url_list']
                            if url_list:
                                video_url = url_list[0].replace('playwm', 'play')
                                
                                async with session.get(video_url, headers=self._get_headers()) as video_resp:
                                    if video_resp.status == 200:
                                        filename = os.path.join(self.download_path, f"tiktok_{video_id}.mp4")
                                        with open(filename, 'wb') as f:
                                            f.write(await video_resp.read())
                                        return filename
            return None
    
    async def _download_via_tikmate_fixed(self, url: str) -> str:
        """Исправленная версия для tikmate.cc с обходом блокировок"""
        async with aiohttp.ClientSession() as session:
            # Используем заголовки как у реального браузера
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://tikmate.cc',
                'Referer': 'https://tikmate.cc/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Сначала получаем cookies
            async with session.get('https://tikmate.cc/', headers=headers) as resp:
                html = await resp.text()
                
                # Пробуем найти токен в разных форматах
                token = None
                patterns = [
                    r'name="token"[^>]*value="([^"]+)"',
                    r'data-token="([^"]+)"',
                    r'id="token"[^>]*value="([^"]+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        token = match.group(1)
                        break
                
                # Если токен не найден, используем захардкоженный или генерируем
                if not token:
                    # Многие сайты принимают пустой токен
                    token = ''
                    print("⚠️ Токен не найден, пробуем без токена")
            
            # Отправляем запрос
            data = {'url': url, 'token': token}
            async with session.post('https://tikmate.cc/download/', data=data, headers=headers) as resp:
                html = await resp.text()
                
                # Ищем ссылку на скачивание в разных форматах
                patterns = [
                    r'href="([^"]+\.mp4[^"]*)"',
                    r'<a[^>]*download[^>]*href="([^"]+\.mp4[^"]*)"',
                    r'<source[^>]*src="([^"]+\.mp4[^"]*)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        video_url = match.group(1)
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        elif video_url.startswith('/'):
                            video_url = 'https://tikmate.cc' + video_url
                        
                        print(f"✅ Найдена ссылка через TikMate")
                        
                        async with session.get(video_url, headers=self._get_headers()) as video_resp:
                            if video_resp.status == 200:
                                filename = os.path.join(self.download_path, f"tiktok_{abs(hash(url))}.mp4")
                                with open(filename, 'wb') as f:
                                    f.write(await video_resp.read())
                                return filename
            return None