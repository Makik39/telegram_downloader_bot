import sqlite3

print("🔍 ПРОВЕРКА РЕФЕРАЛОВ")
print("=" * 40)

# Подключаемся к базе
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Проверяем таблицу referrals
print("\n📊 ТАБЛИЦА REFERRALS:")
cursor.execute("SELECT * FROM referrals")
refs = cursor.fetchall()
if refs:
    for ref in refs:
        print(f"   {ref}")
else:
    print("   ❌ Таблица пуста")

# Проверяем поле referred_by у пользователей
print("\n👥 ПОЛЬЗОВАТЕЛИ С referred_by:")
cursor.execute("SELECT user_id, first_name, referred_by FROM users WHERE referred_by IS NOT NULL")
users = cursor.fetchall()
if users:
    for user in users:
        print(f"   {user[0]} ({user[1]}) -> приглашен: {user[2]}")
else:
    print("   ❌ Нет пользователей с referred_by")

conn.close()
print("\n" + "=" * 40)