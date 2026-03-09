from database import Database
from datetime import datetime

db = Database()
cursor = db.conn.cursor()

# Общее количество
cursor.execute("SELECT COUNT(*) FROM users")
total = cursor.fetchone()[0]
print("=" * 40)
print(f"👥 Всего пользователей: {total}")
print("=" * 40)

# Список всех пользователей
print("\n📋 СПИСОК ПОЛЬЗОВАТЕЛЕЙ:")
cursor.execute("SELECT user_id, first_name, username, join_date FROM users ORDER BY join_date DESC")
for row in cursor.fetchall():
    print(f"  🆔 {row[0]} | {row[1]} | @{row[2]} | {row[3]}")