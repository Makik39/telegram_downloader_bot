import sqlite3
from datetime import datetime
import os

print("🔧 СРОЧНОЕ ИСПРАВЛЕНИЕ РЕФЕРАЛОВ")
print("=" * 50)

# Подключаемся к базе (сначала пробуем /data, потом локальную)
db_paths = ['/data/bot_database.db', 'bot_database.db']
conn = None

for path in db_paths:
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        print(f"✅ База найдена: {path}")
        break

if not conn:
    print("❌ База данных не найдена!")
    exit()

cursor = conn.cursor()

# 1. ПРОВЕРЯЕМ СТРУКТУРУ ТАБЛИЦ
print("\n📊 ПРОВЕРКА СТРУКТУРЫ:")

# Проверяем колонки в users
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Колонки в users: {columns}")

# Добавляем колонку referred_by если её нет
if 'referred_by' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
    print("✅ Добавлена колонка referred_by")

# 2. СОЗДАЁМ ТЕСТОВЫЕ ДАННЫЕ
print("\n🧪 СОЗДАЁМ ТЕСТОВЫЕ ДАННЫЕ:")

# Очищаем старые тестовые записи
cursor.execute("DELETE FROM users WHERE user_id IN (777777, 888888)")
cursor.execute("DELETE FROM referrals WHERE referrer_id=777777 OR referred_id=888888")

# Добавляем тестового приглашающего
date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name, join_date, download_attempts, total_attempts_earned)
    VALUES (?, ?, ?, ?, 3, 3)
''', (777777, 'test_inviter', 'Тест Пригл', date))

# Добавляем тестового приглашённого с referred_by
cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name, referred_by, join_date, download_attempts, total_attempts_earned)
    VALUES (?, ?, ?, ?, ?, 3, 3)
''', (888888, 'test_referral', 'Тест Реф', 777777, date))

print("✅ Тестовые пользователи добавлены")

# Добавляем запись в referrals
cursor.execute('''
    INSERT OR IGNORE INTO referrals (referrer_id, referred_id, date, bonus_amount)
    VALUES (?, ?, ?, 5)
''', (777777, 888888, date))

print("✅ Тестовая реферальная связь добавлена")

# 3. ПРОВЕРЯЕМ РЕЗУЛЬТАТ
print("\n📋 РЕЗУЛЬТАТ:")

cursor.execute("SELECT user_id, first_name, referred_by FROM users WHERE user_id IN (777777, 888888)")
for row in cursor.fetchall():
    print(f"   {row}")

cursor.execute("SELECT * FROM referrals")
for row in cursor.fetchall():
    print(f"   Реферал: {row}")

conn.commit()
conn.close()
print("\n✅ Исправление завершено!")