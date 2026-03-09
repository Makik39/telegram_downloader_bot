import sqlite3
import os

print("🔧 ФИКС БАЗЫ ДАННЫХ")
print("=" * 40)

# Копируем базу
src = '/app/bot_database.db'
dst = '/data/bot_database.db'

# Создаем папку если надо
os.makedirs('/data', exist_ok=True)

# Копируем
import shutil
shutil.copy2(src, dst)

# Проверяем
conn = sqlite3.connect(dst)
users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
print(f"✅ Пользователей в /data: {users}")

conn.close()