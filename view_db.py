import sqlite3
import os

print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 50)

# Проверяем, существует ли файл базы данных
if os.path.exists('bot_database.db'):
    print("✅ Файл базы данных найден!")
    file_size = os.path.getsize('bot_database.db')
    print(f"📁 Размер файла: {file_size} байт")
else:
    print("❌ Файл базы данных НЕ найден!")
    print("   Сначала запустите бота (python bot.py)")
    exit()

# Подключаемся к базе
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Смотрим все таблицы
print("\n📊 ТАБЛИЦЫ В БАЗЕ ДАННЫХ:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if tables:
    for table in tables:
        print(f"  📌 {table[0]}")
        
        # Считаем количество записей в каждой таблице
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"     Записей: {count}")
else:
    print("  ❌ Таблицы не найдены!")

# Смотрим пользователей
print("\n👥 ПОЛЬЗОВАТЕЛИ:")
cursor.execute("SELECT user_id, username, first_name, referred_by, total_downloads, join_date FROM users ORDER BY join_date DESC")
users = cursor.fetchall()

if users:
    for user in users:
        user_id, username, first_name, referred_by, downloads, join_date = user
        print(f"  🆔 ID: {user_id}")
        print(f"     Имя: {first_name}")
        print(f"     Username: @{username}")
        print(f"     Приглашен: {referred_by if referred_by else 'нет'}")
        print(f"     Скачиваний: {downloads}")
        print(f"     Дата: {join_date}")
        print("  " + "-" * 30)
else:
    print("  ❌ Пользователей пока нет")

# Смотрим рефералов
print("\n🔗 РЕФЕРАЛЬНЫЕ СВЯЗИ:")
cursor.execute("""
    SELECT r.referrer_id, u1.first_name, r.referred_id, u2.first_name, r.date 
    FROM referrals r
    LEFT JOIN users u1 ON r.referrer_id = u1.user_id
    LEFT JOIN users u2 ON r.referred_id = u2.user_id
    ORDER BY r.date DESC
""")
refs = cursor.fetchall()

if refs:
    for ref in refs:
        ref_id, ref_name, rec_id, rec_name, date = ref
        print(f"  👤 {ref_name or ref_id} пригласил {rec_name or rec_id}")
        print(f"     Дата: {date}")
        print("  " + "-" * 20)
else:
    print("  ❌ Реферальных связей пока нет")

# Топ рефереров
print("\n🏆 ТОП РЕФЕРЕРОВ:")
cursor.execute("""
    SELECT u.user_id, u.first_name, u.username, COUNT(r.id) as ref_count
    FROM users u
    LEFT JOIN referrals r ON u.user_id = r.referrer_id
    GROUP BY u.user_id
    ORDER BY ref_count DESC
    LIMIT 5
""")
top = cursor.fetchall()

if top:
    for i, (user_id, name, username, count) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        print(f"  {medal} {i}. {name} (@{username}) - {count} рефералов")
else:
    print("  ❌ Нет данных для топа")

conn.close()

print("\n" + "=" * 50)
print("✅ Проверка завершена!")