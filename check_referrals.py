import sqlite3
from database import Database

print("🔍 ПРОВЕРКА РЕФЕРАЛЬНОЙ СИСТЕМЫ")
print("=" * 50)

# Подключаемся к базе
db = Database()

# Проверяем всех пользователей
print("\n📋 ВСЕ ПОЛЬЗОВАТЕЛИ:")
cursor = db.conn.cursor()
cursor.execute("SELECT user_id, username, first_name, referred_by, referral_link FROM users")
users = cursor.fetchall()

if users:
    for user in users:
        user_id, username, name, referred_by, link = user
        print(f"\n🆔 ID: {user_id}")
        print(f"   Имя: {name}")
        print(f"   Username: @{username}")
        print(f"   Приглашен пользователем: {referred_by if referred_by else 'нет'}")
        print(f"   Реферальная ссылка: {link}")
        
        # Проверяем рефералов этого пользователя
        cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
        ref_count = cursor.fetchone()[0]
        print(f"   👥 Рефералов в таблице referrals: {ref_count}")
        
        # Проверяем через функцию
        func_count = db.get_referral_count(user_id)
        print(f"   📊 Рефералов через функцию: {func_count}")
else:
    print("❌ Пользователей нет в базе!")

# Проверяем таблицу referrals
print("\n🔗 ТАБЛИЦА REFERRALS:")
cursor.execute("SELECT * FROM referrals")
refs = cursor.fetchall()

if refs:
    for ref in refs:
        print(f"   ID: {ref[0]}, Пригласивший: {ref[1]}, Приглашенный: {ref[2]}, Дата: {ref[3]}, Бонус: {ref[4]}")
else:
    print("   ❌ Таблица referrals пуста!")

# Проверяем структуру таблиц
print("\n📊 СТРУКТУРА ТАБЛИЦЫ users:")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
for col in columns:
    print(f"   • {col[1]} ({col[2]})")

print("\n📊 СТРУКТУРА ТАБЛИЦЫ referrals:")
cursor.execute("PRAGMA table_info(referrals)")
columns = cursor.fetchall()
for col in columns:
    print(f"   • {col[1]} ({col[2]})")

db.conn.close()
print("\n" + "=" * 50)