import sqlite3
from datetime import datetime
import config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                referred_by INTEGER,
                referral_link TEXT UNIQUE,
                join_date TEXT,
                download_attempts INTEGER DEFAULT 3,
                total_attempts_earned INTEGER DEFAULT 3
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER UNIQUE,
                date TEXT,
                bonus_amount INTEGER DEFAULT 5
            )
        ''')
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name, referred_by=None):
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        link = f"https://t.me/{config.BOT_USERNAME}?start={user_id}"
        self.cursor.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, username, first_name, referred_by, referral_link, join_date, download_attempts, total_attempts_earned) 
            VALUES (?, ?, ?, ?, ?, ?, 3, 3)
        ''', (user_id, username, first_name, referred_by, link, join_date))
        self.conn.commit()
        if referred_by and referred_by != user_id:
            self.add_referral(referred_by, user_id)
    
    def add_referral(self, referrer_id, referred_id):
        self.cursor.execute('SELECT * FROM referrals WHERE referred_id = ?', (referred_id,))
        if not self.cursor.fetchone():
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, date, bonus_amount)
                VALUES (?, ?, ?, 5)
            ''', (referrer_id, referred_id, date))
            self.cursor.execute('''
                UPDATE users SET download_attempts = download_attempts + 5,
                total_attempts_earned = total_attempts_earned + 5
                WHERE user_id = ?
            ''', (referrer_id,))
            self.conn.commit()
    
    def get_referral_count(self, user_id):
        self.cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
        return self.cursor.fetchone()[0]
    
    def get_referral_link(self, user_id):
        self.cursor.execute('SELECT referral_link FROM users WHERE user_id = ?', (user_id,))
        res = self.cursor.fetchone()
        return res[0] if res else None
    
    def get_referral_details(self, user_id):
        self.cursor.execute('''
            SELECT u.user_id, u.username, u.first_name, u.join_date, u.download_attempts, 5
            FROM referrals r JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_attempts(self, user_id):
        self.cursor.execute('SELECT download_attempts FROM users WHERE user_id = ?', (user_id,))
        res = self.cursor.fetchone()
        return res[0] if res else 0
    
    def use_attempt(self, user_id):
        self.cursor.execute('UPDATE users SET download_attempts = download_attempts - 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def add_attempts(self, user_id, amount, reason=""):
        self.cursor.execute('UPDATE users SET download_attempts = download_attempts + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()