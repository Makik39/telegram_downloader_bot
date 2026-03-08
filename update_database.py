import sqlite3
import os

print("🔧 ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ")
print("=" * 50)

# Проверяем, существует ли файл базы данных
if not os.path.exists('bot_database.db'):
    print("❌ Файл базы данных не найден!")
    print("Сначала запустите бота, чтобы создать базу.")
    exit()

# Подключаемся к базе
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Смотрим текущую структуру
print("\n📊 ТЕКУЩАЯ СТРУКТУРА ТАБЛИЦЫ users:")

try:
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  • {col[1]} ({col[2]})")
except:
    print("  Таблица users не найдена")

# Добавляем недостающие колонки
print("\n🔧 ДОБАВЛЯЕМ НОВЫЕ КОЛОНКИ...")

try:
    # Добавляем колонку download_attempts
    cursor.execute("ALTER TABLE users ADD COLUMN download_attempts INTEGER DEFAULT 3")
    print("  ✅ Добавлена колонка: download_attempts")
except sqlite3.OperationalError:
    print("  ⚠️ Колонка download_attempts уже существует")

try:
    # Добавляем колонку total_attempts_earned
    cursor.execute("ALTER TABLE users ADD COLUMN total_attempts_earned INTEGER DEFAULT 3")
    print("  ✅ Добавлена колонка: total_attempts_earned")
except sqlite3.OperationalError:
    print("  ⚠️ Колонка total_attempts_earned уже существует")

try:
    # Добавляем колонку last_attempt_reset
    cursor.execute("ALTER TABLE users ADD COLUMN last_attempt_reset TEXT")
    print("  ✅ Добавлена колонка: last_attempt_reset")
except sqlite3.OperationalError:
    print("  ⚠️ Колонка last_attempt_reset уже существует")

# Создаем таблицу attempts_history, если её нет
print("\n📝 ПРОВЕРКА ТАБЛИЦЫ attempts_history...")

cursor.execute('''
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
print("  ✅ Таблица attempts_history создана или уже существует")

# Обновляем существующих пользователей (ставим им 3 попытки, если нет значения)
cursor.execute('''
    UPDATE users 
    SET download_attempts = 3, total_attempts_earned = 3 
    WHERE download_attempts IS NULL OR total_attempts_earned IS NULL
''')
print(f"  ✅ Обновлено {cursor.rowcount} пользователей")

# Сохраняем изменения
conn.commit()

print("\n📊 НОВАЯ СТРУКТУРА ТАБЛИЦЫ users:")

cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
for col in columns:
    print(f"  • {col[1]} ({col[2]})")

conn.close()

print("\n" + "=" * 50)
print("✅ База данных успешно обновлена!")
print("Теперь можно запускать бота: python bot.py")