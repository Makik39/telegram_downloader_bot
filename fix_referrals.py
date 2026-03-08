import sqlite3
from datetime import datetime

print("🔧 ИСПРАВЛЕНИЕ РЕФЕРАЛЬНОЙ СИСТЕМЫ")
print("=" * 50)

# Подключаемся к базе
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Смотрим всех пользователей у которых есть referred_by
cursor.execute('''
    SELECT user_id, referred_by FROM users 
    WHERE referred_by IS NOT NULL AND referred_by != 0
''')
users_with_ref = cursor.fetchall()

print(f"📊 Найдено пользователей с referred_by: {len(users_with_ref)}")

for user_id, referrer_id in users_with_ref:
    print(f"\n🔄 Проверяем: {referrer_id} -> {user_id}")
    
    # Проверяем, есть ли уже запись в referrals
    cursor.execute('''
        SELECT * FROM referrals WHERE referred_id = ?
    ''', (user_id,))
    
    if cursor.fetchone():
        print(f"   ✅ Запись уже существует")
    else:
        print(f"   ❌ Записи нет - добавляем...")
        
        # Добавляем запись в referrals
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, date, bonus_claimed)
            VALUES (?, ?, ?, ?)
        ''', (referrer_id, user_id, date, 1))
        
        # Начисляем бонусные попытки (5) пригласившему
        cursor.execute('''
            UPDATE users 
            SET download_attempts = download_attempts + 5,
                total_attempts_earned = total_attempts_earned + 5
            WHERE user_id = ?
        ''', (referrer_id,))
        
        print(f"   ✅ Добавлено! Пригласивший получил +5 попыток")

# Сохраняем изменения
conn.commit()

print("\n" + "=" * 50)
print("✅ Проверяем результат:")

# Проверяем таблицу referrals после исправления
cursor.execute('SELECT * FROM referrals')
refs = cursor.fetchall()
print(f"📊 Таблица referrals теперь содержит {len(refs)} записей:")

for ref in refs:
    print(f"   • {ref[1]} -> {ref[2]} (дата: {ref[3]})")

# Проверяем попытки пользователей
print("\n📊 Попытки пользователей:")
cursor.execute('SELECT user_id, first_name, download_attempts FROM users')
users = cursor.fetchall()
for user in users:
    print(f"   • {user[1]} (ID: {user[0]}): {user[2]} попыток")

conn.close()
print("\n✅ Исправление завершено!")