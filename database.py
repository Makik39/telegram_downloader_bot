import sqlite3
import json
from datetime import datetime, timedelta
import config

class Database:
    def __init__(self, db_name='bot_database.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Таблица пользователей с попытками
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                referred_by INTEGER,
                referral_link TEXT UNIQUE,
                join_date TEXT,
                total_downloads INTEGER DEFAULT 0,
                tiktok_downloads INTEGER DEFAULT 0,
                youtube_downloads INTEGER DEFAULT 0,
                download_attempts INTEGER DEFAULT 3,
                total_attempts_earned INTEGER DEFAULT 3,
                last_attempt_reset TEXT
            )
        ''')
        
        # Таблица рефералов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER UNIQUE,
                date TEXT,
                bonus_claimed INTEGER DEFAULT 0,
                bonus_amount INTEGER DEFAULT 5,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица для подсчета переходов по ссылкам
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                click_date TEXT,
                ip TEXT,
                user_agent TEXT
            )
        ''')
        
        # Таблица для истории попыток
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attempts_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                change_amount INTEGER,
                reason TEXT,
                date TEXT,
                remaining_attempts INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()
        print("✅ Таблицы с системой попыток созданы")
    
    def add_user(self, user_id, username, first_name, referred_by=None):
        """Добавляет нового пользователя с начальными попытками"""
        try:
            join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            referral_link = f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
            
            # Проверяем, существует ли уже пользователь
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            existing_user = self.cursor.fetchone()
            
            if existing_user:
                print(f"⚠️ Пользователь {user_id} уже существует")
                return False
            
            # Добавляем нового пользователя
            self.cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, referred_by, referral_link, join_date, download_attempts, total_attempts_earned) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, referred_by, referral_link, join_date, 3, 3))
            
            self.conn.commit()
            print(f"✅ Добавлен новый пользователь: {user_id}, приглашен: {referred_by}")
            
            # Если пользователь пришел по рефералке, даем бонус пригласившему
            if referred_by and referred_by != user_id:
                print(f"🎯 Пользователь пришел по рефералке от {referred_by}")
                
                # Проверяем, существует ли пригласивший
                self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (referred_by,))
                if self.cursor.fetchone():
                    self.add_referral(referred_by, user_id)
                else:
                    print(f"⚠️ Пригласивший {referred_by} еще не зарегистрирован в базе")
            else:
                print("👤 Пользователь без рефералки")
                
            return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении пользователя: {e}")
            return False
    
    def add_referral(self, referrer_id, referred_id):
        """Добавляет запись о реферале и начисляет бонус"""
        try:
            print(f"🔄 Попытка добавить реферала: {referrer_id} -> {referred_id}")
            
            # Проверяем, существует ли пригласивший
            self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (referrer_id,))
            if not self.cursor.fetchone():
                print(f"❌ Пригласивший {referrer_id} не найден в базе")
                return False
            
            # Проверяем, не был ли уже этот пользователь чьим-то рефералом
            self.cursor.execute('''
                SELECT * FROM referrals WHERE referred_id = ?
            ''', (referred_id,))
            
            if self.cursor.fetchone():
                print(f"⚠️ Пользователь {referred_id} уже является чьим-то рефералом")
                return False
            
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            bonus_amount = 5  # 5 попыток за реферала
            
            self.cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, date, bonus_amount)
                VALUES (?, ?, ?, ?)
            ''', (referrer_id, referred_id, date, bonus_amount))
            
            self.conn.commit()
            print(f"✅ Реферал добавлен: {referrer_id} -> {referred_id}")
            
            # Начисляем бонусные попытки пригласившему
            self.add_attempts(referrer_id, bonus_amount, f"Реферал (ID: {referred_id})")
            
            return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении реферала: {e}")
            return False
    
    def add_attempts(self, user_id, amount, reason=""):
        """Добавляет попытки пользователю"""
        try:
            # Получаем текущие попытки
            self.cursor.execute('SELECT download_attempts, total_attempts_earned FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            
            if result:
                current_attempts, total_earned = result
                new_attempts = current_attempts + amount
                new_total_earned = total_earned + amount
                
                # Обновляем попытки
                self.cursor.execute('''
                    UPDATE users 
                    SET download_attempts = ?, total_attempts_earned = ?
                    WHERE user_id = ?
                ''', (new_attempts, new_total_earned, user_id))
                
                # Записываем в историю
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute('''
                    INSERT INTO attempts_history (user_id, change_amount, reason, date, remaining_attempts)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, amount, reason, date, new_attempts))
                
                self.conn.commit()
                return True
            return False
        except Exception as e:
            print(f"Ошибка при добавлении попыток: {e}")
            return False
    
    def use_attempt(self, user_id):
        """Использует одну попытку скачивания"""
        try:
            # Проверяем текущие попытки
            self.cursor.execute('SELECT download_attempts FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            
            if result and result[0] > 0:
                new_attempts = result[0] - 1
                
                # Обновляем попытки
                self.cursor.execute('''
                    UPDATE users SET download_attempts = ? WHERE user_id = ?
                ''', (new_attempts, user_id))
                
                # Записываем в историю
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute('''
                    INSERT INTO attempts_history (user_id, change_amount, reason, date, remaining_attempts)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, -1, "Скачивание видео", date, new_attempts))
                
                self.conn.commit()
                return True
            return False
        except Exception as e:
            print(f"Ошибка при использовании попытки: {e}")
            return False
    
    def get_attempts(self, user_id):
        """Получает количество оставшихся попыток"""
        try:
            self.cursor.execute('SELECT download_attempts FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка в get_attempts: {e}")
            return 0
    
    def get_total_earned_attempts(self, user_id):
        """Получает общее количество заработанных попыток"""
        try:
            self.cursor.execute('SELECT total_attempts_earned FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка в get_total_earned_attempts: {e}")
            return 0
    
    def get_referral_count(self, user_id):
        """Получает количество рефералов пользователя"""
        try:
            self.cursor.execute('''
                SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            count = result[0] if result else 0
            print(f"📊 get_referral_count для {user_id}: {count}")
            return count
        except Exception as e:
            print(f"❌ Ошибка в get_referral_count: {e}")
            return 0
    
    def get_referral_link(self, user_id):
        """Получает реферальную ссылку пользователя"""
        try:
            self.cursor.execute('''
                SELECT referral_link FROM users WHERE user_id = ?
            ''', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка в get_referral_link: {e}")
            return None
    
    def get_user_stats(self, user_id):
        """Получает статистику пользователя"""
        try:
            self.cursor.execute('''
                SELECT total_downloads, tiktok_downloads, youtube_downloads, download_attempts, total_attempts_earned 
                FROM users WHERE user_id = ?
            ''', (user_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Ошибка в get_user_stats: {e}")
            return None
    
    def update_download_stats(self, user_id, platform):
        """Обновляет статистику скачиваний"""
        try:
            self.cursor.execute(f'''
                UPDATE users 
                SET total_downloads = total_downloads + 1,
                    {platform}_downloads = {platform}_downloads + 1
                WHERE user_id = ?
            ''', (user_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка в update_download_stats: {e}")
    
    def get_top_referrers(self, limit=10):
        """Получает топ рефереров"""
        try:
            self.cursor.execute('''
                SELECT u.user_id, u.username, u.first_name, COUNT(r.id) as referral_count,
                       u.total_attempts_earned
                FROM users u
                LEFT JOIN referrals r ON u.user_id = r.referrer_id
                GROUP BY u.user_id
                ORDER BY referral_count DESC
                LIMIT ?
            ''', (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка в get_top_referrers: {e}")
            return []
    
    def get_referral_details(self, user_id):
        """Получает детальную информацию о рефералах"""
        try:
            print(f"🔍 БД: Запрос рефералов для пользователя {user_id}")
            
            # Сначала проверим, есть ли вообще рефералы в таблице
            self.cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
            count = self.cursor.fetchone()[0]
            print(f"      В таблице referrals найдено записей: {count}")
            
            if count == 0:
                return []
            
            # Получаем детальную информацию
            self.cursor.execute('''
                SELECT u.user_id, u.username, u.first_name, u.join_date, 
                       u.total_downloads as downloads, 
                       COALESCE(r.bonus_amount, 5) as bonus_amount
                FROM referrals r
                JOIN users u ON r.referred_id = u.user_id
                WHERE r.referrer_id = ?
                ORDER BY u.join_date DESC
            ''', (user_id,))
            
            result = self.cursor.fetchall()
            print(f"      Получено деталей: {len(result)}")
            
            # Выводим полученные данные
            for ref in result:
                print(f"         → {ref[2]} (ID: {ref[0]})")
            
            return result
        except Exception as e:
            print(f"❌ Ошибка в get_referral_details: {e}")
            return []
    
    def get_user_join_date(self, user_id):
        """Получает дату регистрации пользователя"""
        try:
            self.cursor.execute('SELECT join_date FROM users WHERE user_id = ?', (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "неизвестно"
        except Exception as e:
            print(f"Ошибка в get_user_join_date: {e}")
            return "неизвестно"
    
    def get_attempts_history(self, user_id, limit=10):
        """Получает историю изменений попыток"""
        try:
            self.cursor.execute('''
                SELECT change_amount, reason, date, remaining_attempts
                FROM attempts_history
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (user_id, limit))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка в get_attempts_history: {e}")
            return []